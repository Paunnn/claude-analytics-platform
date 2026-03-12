"""
Metrics calculation engine.

This module calculates key metrics and KPIs from telemetry data
using sync SQLAlchemy for better performance with analytical queries.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
import logging

from config import settings


logger = logging.getLogger(__name__)


class MetricsEngine:
    """
    Metrics calculation engine.

    Calculates various metrics including:
    - Token usage metrics
    - Cost metrics
    - Performance metrics
    - User activity metrics
    """

    def __init__(self, engine: Optional[Engine] = None):
        """
        Initialize MetricsEngine.

        Args:
            engine: SQLAlchemy engine (sync). If None, creates one from settings.
        """
        if engine is None:
            # Create sync engine
            sync_url = settings.database_url
            if 'asyncpg' in sync_url:
                sync_url = sync_url.replace('postgresql+asyncpg://', 'postgresql://')

            self.engine = create_engine(
                sync_url,
                echo=settings.log_level == "DEBUG",
                pool_pre_ping=True,
            )
        else:
            self.engine = engine

        logger.info("MetricsEngine initialized")

    def token_trends_by_practice(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Calculate token usage trends by practice over time.

        Args:
            start_date: Start of date range
            end_date: End of date range

        Returns:
            DataFrame with columns: date, practice, total_input_tokens,
            total_output_tokens, total_cache_read_tokens

        Example:
            >>> metrics = MetricsEngine()
            >>> trends = metrics.token_trends_by_practice()
            >>> print(trends.head())
        """
        logger.info("Calculating token trends by practice")

        query = text("""
            SELECT
                DATE(ar.event_timestamp) as date,
                e.practice,
                SUM(ar.input_tokens) as total_input_tokens,
                SUM(ar.output_tokens) as total_output_tokens,
                SUM(ar.cache_read_tokens) as total_cache_read_tokens,
                SUM(ar.cache_creation_tokens) as total_cache_creation_tokens,
                COUNT(*) as request_count
            FROM api_requests ar
            JOIN user_accounts ua ON ar.user_id = ua.user_id
            JOIN employees e ON ua.employee_id = e.employee_id
            WHERE 1=1
                AND (:start_date IS NULL OR ar.event_timestamp >= :start_date)
                AND (:end_date IS NULL OR ar.event_timestamp <= :end_date)
            GROUP BY DATE(ar.event_timestamp), e.practice
            ORDER BY date, e.practice
        """)

        df = pd.read_sql(
            query,
            self.engine,
            params={
                'start_date': start_date,
                'end_date': end_date
            }
        )

        logger.info(f"Calculated token trends: {len(df)} records")
        return df

    def cost_by_practice_and_level(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Calculate costs aggregated by practice and seniority level.

        Args:
            start_date: Start of date range
            end_date: End of date range

        Returns:
            DataFrame with columns: practice, level, total_cost,
            request_count, avg_cost_per_request

        Example:
            >>> costs = metrics.cost_by_practice_and_level()
            >>> print(costs.head())
        """
        logger.info("Calculating costs by practice and level")

        query = text("""
            SELECT
                e.practice,
                e.level,
                SUM(ar.cost_usd) as total_cost,
                COUNT(*) as request_count,
                AVG(ar.cost_usd) as avg_cost_per_request,
                SUM(ar.input_tokens + ar.output_tokens) as total_tokens
            FROM api_requests ar
            JOIN user_accounts ua ON ar.user_id = ua.user_id
            JOIN employees e ON ua.employee_id = e.employee_id
            WHERE 1=1
                AND (:start_date IS NULL OR ar.event_timestamp >= :start_date)
                AND (:end_date IS NULL OR ar.event_timestamp <= :end_date)
            GROUP BY e.practice, e.level
            ORDER BY total_cost DESC
        """)

        df = pd.read_sql(
            query,
            self.engine,
            params={
                'start_date': start_date,
                'end_date': end_date
            }
        )

        logger.info(f"Calculated costs: {len(df)} practice-level combinations")
        return df

    def peak_usage_heatmap(self) -> pd.DataFrame:
        """
        Calculate usage heatmap: hour of day vs day of week.

        Returns:
            DataFrame with columns: hour_of_day (0-23), day_of_week (0-6),
            request_count, total_cost

        Example:
            >>> heatmap = metrics.peak_usage_heatmap()
            >>> # Pivot for visualization
            >>> pivot = heatmap.pivot(index='hour_of_day', columns='day_of_week', values='request_count')
        """
        logger.info("Calculating peak usage heatmap")

        query = text("""
            SELECT
                EXTRACT(HOUR FROM event_timestamp) as hour_of_day,
                EXTRACT(DOW FROM event_timestamp) as day_of_week,
                COUNT(*) as request_count,
                SUM(cost_usd) as total_cost,
                AVG(duration_ms) as avg_duration_ms
            FROM api_requests
            GROUP BY
                EXTRACT(HOUR FROM event_timestamp),
                EXTRACT(DOW FROM event_timestamp)
            ORDER BY hour_of_day, day_of_week
        """)

        df = pd.read_sql(query, self.engine)

        # Convert to int for cleaner display
        df['hour_of_day'] = df['hour_of_day'].astype(int)
        df['day_of_week'] = df['day_of_week'].astype(int)

        logger.info(f"Calculated heatmap: {len(df)} hour-day combinations")
        return df

    def session_duration_stats(self) -> pd.DataFrame:
        """
        Calculate session duration statistics by practice and terminal type.

        Returns:
            DataFrame with columns: practice, terminal_type, avg_duration_minutes,
            median_duration_minutes, session_count, avg_requests_per_session

        Example:
            >>> stats = metrics.session_duration_stats()
            >>> print(stats.head())
        """
        logger.info("Calculating session duration statistics")

        query = text("""
            SELECT
                e.practice,
                s.terminal_type,
                COUNT(DISTINCT s.session_id) as session_count,
                AVG(EXTRACT(EPOCH FROM (s.session_end - s.session_start)) / 60) as avg_duration_minutes,
                PERCENTILE_CONT(0.5) WITHIN GROUP (
                    ORDER BY EXTRACT(EPOCH FROM (s.session_end - s.session_start)) / 60
                ) as median_duration_minutes,
                COUNT(ar.request_id)::FLOAT / COUNT(DISTINCT s.session_id) as avg_requests_per_session,
                SUM(ar.cost_usd) as total_cost
            FROM sessions s
            JOIN user_accounts ua ON s.user_id = ua.user_id
            JOIN employees e ON ua.employee_id = e.employee_id
            LEFT JOIN api_requests ar ON s.session_id = ar.session_id
            WHERE s.session_end IS NOT NULL
            GROUP BY e.practice, s.terminal_type
            ORDER BY avg_duration_minutes DESC
        """)

        df = pd.read_sql(query, self.engine)

        logger.info(f"Calculated session stats: {len(df)} practice-terminal combinations")
        return df

    def tool_success_rates(self) -> pd.DataFrame:
        """
        Calculate success rates for each tool.

        Returns:
            DataFrame with columns: tool_name, total_executions, successful,
            failed, success_rate, avg_duration_ms

        Example:
            >>> rates = metrics.tool_success_rates()
            >>> print(rates.head())
        """
        logger.info("Calculating tool success rates")

        query = text("""
            SELECT
                t.tool_name,
                COUNT(*) as total_executions,
                SUM(CASE WHEN tr.success THEN 1 ELSE 0 END) as successful,
                SUM(CASE WHEN NOT tr.success THEN 1 ELSE 0 END) as failed,
                AVG(CASE WHEN tr.success THEN 1.0 ELSE 0.0 END) as success_rate,
                AVG(tr.duration_ms) as avg_duration_ms,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY tr.duration_ms) as median_duration_ms,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY tr.duration_ms) as p95_duration_ms
            FROM tool_results tr
            JOIN tools t ON tr.tool_id = t.tool_id
            GROUP BY t.tool_name
            ORDER BY total_executions DESC
        """)

        df = pd.read_sql(query, self.engine)

        logger.info(f"Calculated tool success rates: {len(df)} tools")
        return df

    def cache_efficiency_by_user(self) -> pd.DataFrame:
        """
        Calculate cache efficiency metrics by user.

        Returns:
            DataFrame with columns: email, full_name, practice, level,
            total_requests, cache_hit_rate, total_cache_read_tokens,
            potential_cost_savings

        Example:
            >>> efficiency = metrics.cache_efficiency_by_user()
            >>> print(efficiency.head())
        """
        logger.info("Calculating cache efficiency by user")

        query = text("""
            SELECT
                e.email,
                e.full_name,
                e.practice,
                e.level,
                COUNT(*) as total_requests,
                SUM(ar.cache_read_tokens) as total_cache_read_tokens,
                SUM(ar.cache_creation_tokens) as total_cache_creation_tokens,
                SUM(ar.input_tokens) as total_input_tokens,
                -- Cache hit rate: cache reads / (cache reads + input tokens)
                CASE
                    WHEN SUM(ar.cache_read_tokens + ar.input_tokens) > 0
                    THEN SUM(ar.cache_read_tokens)::FLOAT / SUM(ar.cache_read_tokens + ar.input_tokens)
                    ELSE 0
                END as cache_hit_rate,
                -- Estimated cost savings (cache reads are cheaper)
                SUM(ar.cache_read_tokens) * 0.000001 as estimated_cache_savings,
                SUM(ar.cost_usd) as total_cost
            FROM api_requests ar
            JOIN user_accounts ua ON ar.user_id = ua.user_id
            JOIN employees e ON ua.employee_id = e.employee_id
            GROUP BY e.email, e.full_name, e.practice, e.level
            ORDER BY cache_hit_rate DESC
        """)

        df = pd.read_sql(query, self.engine)

        logger.info(f"Calculated cache efficiency: {len(df)} users")
        return df

    def model_usage_distribution(self) -> pd.DataFrame:
        """
        Calculate model usage distribution with costs and performance.

        Returns:
            DataFrame with columns: model_name, request_count, total_cost,
            avg_cost_per_request, avg_duration_ms, total_tokens

        Example:
            >>> distribution = metrics.model_usage_distribution()
            >>> print(distribution.head())
        """
        logger.info("Calculating model usage distribution")

        query = text("""
            SELECT
                m.model_name,
                m.model_family,
                COUNT(*) as request_count,
                SUM(ar.cost_usd) as total_cost,
                AVG(ar.cost_usd) as avg_cost_per_request,
                AVG(ar.duration_ms) as avg_duration_ms,
                SUM(ar.input_tokens + ar.output_tokens) as total_tokens,
                SUM(ar.input_tokens) as total_input_tokens,
                SUM(ar.output_tokens) as total_output_tokens,
                SUM(ar.cache_read_tokens) as total_cache_read_tokens,
                -- Calculate percentage of total requests
                COUNT(*)::FLOAT / (SELECT COUNT(*) FROM api_requests) * 100 as percentage_of_requests
            FROM api_requests ar
            JOIN models m ON ar.model_id = m.model_id
            GROUP BY m.model_name, m.model_family
            ORDER BY request_count DESC
        """)

        df = pd.read_sql(query, self.engine)

        logger.info(f"Calculated model distribution: {len(df)} models")
        return df

    def top_users_by_cost(self, n: int = 10) -> pd.DataFrame:
        """
        Get top N users by total cost.

        Args:
            n: Number of top users to return

        Returns:
            DataFrame with columns: email, full_name, practice, level,
            total_cost, request_count, avg_cost_per_request,
            total_input_tokens, total_output_tokens

        Example:
            >>> top10 = metrics.top_users_by_cost(n=10)
            >>> print(top10)
        """
        logger.info(f"Calculating top {n} users by cost")

        query = text("""
            SELECT
                e.email,
                e.full_name,
                e.practice,
                e.level,
                e.location,
                SUM(ar.cost_usd) as total_cost,
                COUNT(*) as request_count,
                AVG(ar.cost_usd) as avg_cost_per_request,
                SUM(ar.input_tokens) as total_input_tokens,
                SUM(ar.output_tokens) as total_output_tokens,
                SUM(ar.cache_read_tokens) as total_cache_read_tokens,
                -- Most used model
                (
                    SELECT m.model_name
                    FROM api_requests ar2
                    JOIN models m ON ar2.model_id = m.model_id
                    WHERE ar2.user_id = ar.user_id
                    GROUP BY m.model_name
                    ORDER BY COUNT(*) DESC
                    LIMIT 1
                ) as most_used_model
            FROM api_requests ar
            JOIN user_accounts ua ON ar.user_id = ua.user_id
            JOIN employees e ON ua.employee_id = e.employee_id
            GROUP BY e.email, e.full_name, e.practice, e.level, e.location, ar.user_id
            ORDER BY total_cost DESC
            LIMIT :n
        """)

        df = pd.read_sql(query, self.engine, params={'n': n})

        logger.info(f"Retrieved top {len(df)} users by cost")
        return df

    def calculate_total_cost(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        group_by: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Calculate total costs with optional grouping.

        Args:
            start_date: Start of date range
            end_date: End of date range
            group_by: Optional columns to group by (e.g., ['practice', 'level'])

        Returns:
            DataFrame with cost metrics

        Example:
            >>> costs = metrics.calculate_total_cost(group_by=['practice'])
            >>> print(costs)
        """
        logger.info("Calculating total costs")

        if group_by is None:
            # Overall totals
            query = text("""
                SELECT
                    SUM(cost_usd) as total_cost,
                    COUNT(*) as request_count,
                    AVG(cost_usd) as avg_cost_per_request,
                    SUM(input_tokens + output_tokens) as total_tokens,
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(DISTINCT session_id) as unique_sessions
                FROM api_requests
                WHERE 1=1
                    AND (:start_date IS NULL OR event_timestamp >= :start_date)
                    AND (:end_date IS NULL OR event_timestamp <= :end_date)
            """)
        else:
            # Group by specified columns
            group_cols = ", ".join([f"e.{col}" for col in group_by])
            query = text(f"""
                SELECT
                    {group_cols},
                    SUM(ar.cost_usd) as total_cost,
                    COUNT(*) as request_count,
                    AVG(ar.cost_usd) as avg_cost_per_request,
                    SUM(ar.input_tokens + ar.output_tokens) as total_tokens
                FROM api_requests ar
                JOIN user_accounts ua ON ar.user_id = ua.user_id
                JOIN employees e ON ua.employee_id = e.employee_id
                WHERE 1=1
                    AND (:start_date IS NULL OR ar.event_timestamp >= :start_date)
                    AND (:end_date IS NULL OR ar.event_timestamp <= :end_date)
                GROUP BY {group_cols}
                ORDER BY total_cost DESC
            """)

        df = pd.read_sql(
            query,
            self.engine,
            params={
                'start_date': start_date,
                'end_date': end_date
            }
        )

        logger.info(f"Calculated costs: {len(df)} records")
        return df

    def calculate_daily_active_users(self, days: int = 30) -> pd.DataFrame:
        """
        Calculate daily active users over time.

        Args:
            days: Number of days to look back

        Returns:
            DataFrame with DAU by date

        Example:
            >>> dau = metrics.calculate_daily_active_users(days=30)
            >>> print(dau.head())
        """
        logger.info(f"Calculating daily active users for last {days} days")

        query = text("""
            SELECT
                DATE(event_timestamp) as date,
                COUNT(DISTINCT user_id) as daily_active_users,
                COUNT(*) as total_requests,
                SUM(cost_usd) as total_cost
            FROM api_requests
            WHERE event_timestamp >= CURRENT_DATE - INTERVAL ':days days'
            GROUP BY DATE(event_timestamp)
            ORDER BY date
        """)

        df = pd.read_sql(query, self.engine, params={'days': days})

        logger.info(f"Calculated DAU: {len(df)} days")
        return df
