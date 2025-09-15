# PresentationPro A2A Orchestrator
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy orchestrator code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 orchestrator && \
    chown -R orchestrator:orchestrator /app

USER orchestrator

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    ORCHESTRATOR_PORT=8080 \
    ENVIRONMENT=production \
    LOG_LEVEL=INFO

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose port
EXPOSE 8080

# Run the orchestrator
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--log-level", "info"]