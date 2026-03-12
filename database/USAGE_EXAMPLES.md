# Database Module Usage Examples

## SQLAlchemy 2.0 Async API

This module uses SQLAlchemy 2.0 async style with `asyncpg` driver.

## Basic Usage

### 1. Testing Database Connection

```python
import asyncio
from database import test_connection

async def main():
    is_connected = await test_connection()
    if is_connected:
        print("Database is accessible!")
    else:
        print("Failed to connect to database")

asyncio.run(main())
```

### 2. Creating Tables

```python
import asyncio
from database import init_db

async def main():
    await init_db()
    print("All tables created successfully!")

asyncio.run(main())
```

### 3. Using Sessions (Direct)

```python
import asyncio
from sqlalchemy import select
from database import get_sessionmaker, Employee

async def main():
    SessionLocal = get_sessionmaker()

    async with SessionLocal() as session:
        # Query employees
        result = await session.execute(
            select(Employee).where(Employee.practice == "Data Engineering")
        )
        employees = result.scalars().all()

        for emp in employees:
            print(f"{emp.full_name} - {emp.level}")

asyncio.run(main())
```

### 4. FastAPI Integration

```python
from fastapi import FastAPI, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_session, Employee

app = FastAPI()

@app.get("/employees")
async def get_employees(db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(Employee))
    employees = result.scalars().all()
    return [
        {
            "email": emp.email,
            "full_name": emp.full_name,
            "practice": emp.practice,
            "level": emp.level
        }
        for emp in employees
    ]

@app.get("/employees/{employee_id}")
async def get_employee(employee_id: int, db: AsyncSession = Depends(get_session)):
    result = await db.execute(
        select(Employee).where(Employee.employee_id == employee_id)
    )
    employee = result.scalar_one_or_none()

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    return {
        "email": employee.email,
        "full_name": employee.full_name,
        "practice": employee.practice,
        "level": employee.level
    }
```

### 5. Creating Records

```python
import asyncio
from database import get_sessionmaker, Employee

async def main():
    SessionLocal = get_sessionmaker()

    async with SessionLocal() as session:
        # Create new employee
        new_employee = Employee(
            email="john.doe@example.com",
            full_name="John Doe",
            practice="Platform Engineering",
            level="L5",
            location="United States"
        )

        session.add(new_employee)
        await session.commit()
        await session.refresh(new_employee)

        print(f"Created employee: {new_employee.employee_id}")

asyncio.run(main())
```

### 6. Updating Records

```python
import asyncio
from sqlalchemy import select, update
from database import get_sessionmaker, Employee

async def main():
    SessionLocal = get_sessionmaker()

    async with SessionLocal() as session:
        # Method 1: Fetch and modify
        result = await session.execute(
            select(Employee).where(Employee.email == "john.doe@example.com")
        )
        employee = result.scalar_one()

        employee.level = "L6"
        await session.commit()

        # Method 2: Direct update
        await session.execute(
            update(Employee)
            .where(Employee.email == "john.doe@example.com")
            .values(level="L6")
        )
        await session.commit()

asyncio.run(main())
```

### 7. Deleting Records

```python
import asyncio
from sqlalchemy import select, delete
from database import get_sessionmaker, Employee

async def main():
    SessionLocal = get_sessionmaker()

    async with SessionLocal() as session:
        # Method 1: Fetch and delete
        result = await session.execute(
            select(Employee).where(Employee.email == "john.doe@example.com")
        )
        employee = result.scalar_one()

        await session.delete(employee)
        await session.commit()

        # Method 2: Direct delete
        await session.execute(
            delete(Employee).where(Employee.email == "john.doe@example.com")
        )
        await session.commit()

asyncio.run(main())
```

### 8. Working with Relationships

```python
import asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database import get_sessionmaker, Employee, UserAccount

async def main():
    SessionLocal = get_sessionmaker()

    async with SessionLocal() as session:
        # Eager load related user accounts
        result = await session.execute(
            select(Employee)
            .options(selectinload(Employee.user_accounts))
            .where(Employee.email == "alex.chen@example.com")
        )
        employee = result.scalar_one()

        print(f"Employee: {employee.full_name}")
        print(f"User accounts: {len(employee.user_accounts)}")

        for account in employee.user_accounts:
            print(f"  - {account.user_id}: {account.hostname}")

asyncio.run(main())
```

### 9. Joining Tables

```python
import asyncio
from sqlalchemy import select
from database import get_sessionmaker, APIRequest, Model, UserAccount, Employee

async def main():
    SessionLocal = get_sessionmaker()

    async with SessionLocal() as session:
        # Join API requests with models and employees
        result = await session.execute(
            select(APIRequest, Model, Employee)
            .join(Model, APIRequest.model_id == Model.model_id)
            .join(UserAccount, APIRequest.user_id == UserAccount.user_id)
            .join(Employee, UserAccount.employee_id == Employee.employee_id)
            .where(Employee.practice == "Data Engineering")
            .limit(10)
        )

        for api_request, model, employee in result:
            print(
                f"{employee.full_name} used {model.model_name} "
                f"(cost: ${api_request.cost_usd:.4f})"
            )

asyncio.run(main())
```

### 10. Aggregations

```python
import asyncio
from sqlalchemy import select, func
from database import get_sessionmaker, APIRequest, UserAccount, Employee

async def main():
    SessionLocal = get_sessionmaker()

    async with SessionLocal() as session:
        # Aggregate costs by practice
        result = await session.execute(
            select(
                Employee.practice,
                func.sum(APIRequest.cost_usd).label("total_cost"),
                func.count(APIRequest.request_id).label("request_count")
            )
            .join(UserAccount, APIRequest.user_id == UserAccount.user_id)
            .join(Employee, UserAccount.employee_id == Employee.employee_id)
            .group_by(Employee.practice)
            .order_by(func.sum(APIRequest.cost_usd).desc())
        )

        for row in result:
            print(f"{row.practice}: ${row.total_cost:.2f} ({row.request_count} requests)")

asyncio.run(main())
```

### 11. Bulk Operations

```python
import asyncio
from database import get_sessionmaker, Employee

async def main():
    SessionLocal = get_sessionmaker()

    async with SessionLocal() as session:
        # Bulk insert
        employees = [
            Employee(
                email=f"user{i}@example.com",
                full_name=f"User {i}",
                practice="Backend Engineering",
                level="L4",
                location="United States"
            )
            for i in range(100)
        ]

        session.add_all(employees)
        await session.commit()

        print(f"Inserted {len(employees)} employees")

asyncio.run(main())
```

### 12. Application Lifecycle

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from database import init_db, close_engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    print("Database initialized")

    yield

    # Shutdown
    await close_engine()
    print("Database connection closed")

app = FastAPI(lifespan=lifespan)
```

## Configuration

Database connection is configured via environment variables:

```bash
# .env file
DATABASE_URL=postgresql://claude:analytics@localhost:5432/claude_analytics
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
LOG_LEVEL=INFO  # Set to DEBUG to see SQL queries
```

## Important Notes

1. **Always use async/await**: All database operations must be awaited
2. **Session management**: Use `async with` for automatic session cleanup
3. **Relationships**: Use `selectinload()` or `joinedload()` to avoid N+1 queries
4. **Transactions**: Sessions auto-commit on success, rollback on error
5. **Connection pooling**: Configured via DB_POOL_SIZE and DB_MAX_OVERFLOW

## Model Reference

- **Employee**: User employee data (practice, level, location)
- **UserAccount**: Telemetry user IDs linked to employees
- **Model**: Claude model definitions (opus, sonnet, haiku)
- **Tool**: Claude Code tools (Read, Write, Bash, etc.)
- **Session**: Coding sessions with environment metadata
- **APIRequest**: API call events with token usage and cost
- **ToolDecision**: Tool permission decisions
- **ToolResult**: Tool execution results
- **UserPrompt**: User prompt events
- **APIError**: API error events
