"""
Project OpenBerl - Proof of Concept Demo
Demonstrates the code generation -> optimization pipeline
"""

import asyncio
import os
from openberl_core import Pipeline, UMFRequest, TaskTypes
from adapters.gpt4_adapter import GPT4Adapter
from adapters.mock_optimizer import MockOptimizerAdapter

async def main():
    """Run the proof of concept demo"""
    
    print("🚀 Project OpenBerl - Universal AI Adapter Demo")
    print("=" * 50)
    
    # Initialize adapters
    # Note: Replace with actual API key for real demo
    gpt4_adapter = GPT4Adapter(api_key=os.getenv("OPENAI_API_KEY", "mock-key"))
    optimizer_adapter = MockOptimizerAdapter()
    
    # Create pipeline
    pipeline = Pipeline()
    pipeline.register_adapter(gpt4_adapter)
    pipeline.register_adapter(optimizer_adapter)
    
    # Define the workflow
    pipeline.add_step("generate", TaskTypes.CODE_GENERATION, max_tokens=500, temperature=0.3)
    pipeline.add_step("optimize", TaskTypes.CODE_OPTIMIZATION)
    
    # User request
    user_prompt = "Create a Python function that fetches the top 5 Hacker News stories and returns their titles"
    
    print(f"📝 User Request: {user_prompt}")
    print("\n🔄 Processing Pipeline...")
    
    try:
        # Execute pipeline
        results = await pipeline.execute(user_prompt)
        
        print("\n✅ Pipeline Complete!")
        print("=" * 50)
        
        # Display results
        for step_name, response in results.items():
            print(f"\n📋 Step: {step_name.upper()}")
            print(f"Task Type: {response.task_type}")
            print(f"Model: {response.model_info.get('model', 'unknown')}")
            print(f"Provider: {response.model_info.get('provider', 'unknown')}")
            print("\n📄 Result:")
            print("-" * 30)
            print(response.result)
            print("-" * 30)
            
            if response.metadata:
                print(f"📊 Metadata: {response.metadata}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Note: This demo requires a valid OpenAI API key.")
        print("Set OPENAI_API_KEY environment variable to run with real GPT-4.")

def demo_umf_format():
    """Demonstrate the Universal Message Format"""
    
    print("\n🔧 Universal Message Format (UMF) Example:")
    print("=" * 50)
    
    # Create sample UMF request
    request = UMFRequest(
        task_type=TaskTypes.CODE_GENERATION,
        payload="Create a simple web scraper",
        metadata={"max_tokens": 500, "temperature": 0.7},
        routing={"preferred_models": ["gpt-4"], "fallback": True}
    )
    
    print("📨 Sample UMF Request:")
    print(f"  Task Type: {request.task_type}")
    print(f"  Payload: {request.payload}")
    print(f"  Metadata: {request.metadata}")
    print(f"  Routing: {request.routing}")
    
    print("\n🎯 Key Benefits:")
    print("  ✓ Standardized format across all AI models")
    print("  ✓ Model-agnostic request/response handling")
    print("  ✓ Built-in routing and fallback support")
    print("  ✓ Extensible metadata system")

if __name__ == "__main__":
    demo_umf_format()
    
    print("\n" + "=" * 50)
    print("🚀 Starting Pipeline Demo...")
    print("=" * 50)
    
    # Run the async demo
    asyncio.run(main())