# API Testing Guide - Complete Endpoint Reference

This guide provides curl commands to test every API endpoint.

---

## Prerequisites

```bash
# Ensure services are running
docker compose ps

# Ensure data is loaded
docker compose exec api python scripts/run_etl.py
```

---

## Health Endpoints

### 1. Basic Health Check

```bash
curl http://localhost:8000/health/
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "claude-analytics-api"
}
```

### 2. Readiness Check (with Database)

```bash
curl http://localhost:8000/health/ready
```

**Expected Response:**
```json
{
  "status": "ready",
  "checks": {
    "database": "connected"
  },
  "environment": "development"
}
```

### 3. Liveness Probe

```bash
curl http://localhost:8000/health/live
```

**Expected Response:**
```json
{
  "status": "alive"
}
```

---

## General Endpoints

### 4. Root Endpoint

```bash
curl http://localhost:8000/
```

**Expected Response:**
```json
{
  "service": "Claude Analytics API",
  "version": "1.0.0",
  "status": "running",
  "environment": "development",
  "endpoints": {
    "health": "/health/",
    "analytics": "/analytics/",
    "users": "/users/",
    "docs": "/docs",
    "redoc": "/redoc"
  }
}
```

### 5. Version Information

```bash
curl http://localhost:8000/version
```

---

## Analytics Endpoints

### 6. Overview Summary

```bash
curl http://localhost:8000/analytics/summary/overview | jq '.'
```

**Expected Response:**
```json
{
  "overall": {
    "total_cost": 1240.71,
    "total_requests": 24162,
    "avg_cost_per_request": 0.0514,
    "total_tokens": 5234567,
    "unique_users": 50,
    "unique_sessions": 1000
  },
  "daily_active_users": [...]
}
```

### 7. Token Usage Metrics

```bash
# All token usage
curl http://localhost:8000/analytics/metrics/token-usage | jq '.'

# With date range
curl "http://localhost:8000/analytics/metrics/token-usage?start_date=2026-01-01&end_date=2026-01-31" | jq '.'
```

**Expected Response:**
```json
{
  "data": [
    {
      "date": "2026-01-02",
      "practice": "Backend Engineering",
      "total_input_tokens": 1234,
      "total_output_tokens": 5678,
      "total_cache_read_tokens": 85371,
      "total_cache_creation_tokens": 0,
      "request_count": 145
    }
  ],
  "total_records": 150,
  "start_date": "2026-01-01",
  "end_date": "2026-01-31"
}
```

### 8. Cost Metrics

```bash
# Overall costs
curl http://localhost:8000/analytics/metrics/cost | jq '.'

# Group by practice
curl "http://localhost:8000/analytics/metrics/cost?group_by=practice" | jq '.'

# Group by level
curl "http://localhost:8000/analytics/metrics/cost?group_by=level" | jq '.'
```

### 9. Performance Metrics

```bash
# All performance metrics
curl http://localhost:8000/analytics/metrics/performance | jq '.'

# Filter by model
curl "http://localhost:8000/analytics/metrics/performance?model_name=claude-opus-4-6" | jq '.'
```

### 10. Peak Usage Hours

```bash
curl http://localhost:8000/analytics/metrics/peak-hours | jq '.'
```

**Expected Response:**
```json
{
  "data": [
    {
      "hour_of_day": 9,
      "day_of_week": 1,
      "request_count": 856,
      "total_cost": 42.34,
      "avg_duration_ms": 2341.5
    }
  ],
  "total_records": 168
}
```

### 11. Cache Efficiency

```bash
curl http://localhost:8000/analytics/metrics/cache-efficiency | jq '.'
```

### 12. Top Users by Cost

```bash
# Top 10 users
curl "http://localhost:8000/analytics/metrics/top-users?n=10" | jq '.'

# Top 20 users
curl "http://localhost:8000/analytics/metrics/top-users?n=20" | jq '.'
```

**Expected Response:**
```json
{
  "data": [
    {
      "email": "alex.chen@example.com",
      "full_name": "Alex Chen",
      "practice": "Data Engineering",
      "level": "L5",
      "location": "San Francisco",
      "total_cost": 245.67,
      "request_count": 4523,
      "avg_cost_per_request": 0.0543,
      "total_input_tokens": 125678,
      "total_output_tokens": 456789,
      "total_cache_read_tokens": 789012,
      "most_used_model": "claude-opus-4-6"
    }
  ],
  "total_users": 10
}
```

### 13. Metric Trends

```bash
# Daily cost trend
curl "http://localhost:8000/analytics/trends/cost?time_grain=day" | jq '.'

# Hourly token trend
curl "http://localhost:8000/analytics/trends/tokens?time_grain=hour" | jq '.'

# Weekly request trend
curl "http://localhost:8000/analytics/trends/requests?time_grain=week" | jq '.'

# Monthly session trend
curl "http://localhost:8000/analytics/trends/sessions?time_grain=month" | jq '.'
```

### 14. User Cohort Analysis

```bash
# By practice
curl "http://localhost:8000/analytics/aggregations/user-cohorts?cohort_field=practice" | jq '.'

# By level
curl "http://localhost:8000/analytics/aggregations/user-cohorts?cohort_field=level" | jq '.'

# By location
curl "http://localhost:8000/analytics/aggregations/user-cohorts?cohort_field=location" | jq '.'
```

**Expected Response:**
```json
{
  "cohort_field": "practice",
  "data": [
    {
      "cohort": "Platform Engineering",
      "user_count": 10,
      "total_requests": 5234,
      "total_cost": 289.45,
      "avg_cost_per_request": 0.0553,
      "total_tokens": 1234567,
      "avg_tokens_per_request": 235.9,
      "cache_hit_rate": 0.7834,
      "total_sessions": 234,
      "requests_per_user": 523.4
    }
  ],
  "total_cohorts": 5
}
```

### 15. Rolling Averages

```bash
# 7-day rolling average of costs
curl "http://localhost:8000/analytics/aggregations/rolling-averages?metric=cost&window_days=7" | jq '.'

# 14-day rolling average of tokens
curl "http://localhost:8000/analytics/aggregations/rolling-averages?metric=tokens&window_days=14" | jq '.'
```

### 16. Percentiles

```bash
# Cost percentiles
curl "http://localhost:8000/analytics/aggregations/percentiles?metric=cost_usd" | jq '.'

# Duration percentiles
curl "http://localhost:8000/analytics/aggregations/percentiles?metric=duration_ms" | jq '.'
```

**Expected Response:**
```json
{
  "metric": "cost_usd",
  "percentiles": {
    "0.25": 0.0123,
    "0.5": 0.0456,
    "0.75": 0.0789,
    "0.9": 0.1234,
    "0.95": 0.1567,
    "0.99": 0.2345,
    "min": 0.0001,
    "max": 0.9876,
    "mean": 0.0514,
    "std": 0.0234
  }
}
```

### 17. Tool Usage Statistics

```bash
curl http://localhost:8000/analytics/tools/usage-stats | jq '.'
```

**Expected Response:**
```json
[
  {
    "tool_name": "Read",
    "total_executions": 5432,
    "successful": 5398,
    "failed": 34,
    "success_rate": 0.9937,
    "avg_duration_ms": 34.2,
    "median_duration_ms": 28.5,
    "p95_duration_ms": 89.3
  }
]
```

### 18. Tool Usage Patterns

```bash
curl http://localhost:8000/analytics/tools/usage-patterns | jq '.'
```

### 19. Model Comparison

```bash
curl http://localhost:8000/analytics/models/comparison | jq '.'
```

**Expected Response:**
```json
{
  "data": [
    {
      "model_name": "claude-haiku-4-5-20251001",
      "model_family": "claude-4-5",
      "request_count": 8723,
      "total_cost": 28.96,
      "avg_cost_per_request": 0.0033,
      "avg_duration_ms": 1234.5,
      "total_tokens": 2345678,
      "total_input_tokens": 987654,
      "total_output_tokens": 1358024,
      "total_cache_read_tokens": 4567890,
      "percentage_of_requests": 36.1
    }
  ],
  "total_models": 5
}
```

---

## Machine Learning Endpoints

### 20. Usage Forecast

```bash
# 7-day forecast
curl "http://localhost:8000/analytics/ml/forecast?days=7" | jq '.'

# 30-day forecast
curl "http://localhost:8000/analytics/ml/forecast?days=30" | jq '.'
```

**Expected Response:**
```json
{
  "days": 7,
  "forecast": [
    {
      "date": "2026-02-01",
      "predicted_tokens": 178432.12,
      "lower_bound": 142567.45,
      "upper_bound": 214296.79
    }
  ],
  "total_predictions": 7
}
```

### 21. Anomaly Detection

```bash
curl http://localhost:8000/analytics/ml/anomalies | jq '.'
```

**Expected Response:**
```json
{
  "total_records": 150,
  "anomalies_detected": 8,
  "anomaly_rate": 0.053,
  "data": [
    {
      "date": "2026-01-15",
      "user_email": "alex.chen@example.com",
      "practice": "Data Engineering",
      "total_tokens": 285432,
      "is_anomaly": true,
      "anomaly_score": -0.0234
    }
  ]
}
```

### 22. User Clustering

```bash
curl http://localhost:8000/analytics/ml/user-clusters | jq '.'
```

**Expected Response:**
```json
{
  "total_users": 50,
  "cluster_distribution": {
    "Balanced": 18,
    "Power User": 12,
    "Light User": 11,
    "Tool-Heavy": 9
  },
  "data": [
    {
      "user_email": "alex.chen@example.com",
      "full_name": "Alex Chen",
      "practice": "Data Engineering",
      "cluster_label": "Power User",
      "avg_tokens_per_session": 185432.12,
      "sessions_per_day": 3.47,
      "tool_usage_rate": 1.23,
      "cache_hit_rate": 0.78
    }
  ]
}
```

---

## User Endpoints

### 23. List Users

```bash
# All users
curl http://localhost:8000/users/ | jq '.'

# Filter by practice
curl "http://localhost:8000/users/?practice=Data%20Engineering" | jq '.'

# Filter by level
curl "http://localhost:8000/users/?level=L5" | jq '.'

# Pagination
curl "http://localhost:8000/users/?limit=10&offset=0" | jq '.'
```

### 24. Get Practices

```bash
curl http://localhost:8000/users/practices | jq '.'
```

**Expected Response:**
```json
[
  "Backend Engineering",
  "Data Engineering",
  "Frontend Engineering",
  "ML Engineering",
  "Platform Engineering"
]
```

### 25. Get Levels

```bash
curl http://localhost:8000/users/levels | jq '.'
```

**Expected Response:**
```json
[
  "L3",
  "L4",
  "L5",
  "L6",
  "L7"
]
```

### 26. Get User Metrics

```bash
# Specific user
curl "http://localhost:8000/users/alex.chen@example.com/metrics" | jq '.'

# With date range
curl "http://localhost:8000/users/alex.chen@example.com/metrics?start_date=2026-01-01&end_date=2026-01-31" | jq '.'
```

**Expected Response:**
```json
{
  "email": "alex.chen@example.com",
  "full_name": "Alex Chen",
  "practice": "Data Engineering",
  "level": "L5",
  "total_requests": 4523,
  "total_cost": 245.67,
  "avg_cost_per_request": 0.0543,
  "total_tokens": 987654,
  "total_sessions": 234,
  "cache_hit_rate": 0.7834
}
```

### 27. Get User Sessions

```bash
# Recent sessions
curl "http://localhost:8000/users/alex.chen@example.com/sessions?limit=10" | jq '.'
```

**Expected Response:**
```json
[
  {
    "session_id": "549909e9-05b2-4f64-af14-22d4ed904080",
    "session_start": "2026-01-15T10:23:45",
    "session_end": "2026-01-15T14:56:12",
    "terminal_type": "vscode",
    "os_type": "darwin",
    "host_name": "Alex-MacBook-Pro.local",
    "request_count": 145,
    "total_cost": 8.92
  }
]
```

---

## Batch Testing Script

Save this as `test_all_endpoints.sh`:

```bash
#!/bin/bash

API_URL="http://localhost:8000"

echo "Testing all API endpoints..."
echo ""

# Health
echo "1. Health check..."
curl -s $API_URL/health/ | jq '.'

echo ""
echo "2. Readiness check..."
curl -s $API_URL/health/ready | jq '.'

# Analytics
echo ""
echo "3. Overview summary..."
curl -s $API_URL/analytics/summary/overview | jq '.overall'

echo ""
echo "4. Token usage..."
curl -s $API_URL/analytics/metrics/token-usage | jq '.total_records'

echo ""
echo "5. Cost metrics..."
curl -s $API_URL/analytics/metrics/cost | jq '.data[0]'

echo ""
echo "6. Peak hours..."
curl -s $API_URL/analytics/metrics/peak-hours | jq '.total_records'

echo ""
echo "7. Top users..."
curl -s $API_URL/analytics/metrics/top-users?n=5 | jq '.data | length'

echo ""
echo "8. ML Forecast..."
curl -s $API_URL/analytics/ml/forecast?days=7 | jq '.total_predictions'

echo ""
echo "9. Anomalies..."
curl -s $API_URL/analytics/ml/anomalies | jq '.anomalies_detected'

echo ""
echo "10. User clusters..."
curl -s $API_URL/analytics/ml/user-clusters | jq '.cluster_distribution'

# Users
echo ""
echo "11. Practices..."
curl -s $API_URL/users/practices | jq '.'

echo ""
echo "12. Levels..."
curl -s $API_URL/users/levels | jq '.'

echo ""
echo "✅ All tests complete!"
```

Run with:
```bash
chmod +x test_all_endpoints.sh
./test_all_endpoints.sh
```

---

## Interactive API Documentation

Visit these URLs in your browser:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

Both provide interactive testing of all endpoints!
