FROM python:3.12-slim

WORKDIR /app

RUN pip install uv

COPY adkpy/agents/outline/requirements.txt /tmp/requirements.txt
RUN uv pip install --system --no-cache-dir -r /tmp/requirements.txt

COPY adkpy /app/adkpy

ENV PYTHONPATH=/app/adkpy/agents:/app
WORKDIR /app/adkpy/agents/outline

EXPOSE 10002

CMD ["python", "-m", "outline.a2a_server"]
