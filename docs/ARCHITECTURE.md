# Personal Finance OS — Architecture

> Working document for Phase 0+. The product spec (v1.0) is the source of truth;
> this file records the decisions and layout as they are implemented.

## 1. Product boundary

PFOS is a **personal financial record-keeping and planning tool**. Users record
income, expenses, account balances, savings goals, debts and recurring
obligations manually; the app turns those records into budgeting, analytics,
comparisons and forecasts.

PFOS **never** holds or moves money. There is no custody, payment execution or
bank integration in scope. Subscription billing (a future, separate concern) is
handled by a hosted provider and is not part of the financial engine.

## 2. Stack

| Layer        | Choice                                        |
| ------------ | --------------------------------------------- |
| Frontend     | Next.js App Router + TypeScript               |
| Styling      | Tailwind CSS                                  |
| Components   | shadcn/ui (Phase 3+)                          |
| Charts       | Recharts (Phase 3+)                           |
| State        | TanStack Query, React Hook Form, Zod          |
| Backend      | FastAPI (Python 3.12+)                        |
| ORM          | SQLAlchemy 2.x                                |
| Validation   | Pydantic v2                                   |
| Database     | PostgreSQL                                    |
| Migrations   | Alembic                                       |
| Auth         | Amazon Cognito (OIDC abstraction)             |
| Jobs         | APScheduler (later)                           |
| Testing      | Pytest + Playwright                           |
| Infra        | Docker, Terraform, ECS Fargate, RDS, S3, CI   |

## 3. Architecture shape

A **modular monolith** — one deployable FastAPI backend with clear module
boundaries, no microservices/Kafka/Redis in the initial scope.

| Module        | Responsibility                             |
| ------------- | ------------------------------------------ |
| Identity      | Validate JWTs, user context                |
| Profiles      | Preferences and onboarding                 |
| Accounts      | Manual financial accounts                  |
| Transactions  | Income, expenses, transfers                |
| Ledger        | Account balance calculations               |
| Categories    | Default and custom categories              |
| Budgets       | Budget creation and monitoring             |
| Savings       | Goal allocation and contributions          |
| Bills         | Recurring obligations                      |
| Reports       | Aggregations and analytics                 |
| Notifications | In-app and email notifications             |
| Subscriptions | Plan and feature entitlements              |

Modules expose service functions; they do not reach into each other's database
internals. The transaction service posts account activity through the ledger
service.

## 4. Repository layout

```
finance-dashboard/
├── frontend/            # Next.js app (App Router, feature-based)
├── backend/             # FastAPI app (modular monolith)
│   ├── app/
│   │   ├── core/        # config
│   │   ├── db/          # engine, session, declarative base
│   │   ├── models/      # ORM models (registered for Alembic)
│   │   └── api/v1/      # routers
│   ├── alembic/         # migrations
│   └── tests/
├── infrastructure/      # Terraform (Phase 8)
├── .github/workflows/   # CI
├── docs/                # architecture & decisions
└── docker-compose.yml
```

## 5. Financial correctness invariants (implemented in Phase 2)

These rules govern the transaction/ledger engine and are non-negotiable:

1. **Money is integer minor units** (`BIGINT`) + an explicit `CHAR(3)` currency
   code. Precision is read from ISO 4217 — never assume two decimals.
2. **Balances are derived**, never edited: `Balance = OpeningBalance + Σ LedgerEntries`.
3. Transaction amounts stay **positive**; the sign lives in the ledger entry
   (`+` increase, `−` decrease).
4. **Transfers** post **two ledger entries atomically**, same currency in MVP,
   and are **excluded** from income/expense and net cash flow.
5. **Ledger entries are immutable**; corrections void the original and post a
   corrected transaction, preserving the audit trail.
6. **Idempotency keys** are unique per user.
7. Reporting periods resolve in the **user's timezone** (UTC storage; date-only
   for user-entered calendar dates).

## 6. Data & security posture

- UUID primary keys; **every record is owned by a user**.
- Ownership enforced in application code **and** via PostgreSQL Row-Level
  Security (defence in depth, never RLS alone).
- Cognito JWT validation (issuer/audience/expiry/signature); user IDs are never
  trusted from request bodies.
- Audit logging; no financial data in application logs; encryption at rest and
  in transit; secrets in AWS Secrets Manager.
- NDPA 2023 + GDPR posture: data export and account deletion are first-class;
  **record access is never gated on a subscription**.

## 7. API conventions

- Base URL `/api/v1`, JSON, `Authorization: Bearer <access_token>`.
- Envelopes: `{ "success": true, "data": {}, "meta": {} }` and
  `{ "success": false, "error": { "code", "message", "details" } }`.
- List endpoints paginate (`?page=1&limit=20`).
- Create endpoints honour an `Idempotency-Key` header.

## 8. Local development

- **Full stack (one command):** `docker compose up --build -d`.
- **Host-based:** Postgres in Docker (`docker compose up -d db`), then
  `make backend-dev` and `make frontend-dev`.
- Quality gates: `make fmt`, `make lint`, `make test`, `make check`.

## 9. Build order

The financial engine precedes the dashboard. A dashboard is only a rendering of
the ledger; if the engine is wrong, every chart and budget is wrong.

```
Repository → Auth → Database & Ledger → Accounts & Transactions → Dashboard
→ Budgets → Savings & Bills → Analytics & Reports → Security & Subscription
→ AWS deployment → Beta → Launch
```
