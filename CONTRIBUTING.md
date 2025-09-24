# Contributing to OpenBerl

Welcome to the universal AI protocol. We're building the infrastructure layer that every AI application will use.

## Quick Start

1. **Fork and clone** the repository
2. **Install**: `pip install -r requirements.txt`
3. **Run demo**: `python demo.py`
4. **Build something**: Pick an adapter to implement

## Building Adapters

The most valuable contribution is adding support for new AI models:

```python
class YourModelAdapter(BaseAdapter):
    def get_capabilities(self) -> List[str]:
        return ["code_generation", "text_generation"]
    
    def translate_request(self, umf_request: UMFRequest) -> Dict[str, Any]:
        return {"prompt": umf_request.payload}
    
    def translate_response(self, response: Any, request: UMFRequest) -> UMFResponse:
        return UMFResponse(
            task_type=request.task_type,
            result=response["output"],
            request_id=request.request_id
        )
    
    async def execute(self, umf_request: UMFRequest) -> UMFResponse:
        api_request = self.translate_request(umf_request)
        # Your model API call here
        return self.translate_response(api_response, umf_request)
```

## High-Impact Adapters Needed

- **Claude** - Anthropic's reasoning models
- **Llama** - Local models via Ollama
- **Replicate** - Access to hundreds of models
- **Hugging Face** - Open source ecosystem
- **Gemini** - Google's multimodal AI
- **Deployment Services** - Vercel, Netlify, AWS Lambda

## Standards

- **Minimal** - Less code is better code
- **Async** - Everything is async/await
- **Clean** - No dead code, clear naming
- **Tested** - Include basic tests
- **Documented** - Clear docstrings

## Pull Requests

1. **One feature per PR**
2. **Include example usage**
3. **Test thoroughly**
4. **Update docs if needed**

## Community

- **Be helpful** - We're all building this together
- **Share knowledge** - Explain your approach
- **Think big** - This is infrastructure for everyone

## Questions?

Open an issue or start a discussion. The community is here to help.

---

*Every adapter makes OpenBerl more valuable. You're building the universal standard.*