FROM ghcr.io/astral-sh/uv:python3.12-alpine

WORKDIR /app

COPY adkpy/agents/critic/requirements.txt /tmp/requirements.txt
RUN uv pip install --system --no-cache-dir -r /tmp/requirements.txt

COPY adkpy /app/adkpy

ENV PYTHONPATH=/app/adkpy/agents:/app
WORKDIR /app/adkpy/agents/critic

EXPOSE 10004

CMD ["python", "-m", "critic.a2a_server"]
