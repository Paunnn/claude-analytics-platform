# API Reference

## Base URL
```
http://localhost:8000
```

## Authentication
Currently, the API does not require authentication. In production, configure API key authentication via the `API_KEY` environment variable.

## Interactive Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Health Endpoints

### GET /health/
Basic health check.

**Response:**
```json
{
  "status": "healthy"
}
```

### GET /health/ready
Readiness check including database connectivity.

**Response:**
```json
{
  "status": "ready",
  "database": "connected",
  "redis": "connected"
}
```

---

## Analytics Endpoints

### GET /analytics/metrics/token-usage
Get token usage metrics.

**Query Parameters:**
- `start_date` (optional): Start date (YYYY-MM-DD)
- `end_date` (optional): End date (YYYY-MM-DD)
- `group_by` (optional): Group by field (practice, level, location)

**Example Request:**
```bash
curl "http://localhost:8000/analytics/metrics/token-usage?group_by=practice"
```

**Example Response:**
```json
{
  "total_input_tokens": 1234567,
  "total_output_tokens": 456789,
  "total_cache_read_tokens": 987654,
  "cache_hit_rate": 0.73,
  "breakdown_by_practice": {
    "Data Engineering": 345678,
    "ML Engineering": 234567,
    "Backend Engineering": 123456
  }
}
```

### GET /analytics/metrics/cost
Get cost metrics and breakdowns.

**Query Parameters:**
- `start_date` (optional): Start date
- `end_date` (optional): End date
- `group_by` (optional): Group by field

**Example Response:**
```json
{
  "total_cost": 1234.56,
  "average_cost_per_request": 0.05,
  "cost_breakdown": {
    "Data Engineering": 456.78,
    "ML Engineering": 345.67,
    "Backend Engineering": 234.56
  },
  "top_cost_drivers": [
    {"user_email": "user1@example.com", "cost": 123.45},
    {"user_email": "user2@example.com", "cost": 98.76}
  ]
}
```

### GET /analytics/metrics/performance
Get performance metrics (latency, errors).

**Query Parameters:**
- `model_name` (optional): Filter by model

**Example Response:**
```json
{
  "average_duration_ms": 8543,
  "median_duration_ms": 7234,
  "p95_duration_ms": 15678,
  "error_rate": 0.012,
  "by_model": {
    "claude-opus-4-6": {
      "avg_duration_ms": 10230,
      "error_rate": 0.008
    },
    "claude-sonnet-4-5-20250929": {
      "avg_duration_ms": 8500,
      "error_rate": 0.010
    }
  }
}
```

### GET /analytics/metrics/peak-hours
Get peak usage hours analysis.

**Example Response:**
```json
{
  "peak_hour": 14,
  "peak_day": "Wednesday",
  "hourly_distribution": [
    {"hour": 0, "request_count": 45},
    {"hour": 1, "request_count": 23},
    ...
  ]
}
```

### GET /analytics/insights
Get generated insights and recommendations.

**Query Parameters:**
- `insight_type` (optional): Filter by type (cost, performance, usage)

**Example Response:**
```json
[
  {
    "insight_id": "insight-001",
    "type": "cost",
    "severity": "high",
    "title": "High cache miss rate for Data Engineering team",
    "description": "The Data Engineering team has a cache miss rate of 45%, which is significantly higher than the platform average of 27%.",
    "recommendation": "Review prompt patterns and consider implementing more consistent context to improve cache utilization.",
    "potential_impact": "Could reduce costs by approximately $150/month"
  },
  {
    "insight_id": "insight-002",
    "type": "performance",
    "severity": "medium",
    "title": "Bash tool showing elevated execution times",
    "description": "Bash tool execution time has increased 40% over the past week.",
    "recommendation": "Investigate commands being executed and consider optimization."
  }
]
```

### GET /analytics/insights/executive-summary
Get executive summary with key insights.

**Example Response:**
```json
{
  "key_metrics": {
    "total_cost": 1234.56,
    "total_requests": 12345,
    "active_users": 87,
    "cost_trend": "+5.2%"
  },
  "top_insights": [...],
  "recommendations": [
    "Optimize cache usage to reduce costs by 15%",
    "Consider model switching for backend team"
  ],
  "trends": {
    "usage": "increasing",
    "cost_per_request": "stable",
    "error_rate": "decreasing"
  }
}
```

### GET /analytics/trends/{metric}
Get time-series trend for a specific metric.

**Path Parameters:**
- `metric`: Metric name (cost, tokens, requests, etc.)

**Query Parameters:**
- `time_grain`: Aggregation level (hour, day, week, month)
- `start_date` (optional): Start date
- `end_date` (optional): End date

**Example Request:**
```bash
curl "http://localhost:8000/analytics/trends/cost?time_grain=day"
```

**Example Response:**
```json
{
  "metric": "cost",
  "time_grain": "day",
  "data": [
    {"date": "2026-02-01", "value": 45.67},
    {"date": "2026-02-02", "value": 52.34},
    ...
  ]
}
```

### GET /analytics/predictions/forecast
Get ML-based usage/cost forecast.

**Query Parameters:**
- `metric`: Metric to forecast (default: cost)
- `periods`: Number of periods to forecast (default: 30)

**Example Response:**
```json
{
  "metric": "cost",
  "forecast_periods": 30,
  "forecast": [
    {
      "date": "2026-03-01",
      "predicted_value": 48.50,
      "lower_bound": 42.30,
      "upper_bound": 54.70
    },
    ...
  ],
  "confidence": 0.95
}
```

### GET /analytics/anomalies
Get detected anomalies.

**Query Parameters:**
- `metric`: Metric to check (default: cost)
- `threshold_std`: Standard deviation threshold (default: 2.0)

**Example Response:**
```json
[
  {
    "timestamp": "2026-02-15T14:30:00Z",
    "metric": "cost",
    "actual_value": 125.50,
    "expected_value": 45.30,
    "anomaly_score": 2.8,
    "severity": "high",
    "explanation": "Cost is 2.8 standard deviations above normal"
  }
]
```

---

## User Endpoints

### GET /users/
Get list of users with optional filtering.

**Query Parameters:**
- `practice` (optional): Filter by practice
- `level` (optional): Filter by level
- `location` (optional): Filter by location
- `limit` (default: 100, max: 1000): Maximum records
- `offset` (default: 0): Pagination offset

**Example Request:**
```bash
curl "http://localhost:8000/users/?practice=Data%20Engineering&limit=50"
```

**Example Response:**
```json
{
  "data": [
    {
      "user_id": "abc123...",
      "email": "alex.chen@example.com",
      "full_name": "Alex Chen",
      "practice": "Data Engineering",
      "level": "L5",
      "location": "United States"
    },
    ...
  ],
  "total": 23,
  "limit": 50,
  "offset": 0,
  "has_more": false
}
```

### GET /users/{user_id}
Get detailed information for a specific user.

**Path Parameters:**
- `user_id`: User ID

**Example Response:**
```json
{
  "user_id": "abc123...",
  "email": "alex.chen@example.com",
  "full_name": "Alex Chen",
  "practice": "Data Engineering",
  "level": "L5",
  "location": "United States",
  "total_sessions": 45,
  "total_requests": 1234,
  "total_cost": 123.45,
  "account_created": "2025-12-01T00:00:00Z"
}
```

### GET /users/{user_id}/sessions
Get sessions for a specific user.

**Query Parameters:**
- `start_date` (optional): Filter by start date
- `end_date` (optional): Filter by end date
- `limit` (default: 50, max: 500): Maximum records

**Example Response:**
```json
[
  {
    "session_id": "session-uuid-1",
    "user_id": "abc123...",
    "terminal_type": "vscode",
    "session_start": "2026-02-15T10:30:00Z",
    "session_end": "2026-02-15T11:45:00Z",
    "total_requests": 15,
    "total_cost": 5.67
  },
  ...
]
```

### GET /users/{user_id}/metrics
Get metrics for a specific user.

**Query Parameters:**
- `start_date` (optional): Start date
- `end_date` (optional): End date

**Example Response:**
```json
{
  "user_id": "abc123...",
  "total_tokens": 123456,
  "total_cost": 123.45,
  "average_cost_per_request": 0.05,
  "cache_hit_rate": 0.68,
  "most_used_tools": ["Read", "Bash", "Edit"],
  "preferred_model": "claude-sonnet-4-5-20250929"
}
```

### GET /users/practices/list
Get list of all engineering practices.

**Example Response:**
```json
[
  "Platform Engineering",
  "Data Engineering",
  "ML Engineering",
  "Backend Engineering",
  "Frontend Engineering"
]
```

---

## Error Responses

All endpoints return error responses in the following format:

**Example Error Response:**
```json
{
  "error": "Not Found",
  "detail": "User with ID 'invalid-id' not found",
  "timestamp": "2026-02-15T12:34:56Z"
}
```

**HTTP Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Invalid parameters
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

---

## Rate Limiting

Currently no rate limiting is implemented. For production deployment, consider implementing rate limiting middleware.

## Pagination

Endpoints that return lists support pagination via `limit` and `offset` parameters:

```bash
# Get first 50 users
GET /users/?limit=50&offset=0

# Get next 50 users
GET /users/?limit=50&offset=50
```
