# CLAUDE.md - MCP Server Implementation Directory

This directory contains the Model Context Protocol (MCP) server implementation that exposes tools to agents and external clients through a standardized protocol interface.

## MCP Server Architecture

The MCP server provides a standardized interface for tool discovery, invocation, and management:

```
MCP Server
    ├─> Protocol Handler
    │   ├─> JSON-RPC 2.0 Processing
    │   ├─> Request Validation
    │   ├─> Method Routing
    │   └─> Response Formatting
    │
    ├─> Tool Registry
    │   ├─> Tool Discovery
    │   ├─> Capability Declaration
    │   ├─> Parameter Schemas
    │   └─> Version Management
    │
    ├─> Execution Engine
    │   ├─> Tool Invocation
    │   ├─> Parameter Binding
    │   ├─> Error Handling
    │   └─> Result Transformation
    │
    └─> Transport Layer
        ├─> WebSocket Support
        ├─> HTTP/REST Adapter
        ├─> gRPC Interface
        └─> IPC Communication
```

## Core MCP Protocol Implementation (`server.py`)

### Server Initialization

```python
from typing import Dict, Any, List, Optional
import asyncio
import json
from dataclasses import dataclass
from enum import Enum

class MCPServer:
    """Model Context Protocol server implementation"""

    def __init__(self, config: MCPConfig):
        self.config = config
        self.tools = {}
        self.sessions = {}
        self.handlers = self._initialize_handlers()

    def _initialize_handlers(self) -> Dict[str, Callable]:
        """Initialize JSON-RPC method handlers"""
        return {
            # Discovery methods
            "tools/list": self.handle_list_tools,
            "tools/get": self.handle_get_tool,

            # Invocation methods
            "tools/call": self.handle_call_tool,
            "tools/call_batch": self.handle_batch_call,

            # Session management
            "session/create": self.handle_create_session,
            "session/destroy": self.handle_destroy_session,

            # Meta methods
            "rpc.discover": self.handle_discover,
            "system.listMethods": self.handle_list_methods,
        }

    async def start(self):
        """Start MCP server"""
        # Initialize transport layers
        await self._start_websocket_server()
        await self._start_http_server()

        # Register tools
        await self._register_tools()

        # Start health monitoring
        asyncio.create_task(self._monitor_health())

        logger.info(f"MCP Server started on {self.config.host}:{self.config.port}")

    async def handle_request(self, request: str) -> str:
        """Process JSON-RPC request"""
        try:
            # Parse request
            data = json.loads(request)

            # Validate JSON-RPC format
            if "jsonrpc" not in data or data["jsonrpc"] != "2.0":
                return self._error_response(
                    id=data.get("id"),
                    code=-32600,
                    message="Invalid Request"
                )

            # Route to handler
            method = data.get("method")
            if method not in self.handlers:
                return self._error_response(
                    id=data.get("id"),
                    code=-32601,
                    message="Method not found"
                )

            # Execute handler
            handler = self.handlers[method]
            result = await handler(data.get("params", {}))

            # Format response
            return self._success_response(
                id=data.get("id"),
                result=result
            )

        except json.JSONDecodeError:
            return self._error_response(
                id=None,
                code=-32700,
                message="Parse error"
            )
        except Exception as e:
            logger.error(f"Request handling failed: {e}")
            return self._error_response(
                id=data.get("id") if "data" in locals() else None,
                code=-32603,
                message="Internal error"
            )
```

## Tool Discovery Protocol

### Tool Registration and Discovery

```python
class ToolRegistry:
    """Manage tool registration and discovery"""

    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {}
        self.categories: Dict[str, List[str]] = defaultdict(list)
        self.versions: Dict[str, Dict[str, ToolDefinition]] = defaultdict(dict)

    def register_tool(self, tool: ToolDefinition):
        """Register a tool with the MCP server"""

        # Validate tool definition
        self._validate_tool_definition(tool)

        # Register in main registry
        self.tools[tool.name] = tool

        # Index by category
        for category in tool.categories:
            self.categories[category].append(tool.name)

        # Track versions
        self.versions[tool.name][tool.version] = tool

        logger.info(f"Registered tool: {tool.name} v{tool.version}")

    def discover_tools(
        self,
        category: Optional[str] = None,
        capability: Optional[str] = None,
        version: Optional[str] = None
    ) -> List[ToolDefinition]:
        """Discover tools matching criteria"""

        tools = list(self.tools.values())

        # Filter by category
        if category:
            tools = [
                t for t in tools
                if category in t.categories
            ]

        # Filter by capability
        if capability:
            tools = [
                t for t in tools
                if capability in t.capabilities
            ]

        # Filter by version
        if version:
            tools = [
                t for t in tools
                if self._match_version(t.version, version)
            ]

        return tools

    def get_tool_schema(self, tool_name: str) -> Dict[str, Any]:
        """Get OpenAPI/JSON Schema for tool"""

        tool = self.tools.get(tool_name)
        if not tool:
            raise ToolNotFoundError(tool_name)

        return {
            "openapi": "3.0.0",
            "info": {
                "title": tool.name,
                "version": tool.version,
                "description": tool.description
            },
            "paths": {
                f"/tools/{tool.name}": {
                    "post": {
                        "summary": tool.description,
                        "operationId": tool.name,
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": tool.input_schema
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Success",
                                "content": {
                                    "application/json": {
                                        "schema": tool.output_schema
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
```

### Tool Definition Format

```python
@dataclass
class ToolDefinition:
    """Standard tool definition for MCP"""

    # Basic metadata
    name: str
    version: str
    description: str
    author: str

    # Categorization
    categories: List[str]
    capabilities: List[str]
    tags: List[str]

    # Schema definitions
    input_schema: Dict[str, Any]  # JSON Schema
    output_schema: Dict[str, Any]  # JSON Schema

    # Execution metadata
    async_execution: bool = False
    timeout_seconds: int = 30
    rate_limit: Optional[RateLimit] = None

    # Requirements
    required_permissions: List[str] = field(default_factory=list)
    required_resources: List[str] = field(default_factory=list)

    # Deprecation info
    deprecated: bool = False
    deprecation_message: Optional[str] = None
    replacement_tool: Optional[str] = None

    def to_mcp_format(self) -> Dict[str, Any]:
        """Convert to MCP wire format"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "inputSchema": self.input_schema,
            "outputSchema": self.output_schema,
            "metadata": {
                "categories": self.categories,
                "capabilities": self.capabilities,
                "async": self.async_execution,
                "timeout": self.timeout_seconds,
                "deprecated": self.deprecated
            }
        }
```

## Request/Response Handling

### JSON-RPC Message Processing

```python
class JSONRPCProcessor:
    """Process JSON-RPC 2.0 messages"""

    @staticmethod
    def parse_request(raw_request: str) -> RPCRequest:
        """Parse and validate JSON-RPC request"""

        try:
            data = json.loads(raw_request)
        except json.JSONDecodeError as e:
            raise ParseError(f"Invalid JSON: {e}")

        # Validate required fields
        if "jsonrpc" not in data or data["jsonrpc"] != "2.0":
            raise InvalidRequest("Missing or invalid jsonrpc field")

        if "method" not in data:
            raise InvalidRequest("Missing method field")

        return RPCRequest(
            jsonrpc=data["jsonrpc"],
            method=data["method"],
            params=data.get("params"),
            id=data.get("id")
        )

    @staticmethod
    def format_response(
        result: Any = None,
        error: Optional[RPCError] = None,
        id: Optional[Union[str, int]] = None
    ) -> str:
        """Format JSON-RPC response"""

        response = {
            "jsonrpc": "2.0",
            "id": id
        }

        if error:
            response["error"] = {
                "code": error.code,
                "message": error.message,
                "data": error.data
            }
        else:
            response["result"] = result

        return json.dumps(response)

    @staticmethod
    def format_batch_response(responses: List[Dict]) -> str:
        """Format batch response"""
        return json.dumps(responses)
```

### Tool Invocation Handler

```python
class ToolInvocationHandler:
    """Handle tool invocation requests"""

    def __init__(self, registry: ToolRegistry):
        self.registry = registry
        self.executor = ToolExecutor()

    async def invoke_tool(
        self,
        tool_name: str,
        params: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Invoke a tool with parameters"""

        # Get tool definition
        tool = self.registry.tools.get(tool_name)
        if not tool:
            raise ToolNotFoundError(f"Tool '{tool_name}' not found")

        # Check deprecation
        if tool.deprecated:
            logger.warning(
                f"Tool '{tool_name}' is deprecated: {tool.deprecation_message}"
            )

        # Validate parameters
        self._validate_parameters(params, tool.input_schema)

        # Check permissions
        if session_id:
            session = self.get_session(session_id)
            self._check_permissions(session, tool.required_permissions)

        # Apply rate limiting
        if tool.rate_limit:
            await self._apply_rate_limit(tool_name, session_id, tool.rate_limit)

        # Execute tool
        try:
            if tool.async_execution:
                # Async execution returns task ID
                task_id = await self.executor.execute_async(
                    tool_name=tool_name,
                    params=params,
                    timeout=tool.timeout_seconds
                )
                return {
                    "task_id": task_id,
                    "status": "running",
                    "check_url": f"/tasks/{task_id}"
                }
            else:
                # Synchronous execution
                result = await self.executor.execute(
                    tool_name=tool_name,
                    params=params,
                    timeout=tool.timeout_seconds
                )

                # Validate output
                self._validate_output(result, tool.output_schema)

                return result

        except TimeoutError:
            raise ToolExecutionError(
                f"Tool '{tool_name}' execution timed out after {tool.timeout_seconds}s"
            )
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            raise ToolExecutionError(f"Tool execution failed: {str(e)}")

    def _validate_parameters(
        self,
        params: Dict[str, Any],
        schema: Dict[str, Any]
    ):
        """Validate parameters against JSON Schema"""

        try:
            jsonschema.validate(params, schema)
        except jsonschema.ValidationError as e:
            raise InvalidParametersError(
                f"Parameter validation failed: {e.message}"
            )

    def _validate_output(
        self,
        output: Any,
        schema: Dict[str, Any]
    ):
        """Validate tool output against schema"""

        try:
            jsonschema.validate(output, schema)
        except jsonschema.ValidationError as e:
            logger.error(f"Output validation failed: {e}")
            # Log but don't fail - tool might have partial success
```

## Tool Exposure Patterns

### RESTful Adapter

```python
from fastapi import FastAPI, HTTPException

class MCPRestAdapter:
    """REST API adapter for MCP protocol"""

    def __init__(self, mcp_server: MCPServer):
        self.mcp = mcp_server
        self.app = FastAPI(title="MCP REST API")
        self._setup_routes()

    def _setup_routes(self):
        """Setup REST endpoints"""

        @self.app.get("/tools")
        async def list_tools(
            category: Optional[str] = None,
            capability: Optional[str] = None
        ):
            """List available tools"""
            tools = await self.mcp.list_tools(
                category=category,
                capability=capability
            )
            return {"tools": tools}

        @self.app.get("/tools/{tool_name}")
        async def get_tool(tool_name: str):
            """Get tool definition"""
            tool = await self.mcp.get_tool(tool_name)
            if not tool:
                raise HTTPException(404, f"Tool '{tool_name}' not found")
            return tool

        @self.app.post("/tools/{tool_name}/invoke")
        async def invoke_tool(
            tool_name: str,
            params: Dict[str, Any]
        ):
            """Invoke a tool"""
            try:
                result = await self.mcp.invoke_tool(tool_name, params)
                return {"result": result}
            except ToolNotFoundError:
                raise HTTPException(404, f"Tool '{tool_name}' not found")
            except InvalidParametersError as e:
                raise HTTPException(400, str(e))
            except ToolExecutionError as e:
                raise HTTPException(500, str(e))
```

### WebSocket Handler

```python
import websockets
from websockets.server import WebSocketServerProtocol

class MCPWebSocketHandler:
    """WebSocket handler for MCP protocol"""

    def __init__(self, mcp_server: MCPServer):
        self.mcp = mcp_server
        self.connections: Dict[str, WebSocketServerProtocol] = {}

    async def handle_connection(
        self,
        websocket: WebSocketServerProtocol,
        path: str
    ):
        """Handle WebSocket connection"""

        connection_id = str(uuid4())
        self.connections[connection_id] = websocket

        try:
            # Send welcome message
            await websocket.send(json.dumps({
                "type": "welcome",
                "connection_id": connection_id,
                "protocol_version": "1.0.0"
            }))

            # Handle messages
            async for message in websocket:
                response = await self.handle_message(message, connection_id)
                if response:
                    await websocket.send(response)

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Connection {connection_id} closed")
        finally:
            del self.connections[connection_id]

    async def handle_message(
        self,
        message: str,
        connection_id: str
    ) -> Optional[str]:
        """Handle WebSocket message"""

        try:
            data = json.loads(message)

            # Handle different message types
            if data.get("type") == "rpc":
                # JSON-RPC request
                return await self.mcp.handle_request(data.get("payload"))

            elif data.get("type") == "subscribe":
                # Subscribe to tool events
                tool_name = data.get("tool")
                await self.subscribe_to_tool(connection_id, tool_name)
                return json.dumps({
                    "type": "subscribed",
                    "tool": tool_name
                })

            elif data.get("type") == "ping":
                return json.dumps({"type": "pong"})

        except Exception as e:
            logger.error(f"Message handling failed: {e}")
            return json.dumps({
                "type": "error",
                "message": str(e)
            })
```

## Error Codes and Messages

### Standard MCP Error Codes

```python
class MCPErrorCodes(Enum):
    """Standard MCP error codes"""

    # JSON-RPC errors (-32xxx)
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

    # MCP specific errors (-31xxx)
    TOOL_NOT_FOUND = -31001
    TOOL_EXECUTION_FAILED = -31002
    INVALID_TOOL_PARAMS = -31003
    PERMISSION_DENIED = -31004
    RATE_LIMIT_EXCEEDED = -31005
    SESSION_EXPIRED = -31006
    RESOURCE_UNAVAILABLE = -31007
    TOOL_DEPRECATED = -31008

    # Transport errors (-30xxx)
    CONNECTION_FAILED = -30001
    TIMEOUT = -30002
    PROTOCOL_ERROR = -30003

class MCPError(Exception):
    """Base MCP error class"""

    def __init__(
        self,
        code: int,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ):
        self.code = code
        self.message = message
        self.data = data or {}
        super().__init__(self.message)

    def to_rpc_error(self) -> Dict[str, Any]:
        """Convert to JSON-RPC error format"""
        return {
            "code": self.code,
            "message": self.message,
            "data": self.data
        }
```

### Error Response Formatting

```python
def format_error_response(
    error: Exception,
    request_id: Optional[str] = None
) -> str:
    """Format error response based on error type"""

    if isinstance(error, MCPError):
        error_data = error.to_rpc_error()
    elif isinstance(error, ValidationError):
        error_data = {
            "code": MCPErrorCodes.INVALID_PARAMS.value,
            "message": "Parameter validation failed",
            "data": {"validation_errors": error.errors()}
        }
    elif isinstance(error, TimeoutError):
        error_data = {
            "code": MCPErrorCodes.TIMEOUT.value,
            "message": "Request timed out",
            "data": {}
        }
    else:
        # Generic error
        error_data = {
            "code": MCPErrorCodes.INTERNAL_ERROR.value,
            "message": "Internal server error",
            "data": {"error": str(error)} if Config.DEBUG_MODE else {}
        }

    return json.dumps({
        "jsonrpc": "2.0",
        "error": error_data,
        "id": request_id
    })
```

## Performance Optimization

### Connection Pooling

```python
class ConnectionPool:
    """Manage persistent connections for tool invocations"""

    def __init__(self, max_connections: int = 100):
        self.max_connections = max_connections
        self.connections: Dict[str, Any] = {}
        self.available: asyncio.Queue = asyncio.Queue()
        self.in_use: Set[str] = set()

    async def acquire(self, tool_name: str) -> Any:
        """Acquire connection for tool"""

        key = f"tool:{tool_name}"

        # Try to get existing connection
        if not self.available.empty():
            conn_id = await self.available.get()
            self.in_use.add(conn_id)
            return self.connections[conn_id]

        # Create new connection if under limit
        if len(self.connections) < self.max_connections:
            conn = await self._create_connection(tool_name)
            conn_id = str(uuid4())
            self.connections[conn_id] = conn
            self.in_use.add(conn_id)
            return conn

        # Wait for available connection
        conn_id = await self.available.get()
        self.in_use.add(conn_id)
        return self.connections[conn_id]

    def release(self, conn_id: str):
        """Release connection back to pool"""
        if conn_id in self.in_use:
            self.in_use.remove(conn_id)
            self.available.put_nowait(conn_id)
```

### Request Batching

```python
class BatchProcessor:
    """Process batched tool invocations"""

    def __init__(self, batch_size: int = 10, batch_timeout: float = 0.1):
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.pending_requests: List[PendingRequest] = []
        self.processing = False

    async def add_request(
        self,
        tool_name: str,
        params: Dict[str, Any]
    ) -> asyncio.Future:
        """Add request to batch"""

        future = asyncio.Future()
        request = PendingRequest(
            tool_name=tool_name,
            params=params,
            future=future,
            timestamp=time.time()
        )

        self.pending_requests.append(request)

        # Start processing if batch is full
        if len(self.pending_requests) >= self.batch_size:
            asyncio.create_task(self._process_batch())

        # Start timeout timer
        elif not self.processing:
            asyncio.create_task(self._timeout_processor())

        return future

    async def _process_batch(self):
        """Process pending requests as batch"""

        if self.processing or not self.pending_requests:
            return

        self.processing = True
        batch = self.pending_requests[:self.batch_size]
        self.pending_requests = self.pending_requests[self.batch_size:]

        try:
            # Group by tool for efficient processing
            by_tool = defaultdict(list)
            for request in batch:
                by_tool[request.tool_name].append(request)

            # Process each tool's requests
            for tool_name, requests in by_tool.items():
                results = await self._batch_invoke_tool(
                    tool_name,
                    [r.params for r in requests]
                )

                # Set results on futures
                for request, result in zip(requests, results):
                    if isinstance(result, Exception):
                        request.future.set_exception(result)
                    else:
                        request.future.set_result(result)

        finally:
            self.processing = False

            # Process remaining if any
            if self.pending_requests:
                asyncio.create_task(self._process_batch())
```

## Security Boundaries

### Authentication and Authorization

```python
class MCPAuthenticator:
    """Handle MCP authentication and authorization"""

    def __init__(self):
        self.sessions = {}
        self.api_keys = {}

    async def authenticate(
        self,
        credentials: Dict[str, Any]
    ) -> Optional[Session]:
        """Authenticate client"""

        auth_type = credentials.get("type")

        if auth_type == "api_key":
            return await self._authenticate_api_key(
                credentials.get("api_key")
            )

        elif auth_type == "jwt":
            return await self._authenticate_jwt(
                credentials.get("token")
            )

        elif auth_type == "oauth":
            return await self._authenticate_oauth(
                credentials.get("token"),
                credentials.get("provider")
            )

        return None

    async def authorize(
        self,
        session: Session,
        tool_name: str,
        operation: str = "invoke"
    ) -> bool:
        """Check authorization for tool access"""

        # Get tool requirements
        tool = self.registry.get_tool(tool_name)
        required_permissions = tool.required_permissions

        # Check session permissions
        for permission in required_permissions:
            if not self._has_permission(session, permission):
                logger.warning(
                    f"Session {session.id} denied access to {tool_name}: "
                    f"missing permission {permission}"
                )
                return False

        # Check rate limits
        if not await self._check_rate_limit(session, tool_name):
            return False

        return True

    def _has_permission(
        self,
        session: Session,
        permission: str
    ) -> bool:
        """Check if session has permission"""

        # Check explicit permissions
        if permission in session.permissions:
            return True

        # Check role-based permissions
        for role in session.roles:
            if permission in self.role_permissions.get(role, []):
                return True

        return False
```

### Input Sanitization

```python
class InputSanitizer:
    """Sanitize tool inputs for security"""

    @staticmethod
    def sanitize_params(
        params: Dict[str, Any],
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Sanitize parameters based on schema"""

        sanitized = {}

        for key, value in params.items():
            # Check if parameter is in schema
            if key not in schema.get("properties", {}):
                continue  # Skip unknown parameters

            param_schema = schema["properties"][key]
            param_type = param_schema.get("type")

            # Sanitize based on type
            if param_type == "string":
                sanitized[key] = InputSanitizer._sanitize_string(
                    value,
                    param_schema
                )
            elif param_type == "integer":
                sanitized[key] = InputSanitizer._sanitize_integer(
                    value,
                    param_schema
                )
            elif param_type == "object":
                sanitized[key] = InputSanitizer.sanitize_params(
                    value,
                    param_schema
                )
            elif param_type == "array":
                sanitized[key] = InputSanitizer._sanitize_array(
                    value,
                    param_schema
                )
            else:
                sanitized[key] = value

        return sanitized

    @staticmethod
    def _sanitize_string(value: str, schema: Dict) -> str:
        """Sanitize string values"""

        # Apply max length
        max_length = schema.get("maxLength", 10000)
        value = value[:max_length]

        # Apply pattern if specified
        pattern = schema.get("pattern")
        if pattern and not re.match(pattern, value):
            raise ValueError(f"Value does not match pattern: {pattern}")

        # Remove dangerous patterns
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'data:text/html',
        ]

        for pattern in dangerous_patterns:
            value = re.sub(pattern, '', value, flags=re.IGNORECASE)

        return value
```

## Tool Deprecation

### Deprecation Management

```python
class DeprecationManager:
    """Manage tool deprecation lifecycle"""

    def __init__(self):
        self.deprecations: Dict[str, DeprecationInfo] = {}

    def deprecate_tool(
        self,
        tool_name: str,
        message: str,
        sunset_date: datetime,
        replacement: Optional[str] = None
    ):
        """Mark tool as deprecated"""

        self.deprecations[tool_name] = DeprecationInfo(
            tool_name=tool_name,
            message=message,
            deprecated_at=datetime.utcnow(),
            sunset_date=sunset_date,
            replacement_tool=replacement
        )

        logger.warning(
            f"Tool '{tool_name}' deprecated. Sunset: {sunset_date}. "
            f"Replacement: {replacement or 'None'}"
        )

    def check_deprecation(self, tool_name: str) -> Optional[DeprecationInfo]:
        """Check if tool is deprecated"""

        if tool_name not in self.deprecations:
            return None

        info = self.deprecations[tool_name]

        # Check if past sunset date
        if datetime.utcnow() > info.sunset_date:
            raise ToolSunsetError(
                f"Tool '{tool_name}' has been sunset as of {info.sunset_date}"
            )

        return info

    def get_deprecation_headers(
        self,
        tool_name: str
    ) -> Dict[str, str]:
        """Get deprecation headers for response"""

        info = self.check_deprecation(tool_name)
        if not info:
            return {}

        headers = {
            "Deprecation": "true",
            "Sunset": info.sunset_date.isoformat(),
            "Deprecation-Message": info.message
        }

        if info.replacement_tool:
            headers["Link"] = f"</tools/{info.replacement_tool}>; rel=\"successor-version\""

        return headers
```

## Monitoring and Metrics

### MCP Server Metrics

```python
class MCPMetrics:
    """Track MCP server metrics"""

    def __init__(self):
        self.counters = defaultdict(int)
        self.histograms = defaultdict(list)
        self.gauges = {}

    def record_request(
        self,
        method: str,
        tool: Optional[str] = None,
        success: bool = True,
        duration_ms: float = 0
    ):
        """Record request metrics"""

        # Increment counters
        self.counters["requests_total"] += 1
        self.counters[f"requests_{method}"] += 1

        if tool:
            self.counters[f"tool_invocations_{tool}"] += 1

        if success:
            self.counters["requests_success"] += 1
        else:
            self.counters["requests_failed"] += 1

        # Record duration
        self.histograms["request_duration_ms"].append(duration_ms)
        if tool:
            self.histograms[f"tool_duration_ms_{tool}"].append(duration_ms)

    def get_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format"""

        lines = []

        # Counters
        for name, value in self.counters.items():
            lines.append(f"mcp_{name} {value}")

        # Histograms (simplified - just average)
        for name, values in self.histograms.items():
            if values:
                avg = sum(values) / len(values)
                lines.append(f"mcp_{name}_avg {avg:.2f}")

        # Gauges
        for name, value in self.gauges.items():
            lines.append(f"mcp_{name} {value}")

        return "\n".join(lines)
```

## Troubleshooting

### Common Issues

1. **"Tool not found"**:
   ```python
   # List all registered tools
   tools = mcp_server.registry.list_tools()
   print(f"Available tools: {[t.name for t in tools]}")

   # Check specific tool
   tool = mcp_server.registry.get_tool("tool_name")
   if tool:
       print(f"Tool found: {tool.to_mcp_format()}")
   ```

2. **"Invalid parameters"**:
   ```python
   # Validate parameters against schema
   from jsonschema import validate, ValidationError

   try:
       validate(params, tool.input_schema)
       print("Parameters valid")
   except ValidationError as e:
       print(f"Validation error: {e.message}")
       print(f"Failed at: {e.json_path}")
   ```

3. **"Connection refused"**:
   ```bash
   # Check if MCP server is running
   curl -X POST http://localhost:8090/rpc \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","method":"system.listMethods","id":1}'
   ```

### Debug Mode

Enable MCP server debugging:
```python
# In configuration
MCP_DEBUG = True
MCP_LOG_LEVEL = "DEBUG"
MCP_TRACE_REQUESTS = True

# This enables:
# - Detailed request/response logging
# - Parameter validation details
# - Performance profiling
# - Error stack traces
```

## Migration Guide

### Migrating from Legacy Tool System

```python
# Legacy tool definition
def legacy_tool(param1: str, param2: int) -> dict:
    """Old tool implementation"""
    return {"result": param1 * param2}

# MCP tool definition
mcp_tool = ToolDefinition(
    name="legacy_tool",
    version="2.0.0",
    description="Migrated legacy tool",
    categories=["text"],
    capabilities=["generation"],
    input_schema={
        "type": "object",
        "properties": {
            "param1": {"type": "string"},
            "param2": {"type": "integer"}
        },
        "required": ["param1", "param2"]
    },
    output_schema={
        "type": "object",
        "properties": {
            "result": {"type": "string"}
        }
    }
)

# Adapter for backward compatibility
class LegacyToolAdapter:
    def __init__(self, legacy_func, mcp_def):
        self.legacy = legacy_func
        self.mcp = mcp_def

    async def invoke(self, params: dict) -> dict:
        # Call legacy function
        result = self.legacy(**params)

        # Transform to MCP format
        return self.transform_result(result)
```

## Contact & Support

- **Protocol Issues**: Check MCP specification documentation
- **Tool Registration**: Ensure schema validation passes
- **Performance**: Monitor metrics endpoint at `/metrics`
- **Security**: Report vulnerabilities immediately to security team