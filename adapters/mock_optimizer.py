"""
Mock Code Optimizer Adapter for Project OpenBerl
Simulates a code optimization service for demonstration
"""

import asyncio
from typing import Dict, Any, List
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openberl_core import BaseAdapter, UMFRequest, UMFResponse, TaskTypes

class MockOptimizerAdapter(BaseAdapter):
    """Mock adapter that simulates code optimization"""
    
    def __init__(self):
        super().__init__("mock-optimizer", "demo-key")
    
    def get_capabilities(self) -> List[str]:
        return [TaskTypes.CODE_OPTIMIZATION]
    
    def translate_request(self, umf_request: UMFRequest) -> Dict[str, Any]:
        return {"code": umf_request.payload}
    
    def translate_response(self, model_response: Any, original_request: UMFRequest) -> UMFResponse:
        return UMFResponse(
            task_type=original_request.task_type,
            result=model_response,
            request_id=original_request.request_id,
            metadata={"optimizations_applied": ["removed_unused_imports", "improved_performance"]},
            model_info={"provider": "mock", "model": self.model_name},
            cost_info={"estimated_cost": 0.0}
        )
    
    async def execute(self, umf_request: UMFRequest) -> UMFResponse:
        """Simulate code optimization"""
        
        # Sanitize input to prevent XSS
        code = str(umf_request.payload).replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')
        
        # Simple mock optimization: add performance comments
        optimized_code = f"""# Optimized version
{code}

# Performance improvements applied:
# - Removed unused imports
# - Added error handling
# - Optimized loops"""
        
        # Simulate processing time
        await asyncio.sleep(0.1)
        
        return self.translate_response(optimized_code, umf_request)
    
    async def health_check(self) -> bool:
        """Mock optimizer is always healthy"""
        return True