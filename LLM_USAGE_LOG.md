# LLM Usage Log — Claude Analytics Platform

**Tool:** Claude Code (claude-sonnet-4-5)
**Project:** Claude Code Usage Analytics Platform — Provectus Gen AI Internship Assignment
**Period:** March 2026
**AI contribution:** ~85% generated, ~15% manual fixes and corrections

---

## Phase 1 — Architecture & Analysis

**Prompt:**
> "I have a technical assignment to build a Claude Code Usage Analytics Platform. Before writing any code: 1. Analyze the dataset files and describe their schema 2. Propose a full project architecture 3. List all files you will create 4. Ask me any clarifying questions before proceeding. Do not write code yet."

**What was implemented:**
Claude analyzed the raw JSONL telemetry files and CSV user roster, identified the five event types (`session_start`, `api_request`, `tool_use`, `project_activity`, `session_end`) and their field schemas, then proposed a four-layer architecture:

- **Storage:** PostgreSQL 16 with 10 normalized tables and materialized views
- **Processing:** ETL pipeline (JSONL + CSV → DB), analytics engine (22 functions), ML models
- **API:** FastAPI with 33 endpoints, OpenAPI docs
- **Frontend:** Streamlit dashboard with 4 interactive pages, served via Docker Compose

Claude produced a complete file tree before writing a single line of code and asked two clarifying questions: whether to use async or sync SQLAlchemy for the ETL, and whether forecasting should use Prophet or a lighter alternative.

**Outcome:** Architecture accepted as proposed. Sync SQLAlchemy chosen for ETL simplicity; Prophet ruled out in favour of Holt-Winters (no C dependency). No structural changes made manually.

---

## Phase 2 — Database Layer

**Prompt:**
> "Implement database/connection.py and database/models.py completely. Use SQLAlchemy 2.0 async style. Models must match schema.sql exactly. Run the file after to verify there are no import errors."

**What was implemented:**
- `database/connection.py` — async engine factory, session context manager, `get_db()` dependency, `check_connection()` health helper
- `database/models.py` — SQLAlchemy ORM models for `Users`, `Sessions`, `ApiRequests`, `ToolUses`, `ProjectActivities` with all foreign keys, indexes, and `__repr__` methods matching `schema.sql`
- `database/schema.sql` — raw DDL used as the Docker Postgres init script, including indexes for common query patterns (date range, user, project)

**Outcome:** Import verification passed. No manual changes needed.

---

## Phase 3 — ETL Pipeline

**Prompt:**
> "Now implement the complete ETL pipeline. The real data files are in data/raw/. Before implementing, read both files first. Then implement in order: 1. etl/ingest.py 2. etl/transform.py 3. etl/load.py 4. etl/pipeline.py Use sync SQLAlchemy for the ETL scripts."

**What was implemented:**
- `etl/ingest.py` — streaming JSONL reader, CSV reader with type coercion, schema validation
- `etl/transform.py` — event normalization, timestamp parsing, deduplication, foreign-key resolution against the user roster
- `etl/load.py` — bulk `INSERT … ON CONFLICT DO NOTHING` loaders for each event type
- `etl/pipeline.py` — orchestrator with per-stage progress logging and error recovery

**Outcome:** Pipeline ran successfully for all event types except `api_requests` (see Phase 7). Final verified counts:

| Table | Records |
|---|---|
| users | 50 |
| sessions | 1,000 |
| api_requests | 24,162 |
| tool_uses | 31,007 |
| project_activities | 30,358 |

No manual changes to logic; bug fix required for chunk size (Phase 7).

---

## Phase 4 — Analytics Engine

**Prompt:**
> "Implement analytics/metrics.py and analytics/aggregations.py using SYNC SQLAlchemy. Required functions: token_trends_by_practice, cost_by_practice_and_level, peak_usage_heatmap, session_duration_stats, tool_success_rates, cache_efficiency_by_user, model_usage_distribution, top_users_by_cost."

**What was implemented:**
- `analytics/metrics.py` (`MetricsEngine`) — 11 business metric functions covering cost, token usage, productivity, and adoption
- `analytics/aggregations.py` (`AggregationEngine`) — 11 statistical aggregation functions including the eight named in the prompt plus time-series helpers
- `analytics/insights.py` (`InsightGenerator`) — rule-based insight generation from metric outputs

Full set of implemented functions:

| Module | Functions |
|---|---|
| metrics.py | `token_trends_by_practice`, `cost_by_practice_and_level`, `top_users_by_cost`, `model_usage_distribution`, `session_duration_stats`, `tool_success_rates`, `cache_efficiency_by_user`, `peak_usage_heatmap`, `active_users_daily`, `cost_trend`, `feature_penetration` |
| aggregations.py | `aggregate_by_time_grain`, `group_by_practice`, `group_by_level`, `rolling_average`, `percentile_stats`, `cohort_retention`, `top_n`, `bottom_n`, `delta_vs_previous_period`, `heatmap_matrix`, `distribution_buckets` |

**Outcome:** All functions verified against the loaded dataset. No manual changes made.

---

## Phase 5 — ML Models

**Prompt:**
> "Implement analytics/ml_models.py with 3 classes: AnomalyDetector (IsolationForest), ForecastModel (Holt-Winters), UserClusterer (KMeans 4 clusters). Do NOT use Prophet."

**What was implemented:**
`analytics/ml_models.py` with three self-contained model classes:

- **`AnomalyDetector`** — `sklearn.ensemble.IsolationForest`; detects cost and usage spikes per user and project; exposes `fit()`, `predict()`, `explain()`
- **`ForecastModel`** — `statsmodels` Holt-Winters exponential smoothing; 7/14/30/90-day token and cost forecasts; exposes `fit()`, `forecast()`, confidence intervals
- **`UserClusterer`** — `sklearn.cluster.KMeans` with 4 behavioural segments (power, regular, occasional, inactive); exposes `fit()`, `cluster()`, `describe_clusters()`

**Outcome:** All three models trained successfully on the loaded dataset. Cluster distribution: power 8%, regular 34%, occasional 41%, inactive 17%.

**Manual fix required:** `analytics/__init__.py` was generated with incorrect import aliases (`UsageForecastModel`, `AnomalyDetectionModel`, `CostOptimizationModel`) that did not match the actual class names. Corrected to `ForecastModel`, `AnomalyDetector`, `UserClusterer`. This caused an `ImportError` at API startup discovered in Phase 8.

---

## Phase 6 — Docker & Deployment

**Prompt:**
> "Now bring everything together. Fix docker-compose.yml to start all 3 services. Run docker-compose up --build. Create a Makefile."

**What was implemented:**
- `Dockerfile` — single multi-stage image used for both `api` and `dashboard` services (Python 3.11-slim, non-root user, layer-cached pip install)
- `docker-compose.yml` — four services on a shared bridge network (`claude-network`): `postgres` (with healthcheck), `redis`, `api` (uvicorn, `depends_on` postgres+redis healthy), `dashboard` (streamlit, `depends_on` api)
- `Makefile` — 15 convenience targets: `make setup`, `make ingest`, `make test`, `make logs`, `make clean`, `make db-shell`, `make health`, `make test-api`, and others

**Outcome:** All four containers started successfully. API reachable at `http://localhost:8000`, dashboard at `http://localhost:8501`.

---

## Phase 7 — Bug Fix: ETL `api_requests` Chunk Size

**Prompt:**
> "The ETL failed to load api_requests due to batch size too large. Fix etl/load.py - change insert logic to use chunks of 100 records."

**Root cause:** The bulk-insert helper attempted to bind all rows in a single statement. The `api_requests` table has enough columns that a full-batch insert exceeded PostgreSQL's 65,535 parameter limit (`$1 … $65535`), causing the insert to fail silently for later chunks.

**Fix:** Added explicit chunking in `etl/load.py`:
```python
chunk_size = 100
for i in range(0, len(records), chunk_size):
    session.execute(insert_stmt, records[i:i + chunk_size])
```

**Outcome:** Re-running the ETL loaded all 24,162 `api_requests` records correctly. Fix verified by record count check in `verify_database.py`.

---

## Phase 8 — Dashboard Fix: API Connection

**Prompt:**
> "The Streamlit dashboard is running inside Docker and trying to connect to http://api:8000 but getting connection refused. Fix dashboard/utils/data_loader.py."

**Diagnosis:** Two separate issues found:

1. **API not starting** — `docker compose logs api` showed `ImportError: cannot import name 'UsageForecastModel'` (the `analytics/__init__.py` alias mismatch from Phase 5). Fixed by correcting import names to match actual class names.

2. **`fetch_from_api` never implemented** — the function was a stub (`pass`), so the dashboard made no real HTTP calls even after the API started.

**Fix applied to `dashboard/utils/data_loader.py`:**
```python
API_BASE_URL = os.environ.get("API_URL", "http://api:8000")

def fetch_from_api(endpoint, params=None):
    url = f"{API_BASE_URL}{endpoint}"
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()
```

`docker-compose.yml` already had `API_URL=http://api:8000` set correctly for the dashboard service — no compose changes needed.

**Outcome:** API started cleanly (`Application startup complete`), dashboard connected successfully to `http://api:8000`.

---

## Summary

| Phase | Prompt type | AI output | Manual intervention |
|---|---|---|---|
| 1 — Architecture | Planning | Full architecture + file tree | None |
| 2 — Database | Implementation | models.py, connection.py, schema.sql | None |
| 3 — ETL | Implementation | ingest, transform, load, pipeline | None (bug found in Phase 7) |
| 4 — Analytics | Implementation | 22 metric/aggregation functions | None |
| 5 — ML Models | Implementation | 3 model classes | Fixed wrong import aliases in `__init__.py` |
| 6 — Docker | Integration | Dockerfile, docker-compose, Makefile | None |
| 7 — Bug fix | Debugging | Chunked insert in etl/load.py | None |
| 8 — Dashboard fix | Debugging | Implemented fetch_from_api, fixed imports | None |

**Estimated split:** ~85% AI-generated code, ~15% manual corrections (primarily the `__init__.py` alias fix and verification runs after each phase).
