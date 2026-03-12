"""
User management API endpoints.

Provides endpoints for user data and session information.
"""

from fastapi import APIRouter, Query, HTTPException
from sqlalchemy import create_engine, text
from typing import Dict, Any, List, Optional
from datetime import date, datetime
import logging

from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


def get_engine():
    """Get sync SQLAlchemy engine."""
    sync_url = settings.database_url
    if 'asyncpg' in sync_url:
        sync_url = sync_url.replace('postgresql+asyncpg://', 'postgresql://')
    return create_engine(sync_url, pool_pre_ping=True)


@router.get("/")
async def get_users(
    practice: Optional[str] = Query(None, description="Filter by practice"),
    level: Optional[str] = Query(None, description="Filter by level"),
    location: Optional[str] = Query(None, description="Filter by location"),
    limit: int = Query(100, le=1000, description="Maximum records to return"),
    offset: int = Query(0, description="Offset for pagination")
) -> Dict[str, Any]:
    """
    Get list of users with optional filtering.

    Returns:
        Dictionary with user list and pagination info
    """
    try:
        engine = get_engine()

        query = text("""
            SELECT
                e.employee_id,
                e.email,
                e.full_name,
                e.practice,
                e.level,
                e.location,
                COUNT(DISTINCT ua.user_id) as user_account_count
            FROM employees e
            LEFT JOIN user_accounts ua ON e.employee_id = ua.employee_id
            WHERE 1=1
                AND (:practice IS NULL OR e.practice = :practice)
                AND (:level IS NULL OR e.level = :level)
                AND (:location IS NULL OR e.location = :location)
            GROUP BY e.employee_id, e.email, e.full_name, e.practice, e.level, e.location
            ORDER BY e.email
            LIMIT :limit OFFSET :offset
        """)

        with engine.connect() as conn:
            result = conn.execute(
                query,
                {
                    "practice": practice,
                    "level": level,
                    "location": location,
                    "limit": limit,
                    "offset": offset
                }
            )
            users = [dict(row._mapping) for row in result]

        engine.dispose()

        return {
            "data": users,
            "total": len(users),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/practices")
async def get_practices() -> List[str]:
    """
    Get list of all engineering practices.

    Returns:
        List of practice names
    """
    try:
        engine = get_engine()

        query = text("""
            SELECT DISTINCT practice
            FROM employees
            ORDER BY practice
        """)

        with engine.connect() as conn:
            result = conn.execute(query)
            practices = [row[0] for row in result]

        engine.dispose()

        return practices
    except Exception as e:
        logger.error(f"Error fetching practices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/levels")
async def get_levels() -> List[str]:
    """
    Get list of all seniority levels.

    Returns:
        List of level names
    """
    try:
        engine = get_engine()

        query = text("""
            SELECT DISTINCT level
            FROM employees
            ORDER BY level
        """)

        with engine.connect() as conn:
            result = conn.execute(query)
            levels = [row[0] for row in result]

        engine.dispose()

        return levels
    except Exception as e:
        logger.error(f"Error fetching levels: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{email}/metrics")
async def get_user_metrics(
    email: str,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
) -> Dict[str, Any]:
    """
    Get metrics for a specific user.

    Returns:
        User-level metrics dictionary
    """
    try:
        engine = get_engine()

        start_dt = datetime.combine(start_date, datetime.min.time()) if start_date else None
        end_dt = datetime.combine(end_date, datetime.max.time()) if end_date else None

        query = text("""
            SELECT
                e.email,
                e.full_name,
                e.practice,
                e.level,
                COUNT(*) as total_requests,
                SUM(ar.cost_usd) as total_cost,
                AVG(ar.cost_usd) as avg_cost_per_request,
                SUM(ar.input_tokens + ar.output_tokens) as total_tokens,
                COUNT(DISTINCT ar.session_id) as total_sessions,
                SUM(ar.cache_read_tokens)::FLOAT / NULLIF(SUM(ar.cache_read_tokens + ar.input_tokens), 0) as cache_hit_rate
            FROM api_requests ar
            JOIN user_accounts ua ON ar.user_id = ua.user_id
            JOIN employees e ON ua.employee_id = e.employee_id
            WHERE e.email = :email
                AND (:start_date IS NULL OR ar.event_timestamp >= :start_date)
                AND (:end_date IS NULL OR ar.event_timestamp <= :end_date)
            GROUP BY e.email, e.full_name, e.practice, e.level
        """)

        with engine.connect() as conn:
            result = conn.execute(
                query,
                {
                    "email": email,
                    "start_date": start_dt,
                    "end_date": end_dt
                }
            )
            row = result.fetchone()

        engine.dispose()

        if not row:
            raise HTTPException(status_code=404, detail=f"User {email} not found or has no activity")

        return dict(row._mapping)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{email}/sessions")
async def get_user_sessions(
    email: str,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(50, le=500)
) -> List[Dict[str, Any]]:
    """
    Get sessions for a specific user.

    Returns:
        List of session objects
    """
    try:
        engine = get_engine()

        start_dt = datetime.combine(start_date, datetime.min.time()) if start_date else None
        end_dt = datetime.combine(end_date, datetime.max.time()) if end_date else None

        query = text("""
            SELECT
                s.session_id,
                s.session_start,
                s.session_end,
                s.terminal_type,
                s.os_type,
                s.host_name,
                COUNT(ar.request_id) as request_count,
                SUM(ar.cost_usd) as total_cost
            FROM sessions s
            JOIN user_accounts ua ON s.user_id = ua.user_id
            JOIN employees e ON ua.employee_id = e.employee_id
            LEFT JOIN api_requests ar ON s.session_id = ar.session_id
            WHERE e.email = :email
                AND (:start_date IS NULL OR s.session_start >= :start_date)
                AND (:end_date IS NULL OR s.session_start <= :end_date)
            GROUP BY s.session_id, s.session_start, s.session_end, s.terminal_type, s.os_type, s.host_name
            ORDER BY s.session_start DESC
            LIMIT :limit
        """)

        with engine.connect() as conn:
            result = conn.execute(
                query,
                {
                    "email": email,
                    "start_date": start_dt,
                    "end_date": end_dt,
                    "limit": limit
                }
            )
            sessions = [dict(row._mapping) for row in result]

        engine.dispose()

        return sessions
    except Exception as e:
        logger.error(f"Error fetching user sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
