# Architecture Documentation

## Overview

The Claude Code Usage Analytics Platform is built with a modern, scalable architecture designed for:
- **Real-time analytics** on telemetry data
- **Predictive insights** using machine learning
- **Interactive dashboards** for multiple user personas
- **RESTful API** for programmatic access

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│                  User Layer                         │
│  ┌──────────────┐              ┌──────────────┐    │
│  │   Streamlit  │              │  API Clients │    │
│  │   Dashboard  │              │  (external)  │    │
│  └──────────────┘              └──────────────┘    │
└────────────┬──────────────────────────┬────────────┘
             │                          │
┌────────────▼──────────────────────────▼────────────┐
│               Application Layer                     │
│  ┌──────────────┐              ┌──────────────┐    │
│  │  Dashboard   │              │   FastAPI    │    │
│  │  Components  │◄────────────►│   Backend    │    │
│  └──────────────┘              └──────┬───────┘    │
└───────────────────────────────────────┼────────────┘
                                        │
┌───────────────────────────────────────▼────────────┐
│              Analytics Engine                       │
│  ┌─────────┐  ┌─────────┐  ┌──────────────────┐   │
│  │ Metrics │  │  Aggs   │  │  ML Models       │   │
│  │ Engine  │  │ Engine  │  │  - Forecasting   │   │
│  │         │  │         │  │  - Anomaly Det.  │   │
│  └─────────┘  └─────────┘  └──────────────────┘   │
└───────────────────────────────────────┬────────────┘
                                        │
┌───────────────────────────────────────▼────────────┐
│                 Data Layer                          │
│  ┌──────────────┐              ┌──────────────┐    │
│  │  PostgreSQL  │              │    Redis     │    │
│  │   Database   │              │   (Cache +   │    │
│  │              │              │   Streaming) │    │
│  └──────────────┘              └──────────────┘    │
└────────────────────────────────────────────────────┘
```

## Component Descriptions

### 1. Data Layer

#### PostgreSQL Database
- **Purpose**: Primary data store for telemetry events and analytics
- **Schema Design**:
  - Star schema with fact and dimension tables
  - Materialized views for common aggregations
  - Comprehensive indexes for query optimization
- **Key Tables**:
  - Dimension: `employees`, `user_accounts`, `models`, `tools`, `sessions`
  - Fact: `api_requests`, `tool_decisions`, `tool_results`, `user_prompts`, `api_errors`

#### Redis
- **Purpose**: Caching and real-time streaming
- **Use Cases**:
  - Query result caching (TTL-based)
  - Real-time event streaming simulation
  - Session state management

### 2. ETL Pipeline

#### Data Ingestion
- Reads JSONL telemetry logs and CSV employee data
- Validates file formats and data integrity
- Extracts events from CloudWatch-style log batches

#### Data Transformation
- Cleans and normalizes event data
- Resolves foreign key relationships
- Validates data types and ranges
- Deduplicates records

#### Data Loading
- Bulk inserts using pandas `to_sql()`
- Upsert operations for dimension tables
- Transaction management with rollback on error
- Materialized view refresh

### 3. Analytics Engine

#### Metrics Engine
- Token usage calculations
- Cost analysis and attribution
- Performance metrics (latency, errors)
- User engagement scoring

#### Aggregation Engine
- Time-series aggregations (hourly, daily, weekly, monthly)
- Cohort analysis by practice/level/location
- Rolling averages and trends
- Statistical summaries

#### ML Models

**Usage Forecast Model**
- Algorithm: Facebook Prophet
- Predicts: Token usage, costs, API requests
- Output: 30-day forecast with confidence intervals

**Anomaly Detection Model**
- Algorithm: Isolation Forest
- Detects: Unusual cost/usage patterns
- Output: Anomaly scores and explanations

**Cost Optimization Model**
- Analyzes: Model usage efficiency
- Recommends: Model switching, cache optimization
- Output: ROI calculations for optimizations

### 4. API Layer (FastAPI)

#### Endpoints

**Analytics Endpoints** (`/analytics/...`)
- Metrics retrieval (tokens, cost, performance)
- Insights and recommendations
- Trend analysis
- Forecasts and anomaly detection

**User Endpoints** (`/users/...`)
- User listing and filtering
- User-specific metrics
- Session history

**Health Endpoints** (`/health/...`)
- Health checks
- Readiness probes
- Service status

#### Features
- Automatic OpenAPI documentation
- Request/response validation with Pydantic
- Error handling middleware
- CORS support for web clients

### 5. Dashboard Layer (Streamlit)

#### Pages

1. **Overview** - Executive summary and key metrics
2. **Usage Analysis** - Deep dive into usage patterns
3. **Cost Analysis** - Cost breakdowns and forecasts
4. **User Insights** - Per-user analytics
5. **Tool Analytics** - Tool usage and performance

#### Components
- Reusable chart components (Plotly)
- Filter widgets (date range, practice, level)
- Metric cards with trend indicators
- Role-based view customization

## Data Flow

### ETL Flow
```
JSONL/CSV Files → DataIngester → DataTransformer → DataLoader → PostgreSQL
                                                                      ↓
                                                          Materialized Views
```

### Query Flow
```
Dashboard/API Request → Analytics Engine → PostgreSQL/Redis → Response
                              ↓
                         ML Models (if forecast/anomaly)
```

### Streaming Flow (Real-time)
```
New Events → Redis Stream → Stream Processor → PostgreSQL → Dashboard Update
```

## Deployment Architecture

### Docker Compose Setup

```yaml
services:
  postgres:    # Port 5432
  redis:       # Port 6379
  api:         # Port 8000
  dashboard:   # Port 8501
```

### Networking
- All services connected via `claude-network` bridge
- Health checks ensure startup ordering
- Volume mounts for data persistence

## Scalability Considerations

### Current Architecture
- Single-node deployment via Docker Compose
- Suitable for datasets up to 10M events
- Response time < 1s for common queries

### Future Scaling Options
1. **Horizontal Scaling**
   - Multiple API/Dashboard replicas behind load balancer
   - Read replicas for PostgreSQL
   - Redis cluster for caching

2. **Data Partitioning**
   - Table partitioning by date
   - Archival of old data
   - Separate OLAP database for analytics

3. **Stream Processing**
   - Apache Kafka for event streaming
   - Apache Flink/Spark for real-time aggregations
   - Separate hot/cold storage

## Security Considerations

- Database credentials via environment variables
- API authentication (optional, configurable)
- CORS configuration for web clients
- Input validation for all endpoints
- SQL injection prevention via parameterized queries

## Performance Optimizations

1. **Database**
   - Indexes on frequently queried columns
   - Materialized views for common aggregations
   - Connection pooling

2. **API**
   - Response caching with Redis
   - Async request handling
   - Query result pagination

3. **Dashboard**
   - Streamlit caching decorators
   - Lazy loading of large datasets
   - Client-side chart rendering

## Monitoring & Observability

- Health check endpoints for uptime monitoring
- Structured logging throughout application
- PostgreSQL query logging for optimization
- API request/response logging
