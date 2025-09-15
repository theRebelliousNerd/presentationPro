# CLAUDE.md - ADK/A2A Tools Directory

This directory contains tool implementations that agents use to interact with external services, databases, and perform specialized operations.

## Tool Architecture Principles

### Core Abstraction Layers

```
Agent Request
    ├─> Tool Interface (MCP Protocol)
    │   ├─> Parameter Validation
    │   ├─> Authentication
    │   └─> Rate Limiting
    │
    ├─> Tool Implementation
    │   ├─> Business Logic
    │   ├─> External Service Calls
    │   └─> Response Formatting
    │
    └─> Tool Registry
        ├─> Discovery Endpoint
        ├─> Capability Declaration
        └─> Version Management
```

## Available Tools

### 1. ArangoGraphRAG Tool (`arango_graph_rag_tool.py`)

**Purpose**: Graph-based retrieval augmented generation using ArangoDB

**Key Operations**:
```python
# Document ingestion
ingest_documents(documents: List[Dict], collection: str)

# Similarity search
search_similar(query: str, limit: int = 10)

# Graph traversal
traverse_graph(start_node: str, depth: int = 2)
```

**Configuration**:
```python
ARANGO_CONFIG = {
    "host": "arangodb",  # Docker service name
    "port": 8529,
    "database": "presentations",
    "username": "root",
    "password": os.getenv("ARANGO_PASSWORD", "password")
}
```

### 2. Web Search Tool (`web_search_tool.py`)

**Purpose**: Web search integration with fallback support

**Search Priority**:
1. Bing Search API (if API key available)
2. DuckDuckGo (fallback, no API key required)
3. Cache (if enabled)

**Implementation**:
```python
async def search(
    query: str,
    num_results: int = 10,
    use_cache: bool = True
) -> List[SearchResult]:
    # Check cache first
    if use_cache and query in cache:
        return cache[query]

    # Try Bing API
    if BING_API_KEY:
        results = await search_bing(query, num_results)
    else:
        # Fallback to DuckDuckGo
        results = await search_ddg(query, num_results)

    # Cache results
    if use_cache:
        cache[query] = results

    return results
```

### 3. Assets Ingest Tool (`assets_ingest_tool.py`)

**Purpose**: Process and extract content from uploaded files

**Supported Formats**:
- Documents: PDF, DOCX, TXT, MD
- Presentations: PPTX, KEY
- Images: PNG, JPG, GIF (with OCR)
- Data: CSV, JSON, XLSX

**Processing Pipeline**:
```python
def process_asset(file_path: str) -> ProcessedAsset:
    # 1. Detect file type
    file_type = detect_mime_type(file_path)

    # 2. Extract content
    if file_type == "application/pdf":
        content = extract_pdf_content(file_path)
    elif file_type.startswith("image/"):
        content = extract_image_text_ocr(file_path)
    # ... more formats

    # 3. Extract metadata
    metadata = extract_metadata(file_path)

    # 4. Generate embeddings
    embeddings = generate_embeddings(content)

    return ProcessedAsset(
        content=content,
        metadata=metadata,
        embeddings=embeddings
    )
```

### 4. Telemetry Tool (`telemetry_tool.py`)

**Purpose**: Track agent interactions, token usage, and performance metrics

**Metrics Tracked**:
```python
class TelemetryMetrics:
    # Token usage
    input_tokens: int
    output_tokens: int
    total_tokens: int

    # Performance
    latency_ms: float
    cache_hits: int
    cache_misses: int

    # Errors
    error_count: int
    error_types: List[str]

    # Agent metrics
    agent_calls: Dict[str, int]
    tool_calls: Dict[str, int]
```

**Usage Pattern**:
```python
with telemetry.track("operation_name") as tracker:
    # Perform operation
    result = await some_operation()
    tracker.record_tokens(input=100, output=50)
    return result
```

### 5. Vision Contrast Tool (`vision_contrast_tool.py`)

**Purpose**: Analyze and compare visual elements in images

**Capabilities**:
- Image comparison
- Style extraction
- Color palette analysis
- Layout detection
- Text extraction from images

## Tool Registration Process

### 1. Define Tool Specification

```python
# In tool implementation file
TOOL_SPEC = {
    "name": "my_new_tool",
    "description": "Tool purpose and capabilities",
    "version": "1.0.0",
    "parameters": {
        "type": "object",
        "properties": {
            "param1": {
                "type": "string",
                "description": "Parameter description"
            }
        },
        "required": ["param1"]
    },
    "returns": {
        "type": "object",
        "description": "Return value description"
    }
}
```

### 2. Implement Tool Class

```python
from typing import Any, Dict
from .base import BaseTool

class MyNewTool(BaseTool):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # Initialize tool-specific resources

    async def execute(self, **params) -> Dict[str, Any]:
        # Validate parameters
        self.validate_params(params)

        # Execute tool logic
        result = await self._perform_operation(params)

        # Format response
        return self.format_response(result)

    def cleanup(self):
        # Clean up resources
        pass
```

### 3. Register with Tool Registry

```python
# In tools/__init__.py
from .my_new_tool import MyNewTool

TOOL_REGISTRY = {
    "my_new_tool": MyNewTool,
    # ... other tools
}
```

## Error Handling Patterns

### Standard Error Response

```python
class ToolError(Exception):
    def __init__(
        self,
        message: str,
        error_code: str,
        details: Dict[str, Any] = None,
        retry_after: int = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.retry_after = retry_after

    def to_dict(self):
        return {
            "error": self.message,
            "code": self.error_code,
            "details": self.details,
            "retry_after": self.retry_after
        }
```

### Error Handling Strategy

```python
async def safe_tool_execution(tool_name: str, params: dict):
    try:
        tool = get_tool(tool_name)
        return await tool.execute(**params)

    except ValidationError as e:
        # Parameter validation failed
        return ToolError(
            message="Invalid parameters",
            error_code="INVALID_PARAMS",
            details={"validation_errors": e.errors()}
        )

    except ExternalServiceError as e:
        # External service failure
        return ToolError(
            message="External service unavailable",
            error_code="SERVICE_ERROR",
            details={"service": e.service_name},
            retry_after=30  # Retry after 30 seconds
        )

    except Exception as e:
        # Unexpected error
        logger.exception(f"Tool {tool_name} failed")
        return ToolError(
            message="Internal tool error",
            error_code="INTERNAL_ERROR"
        )
```

## Performance Considerations

### 1. Connection Pooling

```python
# Reuse connections for external services
class ConnectionPool:
    def __init__(self, max_connections: int = 10):
        self._pool = []
        self._max = max_connections

    async def get_connection(self):
        if self._pool:
            return self._pool.pop()
        return await create_new_connection()

    def return_connection(self, conn):
        if len(self._pool) < self._max:
            self._pool.append(conn)
        else:
            conn.close()
```

### 2. Caching Strategy

```python
from functools import lru_cache
from typing import Optional

class ToolCache:
    def __init__(self, ttl_seconds: int = 300):
        self.ttl = ttl_seconds
        self._cache = {}

    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            del self._cache[key]
        return None

    def set(self, key: str, value: Any):
        self._cache[key] = (value, time.time())
```

### 3. Async Best Practices

```python
# Use async for I/O operations
async def fetch_multiple_resources(urls: List[str]):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_url(session, url) for url in urls]
        return await asyncio.gather(*tasks)

# Batch operations when possible
async def batch_process(items: List[Any], batch_size: int = 10):
    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_results = await process_batch(batch)
        results.extend(batch_results)
    return results
```

## Tool Versioning Strategy

### Version Format

```
MAJOR.MINOR.PATCH

MAJOR: Breaking API changes
MINOR: New functionality, backward compatible
PATCH: Bug fixes, performance improvements
```

### Deprecation Process

```python
import warnings
from functools import wraps

def deprecated(version: str, alternative: str = None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            message = f"{func.__name__} is deprecated as of version {version}"
            if alternative:
                message += f". Use {alternative} instead"
            warnings.warn(message, DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Usage
@deprecated(version="2.0.0", alternative="new_method")
def old_method():
    pass
```

## Testing Tool Integrations

### Unit Testing

```python
import pytest
from unittest.mock import Mock, patch

@pytest.mark.asyncio
async def test_tool_execution():
    # Mock external dependencies
    with patch('tools.web_search_tool.search_bing') as mock_search:
        mock_search.return_value = [{"title": "Test", "url": "http://test.com"}]

        # Execute tool
        tool = WebSearchTool()
        results = await tool.execute(query="test")

        # Verify results
        assert len(results) == 1
        assert results[0]["title"] == "Test"
```

### Integration Testing

```python
@pytest.mark.integration
async def test_tool_with_real_service():
    # Test with actual external service
    tool = ArangoGraphRAGTool(test_config)

    # Ingest test document
    await tool.ingest_documents([
        {"id": "1", "content": "Test document"}
    ])

    # Search for document
    results = await tool.search_similar("test")
    assert len(results) > 0
```

## Adding New Tools

### Step-by-Step Guide

1. **Create tool file** in `tools/` directory:
   ```bash
   touch tools/my_new_tool.py
   ```

2. **Define tool interface**:
   ```python
   from typing import Any, Dict
   from .base import BaseTool

   class MyNewTool(BaseTool):
       SPEC = {...}  # Tool specification

       async def execute(self, **params) -> Dict[str, Any]:
           # Implementation
           pass
   ```

3. **Add configuration**:
   ```python
   # In shared/config.py
   MY_NEW_TOOL_CONFIG = {
       "api_key": os.getenv("MY_TOOL_API_KEY"),
       "endpoint": os.getenv("MY_TOOL_ENDPOINT", "https://api.example.com"),
       "timeout": 30
   }
   ```

4. **Register tool**:
   ```python
   # In tools/__init__.py
   from .my_new_tool import MyNewTool

   register_tool("my_new_tool", MyNewTool)
   ```

5. **Add tests**:
   ```python
   # In tests/tools/test_my_new_tool.py
   @pytest.mark.asyncio
   async def test_my_new_tool():
       tool = MyNewTool(test_config)
       result = await tool.execute(param1="value")
       assert result["status"] == "success"
   ```

6. **Update documentation**:
   - Add to this CLAUDE.md
   - Update API documentation
   - Add usage examples

## Security Considerations

### API Key Management

```python
# Never hardcode API keys
API_KEY = os.getenv("TOOL_API_KEY")
if not API_KEY:
    raise ValueError("TOOL_API_KEY environment variable not set")

# Validate API keys
def validate_api_key(key: str) -> bool:
    # Check format
    if not re.match(r"^[A-Za-z0-9-_]{32,}$", key):
        return False
    # Verify with service
    return verify_with_service(key)
```

### Input Sanitization

```python
def sanitize_tool_input(params: Dict[str, Any]) -> Dict[str, Any]:
    # Remove dangerous characters
    for key, value in params.items():
        if isinstance(value, str):
            # Prevent injection attacks
            value = value.replace("<script>", "")
            value = value.replace("javascript:", "")
            params[key] = value

    return params
```

### Rate Limiting

```python
from asyncio import Semaphore

class RateLimiter:
    def __init__(self, max_requests: int, time_window: int):
        self.semaphore = Semaphore(max_requests)
        self.time_window = time_window

    async def acquire(self):
        async with self.semaphore:
            # Perform rate-limited operation
            pass
```

## Troubleshooting

### Common Issues

1. **Tool not found**:
   ```python
   # Check registration
   python -c "from tools import TOOL_REGISTRY; print(TOOL_REGISTRY.keys())"
   ```

2. **External service timeout**:
   ```python
   # Increase timeout in config
   TOOL_CONFIG["timeout"] = 60  # 60 seconds
   ```

3. **Memory leaks**:
   ```python
   # Ensure proper cleanup
   try:
       tool = create_tool()
       result = await tool.execute()
   finally:
       tool.cleanup()
   ```

### Debug Mode

Enable tool debugging:
```bash
export TOOL_DEBUG=true
export TOOL_LOG_LEVEL=DEBUG

# This enables:
# - Detailed request/response logging
# - Performance metrics
# - Connection debugging
```

## Contact & Support

- **Tool Issues**: Create issue with `[TOOL]` prefix
- **New Tool Requests**: Submit design doc first
- **Performance Issues**: Include metrics from telemetry tool