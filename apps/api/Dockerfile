FROM python:3.12-slim
WORKDIR /app
# Build context = repo root (see docker-compose.yml).
COPY apps/api/pyproject.toml .
COPY apps/api/app app
COPY DOSSIER_MAESTRO.md DOSSIER_MAESTRO.md
RUN pip install --no-cache-dir .
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
