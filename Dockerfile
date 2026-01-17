# Stage 1: Build Frontend
FROM node:24-alpine as frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Stage 2: Runtime
FROM python:3.14-slim as runtime

WORKDIR /app

# Install system dependencies if needed (e.g. curl for healthcheck)
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY backend/pyproject.toml backend/README.md ./
RUN pip install --no-cache-dir .

# Copy backend code
COPY backend/src ./src

# Copy docs for Knowledge Base
COPY docs ./docs

# Copy built frontend assets
COPY --from=frontend-builder /app/frontend/dist /app/static

# Copy generated extension into static (merge with frontend)
COPY backend/static/edge.crx /app/static/edge.crx

# Env vars
ENV PYTHONPATH=/app
ENV PORT=13040

# Run
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "13040"]
