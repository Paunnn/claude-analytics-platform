# Claude Analytics Platform - Deployment Guide

## ✅ Prerequisites

1. **Docker Desktop** installed and running
   - Download: https://www.docker.com/products/docker-desktop/
   - Ensure Docker Compose is included (v2.0+)

2. **Make** (optional but recommended for Windows)
   - Git Bash includes make
   - Or use WSL2

3. **Port Availability**
   - 5432 (PostgreSQL)
   - 8000 (API)
   - 8501 (Dashboard)
   - 6379 (Redis)

---

## 🚀 Quick Start

### Option 1: Using Makefile (Recommended)

```bash
# 1. Build and start all services
make setup

# 2. Load data
make ingest

# 3. Test API
make test-api

# 4. View logs
make logs
```

### Option 2: Using Docker Compose Directly

```bash
# 1. Start services
docker compose up --build -d

# 2. Check services are healthy
docker compose ps

# 3. Load data
docker compose exec api python scripts/run_etl.py

# 4. Test API
curl http://localhost:8000/health/
```

---

## 📋 Step-by-Step Deployment

### Step 1: Build and Start Services

```bash
cd claude-analytics-platform
docker compose up --build -d
```

**Expected output:**
```
✅ Network claude-network created
✅ Volume postgres_data created
✅ Volume redis_data created
✅ Container claude-analytics-db started
✅ Container claude-analytics-redis started
✅ Container claude-analytics-api started
✅ Container claude-analytics-dashboard started
```

**Verify services:**
```bash
docker compose ps
```

You should see:
- postgres (healthy)
- redis (healthy)
- api (running)
- dashboard (running)

### Step 2: Check Health

```bash
# Check API health
curl http://localhost:8000/health/
```

**Expected response:**
```json
{
  "status": "healthy",
  "service": "claude-analytics-api"
}
```

```bash
# Check database readiness
curl http://localhost:8000/health/ready
```

**Expected response:**
```json
{
  "status": "ready",
  "checks": {
    "database": "connected"
  },
  "environment": "development"
}
```

### Step 3: Load Data (ETL Pipeline)

```bash
docker compose exec api python scripts/run_etl.py
```

**Expected output:**
```
======================================================================
 STARTING ETL PIPELINE
======================================================================

INFO - PHASE 1: Ingestion
INFO - Reading telemetry logs from data/raw/telemetry_logs.jsonl
INFO - Loaded 50 events
INFO - Reading employees from data/raw/employees.csv
INFO - Loaded 50 employees

INFO - PHASE 2: Transformation
INFO - Transforming employees...
INFO - Employees: 50 records
INFO - Transforming API requests...
INFO - API requests: 24,162 records
INFO - Extracting sessions...
INFO - Sessions: 1,000 records

INFO - PHASE 3: Loading
INFO - Loading employees...
INFO - Loaded 50 employees
INFO - Loading sessions...
INFO - Loaded 1,000 sessions
INFO - Loading API requests...
INFO - Loaded 24,162 API requests

INFO - PHASE 4: Post-processing
INFO - Refreshing materialized views...

======================================================================
 ETL PIPELINE COMPLETE
======================================================================

📊 Summary Statistics:
  Total events processed:    50
  Employees loaded:          50
  Sessions extracted:        1,000
  API requests loaded:       24,162
  Tool decisions loaded:     31,007
  Tool results loaded:       30,358

✅ ETL pipeline completed successfully!
```

### Step 4: Test API Endpoints

```bash
# 1. Overview summary
curl http://localhost:8000/analytics/summary/overview | jq '.'

# 2. Token usage metrics
curl http://localhost:8000/analytics/metrics/token-usage | jq '.'

# 3. Top users by cost
curl http://localhost:8000/analytics/metrics/top-users?n=10 | jq '.'

# 4. Peak usage hours
curl http://localhost:8000/analytics/metrics/peak-hours | jq '.'

# 5. User cohorts
curl http://localhost:8000/analytics/aggregations/user-cohorts?cohort_field=practice | jq '.'

# 6. ML Forecast
curl http://localhost:8000/analytics/ml/forecast?days=7 | jq '.'

# 7. Anomaly detection
curl http://localhost:8000/analytics/ml/anomalies | jq '.'

# 8. User clusters
curl http://localhost:8000/analytics/ml/user-clusters | jq '.'
```

### Step 5: Access Dashboard

Open your browser:
- **Dashboard:** http://localhost:8501
- **API Docs:** http://localhost:8000/docs
- **API ReDoc:** http://localhost:8000/redoc

---

## 🔍 Verification

### Verify Database

```bash
# Open PostgreSQL shell
docker compose exec postgres psql -U claude -d claude_analytics

# Check record counts
SELECT
  'employees' as table, COUNT(*) as count FROM employees
UNION ALL SELECT 'sessions', COUNT(*) FROM sessions
UNION ALL SELECT 'api_requests', COUNT(*) FROM api_requests
UNION ALL SELECT 'tool_results', COUNT(*) FROM tool_results;

# Exit
\q
```

**Expected:**
```
    table      | count
---------------+-------
 employees     |    50
 sessions      | 1,000
 api_requests  | 24,162
 tool_results  | 30,358
```

### Verify API

```bash
# Get users
curl http://localhost:8000/users/ | jq '.total'

# Get practices
curl http://localhost:8000/users/practices

# Get model comparison
curl http://localhost:8000/analytics/models/comparison | jq '.total_models'
```

### Verify Dashboard

1. Open http://localhost:8501
2. You should see 4 pages:
   - 📊 Overview
   - 💰 Cost Analysis
   - 👥 Users
   - 🤖 ML Insights

3. Navigate through each page to verify data loads

---

## 📊 Available Makefile Commands

```bash
make help          # Show all commands
make setup         # Build and start all services
make ingest        # Run ETL pipeline
make run           # Start services (without rebuild)
make test          # Run pytest
make clean         # Stop and remove volumes
make logs          # Show all logs
make logs-api      # Show API logs only
make logs-dashboard # Show dashboard logs
make logs-db       # Show database logs
make restart       # Restart services
make db-shell      # Open PostgreSQL shell
make api-shell     # Open bash in API container
make health        # Check service health
make test-api      # Test API endpoints
make ps            # Show running containers
make stats         # Show resource usage
make full          # Complete setup + ingest + test
```

---

## 🐛 Troubleshooting

### Services won't start

```bash
# Check Docker is running
docker ps

# Check logs
docker compose logs

# Rebuild from scratch
docker compose down -v
docker compose build --no-cache
docker compose up -d
```

### PostgreSQL not ready

```bash
# Wait for PostgreSQL
docker compose exec postgres pg_isready -U claude -d claude_analytics

# Check PostgreSQL logs
docker compose logs postgres
```

### API errors

```bash
# Check API logs
docker compose logs api

# Check if dependencies are installed
docker compose exec api pip list

# Rebuild API
docker compose up --build api
```

### Dashboard errors

```bash
# Check dashboard logs
docker compose logs dashboard

# Test API connectivity from dashboard
docker compose exec dashboard curl http://api:8000/health/
```

### ETL fails

```bash
# Check if data files exist
docker compose exec api ls -la data/raw/

# Run ETL with verbose logging
docker compose exec api python scripts/run_etl.py
```

### Port conflicts

If ports are already in use:

1. Stop conflicting services
2. Or modify `docker-compose.yml`:
```yaml
ports:
  - "5433:5432"  # Use 5433 instead of 5432
  - "8001:8000"  # Use 8001 instead of 8000
  - "8502:8501"  # Use 8502 instead of 8501
```

---

## 🔄 Common Workflows

### Development Workflow

```bash
# 1. Make code changes
# 2. Restart specific service
docker compose restart api

# Or rebuild if requirements changed
docker compose up --build api -d
```

### Reset Everything

```bash
# Full cleanup and restart
make clean
make setup
make ingest
```

### Update Data

```bash
# Re-run ETL (idempotent - safe to run multiple times)
make ingest
```

### View Real-time Logs

```bash
# All services
make logs

# Specific service
make logs-api
```

---

## 📈 Performance Monitoring

```bash
# Container stats
docker stats

# Database size
docker compose exec postgres psql -U claude -d claude_analytics -c "\l+"

# Table sizes
docker compose exec postgres psql -U claude -d claude_analytics -c "
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

---

## 🔒 Production Deployment

For production:

1. **Update .env**:
```bash
ENVIRONMENT=production
LOG_LEVEL=WARNING
SECRET_KEY=<strong-random-key>
API_KEY=<strong-random-key>
```

2. **Use production database**:
```bash
DATABASE_URL=postgresql://user:pass@production-host:5432/claude_analytics
```

3. **Enable HTTPS** (use nginx or Caddy as reverse proxy)

4. **Set resource limits** in docker-compose.yml:
```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
```

5. **Regular backups**:
```bash
# Backup database
docker compose exec postgres pg_dump -U claude claude_analytics > backup.sql

# Restore
cat backup.sql | docker compose exec -T postgres psql -U claude claude_analytics
```

---

## ✅ Success Checklist

- [ ] Docker Desktop is running
- [ ] All 4 containers are healthy (docker compose ps)
- [ ] ETL pipeline completed successfully
- [ ] API health check returns "healthy"
- [ ] API docs accessible at http://localhost:8000/docs
- [ ] Dashboard loads at http://localhost:8501
- [ ] All 4 dashboard pages load without errors
- [ ] API endpoints return data (not empty arrays)
- [ ] PostgreSQL contains data (24,162 API requests)

---

**Next:** Once deployed, see `API_DOCUMENTATION.md` for API endpoint details.
