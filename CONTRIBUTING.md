# Contributing to Project OpenBerl

Welcome to the future of AI interoperability! We're building the universal protocol that connects all AI models.

## Quick Start

1. **Fork the repo** and clone locally
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Run the demo**: `python demo.py`
4. **Pick an issue** labeled `good first issue`

## How to Add a New Adapter

The easiest way to contribute is by adding support for a new AI model:

```python
class YourModelAdapter(BaseAdapter):
    def get_capabilities(self) -> List[str]:
        return ["code_generation"]  # What can your model do?
    
    def translate_request(self, umf_request: UMFRequest) -> Dict[str, Any]:
        # Convert UMF to your model's API format
        return {"prompt": umf_request.payload}
    
    def translate_response(self, response: Any, request: UMFRequest) -> UMFResponse:
        # Convert back to UMF
        return UMFResponse(task_type=request.task_type, result=response["output"])
    
    async def execute(self, umf_request: UMFRequest) -> UMFResponse:
        # Make the API call
        api_request = self.translate_request(umf_request)
        # ... call your model's API
        return self.translate_response(api_response, umf_request)
```

## Adapter Ideas (Help Wanted!)

- **Claude Adapter** - Anthropic's Claude API
- **Llama Adapter** - Local Llama models via Ollama
- **Replicate Adapter** - Access hundreds of models
- **Hugging Face Adapter** - Open source models
- **AWS Bedrock Adapter** - Enterprise AI models
- **Code Deployment Adapter** - Deploy to Vercel/Netlify/AWS

## Code Standards

- **Minimal**: Write the least code that works
- **Async**: All adapters must be async
- **Error Handling**: Graceful failures with clear messages
- **Type Hints**: Use them everywhere
- **Tests**: Add tests for new adapters

## Pull Request Process

1. **One adapter per PR** - Keep it focused
2. **Add example usage** in your PR description
3. **Update README** if you add new task types
4. **Test with the demo** - make sure it works end-to-end

## Community

- **Be respectful** - We're building something bigger than any one company
- **Share knowledge** - Help others understand your adapter
- **Think universal** - How does this help the entire ecosystem?

## Questions?

Open an issue with the `question` label. We're here to help!

---

*Every adapter makes the platform more valuable. You're not just contributing code - you're building the bridge between all AI models.*