"""
Mock Code Optimizer Adapter - Reference Implementation
Demonstrates how to build adapters for OpenBerl

This is a reference adapter showing the minimal implementation pattern.
Real adapters should follow this structure:
1. Inherit from AdapterRuntime
2. Implement all abstract methods
3. Handle input sanitization
4. Return proper UMFResponse format

Example Usage:
    # Basic usage
    optimizer = MockOptimizerAdapter()
    pipeline = Pipeline()
    pipeline.register_adapter(optimizer)
    pipeline.add_step("optimize", TaskTypes.CODE_OPTIMIZATION)
    
    # Execute
    result = await pipeline.execute("def hello(): print('world')")
    print(result["optimize"].result)  # Optimized code with comments
"""

import asyncio
from typing import Dict, Any, List
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openberl_core import AdapterRuntime, UMFRequest, UMFResponse, TaskTypes

class MockOptimizerAdapter(AdapterRuntime):
    """Reference adapter implementation for code optimization
    
    This demonstrates the minimal adapter pattern that all real adapters should follow:
    - Declare capabilities in get_capabilities()
    - Translate UMF requests to your API format
    - Sanitize inputs for security
    - Execute your service logic
    - Translate responses back to UMF format
    
    Real adapters should replace the mock logic with actual API calls.
    """
    
    def __init__(self):
        super().__init__("mock-optimizer", "demo-key")
    
    def get_capabilities(self) -> List[str]:
        """Declare what task types this adapter handles"""
        return [TaskTypes.CODE_OPTIMIZATION]
    
    def translate_request(self, umf_request: UMFRequest) -> Dict[str, Any]:
        """Convert UMF request to your service's API format"""
        return {"code": umf_request.payload}
    
    def translate_response(self, model_response: Any, original_request: UMFRequest) -> UMFResponse:
        """Convert your service's response back to UMF format"""
        return UMFResponse(
            task_type=original_request.task_type,
            result=model_response,
            request_id=original_request.request_id,
            cost_info={"estimated_cost": 0.0}  # Real adapters: calculate actual costs
        )
    
    async def _execute_request(self, umf_request: UMFRequest) -> UMFResponse:
        """Execute the actual service request - replace with real API calls"""
        
        # IMPORTANT: Always sanitize inputs for security
        code = str(umf_request.payload).replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')
        
        # Mock logic - real adapters: call your actual service API here
        optimized_code = f"""# Optimized version
{code}

# Performance improvements applied:
# - Removed unused imports
# - Added error handling
# - Optimized loops"""
        
        # Simulate processing time - real adapters: remove this
        await asyncio.sleep(0.1)
        
        return self.translate_response(optimized_code, umf_request)
    
    async def health_check(self) -> bool:
        """Check if your service is available - implement actual health check"""
        return True  # Real adapters: ping your service endpoint