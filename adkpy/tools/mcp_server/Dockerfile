# MCP Server Dockerfile
# Production-ready container for PresentationPro MCP Server

FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user
RUN groupadd -r mcp && useradd -r -g mcp mcp

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the MCP server code
COPY --chown=mcp:mcp . /app/mcp_server/

# Copy parent tools directory
COPY --chown=mcp:mcp ../ /app/tools/

# Add parent directories to Python path
ENV PYTHONPATH="/app:/app/tools:${PYTHONPATH}"

# Create necessary directories
RUN mkdir -p /tmp/mcp /var/log/mcp && \
    chown -R mcp:mcp /tmp/mcp /var/log/mcp

# Switch to non-root user
USER mcp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8090/health || exit 1

# Expose port
EXPOSE 8090

# Default command
CMD ["python", "-m", "mcp_server.server", "--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8090"]