"""
OpenBerl - Universal AI Protocol
The missing layer that connects all AI models

Copyright (c) 2024 OpenBerl Foundation.
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
    """Universal Message Format for AI model requests"""
    task_type: str
    payload: Any
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    context: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    routing: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    timeout: float = 300.0

@dataclass
class UMFResponse:
    """Universal Message Format for AI model responses"""
    task_type: str
    result: Any
    request_id: str = ""
    response_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    model_info: Dict[str, Any] = field(default_factory=dict)
    cost_info: Dict[str, Any] = field(default_factory=dict)

class BaseAdapter(ABC):
    """Base adapter interface for AI models"""
    
    def __init__(self, model_name: str, api_key: str = None, config: Dict[str, Any] = None):
        self.model_name = model_name
        self.config = config or {}
        self.request_count = 0
        
        # Secure credential handling
        if api_key and api_key != "demo-key":
            if not isinstance(api_key, str) or len(api_key.strip()) < 10:
                raise ValueError(f"Invalid API key format for {model_name}")
        self.api_key = api_key
    
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
    async def execute(self, umf_request: UMFRequest) -> UMFResponse:
        """Execute the request and return UMF response"""
        pass
    
    async def health_check(self) -> bool:
        """Check if adapter is healthy"""
        return True

class ExecutionMode(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"

class Pipeline:
    """AI workflow orchestration"""
    
    def __init__(self, name: str = None, config: Dict[str, Any] = None):
        self.name = name or f"pipeline_{uuid.uuid4().hex[:8]}"
        self.config = config or {}
        self.steps = []
        self.adapters = {}
        self.cost_tracking = {"total_cost": 0.0, "cost_by_step": {}}
    
    def register_adapter(self, adapter: BaseAdapter):
        """Register an adapter for use in pipelines"""
        capabilities = adapter.get_capabilities()
        for capability in capabilities:
            if capability not in self.adapters:
                self.adapters[capability] = []
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
        """Execute pipeline"""
        if execution_mode == ExecutionMode.PARALLEL:
            return await self._execute_parallel(initial_payload)
        else:
            return await self._execute_sequential(initial_payload)
    
    async def _execute_sequential(self, initial_payload: Any) -> Dict[str, UMFResponse]:
        """Execute steps sequentially"""
        results = {}
        current_payload = initial_payload
        
        for step in self.steps:
            adapter = self._select_adapter(step['task_type'])
            
            request = UMFRequest(
                task_type=step['task_type'],
                payload=current_payload,
                metadata=step['params'],
                priority=step.get('priority', 0)
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
        """Select best adapter for task type with validation"""
        # Validate task type is allowed
        if not isinstance(task_type, str) or not task_type.strip():
            raise ValueError(f"Invalid task type: {task_type}")
        
        adapters = self.adapters.get(task_type, [])
        if not adapters:
            raise ValueError(f"No adapter found for task type: {task_type}")
        
        # Validate all adapters support the requested task type
        valid_adapters = [a for a in adapters if task_type in a.get_capabilities()]
        if not valid_adapters:
            raise ValueError(f"No valid adapter found for task type: {task_type}")
        
        # Simple load balancing: use adapter with lowest request count
        return min(valid_adapters, key=lambda a: a.request_count)
    
    async def _execute_parallel(self, initial_payload: Any) -> Dict[str, UMFResponse]:
        """Execute steps in parallel where possible"""
        # For now, just execute sequentially
        # TODO: Implement true parallel execution
        return await self._execute_sequential(initial_payload)
    
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