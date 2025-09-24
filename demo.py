"""
OpenBerl - Universal AI Protocol Demo
See the future of AI model interoperability

Copyright (c) 2024 OpenBerl Foundation.
"""

import asyncio
import os
import time
from datetime import datetime
from openberl_core import Pipeline, TaskTypes
from adapters.gpt4_adapter import GPT4Adapter
from adapters.mock_optimizer import MockOptimizerAdapter

async def main():
    """Demonstrate OpenBerl's universal AI protocol"""
    
    print("🌐 OpenBerl - Universal AI Protocol")
    print("=" * 50)
    print(f"Started: {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 50)
    
    # Initialize adapters
    gpt4_adapter = GPT4Adapter(
        api_key=os.getenv("OPENAI_API_KEY", "demo-key"),
        config={"enable_caching": True, "fallback_model": "gpt-3.5-turbo"}
    )
    optimizer_adapter = MockOptimizerAdapter()
    
    # Create pipeline
    pipeline = Pipeline("demo-pipeline")
    pipeline.register_adapter(gpt4_adapter)
    pipeline.register_adapter(optimizer_adapter)
    
    # Define workflow
    pipeline.add_step("generate", TaskTypes.CODE_GENERATION, max_tokens=800, temperature=0.3)
    pipeline.add_step("optimize", TaskTypes.CODE_OPTIMIZATION)
    
    # Demo requests
    requests = [
        "Create a Python function to fetch weather data from an API",
        "Build a simple web scraper for news headlines",
        "Write a REST API endpoint for user authentication"
    ]
    
    print("🚀 Processing requests through universal protocol...")
    print("-" * 50)
    
    for i, request in enumerate(requests, 1):
        print(f"\n📋 Request {i}: {request}")
        
        try:
            start_time = time.perf_counter()
            
            # Execute through universal protocol
            results = await pipeline.execute(request)
            
            execution_time = time.perf_counter() - start_time
            
            print(f"✅ Completed in {execution_time:.2f}s")
            
            # Show results
            for step_name, response in results.items():
                print(f"\n📊 {step_name.upper()}:")
                print(f"   Model: {response.model_info.get('model', 'unknown')}")
                print(f"   Cost: ${response.cost_info.get('estimated_cost', 0):.6f}")
                print(f"   Tokens: {response.metadata.get('tokens_used', 0)}")
                
                # Preview result
                result_preview = str(response.result)[:150] + "..." if len(str(response.result)) > 150 else str(response.result)
                print(f"   Result: {result_preview}")
        
        except Exception as e:
            print(f"❌ Error: {e}")
            if "demo-key" in str(e) or "API key" in str(e):
                print("💡 Set OPENAI_API_KEY environment variable for full demo")
    
    # Show cost analysis
    try:
        cost_analysis = pipeline.get_cost_analysis()
        print(f"\n💰 Total Cost: ${cost_analysis['total_cost']:.6f}")
    except Exception as e:
        print(f"\n💰 Cost analysis unavailable: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 OpenBerl Benefits Demonstrated:")
    print("  ✓ Universal protocol works with any AI model")
    print("  ✓ Automatic cost optimization and caching")
    print("  ✓ Seamless model chaining and orchestration")
    print("  ✓ Production-ready with error handling")
    print("  ✓ Vendor-agnostic - switch models without code changes")
    
    print(f"\n🌐 Learn more: https://github.com/OPENBERL/Project-OpenBerl")

if __name__ == "__main__":
    asyncio.run(main())