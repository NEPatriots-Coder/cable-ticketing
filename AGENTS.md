# AGENTS.md

## Purpose
This repository is a cable/inventory ticketing system used for request tracking, approvals, receiving, and optics workflows.

## Stack Snapshot
- Frontend: React (`frontend/`), served by Nginx in Docker
- Backend: Flask + SQLAlchemy (`backend/`)
- Database: PostgreSQL in Docker (SQLite is used in backend tests)
- Deploy targets: Docker Compose (local), DigitalOcean App Platform, Helm chart

## Operator Preference
- Keep responses concise and step-by-step.
- Prioritize practical execution over theory.

## Source-of-Truth Run Commands

### Option 1: Docker Compose (preferred)
1. `cp backend/.env.example backend/.env`
2. Fill credentials in `backend/.env` (notification keys optional for core flow).
3. `docker-compose up --build`
4. Open frontend at `http://localhost:3000`

Useful compose commands:
- `docker-compose ps`
- `docker-compose logs -f backend`
- `docker-compose down`
- `docker-compose down -v` (reset local DB)

### Option 2: Local Dev (without Docker)
Backend:
1. `cd backend`
2. `python -m venv venv && source venv/bin/activate`
3. `pip install -r requirements.txt`
4. `python run.py` (binds to port `5001`)

Frontend (new terminal):
1. `cd frontend`
2. `npm install`
3. `npm start`

## Ports and Routing (important)
- Docker Compose:
  - Frontend host: `3000`
  - Backend host: `5001` (container `5000`)
  - Postgres: `5432`
- Frontend API calls are intentionally relative: `baseURL: '/api'` in `frontend/src/api/axiosinstance.js`.
- Docker frontend Nginx proxies `/api` to backend service (`frontend/nginx.conf`).
- If changing backend ports, verify all of these stay consistent:
  - `docker-compose.yml`
  - `backend/run.py`
  - `frontend/package.json` (`proxy` for local React dev)
  - any docs/scripts mentioning health URLs

## Environment Variables
Copy from `backend/.env.example`.
Important vars:
- `DATABASE_URL`
- `SECRET_KEY`
- `AUTH_TOKEN_TTL_SECONDS`
- `APP_URL`
- Optional notifications: `RESEND_API_KEY`, `SENDGRID_API_KEY`, `TWILIO_*`, `AWS_*`
- `RUN_SEED_ON_START` defaults to `false` and should remain false unless intentionally seeding.

## Testing and Validation
- Backend tests: `cd backend && pytest`
- Focused backend test file: `backend/tests/test_ticket_lifecycle.py`
- Frontend tests: `cd frontend && npm test -- --watchAll=false`
- Health endpoint: `/api/health`

## Safe Change Rules for Agents
- Keep `/api` relative routing intact unless explicitly asked to redesign networking.
- Preserve auth behavior (Bearer token, token expiry handling in axios interceptor).
- Do not enable auto-seeding by default.
- Notification failures should not break core ticket flow.
- Prefer minimal, surgical edits over broad refactors.

## High-Value Files
- `README.md` - setup, API overview, workflows
- `docker-compose.yml` - local orchestration and healthchecks
- `backend/app/routes.py` - API behavior
- `backend/app/models.py` - schema/domain logic
- `backend/app/__init__.py` - app config and DB init behavior
- `frontend/src/pages/` - user workflows (dashboard, receiving, optics, approvals)
- `frontend/src/api/axiosinstance.js` - API/auth client behavior
- `.do/app.yaml` - DigitalOcean routing/deploy config
- `helm-chart/` - Kubernetes manifests

## Known Operational Notes
- On macOS, port `5000` can conflict with AirPlay Receiver; project defaults avoid this by using host `5001` for backend.
- Quick helper scripts in repo root:
  - `quick-start.sh`
  - `fix-port-conflict.sh`
  - `check_backend.sh` (DigitalOcean logs via `doctl`)


## PR Checklist (Coreweave Workflow)
Use this before merging changes.

1. Scope and intent
- Jira ticket is linked and acceptance criteria are reflected in the PR description.
- Change is limited to requested scope; no unrelated refactors.

2. Functional validation
- Core flow still works: register/login -> create ticket -> approve/reject -> status progression.
- If inventory touched: receiving and on-hand/inventory movement endpoints still behave correctly.
- If optics touched: request/return submit + admin status actions still work.

3. API and auth
- Protected endpoints still require Bearer auth.
- Token-expiry behavior still clears local auth and forces re-login.
- Response shapes for existing frontend consumers were not unintentionally broken.

4. Data and safety
- No destructive schema/data changes without explicit migration/rollback plan.
- `RUN_SEED_ON_START` remains `false` by default.
- Soft-delete/restore/purge rules remain enforced.

5. Notifications and integrations
- Notification failures remain non-blocking for ticket lifecycle.
- Env-var requirements are documented if new keys were introduced.
- External service credentials are not hardcoded or committed.

6. Deployment and ops
- Docker Compose still comes up clean (`frontend`, `backend`, `postgres` healthy).
- If routing/ports changed, all related files were updated consistently (`docker-compose.yml`, frontend proxy/nginx, backend run/docs).
- DigitalOcean/Helm config updated when deployment behavior changes.

7. Quality checks
- Backend tests run: `cd backend && pytest`
- Frontend test/build sanity run for UI changes: `cd frontend && npm test -- --watchAll=false` and/or `npm run build`
- Manual smoke check includes dashboard and health endpoint (`/api/health`).

8. Change communication
- PR notes include user impact, rollback plan, and any required Slack announcement.
- If workflow changes affect operations, include a short NetSuite/Excel process note in PR description.
