FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install uv

COPY requirements.txt /app/requirements.txt
RUN uv pip install --system --no-cache-dir -r requirements.txt

# Copy entire ADK package (app, agents, tools, a2a, schemas)
COPY . /app

EXPOSE 8088

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8088"]
