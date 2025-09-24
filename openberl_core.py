"""
Project OpenBerl - Universal AI Model Adapter Protocol
Core components: UMF specification and base adapter interface
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json

@dataclass
class UMFRequest:
    """Universal Message Format for AI model requests"""
    task_type: str
    payload: Any
    context: List[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None
    routing: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = []
        if self.metadata is None:
            self.metadata = {}
        if self.routing is None:
            self.routing = {}

@dataclass
class UMFResponse:
    """Universal Message Format for AI model responses"""
    task_type: str
    result: Any
    metadata: Dict[str, Any] = None
    model_info: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.model_info is None:
            self.model_info = {}

class BaseAdapter(ABC):
    """Base class for all AI model adapters"""
    
    def __init__(self, model_name: str, api_key: str = None):
        self.model_name = model_name
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

class Pipeline:
    """Orchestrates multi-step AI workflows"""
    
    def __init__(self):
        self.steps = []
        self.adapters = {}
    
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
    
    async def execute(self, initial_payload: Any) -> Dict[str, UMFResponse]:
        """Execute the entire pipeline"""
        results = {}
        current_payload = initial_payload
        
        for step in self.steps:
            # Find appropriate adapter
            adapters = self.adapters.get(step['task_type'], [])
            if not adapters:
                raise ValueError(f"No adapter found for task type: {step['task_type']}")
            
            # Use first available adapter (can add routing logic later)
            adapter = adapters[0]
            
            # Create UMF request
            request = UMFRequest(
                task_type=step['task_type'],
                payload=current_payload,
                metadata=step['params']
            )
            
            # Execute step
            response = await adapter.execute(request)
            results[step['name']] = response
            
            # Pass result to next step
            current_payload = response.result
        
        return results

# Task type constants
class TaskTypes:
    CODE_GENERATION = "code_generation"
    CODE_OPTIMIZATION = "code_optimization"
    CODE_DEPLOYMENT = "code_deployment"
    TEXT_GENERATION = "text_generation"
    IMAGE_GENERATION = "image_generation"
    TEXT_TO_IMAGE = "text_to_image"
    ANALYSIS = "analysis"