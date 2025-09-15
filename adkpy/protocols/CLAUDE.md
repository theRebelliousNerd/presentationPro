# CLAUDE.md - ADK/A2A Protocols Directory

This directory contains the protocol definitions and contracts that govern agent communication and tool integration in the ADK/A2A system.

## Protocol Architecture Overview

The protocols layer defines the boundaries and contracts between:
- **A2A (Agent-to-Agent)**: Inter-agent communication protocol
- **MCP (Model Context Protocol)**: Tool integration protocol
- **Agent Cards**: Agent capability declarations

## Protocol Decision Tree

```
Request Incoming
    ├─> Is it agent communication?
    │   └─> Use A2A Protocol
    │       ├─> Message format validation
    │       ├─> Session management
    │       └─> Policy enforcement
    │
    └─> Is it tool invocation?
        └─> Use MCP Protocol
            ├─> Tool discovery
            ├─> Parameter validation
            └─> Response formatting
```

## A2A Protocol (`a2a_types.py`)

### Message Format Specification

```python
# Standard A2A Message Structure
{
    "role": "user|assistant|system",
    "content": "message content",
    "metadata": {
        "agent_id": "agent_name",
        "session_id": "uuid",
        "timestamp": "iso8601",
        "trace_id": "uuid",
        "parent_id": "uuid"  # For message chains
    }
}
```

### Protocol Contracts

1. **Session Initialization**
   - Every A2A conversation requires a session_id
   - Sessions track message history and context
   - Sessions have TTL of 1 hour (configurable)

2. **Message Validation**
   - All messages MUST include role and content
   - Metadata MUST include agent_id for tracing
   - Content size limit: 100KB per message

3. **Error Propagation**
   - Errors MUST be wrapped in A2AError type
   - Error codes follow HTTP status conventions
   - Stack traces included only in debug mode

## MCP Protocol (`mcp_types.py`)

### Tool Registration Format

```python
# MCP Tool Definition
{
    "name": "tool_name",
    "description": "Human-readable description",
    "parameters": {
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "..."}
        },
        "required": ["param1"]
    },
    "returns": {
        "type": "object",
        "properties": {...}
    }
}
```

### MCP Request/Response Cycle

```python
# Request
{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "tool_name",
        "arguments": {...}
    },
    "id": "request_id"
}

# Response
{
    "jsonrpc": "2.0",
    "result": {...},
    "id": "request_id"
}
```

## Agent Cards (`agent_cards.py`)

### Capability Declaration Format

```python
# Agent Card Structure
{
    "agent_id": "unique_identifier",
    "name": "display_name",
    "description": "agent purpose",
    "capabilities": [
        {
            "type": "reasoning|generation|analysis",
            "domain": "specific area",
            "constraints": ["list of limitations"]
        }
    ],
    "tools": ["tool1", "tool2"],  # MCP tools this agent can use
    "policies": {
        "max_tokens": 8000,
        "temperature": 0.7,
        "retry_count": 3
    },
    "version": "1.0.0"
}
```

## Version Compatibility Matrix

| Protocol | Version | Compatible With | Breaking Changes |
|----------|---------|-----------------|------------------|
| A2A      | 1.0.0   | All agents      | Initial release  |
| MCP      | 1.0.0   | All tools       | Initial release  |
| Cards    | 1.0.0   | All agents      | Initial release  |

## Protocol Extension Guidelines

### Adding New Message Types

1. **Define in a2a_types.py**:
   ```python
   class NewMessageType(BaseMessage):
       message_type: Literal["new_type"]
       # Additional fields
   ```

2. **Update validators**:
   - Add to MESSAGE_VALIDATORS dict
   - Implement validation logic

3. **Version the change**:
   - Increment minor version for additions
   - Increment major version for breaking changes

### Adding New Tool Protocols

1. **Define in mcp_types.py**:
   ```python
   class NewToolProtocol(BaseToolProtocol):
       protocol_type: Literal["new_protocol"]
       # Protocol-specific fields
   ```

2. **Register with MCP server**:
   - Add to TOOL_PROTOCOLS registry
   - Implement discovery endpoint

## Breaking Change Procedures

### Before Making Breaking Changes

1. **Deprecation Notice** (2 weeks minimum):
   ```python
   @deprecated(version="1.1.0", removal="2.0.0")
   def old_method():
       warnings.warn("Use new_method instead", DeprecationWarning)
   ```

2. **Migration Path**:
   - Provide compatibility shim
   - Document migration steps
   - Support both versions temporarily

3. **Version Update**:
   - Major version bump (1.x.x → 2.0.0)
   - Update all dependent agents
   - Test backward compatibility

## Validation Requirements

### Message Validation

```python
# Required validations for all A2A messages
def validate_a2a_message(message: dict) -> bool:
    # 1. Structure validation
    assert "role" in message
    assert "content" in message

    # 2. Content validation
    assert len(message["content"]) > 0
    assert len(message["content"]) < 100_000

    # 3. Metadata validation
    if "metadata" in message:
        assert "agent_id" in message["metadata"]
        assert is_valid_uuid(message["metadata"].get("session_id"))

    return True
```

### Tool Parameter Validation

```python
# MCP tool parameter validation
def validate_tool_params(tool_name: str, params: dict) -> bool:
    tool_spec = get_tool_specification(tool_name)

    # 1. Required parameters present
    for required in tool_spec["parameters"]["required"]:
        assert required in params

    # 2. Type validation
    for param, spec in tool_spec["parameters"]["properties"].items():
        if param in params:
            assert validate_type(params[param], spec["type"])

    return True
```

## Security Considerations

### Protocol-Level Security

1. **Authentication**:
   - Agent cards include auth tokens
   - Tools require API key validation
   - Session tokens expire after 1 hour

2. **Authorization**:
   - Agents declare required permissions
   - Tools enforce capability checks
   - Rate limiting per agent/session

3. **Data Protection**:
   - Sensitive data marked in metadata
   - PII scrubbing in logging
   - Encryption for inter-service communication

### Input Sanitization

```python
# Required for all protocol inputs
def sanitize_protocol_input(data: Any) -> Any:
    # 1. Size limits
    if isinstance(data, str):
        data = data[:100_000]  # 100KB limit

    # 2. Injection prevention
    data = escape_control_characters(data)

    # 3. Type coercion
    data = enforce_schema_types(data)

    return data
```

## Troubleshooting Guide

### Common Protocol Issues

1. **"Invalid message format"**:
   - Check required fields (role, content)
   - Validate against schema
   - Ensure proper JSON encoding

2. **"Tool not found"**:
   - Verify tool registration
   - Check MCP server connectivity
   - Validate tool name spelling

3. **"Session expired"**:
   - Sessions expire after 1 hour
   - Implement session refresh logic
   - Store critical state externally

### Debug Mode

Enable protocol debugging:
```python
# In environment or config
PROTOCOL_DEBUG=true
PROTOCOL_LOG_LEVEL=DEBUG

# This enables:
# - Full message logging
# - Stack traces in errors
# - Validation details
# - Performance metrics
```

## Performance Considerations

1. **Message Size Optimization**:
   - Keep messages under 10KB when possible
   - Use compression for large payloads
   - Implement pagination for lists

2. **Protocol Overhead**:
   - A2A adds ~200 bytes per message
   - MCP adds ~150 bytes per tool call
   - Use batch operations when available

3. **Connection Pooling**:
   - Reuse protocol connections
   - Implement connection health checks
   - Set appropriate timeouts (30s default)

## Migration Procedures

### Upgrading Protocol Versions

1. **Check compatibility matrix**
2. **Update agent dependencies**:
   ```bash
   pip install adkpy-protocols>=2.0.0
   ```
3. **Run migration script**:
   ```bash
   python -m protocols.migrate --from=1.0 --to=2.0
   ```
4. **Test with staging environment**
5. **Deploy with feature flags**

### Protocol Rollback

If issues occur:
1. **Immediate rollback**:
   ```bash
   docker-compose down
   git checkout previous-version
   docker-compose up --build
   ```
2. **Preserve session state**:
   - Export active sessions
   - Maintain compatibility layer
   - Gradual migration

## Contact & Support

- **Protocol Issues**: Create issue in `/adkpy/protocols/`
- **Breaking Changes**: Requires team review
- **Security Concerns**: Report immediately to security team