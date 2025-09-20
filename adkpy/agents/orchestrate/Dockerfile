FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc g++ && rm -rf /var/lib/apt/lists/*
RUN pip install uv

COPY adkpy/agents/orchestrate/requirements.txt /tmp/requirements.txt
RUN uv pip install --system --no-cache-dir -r /tmp/requirements.txt

COPY adkpy /app/adkpy

ENV PYTHONPATH=/app
WORKDIR /app/adkpy/agents/orchestrate

EXPOSE 10000

CMD ["python", "-m", "agent"]
