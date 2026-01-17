# Stage 1: Build Frontend
FROM node:24-alpine as frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Stage 2: Runtime
# We use a slimmer image for runtime
FROM python:3.14-slim as runtime

# Install system dependencies (curl for healthcheck)
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY backend/pyproject.toml backend/README.md ./
RUN pip install --no-cache-dir .

# Copy Backend Code
COPY backend/src ./src

# Copy Documentation
COPY docs ./docs

# Copy Static Assets
# 1. Frontend Build
COPY --from=frontend-builder /app/frontend/dist /app/static

# 2. Browser Extension (Prebuilt)
# We now use the manually provided CRX3 file as it is verified to work on Android
COPY backend/static/edge.crx /app/static/edge.crx
COPY backend/static/edge.zip /app/static/edge.zip
COPY backend/static/browser-extension.zip /app/static/browser-extension.zip

# Create data directory
RUN mkdir -p /app/data
ENV PORT=13040

# Run
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "13040"]
