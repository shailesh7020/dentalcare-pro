# DentalCare Pro - Developer & Contributor Guide

## 1. Repository & Monorepo Architecture

DentalCare Pro is organized as a unified polyglot enterprise monorepo:

```
dentalcare-pro/
├── backend/            # Python 3.12+ / FastAPI Async REST API Engine
│   ├── app/
│   │   ├── api/        # Domain REST API routers (v1 endpoints)
│   │   ├── core/       # Configurations, logging, telemetry
│   │   ├── models/     # SQLAlchemy 2.0 async ORM models
│   │   ├── schemas/    # Pydantic v2 validation contracts
│   │   ├── services/   # Business logic and domain services
│   │   └── workers/    # Asynchronous task worker queues
│   └── tests/          # Pytest regression & master E2E test suites
├── apps/
│   ├── web/            # Next.js 16 (App Router / Turbopack) React 19 Frontend
│   └── mobile/         # Flutter 3.24+ Cross-Platform Android/iOS Application
├── helm/dentalcare/    # Kubernetes Helm 3 Charts
├── terraform/          # Cloud-Agnostic Infrastructure as Code
├── postgres/           # PostgreSQL 17 HA & PgBouncer configurations
├── monitoring/         # Prometheus, Grafana, Loki & Alertmanager configurations
└── docs/               # Manuals, Ops Runbooks, and Compliance Reports
```

---

## 2. Local Development Setup

### Prerequisites
- Python 3.12 or 3.13
- Node.js 22 LTS & pnpm 11+
- Flutter SDK 3.24+
- Docker & Docker Compose

### Step 2.1: Start Local Supporting Services
```bash
docker-compose up -d db redis
```

### Step 2.2: Backend API Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Step 2.3: Next.js Web Frontend Setup
```bash
cd apps/web
pnpm install
pnpm dev
```
Navigate to `http://localhost:3000`.

### Step 2.4: Flutter Mobile Setup
```bash
cd apps/mobile
flutter pub get
flutter run -d chrome  # Or target iOS Simulator / Android Emulator
```

---

## 3. Coding Standards & Conventions

1. **Python / Backend**:
   - Enforce 100% type annotations (`from __future__ import annotations`).
   - Lint with **Ruff**: `ruff check app/ tests/` (must maintain 0 errors, 0 warnings).
   - Test with **Pytest**: `pytest tests/ -q` (all tests must pass with >90% coverage).
2. **TypeScript / Web**:
   - Strict TypeScript (`tsconfig.json` `strict: true`).
   - Tailwind CSS for all utility styling with accessible contrast.
   - Run Vitest: `npx vitest run`.
3. **Dart / Mobile**:
   - Clean Architecture: Presentation, Domain, Data, Core.
   - Run mobile test runner: `python apps/mobile/test/test_runner.py`.
