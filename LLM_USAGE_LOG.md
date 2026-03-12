# LLM Usage Log

Tool: Claude Code (claude-sonnet-4-5)

This documents how I used Claude to build the analytics platform for the Provectus assignment. Rough split: ~85% AI-generated code, ~15% manual fixes and verification.

## How I worked with it

I used Claude Code as the primary driver for implementation. The workflow was: write a focused prompt for one module, review the output, run it, fix anything broken, move to the next piece. I didn't let it generate the whole project in one shot — going module by module kept the outputs tight and made bugs easier to isolate.

---

## Phase 1 — Architecture

> "I have a technical assignment to build a Claude Code Usage Analytics Platform. Before writing any code: 1. Analyze the dataset files and describe their schema 2. Propose a full project architecture 3. List all files you will create 4. Ask me any clarifying questions before proceeding. Do not write code yet."

Starting with analysis before code was intentional. Claude correctly identified the five event types in the JSONL logs and proposed the four-layer stack (ETL → PostgreSQL → FastAPI → Streamlit). It produced a complete file tree and asked two clarifying questions: async or sync SQLAlchemy for the ETL, and whether to use Prophet for forecasting. I said sync for ETL simplicity and no Prophet (too heavy, unnecessary C dependency). Both were useful things to resolve upfront rather than mid-implementation.

---

## Phase 2 — Database

> "Implement database/connection.py and database/models.py completely. Use SQLAlchemy 2.0 async style. Models must match schema.sql exactly. Run the file after to verify there are no import errors."

The models came out correctly and matched the schema DDL. No manual changes needed.

---

## Phase 3 — ETL Pipeline

> "Now implement the complete ETL pipeline. The real data files are in data/raw/. Before implementing, read both files first. Then implement in order: 1. etl/ingest.py 2. etl/transform.py 3. etl/load.py 4. etl/pipeline.py Use sync SQLAlchemy for the ETL scripts."

Asking it to read the actual source files before writing code matters — it catches field name and type assumptions before they become silent bugs. The pipeline ran successfully for all tables except `api_requests`, which hit a PostgreSQL parameter limit (see Phase 7). Everything else loaded cleanly on the first run.

---

## Phase 4 — Analytics Engine

> "Implement analytics/metrics.py and analytics/aggregations.py using SYNC SQLAlchemy. Required functions: token_trends_by_practice, cost_by_practice_and_level, peak_usage_heatmap, session_duration_stats, tool_success_rates, cache_efficiency_by_user, model_usage_distribution, top_users_by_cost."

Listing the required functions explicitly kept it on track. It implemented 22 functions total — the 8 I named plus related helpers it inferred from context. All verified against the loaded data.

---

## Phase 5 — ML Models

> "Implement analytics/ml_models.py with 3 classes: AnomalyDetector (IsolationForest), ForecastModel (Holt-Winters), UserClusterer (KMeans 4 clusters). Do NOT use Prophet."

The three model classes were implemented correctly. The bug was in `analytics/__init__.py`, which was generated with wrong import aliases (`UsageForecastModel`, `AnomalyDetectionModel`, `CostOptimizationModel`) that didn't match the actual class names (`ForecastModel`, `AnomalyDetector`, `UserClusterer`). I caught it when the API crashed on startup with an `ImportError`. Fixed manually by correcting the aliases.

---

## Phase 6 — Docker and Deployment

> "Now bring everything together. Fix docker-compose.yml to start all 3 services. Run docker-compose up --build. Create a Makefile."

Generated `docker-compose.yml`, `Dockerfile`, and `Makefile` in one pass. No issues. All four containers started cleanly.

---

## Phase 7 — Bug fix: ETL api_requests chunk size

> "The ETL failed to load api_requests due to batch size too large. Fix etl/load.py - change insert logic to use chunks of 100 records."

Root cause: the bulk insert was binding all rows in a single statement. The `api_requests` table has enough columns that a full-batch insert exceeded PostgreSQL's 65,535 bound-parameter limit. Chunking to 100 records per insert fixed it. All 24,162 rows loaded correctly after the change.

---

## Phase 8 — Dashboard fix

> "The Streamlit dashboard is running inside Docker and trying to connect to http://api:8000 but getting connection refused. Fix dashboard/utils/data_loader.py."

Two problems found by reading `docker compose logs api`. First, the API was crashing on startup because of the `__init__.py` import aliases from Phase 5 — that crash prevented any connections from succeeding. Second, `fetch_from_api` in `data_loader.py` was a stub (`pass`) and never made actual HTTP calls. Fixed both. Also found a column name mismatch on the Cost Analysis page: the cache-efficiency chart was referencing `user_email` but the API returns `email`. Fixed that too.

---

## Phase 9 — Project cleanup and documentation rewrite

> "Do a full project cleanup: DELETE all unnecessary files (*_SUMMARY.md, *_GUIDE.md, *_REFERENCE.md, test_*.py in root, llm_history_raw.jsonl, TODO/NOTES/draft files). REWRITE README.md to sound like a human wrote it — no bullet point overload, no '✅ Complete' checkboxes, no '🚀 Key Features' with emojis, plain technical prose, under 150 lines. REWRITE LLM_USAGE_LOG.md the same way. Check every other .md file."

Generated docs tend to read like marketing copy. The rewrite brief was explicit: no emojis, no checkbox lists, no inflated section headers. Claude got it right on the first pass for README.md and this log. Deleted eight files that were either stubs, redundant, or AI-generated noise that wouldn't belong in a real project repo.

---

## Phase 10 — Dashboard pages debugging and fix

> "The Streamlit dashboard only shows the 'app' tab, other pages don't load. The browser console shows 404 errors when calling the API. Diagnose and fix: check docker compose logs for both services, verify API health, check dashboard/pages/ for all page files and import errors. Fix whatever is broken, restart, confirm all 5 pages working."

The API was failing silently on certain routes due to incomplete route registration. Also found that three of the five dashboard pages were stubs — function signatures present, bodies missing. Implemented all five pages (overview, usage analysis, cost analysis, user insights, tool analytics) and fixed the app.py landing page routing.

---

## Phase 11 — Data verification and presentation

> "Check that data is shown correctly and that everything is good. Make a presentation — make sure it's professional. Research presentation design."

Used the loaded dataset to verify chart accuracy against direct SQL queries. Built a 5-slide PDF presentation with real data: cost by practice, model distribution, peak usage heatmap, top users, and cache efficiency. First version was flagged as looking AI-generated — revised to use varied layouts, remove template conventions (uniform bullets, header+body pattern), and let the data drive the structure.

---

## Phase 12 — Real-time and statistical feature audit

> "Check what real-time and advanced statistical features are currently implemented in the codebase. Look in analytics/metrics.py, analytics/aggregations.py, api/ routes, dashboard/ pages, docker-compose.yml (Redis). List what exists and what's missing for: 1. Real-time capabilities (Redis, WebSocket, streaming) 2. Advanced statistical analysis (correlations, percentiles, cohort analysis). Don't implement anything yet, just report what's there."

This was a deliberate audit before adding features. Findings: Redis container was defined and healthy but zero application code touched it. `calculate_user_retention()` and `calculate_correlation_matrix()` were fully implemented in `aggregations.py` but had no API routes. Percentiles, cohort aggregations, rolling averages, and all three ML models were wired through properly. No WebSocket or streaming code existed anywhere.

---

## Phase 13 — Expose buried endpoints and add Redis caching

> "Fix these 3 quick wins: 1. Expose the 2 buried endpoints — GET /analytics/aggregations/correlation-matrix and GET /analytics/aggregations/retention. 2. Add Redis caching to GET /analytics/summary/overview for 60 seconds using redis-py, fall back silently if Redis unavailable. 3. Add a Refresh button to the Overview dashboard page."

Straightforward implementation. Added `_get_redis()` helper with a 1-second connect timeout and silent `except` so Redis failures don't surface to callers. Both new endpoints were one-liners wrapping existing engine methods. The dashboard refresh button calls `st.cache_data.clear()` — simpler and more honest than a polling loop.

---

## What I'd do differently

I'd review `__init__.py` re-exports immediately after generating any module with classes. Claude tends to generate module-level exports in a separate pass and sometimes uses different names than the actual implementations. It's a two-second check that would have avoided the startup crash in Phase 8.

I'd also run a quick `grep -r "pass$"` across generated stubs before committing — the unimplemented `fetch_from_api` would have shown up immediately.
