# Personal Finance OS (PFOS)

A personal financial management platform — record, organise and understand your
money through a unified dashboard. **Tracking and reporting only**: PFOS never
holds or moves funds, and never connects to real bank accounts.

- **Market:** Nigeria first, then international.
- **Model:** Freemium SaaS (free tier is genuinely useful, not crippled).
- **Records:** Manual entry — income, expenses, transfers, accounts, budgets,
  savings goals, recurring bills.

> **Status: Phase 3 — dashboard complete.** The financial engine feeds a live
> overview dashboard (summary cards, cash-flow and spending charts, recent
> activity, account balances). Budgets and further features arrive in later
> phases.

## Repository layout

```
├── frontend/            # Next.js App Router + TypeScript + Tailwind
├── backend/             # FastAPI + SQLAlchemy 2.x + Alembic
├── infrastructure/      # Terraform (Phase 8)
├── docs/                # Architecture and decisions
├── docker-compose.yml   # Full local stack (db + backend + frontend)
└── Makefile             # Developer commands
```

## Prerequisites

- **Docker** with Docker Compose (recommended path).
- **Node.js LTS** and **pnpm** (for host-based frontend dev).
- **Python 3.12+** (for host-based backend dev).

## Quickstart (Docker)

```bash
cp .env.example .env
docker compose up --build -d
```

Then open:

- Frontend: <http://localhost:3000>
- Backend health: <http://localhost:8000/api/v1/health>
- API docs: <http://localhost:8000/api/v1/docs>

The backend applies pending Alembic migrations on startup. Stop with
`docker compose down`. Data persists in the `pgdata` volume.

## Authentication (local development)

The app uses an OIDC-compatible auth layer. By default `AUTH_PROVIDER=dev`
enables a built-in **local identity provider** so the full flow works without
AWS or an email service:

1. Visit <http://localhost:3000/register> and create an account.
2. Complete the 5-stage onboarding wizard (first account included).
3. You land on the dashboard at <http://localhost:3000/dashboard>.

The dev provider is for local development only (in-memory identities, no real
password storage). Switch to **Amazon Cognito** by setting `AUTH_PROVIDER=cognito`
and providing `COGNITO_USER_POOL_ID` / `COGNITO_CLIENT_ID`; the backend verifies
Cognito JWTs (issuer/audience/signature via JWKS) with no code changes.

## Host-based development

Run only Postgres in Docker, then the apps on the host with hot reload:

```bash
docker compose up -d db        # Postgres on :5432
make backend-install           # one-time: venv + deps
make backend-dev               # FastAPI on :8000 (auto-reload)
make frontend-install          # one-time: pnpm install
make frontend-dev              # Next.js on :3000
```

## Quality gates

```bash
make fmt     # format (ruff + prettier)
make lint    # lint (ruff + eslint)
make test    # tests (pytest)
make check   # all of the above
```

## CI

GitHub Actions runs lint, format check, typecheck, tests and a production build
on every push and pull request (see `.github/workflows/ci.yml`).

## Documentation

- [Architecture](docs/ARCHITECTURE.md) — stack, module boundaries and financial
  correctness invariants.
- Product specification v1.0 — the source of truth for scope and acceptance
  criteria.

## Phase roadmap

| Phase | Scope                                | Status     |
| ----- | ------------------------------------ | ---------- |
| 0     | Repo, Docker, ORM, Alembic, CI, docs | Done       |
| 1     | Auth (Cognito) + onboarding          | Done       |
| 2     | Accounts, transactions, ledger       | Done       |
| 3     | Dashboard                            | Done       |
| 4     | Budgets                              | Planned    |
| 5     | Savings + recurring bills            | Planned    |
| 6     | Reports + exports                    | Planned    |
| 7     | Security + subscription readiness    | Planned    |
| 8     | AWS deployment                       | Planned    |
