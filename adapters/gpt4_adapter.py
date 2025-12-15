"""
GPT-4 Adapter for OpenBerl - Demo Version
Simplified for readability and demo usage
"""

import asyncio
import aiohttp
from typing import Dict, Any, List
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openberl_core import AdapterRuntime, UMFRequest, UMFResponse, TaskTypes

class GPT4Adapter(AdapterRuntime):
    """Simple GPT-4 Adapter for demos"""
    
    def __init__(self, api_key: str, config: Dict[str, Any] = None):
        config = config or {}
        super().__init__("gpt-4", api_key, config)
        self.base_url = "https://api.openai.com/v1"
        self.enable_cost_tracking = config.get("enable_cost_tracking", False)
    
    def get_capabilities(self) -> List[str]:
        return [TaskTypes.CODE_GENERATION, TaskTypes.TEXT_GENERATION, TaskTypes.ANALYSIS]
    
    def translate_request(self, umf_request: UMFRequest) -> Dict[str, Any]:
        """Convert UMF request to OpenAI API format"""
        messages = [{"role": "system", "content": "You are a helpful AI assistant."}]
        
        # Add context
        for ctx in umf_request.context:
            if not (isinstance(ctx, dict) and "role" in ctx and "content" in ctx):
                raise ValueError(f"Invalid context format: {ctx}")
            messages.append(ctx)
        
        messages.append({"role": "user", "content": str(umf_request.payload)})
        
        return {
            "model": "gpt-3.5-turbo",  # Hardcoded for demo
            "messages": messages,
            "max_tokens": umf_request.metadata.get("max_tokens", 1000),
            "temperature": umf_request.metadata.get("temperature", 0.7)
        }
    

    
    def translate_response(self, model_response: Dict[str, Any], original_request: UMFRequest) -> UMFResponse:
        """Convert OpenAI response to UMF format"""
        content = model_response["choices"][0]["message"]["content"]
        
        cost_info = {}
        if self.enable_cost_tracking:
            usage = model_response["usage"]
            cost_info = {"estimated_cost": usage["total_tokens"] * 0.00002}  # Simplified cost
        
        return UMFResponse(
            task_type=original_request.task_type,
            result=content,
            request_id=original_request.request_id,
            cost_info=cost_info
        )
    
    async def _execute_request(self, umf_request: UMFRequest) -> UMFResponse:
        """Execute request with simple retry"""
        if not self.api_key or self.api_key == "demo-key":
            raise ValueError("Valid OpenAI API key required. Set OPENAI_API_KEY environment variable.")
        
        api_request = self.translate_request(umf_request)
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        
        # Simple retry (max 2 attempts)
        for attempt in range(2):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}/chat/completions",
                        json=api_request,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status == 200:
                            model_response = await response.json()
                            return self.translate_response(model_response, umf_request)
                        
                        if attempt == 0 and response.status in [429, 500, 502, 503]:
                            await asyncio.sleep(1)
                            continue
                        
                        error_text = await response.text()
                        raise Exception(f"API error {response.status}: {error_text}")
            except asyncio.TimeoutError:
                if attempt == 0:
                    continue
                raise Exception("Request timeout")
        
        raise Exception("Request failed after retry")
    
    async def health_check(self) -> bool:
        """Check if OpenAI API is accessible"""
        try:
            # Simple health check - could ping API
            return bool(self.api_key and self.api_key != "demo-key")
        except Exception:
            return False

