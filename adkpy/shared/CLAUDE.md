# CLAUDE.md - ADK/A2A Shared Directory

This directory contains shared utilities, schemas, and cross-cutting concerns used throughout the ADK/A2A system.

## Shared Components Overview

The shared directory provides foundational components that ensure consistency across all agents and services:

```
Shared Infrastructure
    ├─> Schemas (Pydantic Models)
    │   ├─> Request/Response Models
    │   ├─> Domain Models
    │   └─> Validation Rules
    │
    ├─> Configuration Management
    │   ├─> Environment Variables
    │   ├─> Service Discovery
    │   └─> Feature Flags
    │
    ├─> Telemetry & Observability
    │   ├─> Token Tracking
    │   ├─> Performance Metrics
    │   └─> Distributed Tracing
    │
    └─> Logging Configuration
        ├─> Structured Logging
        ├─> Log Aggregation
        └─> Audit Trail
```

## Schema Management (`schemas.py`)

### Core Schema Principles

1. **Single Source of Truth**: All data models defined once
2. **Strong Typing**: Use Pydantic for runtime validation
3. **Version Compatibility**: Support schema evolution
4. **Documentation**: Auto-generate from models

### Base Schema Models

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

class BaseSchema(BaseModel):
    """Base model for all schemas"""
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }

class PresentationSchema(BaseSchema):
    """Core presentation data model"""
    title: str = Field(..., min_length=1, max_length=200)
    context: str = Field(..., description="User context and goals")
    outline: Optional[OutlineSchema] = None
    slides: List[SlideSchema] = Field(default_factory=list)
    settings: PresentationSettings = Field(default_factory=PresentationSettings)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator('slides')
    def validate_slide_count(cls, v):
        if len(v) > 100:
            raise ValueError("Maximum 100 slides allowed")
        return v

class SlideSchema(BaseSchema):
    """Individual slide model"""
    number: int = Field(..., ge=1)
    title: str = Field(..., max_length=100)
    content: str = Field(..., max_length=5000)
    speaker_notes: Optional[str] = Field(None, max_length=2000)
    layout: SlideLayout = Field(default=SlideLayout.TITLE_AND_CONTENT)
    images: List[ImageSchema] = Field(default_factory=list)

    class Config:
        use_enum_values = True
```

### Schema Evolution Strategy

```python
# Version 1 (original)
class UserInputV1(BaseModel):
    text: str
    files: List[str] = []

# Version 2 (with parameters)
class UserInputV2(BaseModel):
    text: str
    files: List[str] = []
    parameters: Dict[str, Any] = {}  # New field with default

    @classmethod
    def from_v1(cls, v1: UserInputV1) -> 'UserInputV2':
        """Migration from V1 to V2"""
        return cls(
            text=v1.text,
            files=v1.files,
            parameters={}  # Default for new field
        )
```

### Breaking Change Impact Analysis

When modifying schemas, consider impacts on:

1. **API Contracts**: Client compatibility
2. **Database Storage**: Migration requirements
3. **Agent Communication**: Message format changes
4. **Cache Invalidation**: Serialization changes

## Configuration Management (`config.py`)

### Configuration Hierarchy

```python
# Priority order (highest to lowest):
# 1. Environment variables
# 2. Config file (config.yaml)
# 3. Default values

class Config:
    """Centralized configuration management"""

    # Service Discovery
    ADKPY_URL = os.getenv("ADKPY_URL", "http://adkpy:8088")
    ARANGO_URL = os.getenv("ARANGO_URL", "http://arangodb:8529")

    # API Keys (Required)
    GOOGLE_API_KEY = os.getenv("GOOGLE_GENAI_API_KEY")
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_GENAI_API_KEY is required")

    # Optional API Keys
    BING_API_KEY = os.getenv("BING_SEARCH_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # Feature Flags
    ENABLE_CACHING = os.getenv("ENABLE_CACHING", "true").lower() == "true"
    ENABLE_TELEMETRY = os.getenv("ENABLE_TELEMETRY", "true").lower() == "true"
    DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

    # Performance Tuning
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", "10"))
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
    CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))

    # Model Configuration
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini-2.5-flash")
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "8000"))
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

    @classmethod
    def validate(cls):
        """Validate configuration on startup"""
        required = ["GOOGLE_API_KEY"]
        for key in required:
            if not getattr(cls, key):
                raise ValueError(f"Missing required config: {key}")

    @classmethod
    def to_dict(cls) -> dict:
        """Export configuration (with secrets masked)"""
        config = {}
        for key in dir(cls):
            if key.isupper():
                value = getattr(cls, key)
                if "KEY" in key or "PASSWORD" in key:
                    value = "***MASKED***"
                config[key] = value
        return config
```

### Environment-Specific Configuration

```python
class EnvironmentConfig:
    """Environment-aware configuration"""

    @classmethod
    def get_env(cls) -> str:
        return os.getenv("ENVIRONMENT", "development")

    @classmethod
    def is_production(cls) -> bool:
        return cls.get_env() == "production"

    @classmethod
    def get_config(cls) -> Config:
        env = cls.get_env()

        if env == "production":
            return ProductionConfig()
        elif env == "staging":
            return StagingConfig()
        else:
            return DevelopmentConfig()

class ProductionConfig(Config):
    DEBUG_MODE = False
    ENABLE_TELEMETRY = True
    LOG_LEVEL = "INFO"

class DevelopmentConfig(Config):
    DEBUG_MODE = True
    ENABLE_TELEMETRY = False
    LOG_LEVEL = "DEBUG"
```

## Telemetry System (`telemetry.py`)

### Telemetry Tracking Rules

```python
class TelemetryTracker:
    """Unified telemetry tracking across agents"""

    def __init__(self):
        self.metrics = defaultdict(lambda: defaultdict(int))
        self.traces = []

    def track_tokens(
        self,
        agent: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cached: bool = False
    ):
        """Track token usage per agent and model"""
        key = f"{agent}:{model}"
        self.metrics[key]["input_tokens"] += input_tokens
        self.metrics[key]["output_tokens"] += output_tokens
        self.metrics[key]["total_tokens"] += input_tokens + output_tokens

        if cached:
            self.metrics[key]["cache_hits"] += 1

        # Cost tracking
        cost = self.calculate_cost(model, input_tokens, output_tokens)
        self.metrics[key]["total_cost"] += cost

    def track_latency(
        self,
        operation: str,
        duration_ms: float,
        success: bool = True
    ):
        """Track operation latency"""
        self.metrics[operation]["count"] += 1
        self.metrics[operation]["total_ms"] += duration_ms
        self.metrics[operation]["success" if success else "failure"] += 1

        # Calculate percentiles
        if operation not in self.metrics["percentiles"]:
            self.metrics["percentiles"][operation] = []
        self.metrics["percentiles"][operation].append(duration_ms)

    def track_error(
        self,
        agent: str,
        error_type: str,
        error_message: str,
        stack_trace: str = None
    ):
        """Track errors with context"""
        error_key = f"{agent}:{error_type}"
        self.metrics["errors"][error_key] += 1

        if Config.DEBUG_MODE and stack_trace:
            self.traces.append({
                "timestamp": datetime.utcnow().isoformat(),
                "agent": agent,
                "error_type": error_type,
                "message": error_message,
                "stack": stack_trace
            })

    def get_summary(self) -> Dict[str, Any]:
        """Get telemetry summary"""
        return {
            "tokens": self._summarize_tokens(),
            "latency": self._summarize_latency(),
            "errors": dict(self.metrics["errors"]),
            "cost_estimate": self._calculate_total_cost()
        }

    @staticmethod
    def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on model pricing"""
        # Pricing per 1M tokens (example rates)
        pricing = {
            "gemini-2.5-flash": {"input": 0.15, "output": 0.50},
            "gemini-1.5-pro": {"input": 1.00, "output": 2.00},
            "gpt-4": {"input": 10.00, "output": 30.00}
        }

        if model not in pricing:
            return 0.0

        rates = pricing[model]
        input_cost = (input_tokens / 1_000_000) * rates["input"]
        output_cost = (output_tokens / 1_000_000) * rates["output"]

        return input_cost + output_cost
```

### Telemetry Context Manager

```python
from contextlib import contextmanager
import time

@contextmanager
def telemetry_context(operation: str, agent: str = None):
    """Context manager for automatic telemetry tracking"""
    start_time = time.time()
    error = None

    try:
        yield
    except Exception as e:
        error = e
        if agent:
            telemetry.track_error(
                agent=agent,
                error_type=type(e).__name__,
                error_message=str(e),
                stack_trace=traceback.format_exc()
            )
        raise
    finally:
        duration_ms = (time.time() - start_time) * 1000
        telemetry.track_latency(
            operation=operation,
            duration_ms=duration_ms,
            success=(error is None)
        )

# Usage
with telemetry_context("slide_generation", agent="SlideWriter"):
    result = await generate_slide(content)
    telemetry.track_tokens(
        agent="SlideWriter",
        model="gemini-2.5-flash",
        input_tokens=result.usage.input_tokens,
        output_tokens=result.usage.output_tokens
    )
```

## Logging Configuration (`logging_config.py`)

### Structured Logging Setup

```python
import logging
import json
from pythonjsonlogger import jsonlogger

def setup_logging():
    """Configure structured logging for the entire application"""

    # Custom formatter for JSON logs
    class CustomJsonFormatter(jsonlogger.JsonFormatter):
        def add_fields(self, log_record, record, message_dict):
            super().add_fields(log_record, record, message_dict)
            log_record['timestamp'] = datetime.utcnow().isoformat()
            log_record['level'] = record.levelname
            log_record['service'] = 'adkpy'
            log_record['environment'] = Config.get_env()

            # Add trace context if available
            if hasattr(record, 'trace_id'):
                log_record['trace_id'] = record.trace_id
            if hasattr(record, 'agent_id'):
                log_record['agent_id'] = record.agent_id

    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, Config.LOG_LEVEL))

    # Console handler with JSON formatting
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(CustomJsonFormatter())
    logger.addHandler(console_handler)

    # File handler for audit trail
    if Config.ENABLE_AUDIT_LOG:
        audit_handler = logging.FileHandler('/var/log/adkpy/audit.log')
        audit_handler.setFormatter(CustomJsonFormatter())
        audit_handler.setLevel(logging.INFO)
        logger.addHandler(audit_handler)

    # Suppress noisy libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)

    return logger

# Logger factory for agents
def get_logger(name: str) -> logging.Logger:
    """Get a configured logger for a specific component"""
    logger = logging.getLogger(name)

    # Add custom filter for sensitive data
    logger.addFilter(SensitiveDataFilter())

    return logger

class SensitiveDataFilter(logging.Filter):
    """Filter to redact sensitive information from logs"""

    SENSITIVE_PATTERNS = [
        (r'api[_-]?key["\']?\s*[:=]\s*["\']?([^"\'\s]+)', 'api_key=***REDACTED***'),
        (r'password["\']?\s*[:=]\s*["\']?([^"\'\s]+)', 'password=***REDACTED***'),
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '***EMAIL***')
    ]

    def filter(self, record):
        if hasattr(record, 'msg'):
            for pattern, replacement in self.SENSITIVE_PATTERNS:
                record.msg = re.sub(pattern, replacement, str(record.msg), flags=re.IGNORECASE)
        return True
```

### Logging Standards

```python
# Log levels and their usage
"""
DEBUG: Detailed diagnostic information
INFO: General informational messages
WARNING: Warning messages for potential issues
ERROR: Error messages for failures
CRITICAL: Critical failures requiring immediate attention
"""

# Standard log format for different scenarios
logger = get_logger(__name__)

# Agent lifecycle
logger.info("Agent initialized", extra={"agent_id": self.id, "config": config})

# Operation tracking
logger.debug("Starting operation", extra={"operation": "generate_slide", "params": params})

# Performance logging
logger.info("Operation completed", extra={
    "operation": "generate_slide",
    "duration_ms": duration,
    "tokens_used": tokens
})

# Error logging
logger.error("Operation failed", extra={
    "operation": "generate_slide",
    "error": str(e),
    "trace_id": trace_id
}, exc_info=True)

# Audit logging
logger.info("User action", extra={
    "action": "create_presentation",
    "user_id": user_id,
    "ip_address": ip,
    "timestamp": datetime.utcnow().isoformat()
})
```

## Cross-Agent Utilities

### Message Passing Utilities

```python
from typing import Any, Dict, Optional
from uuid import uuid4

class MessageBus:
    """Centralized message passing between agents"""

    def __init__(self):
        self._subscribers = defaultdict(list)
        self._message_queue = asyncio.Queue()

    def subscribe(self, topic: str, handler: callable):
        """Subscribe to a message topic"""
        self._subscribers[topic].append(handler)

    async def publish(self, topic: str, message: Dict[str, Any]):
        """Publish message to a topic"""
        envelope = {
            "id": str(uuid4()),
            "topic": topic,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Notify subscribers
        for handler in self._subscribers[topic]:
            await handler(envelope)

        # Add to queue for persistence
        await self._message_queue.put(envelope)

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast to all subscribers"""
        await self.publish("*", message)
```

### Retry and Circuit Breaker

```python
from typing import TypeVar, Callable
import asyncio

T = TypeVar('T')

class CircuitBreaker:
    """Circuit breaker pattern for external service calls"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open

    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with circuit breaker protection"""

        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half-open"
            else:
                raise Exception("Circuit breaker is open")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result

        except self.expected_exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        """Reset circuit breaker on success"""
        self.failure_count = 0
        self.state = "closed"

    def _on_failure(self):
        """Handle failure"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to retry"""
        return (
            self.last_failure_time and
            time.time() - self.last_failure_time >= self.recovery_timeout
        )

# Retry decorator
def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Retry decorator with exponential backoff"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            attempt = 1
            current_delay = delay

            while attempt <= max_attempts:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts:
                        logger.error(f"Max retries ({max_attempts}) exceeded for {func.__name__}")
                        raise

                    logger.warning(f"Attempt {attempt} failed, retrying in {current_delay}s: {e}")
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
                    attempt += 1

        return wrapper
    return decorator
```

## Type Safety Requirements

### Runtime Type Checking

```python
from typing import get_type_hints, get_origin, get_args
from functools import wraps

def validate_types(func):
    """Decorator for runtime type validation"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        hints = get_type_hints(func)

        # Validate arguments
        bound_args = inspect.signature(func).bind(*args, **kwargs)
        bound_args.apply_defaults()

        for name, value in bound_args.arguments.items():
            if name in hints:
                expected_type = hints[name]
                if not isinstance(value, expected_type):
                    raise TypeError(
                        f"Argument '{name}' expected {expected_type}, got {type(value)}"
                    )

        # Execute function
        result = func(*args, **kwargs)

        # Validate return type
        if 'return' in hints:
            expected_return = hints['return']
            if not isinstance(result, expected_return):
                raise TypeError(
                    f"Return value expected {expected_return}, got {type(result)}"
                )

        return result
    return wrapper
```

## Performance Utilities

### Caching Strategy

```python
from functools import lru_cache
import hashlib
import pickle

class SmartCache:
    """Intelligent caching with TTL and size limits"""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl = ttl_seconds
        self._cache = OrderedDict()
        self._timestamps = {}

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key not in self._cache:
            return None

        # Check TTL
        if time.time() - self._timestamps[key] > self.ttl:
            del self._cache[key]
            del self._timestamps[key]
            return None

        # Move to end (LRU)
        self._cache.move_to_end(key)
        return self._cache[key]

    def set(self, key: str, value: Any):
        """Set value in cache"""
        # Enforce size limit
        if len(self._cache) >= self.max_size:
            # Remove oldest
            oldest = next(iter(self._cache))
            del self._cache[oldest]
            del self._timestamps[oldest]

        self._cache[key] = value
        self._timestamps[key] = time.time()

    @staticmethod
    def make_key(*args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_data = (args, sorted(kwargs.items()))
        return hashlib.md5(pickle.dumps(key_data)).hexdigest()
```

### Performance Monitoring

```python
import psutil
import asyncio

class PerformanceMonitor:
    """System performance monitoring"""

    @staticmethod
    def get_system_metrics() -> Dict[str, Any]:
        """Get current system metrics"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "network_io": psutil.net_io_counters()._asdict(),
            "process_count": len(psutil.pids())
        }

    @staticmethod
    async def monitor_async_task(task: asyncio.Task) -> Dict[str, Any]:
        """Monitor async task performance"""
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss

        try:
            result = await task
            success = True
        except Exception as e:
            result = None
            success = False

        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss

        return {
            "duration_ms": (end_time - start_time) * 1000,
            "memory_delta_mb": (end_memory - start_memory) / 1024 / 1024,
            "success": success,
            "result": result
        }
```

## Migration Procedures

### Schema Migration

```python
# Migration script for schema changes
async def migrate_schemas(from_version: str, to_version: str):
    """Migrate data to new schema version"""

    migrations = {
        ("1.0.0", "1.1.0"): migrate_1_0_to_1_1,
        ("1.1.0", "2.0.0"): migrate_1_1_to_2_0
    }

    migration_func = migrations.get((from_version, to_version))
    if not migration_func:
        raise ValueError(f"No migration path from {from_version} to {to_version}")

    # Run migration
    await migration_func()

    # Update version marker
    await update_schema_version(to_version)
```

## Security Considerations

### Input Validation

```python
from typing import Any
import re

class InputValidator:
    """Centralized input validation"""

    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """Sanitize string input"""
        # Remove control characters
        value = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', value)

        # Limit length
        value = value[:max_length]

        # Escape HTML/SQL
        value = html.escape(value)

        return value

    @staticmethod
    def validate_uuid(value: str) -> bool:
        """Validate UUID format"""
        uuid_pattern = re.compile(
            r'^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$',
            re.IGNORECASE
        )
        return bool(uuid_pattern.match(value))

    @staticmethod
    def validate_api_key(value: str) -> bool:
        """Validate API key format"""
        # Must be alphanumeric with hyphens, 32+ chars
        return bool(re.match(r'^[A-Za-z0-9-]{32,}$', value))
```

## Contact & Support

- **Schema Changes**: Require team review and migration plan
- **Configuration Issues**: Check environment variables first
- **Performance Problems**: Enable telemetry and check metrics
- **Security Concerns**: Report to security team immediately