FROM python:3.11-slim

# Set working directory (project root)
WORKDIR /project

# Install system dependencies (psycopg2 needs libpq)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

RUN mkdir -p certs && \
    curl -o certs/global-bundle.pem https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem

RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /project
USER appuser

EXPOSE 4000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:4000/api/health || exit 1

# Run from the app/ directory so relative imports work (from database import ..., etc.)
# Alembic runs from /project root (alembic revision, alembic upgrade head)
WORKDIR /project/app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "4000", "--workers", "2"]