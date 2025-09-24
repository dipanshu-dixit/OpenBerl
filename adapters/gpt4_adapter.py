"""
Enterprise GPT-4 Adapter for Project OpenBerl
Production-ready implementation with enterprise features

Copyright (c) 2024 OpenBerl Foundation. All rights reserved.
"""

import asyncio
import aiohttp
import time
import hashlib
from typing import Dict, Any, List
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openberl_core import BaseAdapter, UMFRequest, UMFResponse, TaskTypes, AdapterStatus

class GPT4Adapter(BaseAdapter):
    """Enterprise GPT-4 Adapter with advanced capabilities
    
    Features:
    - Intelligent prompt optimization
    - Cost tracking and optimization
    - Response caching
    - Quality scoring
    - Automatic fallback to GPT-3.5
    """
    
    def __init__(self, api_key: str, config: Dict[str, Any] = None):
        config = config or {}
        super().__init__("gpt-4-enterprise", api_key, config)
        self.base_url = "https://api.openai.com/v1"
        self.response_cache = {}
        self.cost_per_token = {"input": 0.00003, "output": 0.00006}
        self.fallback_model = config.get("fallback_model", "gpt-3.5-turbo")
        self.enable_caching = config.get("enable_caching", True)
        self.max_cache_size = config.get("max_cache_size", 1000)
    
    def get_capabilities(self) -> List[str]:
        return [
            TaskTypes.CODE_GENERATION,
            TaskTypes.TEXT_GENERATION,
            TaskTypes.ANALYSIS
        ]
    
    def translate_request(self, umf_request: UMFRequest) -> Dict[str, Any]:
        """Convert UMF request to optimized OpenAI API format"""
        
        # Enterprise system prompts with performance optimization
        system_prompts = {
            TaskTypes.CODE_GENERATION: """You are an enterprise-grade code generation AI. Generate production-ready, secure, and optimized code.
            
Requirements:
            - Include comprehensive error handling
            - Add performance optimizations
            - Follow enterprise coding standards
            - Include security best practices
            - Add detailed documentation""",
            
            TaskTypes.TEXT_GENERATION: """You are an enterprise content generation AI. Create professional, high-quality content.
            
Requirements:
            - Maintain professional tone
            - Ensure factual accuracy
            - Optimize for target audience
            - Include relevant examples""",
            
            TaskTypes.ANALYSIS: """You are an enterprise data analysis AI. Provide comprehensive, actionable insights.
            
Requirements:
            - Include quantitative metrics
            - Provide actionable recommendations
            - Identify risks and opportunities
            - Support conclusions with evidence"""
        }
        
        messages = [
            {"role": "system", "content": system_prompts.get(umf_request.task_type, "You are an enterprise AI assistant.")}
        ]
        
        # Add context with intelligent truncation
        context_tokens = 0
        max_context_tokens = umf_request.metadata.get("max_context_tokens", 2000)
        
        for ctx in reversed(umf_request.context):
            ctx_content = str(ctx.get("content", ""))
            estimated_tokens = len(ctx_content.split()) * 1.3  # Rough token estimation
            
            if context_tokens + estimated_tokens <= max_context_tokens:
                messages.insert(-1, ctx)
                context_tokens += estimated_tokens
            else:
                break
        
        # Optimize payload for better results
        optimized_payload = self._optimize_prompt(str(umf_request.payload), umf_request.task_type)
        messages.append({"role": "user", "content": optimized_payload})
        
        # Dynamic model selection based on complexity
        model = self._select_optimal_model(umf_request)
        
        # Build optimized API request
        api_request = {
            "model": model,
            "messages": messages,
            "max_tokens": min(umf_request.metadata.get("max_tokens", 1000), 4000),
            "temperature": umf_request.metadata.get("temperature", 0.7),
            "top_p": umf_request.metadata.get("top_p", 1.0),
            "frequency_penalty": umf_request.metadata.get("frequency_penalty", 0.0),
            "presence_penalty": umf_request.metadata.get("presence_penalty", 0.0)
        }
        
        return api_request
    
    def _optimize_prompt(self, prompt: str, task_type: str) -> str:
        """Enterprise prompt optimization for better results"""
        
        optimization_templates = {
            TaskTypes.CODE_GENERATION: f"""Generate enterprise-grade code for the following requirement:
            
            {prompt}
            
            Requirements:
            - Production-ready with error handling
            - Include comprehensive comments
            - Follow security best practices
            - Optimize for performance
            - Include unit tests if applicable""",
            
            TaskTypes.ANALYSIS: f"""Provide comprehensive enterprise analysis for:
            
            {prompt}
            
            Include:
            - Executive summary
            - Key findings with metrics
            - Risk assessment
            - Actionable recommendations
            - Implementation roadmap"""
        }
        
        return optimization_templates.get(task_type, prompt)
    
    def _select_optimal_model(self, umf_request: UMFRequest) -> str:
        """Intelligent model selection based on request complexity"""
        
        payload_length = len(str(umf_request.payload))
        complexity_score = payload_length + len(umf_request.context) * 100
        
        # Use GPT-4 for complex tasks, GPT-3.5 for simple ones (cost optimization)
        if complexity_score > 1000 or umf_request.priority > 5:
            return "gpt-4"
        elif umf_request.metadata.get("force_gpt4", False):
            return "gpt-4"
        else:
            return self.fallback_model
    
    def translate_response(self, model_response: Dict[str, Any], original_request: UMFRequest) -> UMFResponse:
        """Convert OpenAI response to enterprise UMF format with analytics"""
        
        content = model_response["choices"][0]["message"]["content"]
        usage = model_response["usage"]
        
        # Calculate costs
        input_cost = usage["prompt_tokens"] * self.cost_per_token["input"]
        output_cost = usage["completion_tokens"] * self.cost_per_token["output"]
        total_cost = input_cost + output_cost
        
        # Quality scoring
        quality_score = self._calculate_quality_score(content, original_request)
        
        return UMFResponse(
            task_type=original_request.task_type,
            result=content,
            request_id=original_request.request_id,
            execution_time=time.time() - original_request.timestamp,
            metadata={
                "tokens_used": usage["total_tokens"],
                "prompt_tokens": usage["prompt_tokens"],
                "completion_tokens": usage["completion_tokens"],
                "model": model_response["model"],
                "finish_reason": model_response["choices"][0]["finish_reason"]
            },
            model_info={
                "provider": "openai",
                "model": self.model_name,
                "version": "enterprise-v1.0"
            },
            cost_info={
                "estimated_cost": total_cost,
                "input_cost": input_cost,
                "output_cost": output_cost,
                "cost_per_token": self.cost_per_token
            },
            quality_metrics={
                "confidence_score": quality_score,
                "response_length": len(content),
                "estimated_accuracy": min(quality_score * 1.2, 1.0)
            }
        )
    
    def _calculate_quality_score(self, content: str, request: UMFRequest) -> float:
        """Enterprise quality scoring algorithm"""
        
        score = 0.8  # Base score
        
        # Length-based scoring
        if len(content) > 100:
            score += 0.1
        
        # Task-specific quality indicators
        if request.task_type == TaskTypes.CODE_GENERATION:
            if "def " in content or "class " in content:
                score += 0.1
            if "try:" in content or "except" in content:
                score += 0.05  # Error handling bonus
        
        return min(score, 1.0)
    
    async def execute(self, umf_request: UMFRequest) -> UMFResponse:
        """Execute request with enterprise features: caching, retries, monitoring"""
        
        # Check cache first
        if self.enable_caching:
            cache_key = self._generate_cache_key(umf_request)
            if cache_key in self.response_cache:
                cached_response = self.response_cache[cache_key]
                self.logger.info(f"Cache hit for request {umf_request.request_id}")
                return cached_response
        
        api_request = self.translate_request(umf_request)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "OpenBerl-Enterprise/1.0"
        }
        
        # Retry logic with exponential backoff
        max_retries = umf_request.retry_config["max_retries"]
        backoff_factor = umf_request.retry_config["backoff_factor"]
        
        for attempt in range(max_retries + 1):
            try:
                timeout = aiohttp.ClientTimeout(total=umf_request.timeout)
                
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(
                        f"{self.base_url}/chat/completions",
                        json=api_request,
                        headers=headers
                    ) as response:
                        
                        if response.status == 200:
                            model_response = await response.json()
                            umf_response = self.translate_response(model_response, umf_request)
                            
                            # Cache successful response
                            if self.enable_caching:
                                self._cache_response(cache_key, umf_response)
                            
                            return umf_response
                        
                        elif response.status == 429:  # Rate limit
                            if attempt < max_retries:
                                wait_time = (backoff_factor ** attempt) * 2
                                self.logger.warning(f"Rate limited, waiting {wait_time}s")
                                await asyncio.sleep(wait_time)
                                continue
                        
                        elif response.status >= 500:  # Server error
                            if attempt < max_retries:
                                wait_time = backoff_factor ** attempt
                                self.logger.warning(f"Server error {response.status}, retrying in {wait_time}s")
                                await asyncio.sleep(wait_time)
                                continue
                        
                        # Fallback to GPT-3.5 for non-critical errors
                        if attempt == max_retries and api_request["model"] == "gpt-4":
                            self.logger.warning("Falling back to GPT-3.5")
                            api_request["model"] = self.fallback_model
                            continue
                        
                        error_text = await response.text()
                        raise Exception(f"OpenAI API error {response.status}: {error_text}")
            
            except asyncio.TimeoutError:
                if attempt < max_retries:
                    wait_time = backoff_factor ** attempt
                    self.logger.warning(f"Timeout, retrying in {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue
                raise Exception("Request timeout after all retries")
            
            except Exception as e:
                if attempt == max_retries:
                    raise
                
                wait_time = backoff_factor ** attempt
                self.logger.warning(f"Error: {e}, retrying in {wait_time}s")
                await asyncio.sleep(wait_time)
        
        raise Exception("Max retries exceeded")
    
    def _generate_cache_key(self, umf_request: UMFRequest) -> str:
        """Generate cache key for request"""
        cache_data = {
            "task_type": umf_request.task_type,
            "payload": str(umf_request.payload),
            "metadata": umf_request.metadata
        }
        return hashlib.md5(str(cache_data).encode()).hexdigest()
    
    def _cache_response(self, cache_key: str, response: UMFResponse):
        """Cache response with size management"""
        if len(self.response_cache) >= self.max_cache_size:
            # Remove oldest entry
            oldest_key = next(iter(self.response_cache))
            del self.response_cache[oldest_key]
        
        self.response_cache[cache_key] = response
    
    async def health_check(self) -> bool:
        """Check OpenAI API health"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/models",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status == 200
        
        except Exception:
            return False