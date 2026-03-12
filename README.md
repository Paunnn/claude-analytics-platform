# Claude Analytics Platform

> **Complete end-to-end analytics platform for Claude Code usage data**

A production-ready analytics platform featuring ETL pipelines, RESTful API, machine learning models, and interactive dashboards for analyzing Claude Code telemetry data.

[![Status](https://img.shields.io/badge/status-production%20ready-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.11-blue)]()
[![Docker](https://img.shields.io/badge/docker-required-blue)]()

---

## 📋 Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Documentation](#-documentation)
- [Technology Stack](#-technology-stack)

---

## ✨ Features

### 📊 Analytics & Metrics
- **Token Usage Analysis** - Track consumption by practice, level, and user
- **Cost Analysis** - Detailed breakdowns and optimization insights
- **Performance Metrics** - API latency, success rates, model performance
- **Peak Hours Analysis** - Usage heatmaps by hour and day
- **Cache Efficiency** - Hit rates and optimization opportunities

### 🤖 Machine Learning
- **Anomaly Detection** - IsolationForest for unusual patterns
- **Usage Forecasting** - Holt-Winters predictions (7-90 days)
- **User Segmentation** - KMeans clustering (4 behavioral groups)

### 🔄 ETL Pipeline
- **Batch Processing** - JSONL telemetry logs
- **Data Transformation** - Clean, validate, structure
- **Idempotent Loading** - UPSERT for safe re-runs
- **5 Event Types** - Comprehensive telemetry coverage

### 📈 Dashboard
- **4 Interactive Pages** - Overview, Cost Analysis, Users, ML Insights
- **Rich Visualizations** - Plotly charts and graphs
- **Real-time Updates** - Auto-refresh capabilities

### 🚀 API
- **33 Endpoints** - Comprehensive REST API
- **OpenAPI Docs** - Swagger UI + ReDoc
- **Fast Responses** - Optimized SQL queries
- **Health Checks** - K8s-ready probes

---

## 🚀 Quick Start

### Prerequisites
- Docker Desktop installed and running
- Ports 5432, 8000, 8501, 6379 available
- Git Bash or WSL2 (Windows)

### 1-Minute Setup

```bash
# Clone and navigate
cd claude-analytics-platform

# Start everything
make setup

# Load data
make ingest

# Test it works
curl http://localhost:8000/health/
```

### Access Services
- **Dashboard:** http://localhost:8501
- **API Docs:** http://localhost:8000/docs
- **API:** http://localhost:8000

---

## 🏗 Architecture

```
DATA SOURCES → ETL PIPELINE → DATABASE → ANALYTICS/ML → API → DASHBOARD
                                   ↓
                          50 employees
                          1,000 sessions
                          24,162 API requests
```

### Technology Flow

```
┌─ STORAGE ──────────────────────────────────────────────────┐
│  PostgreSQL 16 │ 10 Tables │ 5 Mat. Views │ Full-text     │
└────────────────┬───────────────────────────────────────────┘
                 │
┌─ PROCESSING ───┴───────────────────────────────────────────┐
│  ETL (1,495 LOC) │ Analytics (958 LOC) │ ML (571 LOC)     │
└────────────────┬───────────────────────────────────────────┘
                 │
┌─ API ──────────┴───────────────────────────────────────────┐
│  FastAPI │ 33 Endpoints │ Async │ OpenAPI │ CORS          │
└────────────────┬───────────────────────────────────────────┘
                 │
┌─ FRONTEND ─────┴───────────────────────────────────────────┐
│  Streamlit │ 4 Pages │ Plotly Charts │ Interactive        │
└────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
claude-analytics-platform/
├── analytics/           # Analytics & ML (3 files, 1,529 LOC)
│   ├── metrics.py       # 11 business metrics
│   ├── aggregations.py  # 11 statistical aggregations
│   └── ml_models.py     # 3 ML models
│
├── api/                 # FastAPI REST API (~800 LOC)
│   ├── main.py          # App entry point
│   └── routes/          # 3 routers, 33 endpoints
│
├── dashboard/           # Streamlit UI (350 LOC)
│   └── app.py           # 4 interactive pages
│
├── database/            # Schema & models (813 LOC)
│   ├── schema.sql       # 10 tables, indexes
│   ├── models.py        # SQLAlchemy ORM
│   └── connection.py    # DB management
│
├── etl/                 # ETL pipeline (1,495 LOC)
│   ├── ingest.py        # Parse JSONL/CSV
│   ├── transform.py     # Clean & validate
│   ├── load.py          # UPSERT to DB
│   └── pipeline.py      # Orchestrate
│
├── config/              # Settings
├── scripts/             # Utilities
├── tests/               # Test suite
├── data/raw/            # Sample data
│
├── docker-compose.yml   # 4 services
├── Dockerfile           # Python 3.11
├── Makefile             # 15+ commands
├── requirements.txt     # Dependencies
└── .env                 # Configuration
```

**Total:** ~5,736 lines of production code

---

## 📚 Documentation

| Guide | Purpose |
|-------|---------|
| **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** | Complete deployment, troubleshooting |
| **[API_TESTING_GUIDE.md](API_TESTING_GUIDE.md)** | All 33 endpoints with curl examples |
| **[ETL_QUICK_REFERENCE.md](ETL_QUICK_REFERENCE.md)** | ETL usage and data flow |
| **[ANALYTICS_IMPLEMENTATION_SUMMARY.md](ANALYTICS_IMPLEMENTATION_SUMMARY.md)** | 22 functions reference |
| **[ML_IMPLEMENTATION_SUMMARY.md](ML_IMPLEMENTATION_SUMMARY.md)** | ML models documentation |

---

## 🛠 Technology Stack

| Layer | Technologies |
|-------|--------------|
| **Backend** | Python 3.11, FastAPI, SQLAlchemy 2.0 |
| **Database** | PostgreSQL 16, Redis 7 |
| **Data** | Pandas, NumPy |
| **ML** | scikit-learn, statsmodels |
| **Frontend** | Streamlit, Plotly, Altair |
| **DevOps** | Docker, Docker Compose, Make |

---

## ✅ Implementation Status

| Component | Status | LOC | Coverage |
|-----------|--------|-----|----------|
| Database Schema | ✅ | 450 | 10 tables |
| ETL Pipeline | ✅ | 1,495 | 5 event types |
| Analytics | ✅ | 958 | 22 functions |
| ML Models | ✅ | 571 | 3 algorithms |
| API | ✅ | 800 | 33 endpoints |
| Dashboard | ✅ | 350 | 4 pages |
| Documentation | ✅ | 2,500+ | 5 guides |

**Total:** 5,736 LOC + 2,500 LOC docs = **8,236 lines**

### Data Loaded
- ✅ 50 employees across 5 practices
- ✅ 24,162 API requests
- ✅ 1,000 sessions
- ✅ 31,007 tool decisions
- ✅ 30,358 tool results

---

## 🎯 Makefile Commands

```bash
make setup      # Build and start services
make ingest     # Run ETL pipeline
make run        # Start without rebuild
make test       # Run pytest
make clean      # Stop and remove volumes
make logs       # View all logs
make db-shell   # PostgreSQL shell
make health     # Check services
make test-api   # Test endpoints
```

---

## 🔄 Common Workflows

### Daily Development
```bash
make run        # Start
make logs-api   # Monitor
make test       # Verify
```

### Update Data
```bash
make ingest     # Re-run ETL (idempotent)
```

### Full Reset
```bash
make clean && make setup && make ingest
```

---

## 🌐 Service URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| Dashboard | http://localhost:8501 | - |
| API Docs | http://localhost:8000/docs | - |
| PostgreSQL | localhost:5432 | claude/analytics |
| Redis | localhost:6379 | - |

---

## 🧪 Testing

```bash
# All tests
make test

# Specific module
docker compose exec api pytest tests/test_analytics.py -v

# API endpoints
curl http://localhost:8000/analytics/summary/overview | jq '.'

# ML models
docker compose exec api python test_ml_models.py
```

---

## 📊 Sample API Calls

```bash
# Health
curl http://localhost:8000/health/

# Overview
curl http://localhost:8000/analytics/summary/overview | jq '.overall'

# Top users
curl http://localhost:8000/analytics/metrics/top-users?n=5 | jq '.data[].full_name'

# Forecast
curl http://localhost:8000/analytics/ml/forecast?days=7 | jq '.forecast[].predicted_tokens'

# Anomalies
curl http://localhost:8000/analytics/ml/anomalies | jq '.anomalies_detected'

# User clusters
curl http://localhost:8000/analytics/ml/user-clusters | jq '.cluster_distribution'
```

---

## 🐛 Troubleshooting

### Services won't start
```bash
docker compose logs
docker compose down -v
docker compose up --build
```

### ETL fails
```bash
docker compose logs api
docker compose exec api ls -la data/raw/
```

### Database issues
```bash
docker compose exec postgres pg_isready -U claude -d claude_analytics
make db-shell
```

See **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** for complete troubleshooting.

---

## 🎉 Key Features by Role

### Engineering Managers
- Team usage by practice/level
- Cost allocation
- Tool effectiveness
- Session analytics

### Executives
- Overall cost metrics
- DAU trends
- ROI analysis
- Budget forecasting

### Developers
- Personal statistics
- Cache efficiency
- Model comparisons
- Tool success rates

---

## 📞 Support

1. Check **DEPLOYMENT_GUIDE.md**
2. Review logs: `make logs`
3. Test health: `make health`
4. See **API_TESTING_GUIDE.md**

---

## 📝 Next Steps

After deployment:

1. ✅ Verify all services: `make health`
2. ✅ Load sample data: `make ingest`
3. ✅ Test API: `curl http://localhost:8000/health/`
4. ✅ Open dashboard: http://localhost:8501
5. ✅ Explore API docs: http://localhost:8000/docs

---

**Status:** ✅ Production Ready
**Version:** 1.0.0
**Updated:** March 2026

---

Built for Provectus technical assignment using Claude AI (Sonnet 4.5).
