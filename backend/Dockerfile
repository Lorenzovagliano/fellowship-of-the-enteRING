FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install poetry

COPY pyproject.toml poetry.lock* ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

COPY . .

RUN poetry install --no-interaction --no-ansi

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "pdfextractor.api:app", "--host", "0.0.0.0", "--port", "8000"]
