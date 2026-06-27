FROM python:3.12-slim

WORKDIR /app

# Системные зависимости для psycopg2-binary и cryptography
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Применяем миграции и запускаем
CMD alembic upgrade head && uvicorn src.main:app --host 0.0.0.0 --port 8000