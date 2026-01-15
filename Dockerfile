# Stage 1: Build Frontend
FROM node:20-alpine as frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Stage 2: Runtime
FROM python:3.10-slim as runtime

WORKDIR /app

# Install system dependencies if needed (e.g. curl for healthcheck)
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY backend/pyproject.toml backend/README.md ./
RUN pip install --no-cache-dir .

# Copy backend code
COPY backend/src ./src

# Copy built frontend assets
COPY --from=frontend-builder /app/frontend/dist /app/static

# Env vars
ENV PYTHONPATH=/app
ENV PORT=8000

# Run
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
