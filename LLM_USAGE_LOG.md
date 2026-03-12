# LLM Usage Log — Claude Analytics Platform

## Overview

This document records the AI-assisted development process for the Claude Analytics Platform, a full-stack application for tracking and visualising Claude Code usage across an organisation.

| Field | Detail |
|---|---|
| **Primary AI tool** | Claude Code (claude-sonnet-4-5) |
| **Development period** | 2026-03 |
| **AI code contribution** | ~85% generated, ~15% manual fixes |
| **Total events ingested** | 92,930 |

---

## Development Phases

### 1. Initial Project Analysis and Architecture Design

**Prompt theme:** "Analyse this JSONL telemetry format and design a full-stack analytics platform."

Claude reviewed the raw Claude Code telemetry schema (JSONL event logs + CSV user roster) and proposed the overall architecture:

- PostgreSQL for persistent storage with a normalised schema
- FastAPI backend serving a REST analytics API
- Streamlit dashboard for interactive visualisation
- ETL pipeline for ingesting JSONL/CSV sources
- Docker Compose for local orchestration

Output: directory structure, module boundaries, dependency graph, and a phased implementation plan.

---

### 2. Database Models and Connection Setup

**Prompt theme:** "Implement SQLAlchemy models and Alembic migrations for the telemetry schema."

Claude generated:

- `database/models.py` — ORM models for `sessions`, `api_requests`, `tool_uses`, `project_activities`, `users`
- `database/connection.py` — engine factory, session management, health-check helpers
- `database/schema.sql` — raw DDL used as the Docker init script
- Index strategy for the most common query patterns (date range, user, project)

---

### 3. ETL Pipeline Implementation (JSONL / CSV)

**Prompt theme:** "Write an ETL pipeline that reads Claude Code JSONL event files and a CSV user roster and loads them into PostgreSQL."

Claude implemented:

- `etl/extractors/` — JSONL stream reader, CSV reader with type coercion
- `etl/transformers/` — event normalisation, deduplication, foreign-key resolution
- `etl/loaders/` — bulk-insert with `INSERT … ON CONFLICT DO NOTHING`
- `etl/pipeline.py` — orchestrator with progress logging and error recovery
- `scripts/run_etl.py` — CLI entry point

**Bug found during execution (see §8):** chunk-size parameter caused silent truncation on `api_requests` bulk inserts.

---

### 4. Analytics Engine (22 Metric Functions)

**Prompt theme:** "Implement an analytics engine covering cost, usage, productivity, and adoption metrics."

Claude produced `analytics/metrics.py` (`MetricsEngine`) with 22 functions across four categories:

| Category | Example metrics |
|---|---|
| Cost | `total_cost`, `cost_by_user`, `cost_by_practice`, `cost_trend` |
| Usage | `session_count`, `tokens_per_session`, `active_users_daily` |
| Productivity | `tool_adoption_rate`, `avg_turns_per_session`, `code_acceptance_rate` |
| Adoption | `new_user_cohort`, `retention_by_week`, `feature_penetration` |

Also generated `analytics/aggregations.py` (`AggregationEngine`) and `analytics/insights.py` (`InsightGenerator`).

---

### 5. ML Models (IsolationForest, Holt-Winters, KMeans)

**Prompt theme:** "Add ML-based anomaly detection, usage forecasting, and user clustering."

Claude implemented `analytics/ml_models.py` with three model classes:

- **`AnomalyDetector`** — wraps `sklearn.ensemble.IsolationForest`; detects cost and usage spikes per user/project
- **`ForecastModel`** — Holt-Winters exponential smoothing (`statsmodels`) for 7/30-day cost and token forecasts
- **`UserClusterer`** — KMeans clustering (`sklearn`) to segment users by usage behaviour (power, moderate, occasional)

Each class exposes `fit`, `predict`/`forecast`/`cluster`, and `explain` methods.

*Note: `analytics/__init__.py` originally imported these under incorrect alias names (`UsageForecastModel`, `AnomalyDetectionModel`, `CostOptimizationModel`), which caused an `ImportError` at API startup. Fixed in a later session (see §9).*

---

### 6. FastAPI Endpoints Implementation

**Prompt theme:** "Expose the analytics engine through a versioned REST API with filtering and pagination."

Claude generated:

- `api/main.py` — app factory, CORS, lifespan hooks, structured logging
- `api/routes/analytics.py` — cost, usage, productivity, and insight endpoints
- `api/routes/users.py` — user list, user detail, team endpoints
- `api/routes/health.py` — `/health` and `/ready` liveness/readiness probes
- `api/schemas.py` — Pydantic v2 request/response models
- `api/dependencies.py` — DB session injection, pagination helpers

---

### 7. Streamlit Dashboard Implementation

**Prompt theme:** "Build a Streamlit dashboard with Overview, Cost Analysis, User Analytics, and Insights pages."

Claude generated:

- `dashboard/app.py` — multi-page router with sidebar navigation
- `dashboard/pages/` — one module per page (`overview.py`, `cost_analysis.py`, `user_analytics.py`, `insights.py`, `ml_insights.py`)
- `dashboard/utils/data_loader.py` — cached API fetch helpers (`fetch_from_api`, `load_key_metrics`, `load_cost_trend`, etc.)
- `dashboard/utils/charts.py` — reusable Plotly chart builders
- `dashboard/components/` — shared UI components (metric cards, filters, tables)

*Note: `fetch_from_api` was initially left as a stub (`pass`). Implemented in a later session to read `API_URL` from the environment and make real HTTP requests.*

---

### 8. Docker Setup and Deployment

**Prompt theme:** "Containerise the platform with Docker Compose including Postgres, Redis, API, and dashboard."

Claude generated:

- `Dockerfile` — multi-stage build; single image used for both `api` and `dashboard` services
- `docker-compose.yml` — four services (`postgres`, `redis`, `api`, `dashboard`) on a shared bridge network with health-checks and `depends_on` ordering
- `Makefile` — convenience targets (`make up`, `make etl`, `make logs`, `make test`)
- `.env.example` — environment variable documentation

---

### 9. Bug Fixes

#### 9a. ETL `api_requests` Bulk Insert Chunk Size

**Found during:** actual ETL execution against the full 92,930-event dataset.

**Symptom:** `api_requests` table row count was lower than expected after a full load; no error was raised.

**Root cause:** the bulk-insert helper was using a chunk size that exceeded the PostgreSQL parameter limit (`$1 … $65535`) for wide rows, causing later chunks to be silently skipped.

**Fix:** reduced chunk size in `etl/loaders/bulk_insert.py` so that `num_rows × num_columns ≤ 65535`.

#### 9b. `analytics/__init__.py` Wrong Import Names (ImportError at API Startup)

**Found during:** `docker compose logs api` investigation in March 2026.

**Symptom:** API container crashed immediately with `ImportError: cannot import name 'UsageForecastModel'`.

**Root cause:** `analytics/__init__.py` referenced three names that did not exist in `ml_models.py`.

**Fix:** updated imports to match the actual class names (`ForecastModel`, `AnomalyDetector`, `UserClusterer`).

#### 9c. `fetch_from_api` Stub Never Implemented

**Found during:** same debugging session as 9b.

**Symptom:** dashboard showed no data despite the API being healthy.

**Fix:** implemented `fetch_from_api` in `dashboard/utils/data_loader.py` to read `API_URL` from the environment and issue real HTTP GET requests.

---

## Validation Approach

| Step | Method |
|---|---|
| Module-level imports | `python -c "import <module>"` after each phase |
| ETL record counts | `verify_database.py` — confirmed 92,930 events loaded |
| API endpoint health | `pytest tests/` + manual `curl /health` returning `200 OK` |
| Dashboard rendering | Ran `streamlit run dashboard/app.py` locally before containerising |
| Container integration | `docker compose up` end-to-end; checked all four service logs |

---

## Reflections

- AI code generation was most effective for boilerplate-heavy tasks (ORM models, Pydantic schemas, Docker config) and for generating consistent patterns across many similar functions (the 22 metric functions).
- Manual intervention was needed for: catching the chunk-size ETL bug (required running real data), fixing the `__init__.py` import aliases (class naming mismatch between generation sessions), and wiring up the `fetch_from_api` stub that was missed.
- The 85/15 split reflects a workflow where Claude drafted full modules and a human reviewed, ran, and patched the results.
