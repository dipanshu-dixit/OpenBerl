"""
GPT-4 Adapter for Project OpenBerl
Demonstrates how to implement the BaseAdapter interface
"""

import asyncio
import aiohttp
from typing import Dict, Any, List
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openberl_core import BaseAdapter, UMFRequest, UMFResponse, TaskTypes

class GPT4Adapter(BaseAdapter):
    """Adapter for OpenAI GPT-4 API"""
    
    def __init__(self, api_key: str):
        super().__init__("gpt-4", api_key)
        self.base_url = "https://api.openai.com/v1"
    
    def get_capabilities(self) -> List[str]:
        return [
            TaskTypes.CODE_GENERATION,
            TaskTypes.TEXT_GENERATION,
            TaskTypes.ANALYSIS
        ]
    
    def translate_request(self, umf_request: UMFRequest) -> Dict[str, Any]:
        """Convert UMF request to OpenAI API format"""
        
        # Build system prompt based on task type
        system_prompts = {
            TaskTypes.CODE_GENERATION: "You are an expert programmer. Generate clean, working code based on the user's request.",
            TaskTypes.TEXT_GENERATION: "You are a helpful assistant that generates high-quality text.",
            TaskTypes.ANALYSIS: "You are an expert analyst. Provide detailed, accurate analysis."
        }
        
        messages = [
            {"role": "system", "content": system_prompts.get(umf_request.task_type, "You are a helpful assistant.")}
        ]
        
        # Add context if provided
        for ctx in umf_request.context:
            messages.append(ctx)
        
        # Add current request
        messages.append({"role": "user", "content": str(umf_request.payload)})
        
        # Build API request
        api_request = {
            "model": "gpt-4",
            "messages": messages,
            "max_tokens": umf_request.metadata.get("max_tokens", 1000),
            "temperature": umf_request.metadata.get("temperature", 0.7)
        }
        
        return api_request
    
    def translate_response(self, model_response: Dict[str, Any], original_request: UMFRequest) -> UMFResponse:
        """Convert OpenAI response to UMF format"""
        
        content = model_response["choices"][0]["message"]["content"]
        
        return UMFResponse(
            task_type=original_request.task_type,
            result=content,
            metadata={
                "tokens_used": model_response["usage"]["total_tokens"],
                "model": model_response["model"]
            },
            model_info={
                "provider": "openai",
                "model": self.model_name
            }
        )
    
    async def execute(self, umf_request: UMFRequest) -> UMFResponse:
        """Execute request against OpenAI API"""
        
        api_request = self.translate_request(umf_request)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                json=api_request,
                headers=headers
            ) as response:
                if response.status != 200:
                    raise Exception(f"OpenAI API error: {response.status}")
                
                model_response = await response.json()
                return self.translate_response(model_response, umf_request)