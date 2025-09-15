# CLAUDE.md - ADK/A2A FastAPI Application Directory

This directory contains the FastAPI application that serves as the API gateway for the ADK/A2A system, handling HTTP requests, routing to agents, and managing the presentation generation workflow.

## API Gateway Architecture

The FastAPI application acts as the primary entry point for all client interactions:

```
Client Request
    ├─> API Gateway (FastAPI)
    │   ├─> Request Validation
    │   ├─> Authentication/Authorization
    │   ├─> Rate Limiting
    │   └─> CORS Handling
    │
    ├─> Endpoint Routing
    │   ├─> /v1/clarify
    │   ├─> /v1/outline
    │   ├─> /v1/slide
    │   └─> /v1/polish
    │
    ├─> Agent Orchestration
    │   ├─> Agent Selection
    │   ├─> Request Transformation
    │   └─> Response Aggregation
    │
    └─> Response Formatting
        ├─> JSON Serialization
        ├─> Error Formatting
        └─> Telemetry Injection
```

## Core Application Structure (`main.py`)

### Application Initialization

```python
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    # Startup
    await initialize_agents()
    await connect_to_services()
    await load_configuration()
    logger.info("ADK/A2A API Gateway started")

    yield

    # Shutdown
    await cleanup_agents()
    await disconnect_services()
    logger.info("ADK/A2A API Gateway stopped")

app = FastAPI(
    title="ADK/A2A Presentation API",
    version="1.0.0",
    description="AI-powered presentation generation using Agent Development Kit",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    GZipMiddleware,
    minimum_size=1000  # Compress responses > 1KB
)
```

## API Endpoint Definitions

### 1. Clarification Endpoint

```python
@app.post("/v1/clarify", response_model=ClarifyResponse)
async def clarify_presentation(
    request: ClarifyRequest,
    session: Session = Depends(get_session)
) -> ClarifyResponse:
    """
    Clarify presentation goals through conversational AI.

    This endpoint:
    1. Analyzes user input (text and files)
    2. Generates clarifying questions
    3. Maintains conversation context
    4. Returns refined understanding metrics
    """

    try:
        # Validate request
        validate_clarify_request(request)

        # Process uploaded files if any
        enriched_context = {}
        if request.files:
            enriched_context = await process_files(request.files)

        # Prepare agent input
        agent_input = {
            "user_input": request.text,
            "conversation_history": request.conversation_history,
            "enriched_context": enriched_context,
            "context_meter": request.context_meter
        }

        # Execute clarifier agent
        clarifier = ClarifierAgent(model=request.model or DEFAULT_MODEL)
        result = await clarifier.execute(agent_input)

        # Track telemetry
        telemetry.track_tokens(
            agent="clarifier",
            model=request.model,
            input_tokens=result.usage.input_tokens,
            output_tokens=result.usage.output_tokens
        )

        # Format response
        return ClarifyResponse(
            questions=result.questions,
            context_understanding=result.understanding_score,
            suggested_parameters=result.parameters,
            telemetry=telemetry.get_summary()
        )

    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())
    except Exception as e:
        logger.error(f"Clarification failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

### 2. Outline Generation Endpoint

```python
@app.post("/v1/outline", response_model=OutlineResponse)
async def generate_outline(
    request: OutlineRequest,
    session: Session = Depends(get_session)
) -> OutlineResponse:
    """
    Generate presentation outline based on clarified goals.

    Pipeline:
    1. Validate context completeness
    2. Generate structured outline
    3. Apply critic review
    4. Return refined outline
    """

    try:
        # Ensure sufficient context
        if request.context_meter < 25:
            raise HTTPException(
                status_code=400,
                detail="Insufficient context for outline generation"
            )

        # Orchestrate outline generation
        orchestrator = SequentialOrchestrator()
        result = await orchestrator.execute(
            agents=["outline_generator", "critic"],
            input_data={
                "context": request.context,
                "parameters": request.parameters,
                "target_slides": request.target_slides
            },
            session_id=session.id
        )

        # Extract outline from results
        outline = result["results"][0]["result"]["outline"]
        critique = result["results"][1]["result"]["feedback"]

        # Apply refinements from critique
        if critique.requires_revision:
            outline = await refine_outline(outline, critique)

        return OutlineResponse(
            outline=outline,
            critique=critique,
            estimated_generation_time=calculate_generation_time(outline),
            telemetry=telemetry.get_summary()
        )

    except Exception as e:
        logger.error(f"Outline generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

### 3. Slide Generation Endpoint

```python
@app.post("/v1/slide", response_model=SlideResponse)
async def generate_slide(
    request: SlideRequest,
    session: Session = Depends(get_session),
    background_tasks: BackgroundTasks = BackgroundTasks()
) -> SlideResponse:
    """
    Generate individual slide content.

    Features:
    - Parallel content and image generation
    - Research integration
    - Design consistency
    - Speaker notes generation
    """

    try:
        # Validate slide number
        if request.slide_number < 1 or request.slide_number > len(request.outline.slides):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid slide number: {request.slide_number}"
            )

        # Get slide outline
        slide_outline = request.outline.slides[request.slide_number - 1]

        # Parallel execution for efficiency
        tasks = []

        # Task 1: Generate slide content
        tasks.append(
            generate_slide_content(
                slide_outline=slide_outline,
                context=request.context,
                model=request.model
            )
        )

        # Task 2: Research if needed
        if request.enable_research and slide_outline.requires_research:
            tasks.append(
                research_slide_topic(
                    topic=slide_outline.topic,
                    depth=request.research_depth
                )
            )

        # Task 3: Generate speaker notes
        if request.generate_speaker_notes:
            tasks.append(
                generate_speaker_notes(
                    slide_outline=slide_outline,
                    context=request.context
                )
            )

        # Execute tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        slide_content = results[0]
        research_data = results[1] if len(results) > 1 else None
        speaker_notes = results[2] if len(results) > 2 else None

        # Enrich content with research
        if research_data:
            slide_content = enrich_with_research(slide_content, research_data)

        # Schedule background image generation
        if request.generate_images:
            background_tasks.add_task(
                generate_slide_images,
                slide_id=slide_content.id,
                content=slide_content,
                style=request.design_style
            )

        return SlideResponse(
            slide=slide_content,
            speaker_notes=speaker_notes,
            research_sources=research_data.sources if research_data else [],
            telemetry=telemetry.get_summary()
        )

    except Exception as e:
        logger.error(f"Slide generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

### 4. Content Polishing Endpoint

```python
@app.post("/v1/polish", response_model=PolishResponse)
async def polish_content(
    request: PolishRequest,
    session: Session = Depends(get_session)
) -> PolishResponse:
    """
    Polish and refine generated content.

    Polishing types:
    - Grammar and style improvements
    - Consistency checks
    - Tone adjustments
    - Technical accuracy
    """

    try:
        polisher = NotesPolisherAgent(model=request.model)

        polished_content = await polisher.execute({
            "content": request.content,
            "polish_type": request.polish_type,
            "target_audience": request.target_audience,
            "tone": request.tone
        })

        return PolishResponse(
            original=request.content,
            polished=polished_content.result,
            changes=polished_content.changes,
            improvement_score=polished_content.score,
            telemetry=telemetry.get_summary()
        )

    except Exception as e:
        logger.error(f"Content polishing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

## Endpoint Versioning

### Version Management Strategy

```python
from fastapi import APIRouter

# Version 1 routes
v1_router = APIRouter(prefix="/v1", tags=["v1"])

@v1_router.post("/clarify")
async def clarify_v1(request: ClarifyRequestV1):
    # V1 implementation
    pass

# Version 2 routes (with breaking changes)
v2_router = APIRouter(prefix="/v2", tags=["v2"])

@v2_router.post("/clarify")
async def clarify_v2(request: ClarifyRequestV2):
    # V2 implementation with new features
    pass

# Register routers
app.include_router(v1_router)
app.include_router(v2_router)

# Deprecation headers
@app.middleware("http")
async def add_deprecation_headers(request: Request, call_next):
    response = await call_next(request)

    if request.url.path.startswith("/v1/"):
        response.headers["Deprecation"] = "version=\"v1\""
        response.headers["Sunset"] = "2025-12-31"
        response.headers["Link"] = "</v2/docs>; rel=\"successor-version\""

    return response
```

## Authentication & Authorization

### API Key Authentication

```python
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    """Verify API key for authentication"""

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"}
        )

    # Validate API key
    if not await validate_api_key(api_key):
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )

    # Get user/tenant from API key
    user = await get_user_from_api_key(api_key)

    return user

# Protected endpoints
@app.post("/v1/clarify", dependencies=[Depends(verify_api_key)])
async def clarify_protected(request: ClarifyRequest):
    pass
```

### JWT Authorization

```python
from fastapi_jwt_auth import AuthJWT
from pydantic import BaseModel

class JWTSettings(BaseModel):
    authjwt_secret_key: str = Config.JWT_SECRET
    authjwt_algorithm: str = "HS256"
    authjwt_access_token_expires: int = 3600

@AuthJWT.load_config
def get_jwt_config():
    return JWTSettings()

@app.post("/auth/login")
async def login(credentials: LoginCredentials, Authorize: AuthJWT = Depends()):
    """Authenticate and return JWT token"""

    user = await authenticate_user(credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Create JWT token
    access_token = Authorize.create_access_token(
        subject=user.id,
        user_claims={"role": user.role}
    )

    return {"access_token": access_token}

@app.post("/v1/clarify")
async def clarify_jwt(
    request: ClarifyRequest,
    Authorize: AuthJWT = Depends()
):
    """Protected endpoint with JWT"""

    Authorize.jwt_required()
    current_user = Authorize.get_jwt_subject()

    # Process request with user context
    pass
```

## Request Validation

### Pydantic Models for Validation

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any

class ClarifyRequest(BaseModel):
    """Request model for clarification endpoint"""

    text: str = Field(..., min_length=10, max_length=10000)
    files: Optional[List[str]] = Field(default=[], max_items=10)
    conversation_history: List[Dict[str, str]] = Field(default=[])
    context_meter: int = Field(default=0, ge=0, le=100)
    model: Optional[str] = Field(default="gemini-2.5-flash")

    @validator('model')
    def validate_model(cls, v):
        allowed_models = [
            "gemini-2.5-flash",
            "gemini-1.5-pro",
            "gpt-4",
            "claude-3"
        ]
        if v not in allowed_models:
            raise ValueError(f"Model must be one of {allowed_models}")
        return v

    @validator('files')
    def validate_files(cls, v):
        for file_path in v:
            if not file_path.startswith("/uploads/"):
                raise ValueError("Invalid file path")
        return v

    class Config:
        schema_extra = {
            "example": {
                "text": "I need a presentation about AI trends",
                "files": ["/uploads/research.pdf"],
                "conversation_history": [],
                "context_meter": 25,
                "model": "gemini-2.5-flash"
            }
        }
```

### Custom Validators

```python
from fastapi import Query, Path, Body

@app.get("/presentations/{presentation_id}/slides/{slide_number}")
async def get_slide(
    presentation_id: str = Path(
        ...,
        regex="^[a-zA-Z0-9-]{36}$",
        description="UUID of the presentation"
    ),
    slide_number: int = Path(
        ...,
        ge=1,
        le=100,
        description="Slide number (1-100)"
    ),
    include_notes: bool = Query(
        default=False,
        description="Include speaker notes"
    )
):
    """Get specific slide with validation"""
    pass
```

## Response Formatting

### Standardized Response Structure

```python
from typing import Generic, TypeVar, Optional

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    """Standardized API response wrapper"""

    success: bool
    data: Optional[T]
    error: Optional[str]
    message: Optional[str]
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": {"result": "example"},
                "error": None,
                "message": "Operation successful",
                "metadata": {
                    "timestamp": "2024-01-01T00:00:00Z",
                    "request_id": "uuid",
                    "duration_ms": 100
                }
            }
        }

# Success response helper
def success_response(data: Any, message: str = None) -> APIResponse:
    return APIResponse(
        success=True,
        data=data,
        message=message or "Success",
        metadata={
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": str(uuid4())
        }
    )

# Error response helper
def error_response(
    error: str,
    status_code: int = 500,
    details: Dict = None
) -> APIResponse:
    return APIResponse(
        success=False,
        error=error,
        data=None,
        metadata={
            "timestamp": datetime.utcnow().isoformat(),
            "status_code": status_code,
            "details": details or {}
        }
    )
```

## Error Handling

### Global Exception Handler

```python
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle value errors"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_response(
            error=str(exc),
            status_code=400
        ).dict()
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed feedback"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response(
            error="Validation failed",
            status_code=422,
            details={"validation_errors": errors}
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler"""

    # Log full exception
    logger.exception(f"Unhandled exception: {exc}")

    # Return sanitized error
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response(
            error="Internal server error",
            status_code=500,
            details={
                "request_id": request.state.request_id if hasattr(request.state, 'request_id') else None
            }
        ).dict()
    )
```

### Custom Error Classes

```python
class ADKException(Exception):
    """Base exception for ADK errors"""
    def __init__(self, message: str, status_code: int = 500, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class AgentNotFoundError(ADKException):
    """Raised when requested agent is not available"""
    def __init__(self, agent_name: str):
        super().__init__(
            message=f"Agent '{agent_name}' not found",
            status_code=404,
            details={"agent": agent_name}
        )

class InsufficientContextError(ADKException):
    """Raised when context is insufficient for operation"""
    def __init__(self, required_context: int, current_context: int):
        super().__init__(
            message=f"Insufficient context: {current_context}% (required: {required_context}%)",
            status_code=400,
            details={
                "required": required_context,
                "current": current_context
            }
        )
```

## CORS Configuration

### Dynamic CORS Setup

```python
from typing import List

def get_allowed_origins() -> List[str]:
    """Get allowed origins from environment"""
    origins = []

    # Always allow localhost for development
    if Config.ENVIRONMENT == "development":
        origins.extend([
            "http://localhost:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3000"
        ])

    # Production origins
    if Config.ALLOWED_ORIGINS:
        origins.extend(Config.ALLOWED_ORIGINS.split(","))

    return origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Request-ID"],
    max_age=3600  # Cache preflight requests for 1 hour
)
```

## Rate Limiting

### Request Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Create limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per minute"],
    storage_uri=Config.REDIS_URL if Config.REDIS_URL else None
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply rate limits to endpoints
@app.post("/v1/clarify")
@limiter.limit("10 per minute")  # Stricter limit for expensive operation
async def clarify_rate_limited(
    request: Request,
    clarify_request: ClarifyRequest
):
    pass

# Custom rate limit by API key
def get_api_key_limit(request: Request) -> str:
    """Get rate limit based on API key tier"""
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return "10 per minute"

    tier = get_api_key_tier(api_key)
    limits = {
        "free": "10 per minute",
        "basic": "60 per minute",
        "premium": "300 per minute",
        "enterprise": "1000 per minute"
    }

    return limits.get(tier, "10 per minute")

@app.post("/v1/generate")
@limiter.limit(get_api_key_limit)
async def generate_with_tier_limit(request: Request):
    pass
```

## Health Checks

### Health and Readiness Endpoints

```python
from fastapi import status
from typing import Dict, Any

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": app.version
    }

@app.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check() -> Dict[str, Any]:
    """Detailed readiness check"""

    checks = {
        "database": False,
        "agents": False,
        "cache": False,
        "external_services": False
    }

    try:
        # Check database
        checks["database"] = await check_database_connection()

        # Check agents
        checks["agents"] = await check_agent_availability()

        # Check cache
        checks["cache"] = await check_cache_connection()

        # Check external services
        checks["external_services"] = await check_external_services()

    except Exception as e:
        logger.error(f"Readiness check failed: {e}")

    # Determine overall readiness
    is_ready = all(checks.values())

    if not is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not ready",
                "checks": checks
            }
        )

    return {
        "status": "ready",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/metrics")
async def metrics():
    """Prometheus-compatible metrics endpoint"""
    metrics = []

    # Request metrics
    metrics.append(f"http_requests_total {request_counter.total}")
    metrics.append(f"http_request_duration_seconds {request_duration.mean}")

    # Agent metrics
    for agent, count in agent_calls.items():
        metrics.append(f'agent_calls_total{{agent="{agent}"}} {count}')

    # Token metrics
    metrics.append(f"tokens_used_total {telemetry.total_tokens}")

    return PlainTextResponse("\n".join(metrics))
```

## Middleware Configuration

### Request ID Middleware

```python
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add unique request ID to all requests"""

    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    request.state.request_id = request_id

    # Add to logger context
    logger.contextvars.bind(request_id=request_id)

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response
```

### Timing Middleware

```python
import time

@app.middleware("http")
async def add_process_time(request: Request, call_next):
    """Track request processing time"""

    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    response.headers["X-Process-Time"] = str(process_time)

    # Log slow requests
    if process_time > 1.0:
        logger.warning(
            f"Slow request: {request.method} {request.url.path} "
            f"took {process_time:.2f}s"
        )

    return response
```

## Security Considerations

### Input Sanitization

```python
from html import escape
import re

def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent injection attacks"""

    # Remove null bytes
    text = text.replace('\x00', '')

    # Escape HTML
    text = escape(text)

    # Remove potentially dangerous patterns
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
    ]

    for pattern in dangerous_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    return text

# Apply to all text inputs
@app.middleware("http")
async def sanitize_request_body(request: Request, call_next):
    """Sanitize all text fields in request body"""

    if request.method in ["POST", "PUT", "PATCH"]:
        body = await request.body()
        # Process and sanitize body
        # ... sanitization logic

    return await call_next(request)
```

### Security Headers

```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from secure import SecureHeaders

secure_headers = SecureHeaders()

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""

    response = await call_next(request)

    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"

    return response

# Trusted host validation
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "*.presentationpro.ai"]
)
```

## Performance Optimization

### Response Caching

```python
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache
from fastapi_cache.backends.redis import RedisBackend

@app.on_event("startup")
async def startup():
    """Initialize caching"""
    redis = aioredis.from_url(Config.REDIS_URL, encoding="utf8", decode_responses=True)
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")

@app.get("/v1/templates")
@cache(expire=3600)  # Cache for 1 hour
async def get_templates():
    """Get presentation templates (cached)"""
    return await load_templates()
```

### Database Connection Pooling

```python
from databases import Database

database = Database(
    Config.DATABASE_URL,
    min_size=5,
    max_size=20,
    command_timeout=60,
    connection_timeout=10
)

@app.on_event("startup")
async def startup_database():
    await database.connect()

@app.on_event("shutdown")
async def shutdown_database():
    await database.disconnect()
```

## Deployment Configuration

### Uvicorn Settings

```python
# In main.py or run.py
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8088,
        workers=4,  # Number of worker processes
        loop="uvloop",  # High-performance event loop
        log_level="info",
        access_log=True,
        reload=Config.ENVIRONMENT == "development",
        ssl_keyfile=Config.SSL_KEY if Config.SSL_KEY else None,
        ssl_certfile=Config.SSL_CERT if Config.SSL_CERT else None
    )
```

### Docker Configuration

```dockerfile
# Dockerfile for FastAPI app
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run with gunicorn for production
CMD ["gunicorn", "app.main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8088", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
```

## Monitoring & Telemetry

### Application Metrics

```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

active_requests = Gauge(
    'http_requests_active',
    'Active HTTP requests'
)

@app.middleware("http")
async def track_metrics(request: Request, call_next):
    """Track application metrics"""

    # Increment active requests
    active_requests.inc()

    # Track duration
    start_time = time.time()

    try:
        response = await call_next(request)

        # Record metrics
        request_count.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()

        request_duration.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(time.time() - start_time)

        return response

    finally:
        active_requests.dec()
```

## Contact & Support

- **API Issues**: Check `/docs` for OpenAPI documentation
- **Performance**: Enable metrics endpoint and check Prometheus
- **Security**: Report vulnerabilities to security team immediately
- **Breaking Changes**: Follow versioning guidelines and deprecation policy