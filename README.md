# JDownloader 2 Web Manager

![JDownloader Manager Logo](images/logo.png)

A secure, production-ready web interface for managing JDownloader 2 downloads via a mocked API. Built with Domain-Driven Design (DDD) and DevSecOps best practices.

## Features

- **Cyberpunk UI**: Modern, dark-mode interface with neon accents.
- **Secure Access**: JWT-based authentication.
- **Mocked API**: Emulates JDownloader 2 "Deprecated API" for development.
- **Real-time Updates**: Live download progress and speed monitoring.
- **Production Ready**: Dockerized, CI/CD pipelines, and observability built-in.

## Tech Stack

- **Backend**: Python FastAPI, Pydantic, Opentelemetry
- **Frontend**: React, TypeScript, Vite, TailwindCSS
- **Infrastructure**: Docker, GitHub Actions

## Quick Start (Docker / Portainer)

This stack is designed to run alongside your existing JDownloader container.

**1. Docker Compose Configuration**
Copy this into Portainer -> Stacks -> Add stack:

```yaml
services:
  app:
    # Use the official image from GitHub Container Registry
    image: ghcr.io/eidolf/er-j-manager:latest
    container_name: jdownloader-manager
    # If you cannot connect to JD on the host (bound to 127.0.0.1), uncomment this and comment out 'ports':
    # network_mode: "host"
    ports:
      - "13040:13040"
    # Mapping "host.docker.internal" allows the container to talk to your Host OS
    extra_hosts:
      - "host.docker.internal:host-gateway"
    environment:
      - PROJECT_NAME=JDownloader Manager
      - SECRET_KEY=change_this_to_a_secure_random_string # <--- IMPORTANT: Change this in production!
      # Optional: Set a PIN for initial admin setup if needed
      # - ACCESS_PIN=1234
    volumes:
      - jdm_data:/app/data
    restart: unless-stopped

volumes:
  jdm_data:
```

> **Note for Local-Host Users:**
> If your JDownloader runs on the same machine but is strictly bound to `127.0.0.1` (localhost) and refuses connections:
> 1. Use `network_mode: "host"` in your compose file.
> 2. Remove the `ports` section.
> 3. Use `http://127.0.0.1:3128` in the Settings.

**2. Access the application**:
- Web UI: http://<your-ip>:13040
- Default Credentials: `admin` / `admin`

## Development Setup

### Backend

```bash
cd backend
pip install -e .[dev]
uvicorn src.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Architecture

This project follows **Domain-Driven Design (DDD)** principles:

- `src/domain`: Business logic and models (independent of framework).
- `src/infrastructure`: External services (Mocked API).
- `src/api`: Application layer (FastAPI routes).
- `src/core`: Configuration and security.

## Versioning & Release

We use **Date-Based Versioning** (`YYYY.MM.PATCH`).

- **CI/CD**:
    - `ci-orchestrator.yml`: Runs on push/PR to main.
    - `pr-orchestrator.yml`: Labels PRs automagically.
    - `release.yml`: Manual trigger (Nightly, Beta, Stable).
    - `rollback.yml`: Emergency deletion of releases.

- **Trigger a Release**:
    Go to Actions > Release Workflow > Run workflow > Select type (Nightly/Beta/Stable).

## Local Validation (Pre-Flight)

Avoid "trial-and-error" commits by running checks locally using the included scripts.

1.  **Setup Environment**:
    Checks for `act`, `docker`, and language runtimes.
    ```bash
    ./scripts/setup_local_ci.sh
    ```

2.  **Run Pre-Flight Check**:
    **Fast Mode** (Linters only):
    ```bash
    ./scripts/preflight.sh
    ```
    **Full Mode** (Simulates GitHub Actions via `act`):
    ```bash
    ./scripts/preflight.sh full
    # Note: Requires Docker running. Uses .env or .secrets for environment variables.
    ```

## CI/CD Service Levels

- **Economy** (Default): Fast checks, linting, unit tests.
- **Full**: Runs E2E tests and exhaustive suites (triggered on Release or Main).

## License

Proprietary / Internal Use Only.
