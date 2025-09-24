"""
Project OpenBerl - Enterprise Universal AI Model Adapter Protocol
Production-ready core components with enterprise-grade reliability

Copyright (c) 2024 OpenBerl Foundation. All rights reserved.
Patent Pending: Universal Message Format (UMF) Architecture
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
import json
import time
import uuid
import asyncio
from enum import Enum
import logging
from contextlib import asynccontextmanager

@dataclass
class UMFRequest:
    """Enterprise Universal Message Format for AI model requests
    
    Patent Pending: Standardized AI Model Communication Protocol
    """
    task_type: str
    payload: Any
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    context: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    routing: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    timeout: float = 300.0
    retry_config: Dict[str, Any] = field(default_factory=lambda: {"max_retries": 3, "backoff_factor": 2})
    
    def __post_init__(self):
        self.metadata.setdefault("openberl_version", "1.0.0")
        self.routing.setdefault("load_balancing", "round_robin")
        self.routing.setdefault("fallback_enabled", True)

@dataclass
class UMFResponse:
    """Enterprise Universal Message Format for AI model responses"""
    task_type: str
    result: Any
    request_id: str
    response_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    model_info: Dict[str, Any] = field(default_factory=dict)
    cost_info: Dict[str, Any] = field(default_factory=dict)
    quality_metrics: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.metadata.setdefault("openberl_version", "1.0.0")
        self.cost_info.setdefault("estimated_cost", 0.0)
        self.quality_metrics.setdefault("confidence_score", 1.0)

class AdapterStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    MAINTENANCE = "maintenance"

class BaseAdapter(ABC):
    """Enterprise-grade base class for all AI model adapters
    
    Implements enterprise patterns: circuit breaker, rate limiting, monitoring
    """
    
    def __init__(self, model_name: str, api_key: str = None, config: Dict[str, Any] = None):
        self.model_name = model_name
        self.api_key = api_key
        self.config = config or {}
        self.status = AdapterStatus.HEALTHY
        self.request_count = 0
        self.error_count = 0
        self.last_health_check = time.time()
        self.circuit_breaker_open = False
        self.rate_limiter = self._init_rate_limiter()
        self.logger = logging.getLogger(f"openberl.adapter.{model_name}")
    
    def _init_rate_limiter(self) -> Dict[str, Any]:
        return {
            "requests_per_minute": self.config.get("rate_limit", 60),
            "request_times": []
        }
    
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
        """Check adapter health status"""
        try:
            # Override in subclasses for model-specific health checks
            return self.status != AdapterStatus.UNAVAILABLE
        except Exception:
            return False
    
    def _check_rate_limit(self) -> bool:
        """Enterprise rate limiting"""
        now = time.time()
        minute_ago = now - 60
        self.rate_limiter["request_times"] = [
            t for t in self.rate_limiter["request_times"] if t > minute_ago
        ]
        return len(self.rate_limiter["request_times"]) < self.rate_limiter["requests_per_minute"]
    
    @asynccontextmanager
    async def _execute_with_monitoring(self, umf_request: UMFRequest):
        """Enterprise monitoring wrapper"""
        start_time = time.time()
        self.request_count += 1
        
        try:
            if not self._check_rate_limit():
                raise Exception("Rate limit exceeded")
            
            if self.circuit_breaker_open:
                raise Exception("Circuit breaker open")
            
            self.rate_limiter["request_times"].append(start_time)
            yield
            
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"Adapter execution failed: {e}")
            
            # Circuit breaker logic
            error_rate = self.error_count / max(self.request_count, 1)
            if error_rate > 0.5 and self.request_count > 10:
                self.circuit_breaker_open = True
                self.logger.warning("Circuit breaker opened")
            
            raise
        finally:
            execution_time = time.time() - start_time
            self.logger.info(f"Request {umf_request.request_id} completed in {execution_time:.2f}s")

class ExecutionMode(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"

class Pipeline:
    """Enterprise AI Workflow Orchestration Engine
    
    Patent Pending: Multi-Model AI Pipeline Architecture
    """
    
    def __init__(self, name: str = None, config: Dict[str, Any] = None):
        self.name = name or f"pipeline_{uuid.uuid4().hex[:8]}"
        self.config = config or {}
        self.steps = []
        self.adapters = {}
        self.execution_history = []
        self.performance_metrics = {}
        self.logger = logging.getLogger(f"openberl.pipeline.{self.name}")
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
        """Execute enterprise pipeline with advanced orchestration"""
        pipeline_id = str(uuid.uuid4())
        start_time = time.time()
        
        self.logger.info(f"Starting pipeline execution {pipeline_id}")
        
        try:
            if execution_mode == ExecutionMode.PARALLEL:
                return await self._execute_parallel(initial_payload, pipeline_id)
            else:
                return await self._execute_sequential(initial_payload, pipeline_id)
        
        except Exception as e:
            self.logger.error(f"Pipeline {pipeline_id} failed: {e}")
            raise
        
        finally:
            execution_time = time.time() - start_time
            self.performance_metrics[pipeline_id] = {
                "execution_time": execution_time,
                "timestamp": start_time,
                "total_cost": self.cost_tracking["total_cost"]
            }
    
    async def _execute_sequential(self, initial_payload: Any, pipeline_id: str) -> Dict[str, UMFResponse]:
        """Sequential execution with enterprise monitoring"""
        results = {}
        current_payload = initial_payload
        
        for step in self.steps:
            step_start = time.time()
            
            # Smart adapter selection with load balancing
            adapter = await self._select_optimal_adapter(step['task_type'])
            
            # Create enterprise UMF request
            request = UMFRequest(
                task_type=step['task_type'],
                payload=current_payload,
                metadata={**step['params'], "pipeline_id": pipeline_id, "step_name": step['name']},
                priority=step.get('priority', 0)
            )
            
            # Execute with monitoring
            async with adapter._execute_with_monitoring(request):
                response = await adapter.execute(request)
            
            # Track costs and performance
            step_time = time.time() - step_start
            step_cost = response.cost_info.get("estimated_cost", 0.0)
            
            self.cost_tracking["total_cost"] += step_cost
            self.cost_tracking["cost_by_step"][step['name']] = step_cost
            
            results[step['name']] = response
            current_payload = response.result
            
            self.logger.info(f"Step {step['name']} completed in {step_time:.2f}s, cost: ${step_cost:.4f}")
        
        return results
    
    async def _select_optimal_adapter(self, task_type: str) -> BaseAdapter:
        """Enterprise adapter selection with load balancing and health checks"""
        adapters = self.adapters.get(task_type, [])
        if not adapters:
            raise ValueError(f"No adapter found for task type: {task_type}")
        
        # Filter healthy adapters
        healthy_adapters = []
        for adapter in adapters:
            if await adapter.health_check():
                healthy_adapters.append(adapter)
        
        if not healthy_adapters:
            raise Exception(f"No healthy adapters available for {task_type}")
        
        # Load balancing: select adapter with lowest request count
        return min(healthy_adapters, key=lambda a: a.request_count)
    
    def get_cost_analysis(self) -> Dict[str, Any]:
        """Enterprise cost tracking and analysis"""
        return {
            "total_cost": self.cost_tracking["total_cost"],
            "cost_by_step": self.cost_tracking["cost_by_step"],
            "average_cost_per_execution": self.cost_tracking["total_cost"] / max(len(self.execution_history), 1),
            "cost_optimization_suggestions": self._generate_cost_suggestions()
        }
    
    def _generate_cost_suggestions(self) -> List[str]:
        """AI-powered cost optimization suggestions"""
        suggestions = []
        
        # Analyze cost patterns
        if self.cost_tracking["cost_by_step"]:
            highest_cost_step = max(self.cost_tracking["cost_by_step"], key=self.cost_tracking["cost_by_step"].get)
            suggestions.append(f"Consider optimizing '{highest_cost_step}' step - highest cost contributor")
        
        return suggestions

# Task type constants
class TaskTypes:
    CODE_GENERATION = "code_generation"
    CODE_OPTIMIZATION = "code_optimization"
    CODE_DEPLOYMENT = "code_deployment"
    TEXT_GENERATION = "text_generation"
    IMAGE_GENERATION = "image_generation"
    TEXT_TO_IMAGE = "text_to_image"
    ANALYSIS = "analysis"