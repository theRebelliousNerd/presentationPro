FROM ghcr.io/astral-sh/uv:python3.12-alpine

WORKDIR /app

COPY adkpy/agents/design/requirements.txt /tmp/requirements.txt
RUN uv pip install --system --no-cache-dir -r /tmp/requirements.txt

COPY adkpy /app/adkpy

ENV PYTHONPATH=/app/adkpy/agents:/app
WORKDIR /app/adkpy/agents/design

EXPOSE 10006

CMD ["python", "-m", "design.a2a_server"]
