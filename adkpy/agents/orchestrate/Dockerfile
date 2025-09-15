FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster package installation
RUN pip install uv

# Copy requirements and install Python dependencies using uv
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# Copy the orchestrate agent code
COPY . .

# Environment variables (can be overridden at runtime)
ENV GOOGLE_GENAI_API_KEY=""
ENV REMOTE_AGENT_ADDRESSES=""
ENV PORT=10000

# Expose the port
EXPOSE 10000

# Run the orchestrate agent
CMD ["python", "-m", "agent"]