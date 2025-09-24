"""
GPT-4 Adapter for OpenBerl
Production-ready implementation

Copyright (c) 2024 OpenBerl Foundation.
"""

import asyncio
import aiohttp
import time
import hashlib
from typing import Dict, Any, List
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openberl_core import BaseAdapter, UMFRequest, UMFResponse, TaskTypes

class GPT4Adapter(BaseAdapter):
    """GPT-4 Adapter with intelligent routing and cost optimization"""
    
    def __init__(self, api_key: str, config: Dict[str, Any] = None):
        config = config or {}
        super().__init__("gpt-4", api_key, config)
        self.base_url = "https://api.openai.com/v1"
        self.response_cache = {}
        self.cost_per_token = {"input": 0.00003, "output": 0.00006}
        self.fallback_model = config.get("fallback_model", "gpt-3.5-turbo")
        self.enable_caching = config.get("enable_caching", True)
    
    def get_capabilities(self) -> List[str]:
        return [
            TaskTypes.CODE_GENERATION,
            TaskTypes.TEXT_GENERATION,
            TaskTypes.ANALYSIS
        ]
    
    def translate_request(self, umf_request: UMFRequest) -> Dict[str, Any]:
        """Convert UMF request to OpenAI API format"""
        
        system_prompts = {
            TaskTypes.CODE_GENERATION: "You are an expert programmer. Generate clean, production-ready code with proper error handling and documentation.",
            TaskTypes.TEXT_GENERATION: "You are a skilled writer. Create clear, engaging, and accurate content.",
            TaskTypes.ANALYSIS: "You are an expert analyst. Provide comprehensive insights with actionable recommendations."
        }
        
        messages = [
            {"role": "system", "content": system_prompts.get(umf_request.task_type, "You are a helpful AI assistant.")}
        ]
        
        # Add context with validation
        for ctx in umf_request.context:
            if isinstance(ctx, dict) and "role" in ctx and "content" in ctx:
                messages.append(ctx)
            else:
                raise ValueError(f"Invalid context format: {ctx}")
        
        # Add user request
        messages.append({"role": "user", "content": str(umf_request.payload)})
        
        # Select model based on complexity
        model = self._select_model(umf_request)
        
        return {
            "model": model,
            "messages": messages,
            "max_tokens": umf_request.metadata.get("max_tokens", 1000),
            "temperature": umf_request.metadata.get("temperature", 0.7)
        }
    
    def _select_model(self, umf_request: UMFRequest) -> str:
        """Select optimal model based on task complexity"""
        payload_length = len(str(umf_request.payload))
        complexity_score = payload_length + len(umf_request.context) * 100
        
        # Use GPT-4 for complex tasks, fallback for simple ones
        if complexity_score > 1000 or umf_request.priority > 5:
            return "gpt-4"
        return self.fallback_model
    
    def translate_response(self, model_response: Dict[str, Any], original_request: UMFRequest) -> UMFResponse:
        """Convert OpenAI response to UMF format"""
        
        content = model_response["choices"][0]["message"]["content"]
        usage = model_response["usage"]
        
        # Calculate costs
        input_cost = usage["prompt_tokens"] * self.cost_per_token["input"]
        output_cost = usage["completion_tokens"] * self.cost_per_token["output"]
        total_cost = input_cost + output_cost
        
        return UMFResponse(
            task_type=original_request.task_type,
            result=content,
            request_id=original_request.request_id,
            execution_time=time.time() - original_request.timestamp,
            metadata={
                "tokens_used": usage["total_tokens"],
                "model": model_response["model"]
            },
            model_info={
                "provider": "openai",
                "model": self.model_name
            },
            cost_info={
                "estimated_cost": total_cost,
                "input_cost": input_cost,
                "output_cost": output_cost
            }
        )
    
    async def execute(self, umf_request: UMFRequest) -> UMFResponse:
        """Execute request with caching and retries"""
        
        # Validate API key before execution
        if not self.api_key or self.api_key == "demo-key":
            raise ValueError("Valid OpenAI API key required. Set OPENAI_API_KEY environment variable.")
        
        # Check cache
        if self.enable_caching:
            cache_key = self._generate_cache_key(umf_request)
            if cache_key in self.response_cache:
                return self.response_cache[cache_key]
        
        api_request = self.translate_request(umf_request)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Retry with exponential backoff
        for attempt in range(3):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}/chat/completions",
                        json=api_request,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=umf_request.timeout)
                    ) as response:
                        
                        if response.status == 200:
                            model_response = await response.json()
                            umf_response = self.translate_response(model_response, umf_request)
                            
                            # Cache response
                            if self.enable_caching:
                                self._cache_response(cache_key, umf_response)
                            
                            return umf_response
                        
                        elif response.status == 429 and attempt < 2:
                            await asyncio.sleep(2 ** attempt)
                            continue
                        
                        elif response.status >= 500 and attempt < 2:
                            await asyncio.sleep(2 ** attempt)
                            continue
                        
                        # Fallback to cheaper model
                        if api_request["model"] == "gpt-4":
                            api_request["model"] = self.fallback_model
                            continue
                        
                        error_text = await response.text()
                        raise Exception(f"OpenAI API error {response.status}: {error_text}")
            
            except asyncio.TimeoutError:
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise Exception("Request timeout")
        
        raise Exception("Max retries exceeded")
    
    def _generate_cache_key(self, umf_request: UMFRequest) -> str:
        """Generate cache key"""
        cache_data = f"{umf_request.task_type}:{umf_request.payload}:{umf_request.metadata}"
        return hashlib.md5(cache_data.encode()).hexdigest()
    
    def _cache_response(self, cache_key: str, response: UMFResponse):
        """Cache response"""
        if len(self.response_cache) >= 1000:
            # Remove oldest entry
            oldest_key = next(iter(self.response_cache))
            del self.response_cache[oldest_key]
        
        self.response_cache[cache_key] = response