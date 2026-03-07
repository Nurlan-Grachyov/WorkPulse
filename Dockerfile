FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# системные зависимости (если нужны для psycopg/asyncpg и т.п.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# зависимости через poetry
COPY pyproject.toml poetry.lock* ./
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root

# alembic-конфиг (лежит в корне проекта)
COPY alembic.ini ./

# исходники: вся структура src/, tests/ по необходимости
COPY ./src ./src

CMD ["uvicorn", "src.application.main:fastapi_app", "--host", "0.0.0.0", "--port", "8001"]
