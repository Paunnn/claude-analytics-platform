# ETL Pipeline Quick Reference

## 📦 Module Overview

```
etl/
├── ingest.py      (242 lines) - Read JSONL/CSV, parse events
├── transform.py   (471 lines) - Clean, validate, structure data
├── load.py        (481 lines) - Insert into PostgreSQL (UPSERT)
└── pipeline.py    (301 lines) - Orchestrate all stages
                   ─────────────
                   1,495 lines total
```

---

## 🔄 Data Flow

```
[telemetry_logs.jsonl]  [employees.csv]
         │                     │
         ▼                     ▼
    ┌─────────────────────────────┐
    │  INGESTION (ingest.py)      │
    │  - Parse JSONL batches      │
    │  - Extract logEvents        │
    │  - Parse nested JSON        │
    └──────────┬──────────────────┘
               │
         [Raw Events]
               │
               ▼
    ┌─────────────────────────────┐
    │  TRANSFORMATION             │
    │  (transform.py)             │
    │  - Clean employees          │
    │  - Extract sessions         │
    │  - Transform 5 event types  │
    └──────────┬──────────────────┘
               │
        [DataFrames]
               │
               ▼
    ┌─────────────────────────────┐
    │  LOADING (load.py)          │
    │  - UPSERT dimensions        │
    │  - Bulk insert facts        │
    │  - Resolve foreign keys     │
    └──────────┬──────────────────┘
               │
               ▼
        [PostgreSQL DB]
               │
               ▼
    ┌─────────────────────────────┐
    │  POST-PROCESSING            │
    │  - Refresh mat. views       │
    │  - Report statistics        │
    └─────────────────────────────┘
```

---

## 🎯 Usage Examples

### Basic Usage

```python
from etl.pipeline import ETLPipeline

# Initialize
pipeline = ETLPipeline(data_dir="data/raw")

# Run complete ETL
stats = pipeline.run_full_pipeline()

# Check results
print(f"Processed {stats['total_events']:,} events")
print(f"Loaded {stats['api_requests_loaded']:,} API requests")
```

### Step-by-Step Usage

```python
from etl.ingest import DataIngester
from etl.transform import DataTransformer
from etl.load import DataLoader

# Step 1: Ingest
ingester = DataIngester("data/raw")
events = ingester.ingest_telemetry_logs()
employees_df = ingester.ingest_employees()

print(f"Loaded {len(events)} events")
print(ingester.get_event_count_by_type(events))

# Step 2: Transform
transformer = DataTransformer()
employees_clean = transformer.transform_employees(employees_df)
api_requests_df = transformer.transform_api_requests(events)
sessions_df = transformer.extract_sessions(events)

print(f"Transformed {len(api_requests_df)} API requests")
print(f"Extracted {len(sessions_df)} sessions")

# Step 3: Load
loader = DataLoader()
loader.load_employees(employees_clean)
loader.load_sessions(sessions_df)
loader.load_api_requests(api_requests_df)
loader.refresh_materialized_views()

print("Data loaded successfully!")
```

---

## 📊 Event Type Transformations

| Event Type | Input (Events) | Transform Method | Output (DataFrame) |
|------------|----------------|------------------|--------------------|
| **claude_code.api_request** | 24,162 | `transform_api_requests()` | event_timestamp, session_id, user_id, model_name, input_tokens, output_tokens, cache_*_tokens, cost_usd, duration_ms |
| **claude_code.tool_decision** | 31,007 | `transform_tool_decisions()` | event_timestamp, session_id, user_id, tool_name, decision, source |
| **claude_code.tool_result** | 30,358 | `transform_tool_results()` | event_timestamp, session_id, user_id, tool_name, decision_type, decision_source, success, duration_ms, result_size_bytes |
| **claude_code.user_prompt** | 7,111 | `transform_user_prompts()` | event_timestamp, session_id, user_id, prompt_length |
| **claude_code.api_error** | 292 | `transform_api_errors()` | event_timestamp, session_id, user_id, model_name, error_message, status_code, attempt, duration_ms |

---

## 🔑 Key Features

### Idempotency
```python
# Safe to run multiple times
pipeline.run_full_pipeline()  # First run
pipeline.run_full_pipeline()  # Second run - UPSERTs duplicates
```

### Foreign Key Resolution
```python
# Models and tools are resolved automatically
df['model_id'] = df['model_name'].apply(loader._get_model_id)
df['tool_id'] = df['tool_name'].apply(loader._get_tool_id)
```

### Error Handling
```python
try:
    stats = pipeline.run_full_pipeline()
except Exception as e:
    print(f"ETL failed: {e}")
    pipeline.rollback_transaction()
```

---

## 🐛 Debugging

### Check Ingestion
```python
from etl.ingest import DataIngester

ingester = DataIngester("data/raw")
events = ingester.ingest_telemetry_logs()

# Show first event
print(events[0])

# Count by type
counts = ingester.get_event_count_by_type(events)
for event_type, count in counts.items():
    print(f"{event_type}: {count:,}")
```

### Check Transformation
```python
from etl.transform import DataTransformer

transformer = DataTransformer()
api_df = transformer.transform_api_requests(events)

# Show columns
print(api_df.columns.tolist())

# Show sample rows
print(api_df.head(3))

# Check for nulls
print(api_df.isnull().sum())
```

### Check Loading
```python
from sqlalchemy import text

# Count loaded records
with loader.session as session:
    result = session.execute(text("SELECT COUNT(*) FROM api_requests"))
    count = result.scalar()
    print(f"API requests in DB: {count:,}")
```

---

## ⚠️ Common Issues

### Issue: "No module named 'pandas'"
**Solution:** Install dependencies
```bash
pip install -r requirements.txt
```

### Issue: "database 'claude_analytics' does not exist"
**Solution:** Create database
```bash
psql -U postgres -c "CREATE DATABASE claude_analytics"
```

### Issue: "table 'employees' does not exist"
**Solution:** Run schema.sql
```bash
psql -U claude -d claude_analytics < database/schema.sql
```

### Issue: "Foreign key constraint violation"
**Solution:** Load dimension tables before fact tables (pipeline does this automatically)

---

## 📈 Performance Tips

1. **Bulk Loading:** Uses `pandas.to_sql()` with `method='multi'` for fast inserts
2. **Batch Size:** Processes 1000 records at a time (configurable via `chunksize`)
3. **Indexes:** Database has indexes on event_timestamp, user_id, session_id
4. **Materialized Views:** Refresh after loading for pre-computed aggregations

---

## 🔍 Validation Queries

### After ETL, verify data:

```sql
-- Count all tables
SELECT 'employees' as table, COUNT(*) FROM employees
UNION ALL SELECT 'sessions', COUNT(*) FROM sessions
UNION ALL SELECT 'api_requests', COUNT(*) FROM api_requests
UNION ALL SELECT 'tool_results', COUNT(*) FROM tool_results;

-- Sample API requests
SELECT event_timestamp, user_id, model_id, cost_usd
FROM api_requests
ORDER BY event_timestamp DESC
LIMIT 5;

-- Sample tool results
SELECT event_timestamp, tool_id, success, duration_ms
FROM tool_results
ORDER BY event_timestamp DESC
LIMIT 5;
```

---

## 📝 Sample Data

### Event Structure (after ingestion)
```python
{
    'body': 'claude_code.api_request',
    'attributes': {
        'event.timestamp': '2026-01-02T04:24:01.206Z',
        'user.email': 'sage.kim@example.com',
        'user.id': '41af9bfb575be874...',
        'session.id': '549909e9-05b2-4f64-af14-22d4ed904080',
        'model': 'claude-opus-4-6',
        'input_tokens': '0',
        'output_tokens': '259',
        'cache_read_tokens': '85371',
        'cost_usd': '0.16485439054186743',
        'duration_ms': '10467'
    },
    'scope': {'name': 'com.anthropic.claude_code.events', 'version': '2.1.44'},
    'resource': {
        'host.name': 'Sages-MacBook-Air.local',
        'os.type': 'darwin',
        'user.practice': 'Frontend Engineering'
    }
}
```

### Transformed DataFrame
```
   event_timestamp              session_id                            user_id           model_name  input_tokens  output_tokens  cost_usd
0  2026-01-02 04:24:01.206+00  549909e9-...  41af9bfb575be874...  claude-opus-4-6             0            259  0.164854
```

---

**For complete details, see:** `ETL_IMPLEMENTATION_SUMMARY.md`
