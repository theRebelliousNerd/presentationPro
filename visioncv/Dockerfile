FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY visioncv /app/visioncv
COPY requirements.txt /app/requirements.txt

RUN apt-get update -y && apt-get install -y --no-install-recommends \
      build-essential \
      tesseract-ocr \
      libglib2.0-0 \
      libgl1 \
    && pip install -r /app/requirements.txt \
    && apt-get purge -y --auto-remove build-essential \
    && rm -rf /var/lib/apt/lists/*

EXPOSE 9170

CMD ["python", "-m", "visioncv.agent", "--transport", "http", "--host", "0.0.0.0", "--port", "9170"]
