FROM python:3.12-slim

WORKDIR /app

RUN pip install uv

COPY adkpy/agents/clarifier/requirements.txt /tmp/requirements.txt
RUN uv pip install --system --no-cache-dir -r /tmp/requirements.txt

COPY adkpy /app/adkpy

ENV PYTHONPATH=/app/adkpy/agents:/app
WORKDIR /app/adkpy/agents/clarifier

EXPOSE 10001

CMD ["python", "-m", "clarifier.a2a_server"]
