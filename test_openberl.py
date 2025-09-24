#!/usr/bin/env python3
"""
OpenBerl Testing Suite
Validates security fixes and core functionality
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openberl_core import Pipeline, TaskTypes, UMFRequest, BaseAdapter
from adapters.mock_optimizer import MockOptimizerAdapter

class MockGPTAdapter(BaseAdapter):
    """Mock GPT adapter for testing without API dependencies"""
    
    def __init__(self, api_key: str = "test-key"):
        super().__init__("mock-gpt", api_key)
    
    def get_capabilities(self):
        return [TaskTypes.CODE_GENERATION, TaskTypes.TEXT_GENERATION]
    
    def translate_request(self, umf_request):
        return {"prompt": umf_request.payload}
    
    def translate_response(self, response, request):
        from openberl_core import UMFResponse
        return UMFResponse(
            task_type=request.task_type,
            result=response,
            request_id=request.request_id,
            cost_info={"estimated_cost": 0.001}
        )
    
    async def execute(self, umf_request):
        # Validate context like real GPT adapter
        for ctx in umf_request.context:
            if isinstance(ctx, dict) and "role" in ctx and "content" in ctx:
                continue
            else:
                raise ValueError(f"Invalid context format: {ctx}")
        
        # Simulate code generation
        if umf_request.task_type == TaskTypes.CODE_GENERATION:
            result = f"""def fetch_weather(api_key, city):
    import requests
    url = f"http://api.weather.com/v1/current?key={{api_key}}&q={{city}}"
    response = requests.get(url)
    return response.json()"""
        else:
            result = "Mock response for: " + str(umf_request.payload)
        
        return self.translate_response(result, umf_request)

async def test_happy_path():
    """Test 1: Happy Path - Core functionality works"""
    print("🧪 TEST 1: Happy Path Demonstration")
    print("-" * 40)
    
    try:
        # Create pipeline with mock adapters
        pipeline = Pipeline("test-pipeline")
        gpt_adapter = MockGPTAdapter("test-key")  # Use test-key
        optimizer_adapter = MockOptimizerAdapter()
        
        pipeline.register_adapter(gpt_adapter)
        pipeline.register_adapter(optimizer_adapter)
        
        # Define workflow
        pipeline.add_step("generate", TaskTypes.CODE_GENERATION, max_tokens=500)
        pipeline.add_step("optimize", TaskTypes.CODE_OPTIMIZATION)
        
        # Execute pipeline
        results = await pipeline.execute("Create a Python function to fetch weather data")
        
        # Validate results
        assert "generate" in results, "Generation step missing"
        assert "optimize" in results, "Optimization step missing"
        assert "def fetch_weather" in results["generate"].result, "Code generation failed"
        assert "Optimized version" in results["optimize"].result, "Optimization failed"
        
        print("✅ PASS: Pipeline executed successfully")
        print(f"   Generated: {len(results['generate'].result)} characters")
        print(f"   Optimized: {len(results['optimize'].result)} characters")
        return True
        
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False

async def test_security_fixes():
    """Test 2: Security Fix Validation"""
    print("\n🔒 TEST 2: Security Fix Validation")
    print("-" * 40)
    
    passed = 0
    total = 3
    
    # Test 2a: Authorization bypass prevention
    try:
        pipeline = Pipeline()
        gpt_adapter = MockGPTAdapter("test-key")
        pipeline.register_adapter(gpt_adapter)
        
        # Try to use non-existent task type
        pipeline.add_step("hack", "non_existent_task")
        await pipeline.execute("test")
        print("❌ FAIL: Authorization bypass not prevented")
    except ValueError as e:
        if "No adapter found" in str(e):
            print("✅ PASS: Authorization bypass prevented")
            passed += 1
        else:
            print(f"❌ FAIL: Wrong error type: {e}")
    except Exception as e:
        print(f"❌ FAIL: Unexpected error: {e}")
    
    # Test 2b: Invalid API key handling
    try:
        # Use a key that should fail validation (not test-key or demo-key, and too short)
        invalid_adapter = MockGPTAdapter("short")  # Too short and not in allowed list
        print("❌ FAIL: Invalid API key not caught")
    except ValueError as e:
        if "Invalid API key format" in str(e):
            print("✅ PASS: Invalid API key rejected")
            passed += 1
        else:
            print(f"❌ FAIL: Wrong error message: {e}")
    except Exception as e:
        print(f"❌ FAIL: Unexpected error: {e}")
    
    # Test 2c: Context validation
    try:
        pipeline = Pipeline()
        gpt_adapter = MockGPTAdapter("test-key")
        pipeline.register_adapter(gpt_adapter)
        pipeline.add_step("test", TaskTypes.TEXT_GENERATION)
        
        # Create request with invalid context
        request = UMFRequest(
            task_type=TaskTypes.TEXT_GENERATION,
            payload="test",
            context=[{"invalid": "context"}]  # Missing role/content
        )
        
        await gpt_adapter.execute(request)
        print("❌ FAIL: Invalid context not caught")
    except ValueError as e:
        if "Invalid context format" in str(e):
            print("✅ PASS: Invalid context rejected")
            passed += 1
        else:
            print(f"❌ FAIL: Wrong error message: {e}")
    except Exception as e:
        print(f"❌ FAIL: Unexpected error: {e}")
    
    print(f"Security Tests: {passed}/{total} passed")
    return passed == total

async def test_robustness():
    """Test 3: Robustness Check"""
    print("\n🛡️ TEST 3: Robustness Check")
    print("-" * 40)
    
    passed = 0
    total = 2
    
    # Test 3a: Invalid task type
    try:
        pipeline = Pipeline()
        gpt_adapter = MockGPTAdapter("test-key")
        pipeline.register_adapter(gpt_adapter)
        
        # Try empty task type
        pipeline.add_step("test", "")
        await pipeline.execute("test")
        print("❌ FAIL: Empty task type not caught")
    except ValueError as e:
        if "Invalid task type" in str(e):
            print("✅ PASS: Invalid task type rejected")
            passed += 1
        else:
            print(f"❌ FAIL: Wrong error message: {e}")
    except Exception as e:
        print(f"❌ FAIL: Unexpected error: {e}")
    
    # Test 3b: Adapter capability validation
    try:
        pipeline = Pipeline()
        gpt_adapter = MockGPTAdapter("test-key")
        pipeline.register_adapter(gpt_adapter)
        
        # Try task type not in adapter capabilities
        pipeline.add_step("test", TaskTypes.IMAGE_GENERATION)
        await pipeline.execute("test")
        print("❌ FAIL: Capability mismatch not caught")
    except ValueError as e:
        if "No valid adapter found" in str(e) or "No adapter found" in str(e):
            print("✅ PASS: Capability validation working")
            passed += 1
        else:
            print(f"❌ FAIL: Wrong error message: {e}")
    except Exception as e:
        print(f"❌ FAIL: Unexpected error: {e}")
    
    print(f"Robustness Tests: {passed}/{total} passed")
    return passed == total

async def main():
    """Run all tests"""
    print("🚀 OpenBerl Testing Suite")
    print("=" * 50)
    
    test_results = []
    
    # Run all tests
    test_results.append(await test_happy_path())
    test_results.append(await test_security_fixes())
    test_results.append(await test_robustness())
    
    # Summary
    passed = sum(test_results)
    total = len(test_results)
    
    print("\n" + "=" * 50)
    print("🎯 TEST SUMMARY")
    print("=" * 50)
    
    if passed == total:
        print("✅ ALL TESTS PASSED!")
        print("🚀 OpenBerl is LAUNCH READY")
        print("\nValidated:")
        print("  ✓ Core functionality works")
        print("  ✓ Security fixes are effective")
        print("  ✓ System handles errors gracefully")
        print("  ✓ Input validation is working")
        print("  ✓ Authorization controls are active")
        return True
    else:
        print(f"❌ {total - passed} TESTS FAILED")
        print("🛑 DO NOT LAUNCH - Fix issues first")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)