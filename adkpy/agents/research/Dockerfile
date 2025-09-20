FROM python:3.12-slim

WORKDIR /app

RUN pip install --upgrade pip && pip install uv

COPY adkpy/agents/research/requirements.txt /tmp/requirements.txt
RUN uv pip install --system --no-cache-dir -r /tmp/requirements.txt

COPY adkpy /app/adkpy

ENV PYTHONPATH=/app/adkpy/agents:/app
WORKDIR /app/adkpy/agents/research

EXPOSE 10008

CMD ["python", "-m", "research.a2a_server"]
