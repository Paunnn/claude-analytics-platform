# Claude Analytics Platform

Analytics platform for Claude Code telemetry data. It processes JSONL event logs and a CSV user roster, stores everything in PostgreSQL, exposes a REST API, and renders an interactive Streamlit dashboard.

The dataset covers 50 engineers across 5 practices, producing roughly 86,500 events over three months.

## Running it

You need Docker Desktop. Ports 5432, 6379, 8000, and 8501 must be free.

```bash
make setup    # builds images and starts all four services
make ingest   # runs the ETL pipeline against data/raw/
```

Dashboard: http://localhost:8501
API docs: http://localhost:8000/docs

To stop and wipe volumes: `make clean`

## Architecture

Raw data flows through an ETL pipeline into PostgreSQL, then gets queried by a FastAPI backend that the dashboard calls. The pipeline and API share one Docker image — only the startup command differs between the two services.

```
data/raw/ (JSONL + CSV)
  → etl/           parse, transform, bulk-insert
  → PostgreSQL      10 tables, date and user indexes
  → api/            FastAPI, 33 endpoints
  → dashboard/      Streamlit, 5 pages
```

PostgreSQL is the primary store. Redis is used for short-term caching of expensive aggregation endpoints (60-second TTL); the API falls back silently if Redis is unavailable.

The API also exposes a WebSocket endpoint at `ws://localhost:8000/ws/metrics` that streams live metric snapshots from the database on a configurable interval (default 5 seconds). The client can adjust the interval at runtime by sending `{"interval": N}`. A test client is at `scripts/ws_client.py`.

The analytics layer (`analytics/`) runs inside the API process; there's no separate worker. The three ML models (IsolationForest for anomaly detection, Holt-Winters for forecasting, KMeans for user segmentation) are instantiated on demand per request, not preloaded at startup.

## API endpoints

Full interactive docs are at http://localhost:8000/docs. The main ones:

| Endpoint | What it does |
|---|---|
| `GET /health/` | Liveness check |
| `GET /analytics/summary/overview` | Aggregated cost, requests, active users |
| `GET /analytics/metrics/cost?group_by=practice` | Cost breakdown by practice or level |
| `GET /analytics/metrics/top-users?n=10` | Top users by spend |
| `GET /analytics/metrics/cache-efficiency` | Cache hit rates per user |
| `GET /analytics/models/comparison` | Request distribution across models |
| `GET /analytics/ml/forecast?days=7` | Holt-Winters token forecast |
| `GET /analytics/ml/anomalies` | IsolationForest anomaly list |
| `GET /analytics/ml/user-clusters` | KMeans user segments |
| `GET /users/` | User list with practice/level filters |

## Project layout

```
analytics/      metrics, aggregations, and ML models
api/            FastAPI app and route handlers
dashboard/      Streamlit pages and data fetchers
database/       SQLAlchemy models, schema DDL, connection helpers
etl/            ingest, transform, load, pipeline orchestrator
config/         settings module
data/raw/       source JSONL and CSV files
tests/          pytest suite
```

## Common tasks

```bash
make setup          # build and start
make ingest         # run ETL (idempotent, safe to re-run)
make test           # run pytest
make logs           # tail all service logs
make logs-api       # tail API only
make db-shell       # psql into the database
make health         # check all service health endpoints
make clean          # stop containers and drop volumes
```

Built for the Provectus Gen AI Internship technical assignment, March 2026.

## LLM Usage Log

**Tool:** Claude Code (claude-sonnet-4-6) — used as the primary implementation driver throughout. Rough split: ~85% AI-generated code, ~15% manual fixes and verification.

**Workflow:** one focused prompt per module, review output, run it, fix what broke, move on. Going module by module kept outputs tight and bugs easy to isolate.

**Key prompts:**

*Architecture (before any code):*
> "Analyze the dataset files and describe their schema. Propose a full project architecture. List all files you will create. Ask clarifying questions before proceeding. Do not write code yet."

Claude identified the five event types in the JSONL logs and proposed the four-layer stack (ETL → PostgreSQL → FastAPI → Streamlit). It asked whether to use async SQLAlchemy and Prophet — I said sync for simplicity and no Prophet (unnecessary C dependency). Resolved upfront instead of mid-implementation.

*ETL pipeline:*
> "Implement the complete ETL pipeline. Read the actual data files in data/raw/ first, then implement etl/ingest.py, etl/transform.py, etl/load.py, etl/pipeline.py in order."

Asking it to read source files before writing catches field name assumptions before they become silent bugs.

*ML models:*
> "Implement analytics/ml_models.py with 3 classes: AnomalyDetector (IsolationForest), ForecastModel (Holt-Winters), UserClusterer (KMeans 4 clusters). Do NOT use Prophet."

**How I validated output:**

- Ran every module immediately after generation and checked for import errors
- Verified ETL row counts against source file line counts (24,162 api_requests)
- Cross-checked dashboard chart values against direct `psql` queries on the same aggregations
- Caught a bug where `analytics/__init__.py` exported wrong class aliases — found it from an `ImportError` on API startup, fixed manually
- Caught unimplemented stubs (`fetch_from_api` was `pass`) by reading docker compose logs when the dashboard showed no data

Full phase-by-phase detail is in [LLM_USAGE_LOG.md](./LLM_USAGE_LOG.md).
