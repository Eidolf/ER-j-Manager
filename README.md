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

## Quick Start (Docker)

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd ER-j-Manager
    ```

2.  **Run with Docker Compose**:
    ```bash
    docker-compose up --build
    ```

3.  **Access the application**:
    - Web UI: http://localhost:13040
    - API Docs: http://localhost:13040/docs
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
