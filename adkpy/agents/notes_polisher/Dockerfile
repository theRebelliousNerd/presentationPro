FROM ghcr.io/astral-sh/uv:python3.12-alpine

WORKDIR /app

COPY adkpy/agents/notes_polisher/requirements.txt /tmp/requirements.txt
RUN uv pip install --system --no-cache-dir -r /tmp/requirements.txt

COPY adkpy /app/adkpy

ENV PYTHONPATH=/app/adkpy/agents:/app
WORKDIR /app/adkpy/agents/notes_polisher

EXPOSE 10005

CMD ["python", "-m", "notes_polisher.a2a_server"]
