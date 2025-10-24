FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install poetry \
    && poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-root --only main

COPY src ./src
COPY scripts ./scripts
COPY alembic.ini ./
COPY migrations ./migrations

ENV PYTHONPATH=/app/src
ENV INIT_FLAG=/app/.initialized

CMD ["bash", "-c", "\
if [ ! -f $INIT_FLAG ]; then \
    poetry run alembic upgrade head && \
    poetry run python ./scripts/seed_db.py --clear && \
    touch $INIT_FLAG; \
fi; \
poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 \
"]
