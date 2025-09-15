# MCP Server for PresentationPro Tools

A production-ready Model Context Protocol (MCP) server that exposes all PresentationPro ADK tools through a standardized interface.

## Features

- **Complete Tool Suite**: Exposes all ADK tools (ArangoRAG, WebSearch, Vision, Telemetry, Assets)
- **Multiple Transports**: Supports stdio, HTTP, and streamable HTTP transports
- **Production Ready**: Includes health checks, logging, rate limiting, and telemetry
- **Docker Support**: Fully containerized with Docker and docker-compose
- **Type Safety**: Full Pydantic schemas for request/response validation
- **Extensible**: Easy to add new tools through the registry system

## Available Tools

### 1. ArangoRAG Tools
- `arango_rag_ingest`: Ingest documents into ArangoDB for retrieval
- `arango_rag_retrieve`: Retrieve relevant chunks using BM25 search

### 2. Web Search
- `web_search`: Search the web using Bing API or DuckDuckGo fallback

### 3. Vision Analysis
- `vision_analyze`: Analyze images for contrast and visibility

### 4. Telemetry
- `telemetry_record`: Record usage telemetry events
- `telemetry_aggregate`: Get aggregated telemetry statistics

### 5. Assets Processing
- `assets_ingest`: Process and ingest uploaded files (PDF, DOCX, TXT, etc.)

### 6. Composite Tools
- `research_topic`: Research using both web search and RAG
- `process_presentation_assets`: Complete asset processing pipeline

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Start the MCP server with ArangoDB
docker compose up -d

# View logs
docker compose logs -f mcp-server

# Stop services
docker compose down
```

### Using Python Directly

```bash
# Install dependencies
pip install -r requirements.txt

# Run in streamable HTTP mode (default)
python -m mcp_server.server

# Run in stdio mode (for MCP clients)
python -m mcp_server.server --transport stdio

# Run in HTTP mode with custom port
python -m mcp_server.server --transport http --port 8091
```

### Using as MCP Server with Claude Desktop

```bash
# Install the server
uv run mcp install mcp_server/server.py --name "PresentationPro Tools"

# Or with environment variables
uv run mcp install mcp_server/server.py \
  --name "PresentationPro Tools" \
  -v GOOGLE_GENAI_API_KEY=your_key \
  -v BING_SEARCH_API_KEY=your_key
```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# API Keys
GOOGLE_GENAI_API_KEY=your_google_api_key
BING_SEARCH_API_KEY=your_bing_api_key  # Optional, falls back to DuckDuckGo

# Database
ARANGO_HOST=localhost
ARANGO_PORT=8529
ARANGO_DATABASE=presentationpro
ARANGO_USERNAME=  # Optional
ARANGO_PASSWORD=  # Optional

# Server
HOST=0.0.0.0
PORT=8090
LOG_LEVEL=INFO

# Telemetry
MCP_TELEMETRY_SINK=/tmp/mcp_telemetry.jsonl
TELEMETRY_ENABLED=true

# Cache
WEB_SEARCH_CACHE=/tmp/web_search_cache.json
CACHE_TTL=3600

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Authentication (Optional)
AUTH_ENABLED=false
MCP_AUTH_TOKEN=your_secret_token
```

## API Endpoints

### Health Check
```http
GET /health
```

### List Tools
```http
POST /tools/list
Content-Type: application/json

{
  "category": "search",  // Optional filter
  "includeDeprecated": false
}
```

### Call Tool
```http
POST /tools/call
Content-Type: application/json

{
  "name": "web_search",
  "arguments": {
    "query": "AI presentation tools",
    "top_k": 5
  }
}
```

### MCP Protocol Endpoint
```http
POST /mcp
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}
```

### Streaming Endpoint
```http
GET /mcp/stream
Accept: text/event-stream
```

## Tool Examples

### Web Search
```python
# Using the MCP client
result = await session.call_tool("web_search", {
    "query": "latest AI trends 2024",
    "top_k": 10,
    "allow_domains": ["arxiv.org", "openai.com"]
})
```

### Document Ingestion
```python
result = await session.call_tool("arango_rag_ingest", {
    "presentationId": "pres_123",
    "assets": [
        {
            "name": "research.pdf",
            "path": "/uploads/research.pdf",
            "kind": "document"
        }
    ]
})
```

### Vision Analysis
```python
result = await session.call_tool("vision_analyze", {
    "screenshotDataUrl": "data:image/png;base64,..."
})
```

### Composite Research
```python
result = await session.call_tool("research_topic", {
    "topic": "sustainable energy",
    "presentationId": "pres_123",
    "search_limit": 10,
    "retrieve_limit": 5
})
```

## Development

### Running Tests
```bash
pytest tests/ -v --cov=mcp_server
```

### Type Checking
```bash
mypy mcp_server --strict
```

### Adding New Tools

1. Create a wrapper class in `tool_wrappers.py`:
```python
class MyToolWrapper(BaseToolWrapper):
    def _initialize_tool(self):
        self.tool = MyActualTool()

    def my_method(self, **kwargs):
        return self.tool.execute(**kwargs)
```

2. Register in the server's `_register_tools()` method:
```python
my_wrapper = MyToolWrapper()
self.registry.register_tool("my_tool", my_wrapper)
```

3. Add MCP decorator in `_register_mcp_tools()`:
```python
@self.mcp.tool()
async def my_tool(**kwargs):
    wrapper = self.registry.get_tool("my_tool")
    return await wrapper.execute("my_method", kwargs)
```

## Architecture

```
mcp_server/
├── server.py           # Main MCP server implementation
├── tool_registry.py    # Tool registration and management
├── tool_wrappers.py    # Wrapper classes for each tool
├── schemas.py          # MCP protocol schemas
├── config.py           # Configuration management
├── Dockerfile          # Container configuration
├── requirements.txt    # Python dependencies
└── docker-compose.yml  # Multi-container setup
```

### Design Principles

1. **Separation of Concerns**: Tools, registry, and server are separate modules
2. **Type Safety**: All inputs/outputs validated with Pydantic
3. **Error Handling**: Comprehensive error handling at every level
4. **Async First**: Full async/await support throughout
5. **Extensibility**: Easy to add new tools without modifying core
6. **Production Ready**: Includes logging, monitoring, and health checks

## Monitoring

### Telemetry
Telemetry events are automatically recorded to the configured sink file. View aggregated statistics:

```bash
curl -X POST http://localhost:8090/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "telemetry_aggregate", "arguments": {}}'
```

### Logs
Logs are written to both stdout and the configured log file. In Docker:

```bash
docker compose logs -f mcp-server
```

### Health Check
```bash
curl http://localhost:8090/health
```

## Security

### Authentication (Optional)
Enable authentication by setting:
```env
AUTH_ENABLED=true
MCP_AUTH_TOKEN=your_secret_token
```

Then include the token in requests:
```http
Authorization: Bearer your_secret_token
```

### Rate Limiting
Configured via environment variables:
- `RATE_LIMIT_REQUESTS`: Max requests per window
- `RATE_LIMIT_WINDOW`: Window size in seconds

### CORS
Configure allowed origins:
```env
CORS_ORIGINS=["https://app.example.com", "http://localhost:3000"]
```

## Troubleshooting

### Common Issues

1. **ArangoDB Connection Failed**
   - Ensure ArangoDB is running: `docker compose ps`
   - Check connection settings in `.env`

2. **Tool Not Found**
   - Verify tool is registered in `server.py`
   - Check logs for registration errors

3. **Rate Limit Exceeded**
   - Adjust `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW`
   - Or disable: `RATE_LIMIT_ENABLED=false`

4. **Memory Issues**
   - Adjust Docker memory limits in `docker-compose.yml`
   - Reduce cache sizes and TTLs

## License

Part of the PresentationPro project. See main project LICENSE.

## Support

For issues or questions, please open an issue in the main PresentationPro repository.