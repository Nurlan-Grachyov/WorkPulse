FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# системные зависимости при необходимости (asyncpg, psycopg, gcc и т.п.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# зависимости через poetry (если ты на poetry)
COPY pyproject.toml poetry.lock* ./
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root
COPY alembic.ini ./
# исходники
COPY ./app ./app

# если есть отдельный auth.py, etc. в корне, тоже скопируй:
# COPY ./auth.py ./auth.py

# команда запуска: тот же fastapi_app, что и у тебя в main.py
CMD ["uvicorn", "app.main:fastapi_app", "--host", "0.0.0.0", "--port", "8001"]
