"""
OpenBerl - Universal AI Adapter Framework
The missing layer that connects all AI models

Copyright (c) 2025 OpenBerl Foundation.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import time
import uuid
import asyncio
from enum import Enum

@dataclass
class UMFRequest:
    """Standard request format for AI adapters - v0 minimal"""
    task_type: str  # Required: adapter selection and routing
    payload: Any    # Required: the actual request content
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))  # Required: response linking
    context: List[Dict[str, Any]] = field(default_factory=list)  # Required: GPT4Adapter validation
    metadata: Dict[str, Any] = field(default_factory=dict)  # Required: adapter parameters (max_tokens, temperature)
    
    # TODO v1: Add back for advanced features
    # timestamp: float = field(default_factory=time.time)
    # routing: Dict[str, Any] = field(default_factory=dict)
    # priority: int = 0
    # timeout: float = 300.0

@dataclass
class UMFResponse:
    """Standard response format from AI adapters - v0 minimal"""
    task_type: str  # Required: pipeline step identification
    result: Any     # Required: the actual response content
    request_id: str = ""  # Required: links response to request
    cost_info: Dict[str, Any] = field(default_factory=dict)  # Required: pipeline cost tracking
    
    # TODO v1: Add back for monitoring and debugging
    # response_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    # timestamp: float = field(default_factory=time.time)
    # execution_time: float = 0.0
    # metadata: Dict[str, Any] = field(default_factory=dict)
    # model_info: Dict[str, Any] = field(default_factory=dict)

class AdapterInterface(ABC):
    """Pure interface for AI model adapters"""
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of task types this adapter can handle"""
        pass
    
    @abstractmethod
    def translate_request(self, umf_request: UMFRequest) -> Dict[str, Any]:
        """Convert UMF request to model-specific API call"""
        pass
    
    @abstractmethod
    def translate_response(self, model_response: Any, original_request: UMFRequest) -> UMFResponse:
        """Convert model response back to UMF format"""
        pass
    
    @abstractmethod
    async def _execute_request(self, umf_request: UMFRequest) -> UMFResponse:
        """Execute the actual model request - implement model-specific logic"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if adapter is healthy"""
        pass

class AdapterRuntime(AdapterInterface):
    """Shared runtime logic for all adapters"""
    
    def __init__(self, model_name: str, api_key: str = None, config: Dict[str, Any] = None):
        self.model_name = model_name
        self.config = config or {}
        self.request_count = 0
        
        # Secure credential handling
        if api_key and api_key not in ["demo-key", "test-key"]:
            if not isinstance(api_key, str) or len(api_key.strip()) == 0 or len(api_key.strip()) < 10:
                raise ValueError(f"Invalid API key format for {model_name}")
        self.api_key = api_key
    
    async def execute(self, umf_request: UMFRequest) -> UMFResponse:
        """Execute with timing and error wrapping"""
        self.request_count += 1
        
        try:
            response = await self._execute_request(umf_request)
            return response
        except Exception as e:
            # Wrap errors in standard format
            return UMFResponse(
                task_type=umf_request.task_type,
                result=f"Error: {str(e)}",
                request_id=umf_request.request_id,
                cost_info={"error": True, "estimated_cost": 0.0}
            )
    
    async def health_check(self) -> bool:
        """Default health check - override in subclasses for actual validation"""
        return True

# Backward compatibility alias
BaseAdapter = AdapterRuntime

class ExecutionMode(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"

class Pipeline:
    """AI adapter workflow orchestration"""
    
    def __init__(self, name: str = None, config: Dict[str, Any] = None):
        self.name = name or f"pipeline_{uuid.uuid4().hex[:8]}"
        self.config = config or {}
        self.steps = []
        self.adapters = {}
        self.cost_tracking = {"total_cost": 0.0, "cost_by_step": {}}
    
    def register_adapter(self, adapter: BaseAdapter):
        """Register an AI adapter for pipeline execution"""
        capabilities = adapter.get_capabilities()
        for capability in capabilities:
            if capability not in self.adapters:
                self.adapters[capability] = []
            # Prevent duplicate registration
            if adapter not in self.adapters[capability]:
                self.adapters[capability].append(adapter)
    
    def add_step(self, name: str, task_type: str, **kwargs):
        """Add a step to the pipeline"""
        self.steps.append({
            'name': name,
            'task_type': task_type,
            'params': kwargs
        })
        return self
    
    async def execute(self, initial_payload: Any, execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL) -> Dict[str, UMFResponse]:
        """Execute adapter pipeline with validation"""
        # Validate pipeline configuration before execution
        self._validate_pipeline_security()
        
        if execution_mode == ExecutionMode.PARALLEL:
            return await self._execute_parallel(initial_payload)
        else:
            return await self._execute_sequential(initial_payload)
    
    def _validate_pipeline_security(self):
        """Validate adapter pipeline configuration"""
        if not self.steps:
            raise ValueError("Pipeline has no steps configured")
        
        # Validate each step has authorized adapters
        for step in self.steps:
            task_type = step['task_type']
            if not isinstance(task_type, str) or not task_type.strip():
                raise ValueError(f"Invalid task type in step '{step['name']}': {task_type}")
            
            # Ensure task type is in our allowed list (server-side validation)
            allowed_task_types = {
                TaskTypes.CODE_GENERATION,
                TaskTypes.CODE_OPTIMIZATION, 
                TaskTypes.CODE_DEPLOYMENT,
                TaskTypes.TEXT_GENERATION,
                TaskTypes.IMAGE_GENERATION,
                TaskTypes.ANALYSIS
            }
            
            if task_type not in allowed_task_types:
                raise ValueError(f"Unauthorized task type: {task_type}")
    
    async def _execute_sequential(self, initial_payload: Any) -> Dict[str, UMFResponse]:
        """Execute steps sequentially"""
        results = {}
        current_payload = initial_payload
        
        for step in self.steps:
            adapter = self._select_adapter(step['task_type'])
            
            request = UMFRequest(
                task_type=step['task_type'],
                payload=current_payload,
                metadata=step['params']
            )
            
            response = await adapter.execute(request)
            
            # Track costs
            step_cost = response.cost_info.get("estimated_cost", 0.0)
            self.cost_tracking["total_cost"] += step_cost
            self.cost_tracking["cost_by_step"][step['name']] = step_cost
            
            results[step['name']] = response
            current_payload = response.result
        
        return results
    
    def _select_adapter(self, task_type: str) -> BaseAdapter:
        """Select optimal adapter for task type with validation"""
        # Adapter validation - ensure task type compatibility
        if not isinstance(task_type, str) or not task_type.strip():
            raise ValueError(f"Invalid task type: {task_type}")
        
        # Get registered adapters for this task type
        adapters = self.adapters.get(task_type, [])
        if not adapters:
            raise ValueError(f"No adapter found for task type: {task_type}")
        
        # Verify adapter capabilities match task requirements
        authorized_adapters = []
        for adapter in adapters:
            try:
                capabilities = adapter.get_capabilities()
                if task_type in capabilities:
                    authorized_adapters.append(adapter)
            except Exception:
                # Skip adapters that fail capability check
                continue
        
        if not authorized_adapters:
            raise ValueError(f"No authorized adapter found for task type: {task_type}")
        
        # Simple load balancing across available adapters
        return min(authorized_adapters, key=lambda a: a.request_count)
    
    async def _execute_parallel(self, initial_payload: Any) -> Dict[str, UMFResponse]:
        """Execute independent steps in parallel"""
        # For steps that don't depend on previous results, run in parallel
        # For now, identify independent steps and run them concurrently
        
        if len(self.steps) <= 1:
            return await self._execute_sequential(initial_payload)
        
        # Simple parallel execution: run all steps with same input concurrently
        # This works for analysis/processing tasks that don't chain
        tasks = []
        for step in self.steps:
            adapter = self._select_adapter(step['task_type'])
            request = UMFRequest(
                task_type=step['task_type'],
                payload=initial_payload,
                metadata=step['params'],
                priority=step.get('priority', 0)
            )
            tasks.append(self._execute_step(adapter, request, step['name']))
        
        # Execute all steps concurrently
        step_results = await asyncio.gather(*tasks)
        
        # Combine results
        results = {}
        for step_name, response in step_results:
            results[step_name] = response
            step_cost = response.cost_info.get("estimated_cost", 0.0)
            self.cost_tracking["total_cost"] += step_cost
            self.cost_tracking["cost_by_step"][step_name] = step_cost
        
        return results
    
    async def _execute_step(self, adapter: BaseAdapter, request: UMFRequest, step_name: str) -> tuple:
        """Execute a single step and return name, response tuple"""
        try:
            response = await adapter.execute(request)
            return step_name, response
        except Exception as e:
            # Create error response for failed step
            from openberl_core import UMFResponse
            error_response = UMFResponse(
                task_type=request.task_type,
                result=f"Error in step '{step_name}': {str(e)}",
                request_id=request.request_id,
                cost_info={"error": True, "error_message": str(e)}
            )
            return step_name, error_response
    
    def get_cost_analysis(self) -> Dict[str, Any]:
        """Get cost analysis"""
        return {
            "total_cost": self.cost_tracking["total_cost"],
            "cost_by_step": self.cost_tracking["cost_by_step"]
        }

class TaskTypes:
    CODE_GENERATION = "code_generation"
    CODE_OPTIMIZATION = "code_optimization"
    CODE_DEPLOYMENT = "code_deployment"
    TEXT_GENERATION = "text_generation"
    IMAGE_GENERATION = "image_generation"
    ANALYSIS = "analysis"
