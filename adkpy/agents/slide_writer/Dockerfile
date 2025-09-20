FROM python:3.12-slim

WORKDIR /app

RUN pip install uv

COPY adkpy/agents/slide_writer/requirements.txt /tmp/requirements.txt
RUN uv pip install --system --no-cache-dir -r /tmp/requirements.txt

COPY adkpy /app/adkpy

ENV PYTHONPATH=/app/adkpy/agents:/app
WORKDIR /app/adkpy/agents/slide_writer

EXPOSE 10003

CMD ["python", "-m", "slide_writer.a2a_server"]
