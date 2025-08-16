# Fast Development Guide

When the codebase is evolving quickly, use this checklist to keep the backend, frontend, and container images in sync.

## Backend updates (`src/` and `web_api/`)

1. Pull the latest changes:
   ```bash
   git pull
   ```
2. Install or update Python dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```
3. Run the test suite to catch regressions:
   ```bash
   pytest
   ```
4. Restart any running development servers.

## Frontend updates (`web_ui/` and `netscan-orchestrator-ui/`)

1. Use Node 20 (see [DEV-SETUP](DEV-SETUP.md)).
2. When `package.json` or `package-lock.json` changes, reinstall dependencies and rebuild assets:
   ```bash
   npm install
   npm run build
   ```
3. For live development, use `npm run dev` in the appropriate directory.

## Updating requirements

- After adding or removing Python packages, update `requirements.txt` and run `pip install -r requirements.txt`.
- Commit `requirements.txt` so others receive the change.
- Rebuild Docker images so the new dependencies are included.

## Building and running Docker

1. Build an image with the latest code and dependencies:
   ```bash
   docker build -t netscan-orchestrator .
   # or
   docker compose build
   ```
2. Run the container:
   ```bash
   docker run -p 8000:8000 netscan-orchestrator
   # or
   docker compose up
   ```
3. Verify the container is healthy:
   ```bash
   curl http://localhost:8000/healthz
   ```
   The endpoint should return `{"status": "ok"}`. The web UI is available at `http://localhost:5000` when using Docker Compose.

## Summary checklist

- [ ] `pip install -r requirements.txt`
- [ ] `pip install -e .`
- [ ] `npm install && npm run build`
- [ ] `pytest`
- [ ] `docker compose up --build`
- [ ] `curl http://localhost:8000/healthz`
