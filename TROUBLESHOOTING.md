# OpenBerl Troubleshooting Guide

Common issues and solutions when using the AI Adapter Framework.

## 🚀 Quick Fixes

### "No adapter found for task type"

**Problem:** Pipeline can't find an adapter for your task.

```python
ValueError: No adapter found for task type: code_generation
```

**Solutions:**
1. **Register the adapter:**
   ```python
   pipeline.register_adapter(GPT4Adapter("your-key"))
   ```

2. **Check task type spelling:**
   ```python
   # Correct
   TaskTypes.CODE_GENERATION
   # Wrong
   "code-generation"
   ```

3. **Verify adapter capabilities:**
   ```python
   adapter = GPT4Adapter("your-key")
   print(adapter.get_capabilities())  # Should include your task type
   ```

### "Invalid API key format"

**Problem:** API key validation fails.

```python
ValueError: Invalid API key format for gpt-4
```

**Solutions:**
1. **Set environment variable:**
   ```bash
   export OPENAI_API_KEY="sk-your-actual-key-here"
   ```

2. **Check key format:**
   - OpenAI keys start with `sk-`
   - Anthropic keys start with `sk-ant-`
   - Keys should be 40+ characters

3. **For testing only:**
   ```python
   # Use demo mode (limited functionality)
   adapter = GPT4Adapter("demo-key")
   ```

### "Invalid context format"

**Problem:** Context data is malformed.

```python
ValueError: Invalid context format: {'content': 'test'}
```

**Solution:**
```python
# Correct context format
context = [
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "Previous message"}
]

request = UMFRequest(
    task_type=TaskTypes.TEXT_GENERATION,
    payload="Your request",
    context=context
)
```

## 🔧 Installation Issues

### "Module not found: openberl"

**Problem:** OpenBerl not installed or not in Python path.

**Solutions:**
1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Check Python path:**
   ```python
   import sys
   sys.path.append('/path/to/Project-OpenBerl')
   ```

3. **Use relative imports:**
   ```python
   from openberl_core import Pipeline, TaskTypes
   ```

### "aiohttp not found"

**Problem:** Missing async HTTP dependency.

**Solution:**
```bash
pip install aiohttp>=3.9.0
```

## ⚡ Performance Issues

### Slow Response Times

**Problem:** Requests taking too long.

**Diagnostics:**
```python
import time
start = time.time()
result = await pipeline.execute("test")
print(f"Took {time.time() - start:.2f}s")
```

**Solutions:**
1. **Enable caching:**
   ```python
   adapter = GPT4Adapter("key", config={"enable_caching": True})
   ```

2. **Use faster models:**
   ```python
   config = {"fallback_model": "gpt-3.5-turbo"}
   adapter = GPT4Adapter("key", config)
   ```

3. **Reduce token limits:**
   ```python
   pipeline.add_step("generate", TaskTypes.CODE_GENERATION, max_tokens=500)
   ```

### Memory Usage Growing

**Problem:** Memory increases over time.

**Solutions:**
1. **Limit cache size:**
   ```python
   # Cache is automatically limited to 1000 entries
   # No action needed - this is handled automatically
   ```

2. **Clear cache manually:**
   ```python
   adapter.response_cache.clear()
   ```

## 🌐 Network Issues

### "Request timeout"

**Problem:** API calls timing out.

**Solutions:**
1. **Increase timeout:**
   ```python
   request = UMFRequest(
       task_type=TaskTypes.CODE_GENERATION,
       payload="your request",
       timeout=600.0  # 10 minutes
   )
   ```

2. **Check network connectivity:**
   ```bash
   curl -I https://api.openai.com/v1/models
   ```

3. **Use retry logic:**
   ```python
   # Automatic retries are built-in
   # No additional configuration needed
   ```

### "Rate limit exceeded"

**Problem:** Too many requests to AI provider.

**Solutions:**
1. **Wait and retry:**
   ```python
   # Automatic exponential backoff is built-in
   # The adapter will handle rate limits automatically
   ```

2. **Use multiple API keys:**
   ```python
   # Register multiple adapters with different keys
   pipeline.register_adapter(GPT4Adapter("key1"))
   pipeline.register_adapter(GPT4Adapter("key2"))
   ```

## 🔨 Development Issues

### Custom Adapter Not Working

**Problem:** Your custom adapter isn't being called.

**Checklist:**
1. **Implement all required methods:**
   ```python
   class MyAdapter(BaseAdapter):
       def get_capabilities(self) -> List[str]:
           return ["my_task_type"]
       
       def translate_request(self, request): ...
       def translate_response(self, response, request): ...
       async def execute(self, request): ...
   ```

2. **Register the adapter:**
   ```python
   pipeline.register_adapter(MyAdapter())
   ```

3. **Use correct task type:**
   ```python
   # Must match what get_capabilities() returns
   pipeline.add_step("step1", "my_task_type")
   ```

### Pipeline Steps Not Chaining

**Problem:** Output from one step not reaching the next.

**Solution:**
```python
# Ensure each step returns result in UMFResponse.result
return UMFResponse(
    task_type=request.task_type,
    result="This becomes input to next step",
    request_id=request.request_id
)
```

## 📊 Debugging Tips

### Enable Verbose Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now you'll see detailed execution logs
result = await pipeline.execute("test")
```

### Inspect Adapter State

```python
# Check registered adapters
print("Registered adapters:", pipeline.adapters)

# Check adapter capabilities
for task_type, adapters in pipeline.adapters.items():
    print(f"{task_type}: {len(adapters)} adapters")

# Check request counts
for adapters in pipeline.adapters.values():
    for adapter in adapters:
        print(f"{adapter.model_name}: {adapter.request_count} requests")
```

### Test Individual Components

```python
# Test adapter directly
adapter = GPT4Adapter("your-key")
request = UMFRequest(task_type=TaskTypes.TEXT_GENERATION, payload="Hello")
response = await adapter.execute(request)
print(response.result)

# Test pipeline step by step
pipeline = Pipeline()
pipeline.register_adapter(adapter)
pipeline.add_step("test", TaskTypes.TEXT_GENERATION)
result = await pipeline.execute("Hello")
```

## 🆘 Still Need Help?

1. **Search existing issues:** [GitHub Issues](https://github.com/OPENBERL/Project-OpenBerl/issues)
2. **Ask the community:** [GitHub Discussions](https://github.com/OPENBERL/Project-OpenBerl/discussions)
3. **Report a bug:** Use our [bug report template](/.github/ISSUE_TEMPLATE/bug_report.md)
4. **Get support:** Use our [support template](/.github/ISSUE_TEMPLATE/support_question.md)

**When asking for help, include:**
- Your code (minimal example that reproduces the issue)
- Full error messages
- Environment details (Python version, OS, OpenBerl version)
- What you've already tried

---

*The OpenBerl adapter community is here to help. Don't hesitate to ask questions!*