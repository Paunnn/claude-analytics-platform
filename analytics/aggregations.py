"""
Data aggregation engine.

This module provides time-series aggregations and statistical summaries
using sync SQLAlchemy for analytical queries.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
import logging

from config import settings


logger = logging.getLogger(__name__)


class AggregationEngine:
    """
    Data aggregation engine for time-series and statistical analysis.

    Provides various aggregation functions:
    - Temporal aggregations (hourly, daily, weekly, monthly)
    - Statistical summaries
    - Cohort analysis
    - Correlation analysis
    """

    def __init__(self, engine: Optional[Engine] = None):
        """
        Initialize AggregationEngine.

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

        logger.info("AggregationEngine initialized")

    def aggregate_by_time(
        self,
        metric: str = "cost",
        time_grain: str = "day",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Aggregate metrics by time period.

        Args:
            metric: Metric to aggregate ('cost', 'tokens', 'requests', 'sessions')
            time_grain: Aggregation level ('hour', 'day', 'week', 'month')
            start_date: Start of date range
            end_date: End of date range

        Returns:
            Time-series DataFrame with aggregated metrics

        Example:
            >>> agg = AggregationEngine()
            >>> daily_cost = agg.aggregate_by_time('cost', 'day')
        """
        logger.info(f"Aggregating {metric} by {time_grain}")

        # Map time grain to PostgreSQL date_trunc function
        time_grain_map = {
            'hour': 'hour',
            'day': 'day',
            'week': 'week',
            'month': 'month'
        }

        if time_grain not in time_grain_map:
            raise ValueError(f"Invalid time_grain: {time_grain}. Must be one of {list(time_grain_map.keys())}")

        # Build metric calculation based on requested metric
        if metric == 'cost':
            metric_expr = "SUM(ar.cost_usd) as value"
        elif metric == 'tokens':
            metric_expr = "SUM(ar.input_tokens + ar.output_tokens) as value"
        elif metric == 'requests':
            metric_expr = "COUNT(*) as value"
        elif metric == 'sessions':
            metric_expr = "COUNT(DISTINCT ar.session_id) as value"
        else:
            raise ValueError(f"Invalid metric: {metric}. Must be one of ['cost', 'tokens', 'requests', 'sessions']")

        query = text(f"""
            SELECT
                DATE_TRUNC(:time_grain, ar.event_timestamp) as time_bucket,
                {metric_expr},
                COUNT(*) as request_count,
                COUNT(DISTINCT ar.user_id) as unique_users
            FROM api_requests ar
            WHERE 1=1
                AND (:start_date IS NULL OR ar.event_timestamp >= :start_date)
                AND (:end_date IS NULL OR ar.event_timestamp <= :end_date)
            GROUP BY DATE_TRUNC(:time_grain, ar.event_timestamp)
            ORDER BY time_bucket
        """)

        df = pd.read_sql(
            query,
            self.engine,
            params={
                'time_grain': time_grain,
                'start_date': start_date,
                'end_date': end_date
            }
        )

        logger.info(f"Aggregated {len(df)} time periods")
        return df

    def aggregate_by_user_cohort(
        self,
        cohort_field: str = "level"
    ) -> pd.DataFrame:
        """
        Aggregate metrics by user cohort.

        Args:
            cohort_field: Field to group by ('level', 'practice', 'location')

        Returns:
            DataFrame with cohort-level aggregations

        Example:
            >>> cohorts = agg.aggregate_by_user_cohort('level')
            >>> print(cohorts)
        """
        logger.info(f"Aggregating by cohort: {cohort_field}")

        valid_fields = ['level', 'practice', 'location']
        if cohort_field not in valid_fields:
            raise ValueError(f"Invalid cohort_field: {cohort_field}. Must be one of {valid_fields}")

        query = text(f"""
            SELECT
                e.{cohort_field} as cohort,
                COUNT(DISTINCT e.employee_id) as user_count,
                COUNT(*) as total_requests,
                SUM(ar.cost_usd) as total_cost,
                AVG(ar.cost_usd) as avg_cost_per_request,
                SUM(ar.input_tokens + ar.output_tokens) as total_tokens,
                AVG(ar.input_tokens + ar.output_tokens) as avg_tokens_per_request,
                SUM(ar.cache_read_tokens)::FLOAT / NULLIF(SUM(ar.cache_read_tokens + ar.input_tokens), 0) as cache_hit_rate,
                COUNT(DISTINCT ar.session_id) as total_sessions,
                COUNT(*)::FLOAT / COUNT(DISTINCT e.employee_id) as requests_per_user
            FROM api_requests ar
            JOIN user_accounts ua ON ar.user_id = ua.user_id
            JOIN employees e ON ua.employee_id = e.employee_id
            GROUP BY e.{cohort_field}
            ORDER BY total_cost DESC
        """)

        df = pd.read_sql(query, self.engine)

        logger.info(f"Aggregated {len(df)} cohorts")
        return df

    def calculate_rolling_averages(
        self,
        metric: str = "cost",
        window_days: int = 7
    ) -> pd.DataFrame:
        """
        Calculate rolling averages over time.

        Args:
            metric: Metric to calculate rolling average for
            window_days: Rolling window size in days

        Returns:
            DataFrame with rolling averages

        Example:
            >>> rolling = agg.calculate_rolling_averages('cost', window_days=7)
            >>> print(rolling.head())
        """
        logger.info(f"Calculating {window_days}-day rolling average for {metric}")

        # First get daily aggregates
        daily_df = self.aggregate_by_time(metric=metric, time_grain='day')

        # Calculate rolling average using pandas
        daily_df['rolling_avg'] = daily_df['value'].rolling(window=window_days, min_periods=1).mean()
        daily_df['rolling_sum'] = daily_df['value'].rolling(window=window_days, min_periods=1).sum()

        logger.info(f"Calculated rolling averages: {len(daily_df)} days")
        return daily_df

    def calculate_percentiles(
        self,
        metric: str = "cost_usd",
        percentiles: List[float] = [0.25, 0.5, 0.75, 0.9, 0.95, 0.99]
    ) -> Dict[str, float]:
        """
        Calculate percentile distribution for a metric.

        Args:
            metric: Metric to analyze (column name in api_requests)
            percentiles: List of percentile values (0-1)

        Returns:
            Dictionary mapping percentile to value

        Example:
            >>> p = agg.calculate_percentiles('cost_usd', [0.5, 0.9, 0.99])
            >>> print(f"Median: ${p[0.5]:.2f}")
        """
        logger.info(f"Calculating percentiles for {metric}")

        # Build percentile expressions
        percentile_exprs = []
        for p in percentiles:
            percentile_exprs.append(
                f"PERCENTILE_CONT({p}) WITHIN GROUP (ORDER BY {metric}) as p{int(p*100)}"
            )

        query = text(f"""
            SELECT
                {', '.join(percentile_exprs)},
                MIN({metric}) as min_value,
                MAX({metric}) as max_value,
                AVG({metric}) as mean_value,
                STDDEV({metric}) as std_value
            FROM api_requests
        """)

        result = pd.read_sql(query, self.engine)

        # Convert to dictionary
        percentile_dict = {}
        for p in percentiles:
            col_name = f'p{int(p*100)}'
            percentile_dict[p] = float(result[col_name].iloc[0])

        # Add summary stats
        percentile_dict['min'] = float(result['min_value'].iloc[0])
        percentile_dict['max'] = float(result['max_value'].iloc[0])
        percentile_dict['mean'] = float(result['mean_value'].iloc[0])
        percentile_dict['std'] = float(result['std_value'].iloc[0]) if result['std_value'].iloc[0] else 0

        logger.info(f"Calculated {len(percentiles)} percentiles")
        return percentile_dict

    def calculate_correlation_matrix(
        self,
        metrics: List[str] = ['input_tokens', 'output_tokens', 'cost_usd', 'duration_ms']
    ) -> pd.DataFrame:
        """
        Calculate correlation matrix between metrics.

        Args:
            metrics: List of metric names to correlate

        Returns:
            Correlation matrix DataFrame

        Example:
            >>> corr = agg.calculate_correlation_matrix()
            >>> print(corr)
        """
        logger.info(f"Calculating correlation matrix for {len(metrics)} metrics")

        # Get data for correlation analysis
        metrics_str = ', '.join(metrics)
        query = text(f"""
            SELECT {metrics_str}
            FROM api_requests
            WHERE cost_usd IS NOT NULL
                AND duration_ms IS NOT NULL
            LIMIT 10000
        """)

        df = pd.read_sql(query, self.engine)

        # Calculate correlation matrix
        corr_matrix = df.corr()

        logger.info(f"Calculated correlation matrix: {corr_matrix.shape}")
        return corr_matrix

    def aggregate_tool_usage_patterns(self) -> pd.DataFrame:
        """
        Aggregate tool usage patterns by user characteristics.

        Returns:
            DataFrame showing tool preferences by user segments

        Example:
            >>> patterns = agg.aggregate_tool_usage_patterns()
            >>> print(patterns.head())
        """
        logger.info("Aggregating tool usage patterns")

        query = text("""
            SELECT
                e.practice,
                e.level,
                t.tool_name,
                COUNT(*) as usage_count,
                SUM(CASE WHEN tr.success THEN 1 ELSE 0 END) as successful_count,
                AVG(tr.duration_ms) as avg_duration_ms,
                COUNT(DISTINCT tr.user_id) as unique_users
            FROM tool_results tr
            JOIN tools t ON tr.tool_id = t.tool_id
            JOIN user_accounts ua ON tr.user_id = ua.user_id
            JOIN employees e ON ua.employee_id = e.employee_id
            GROUP BY e.practice, e.level, t.tool_name
            HAVING COUNT(*) >= 10  -- Only include patterns with sufficient data
            ORDER BY e.practice, usage_count DESC
        """)

        df = pd.read_sql(query, self.engine)

        logger.info(f"Aggregated {len(df)} tool usage patterns")
        return df

    def calculate_user_retention(
        self,
        period: str = "week"
    ) -> pd.DataFrame:
        """
        Calculate user retention cohorts.

        Args:
            period: Retention period ('day', 'week', 'month')

        Returns:
            Retention cohort matrix

        Example:
            >>> retention = agg.calculate_user_retention('week')
            >>> print(retention.head())
        """
        logger.info(f"Calculating user retention by {period}")

        query = text(f"""
            WITH user_first_activity AS (
                SELECT
                    user_id,
                    DATE_TRUNC(:period, MIN(event_timestamp)) as cohort_period
                FROM api_requests
                GROUP BY user_id
            ),
            user_activity AS (
                SELECT
                    ar.user_id,
                    DATE_TRUNC(:period, ar.event_timestamp) as activity_period
                FROM api_requests ar
                GROUP BY ar.user_id, DATE_TRUNC(:period, ar.event_timestamp)
            )
            SELECT
                ufa.cohort_period,
                ua.activity_period,
                COUNT(DISTINCT ufa.user_id) as cohort_size,
                COUNT(DISTINCT ua.user_id) as retained_users,
                COUNT(DISTINCT ua.user_id)::FLOAT / COUNT(DISTINCT ufa.user_id) as retention_rate
            FROM user_first_activity ufa
            LEFT JOIN user_activity ua
                ON ufa.user_id = ua.user_id
                AND ua.activity_period >= ufa.cohort_period
            GROUP BY ufa.cohort_period, ua.activity_period
            ORDER BY ufa.cohort_period, ua.activity_period
        """)

        df = pd.read_sql(query, self.engine, params={'period': period})

        logger.info(f"Calculated retention: {len(df)} cohort-period combinations")
        return df

    def aggregate_model_usage_trends(self) -> pd.DataFrame:
        """
        Aggregate model usage trends over time.

        Returns:
            DataFrame with model adoption and usage trends

        Example:
            >>> trends = agg.aggregate_model_usage_trends()
            >>> print(trends.head())
        """
        logger.info("Aggregating model usage trends")

        query = text("""
            SELECT
                DATE(ar.event_timestamp) as date,
                m.model_name,
                m.model_family,
                COUNT(*) as request_count,
                SUM(ar.cost_usd) as total_cost,
                AVG(ar.duration_ms) as avg_duration_ms,
                SUM(ar.input_tokens + ar.output_tokens) as total_tokens
            FROM api_requests ar
            JOIN models m ON ar.model_id = m.model_id
            GROUP BY DATE(ar.event_timestamp), m.model_name, m.model_family
            ORDER BY date, request_count DESC
        """)

        df = pd.read_sql(query, self.engine)

        logger.info(f"Aggregated model trends: {len(df)} date-model combinations")
        return df

    def aggregate_hourly_patterns(self) -> pd.DataFrame:
        """
        Aggregate usage patterns by hour of day across all days.

        Returns:
            DataFrame with hourly statistics

        Example:
            >>> hourly = agg.aggregate_hourly_patterns()
            >>> print(hourly)
        """
        logger.info("Aggregating hourly patterns")

        query = text("""
            SELECT
                EXTRACT(HOUR FROM event_timestamp) as hour_of_day,
                COUNT(*) as total_requests,
                SUM(cost_usd) as total_cost,
                AVG(cost_usd) as avg_cost,
                AVG(duration_ms) as avg_duration_ms,
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(DISTINCT session_id) as unique_sessions
            FROM api_requests
            GROUP BY EXTRACT(HOUR FROM event_timestamp)
            ORDER BY hour_of_day
        """)

        df = pd.read_sql(query, self.engine)
        df['hour_of_day'] = df['hour_of_day'].astype(int)

        logger.info(f"Aggregated hourly patterns: {len(df)} hours")
        return df

    def aggregate_by_practice_over_time(
        self,
        time_grain: str = "day"
    ) -> pd.DataFrame:
        """
        Aggregate metrics by practice over time.

        Args:
            time_grain: Time granularity ('day', 'week', 'month')

        Returns:
            DataFrame with practice trends over time

        Example:
            >>> trends = agg.aggregate_by_practice_over_time('day')
            >>> # Pivot for visualization
            >>> pivot = trends.pivot(index='time_bucket', columns='practice', values='total_cost')
        """
        logger.info(f"Aggregating by practice over time ({time_grain})")

        query = text(f"""
            SELECT
                DATE_TRUNC(:time_grain, ar.event_timestamp) as time_bucket,
                e.practice,
                COUNT(*) as request_count,
                SUM(ar.cost_usd) as total_cost,
                AVG(ar.cost_usd) as avg_cost,
                SUM(ar.input_tokens + ar.output_tokens) as total_tokens,
                COUNT(DISTINCT ar.user_id) as unique_users
            FROM api_requests ar
            JOIN user_accounts ua ON ar.user_id = ua.user_id
            JOIN employees e ON ua.employee_id = e.employee_id
            GROUP BY DATE_TRUNC(:time_grain, ar.event_timestamp), e.practice
            ORDER BY time_bucket, e.practice
        """)

        df = pd.read_sql(query, self.engine, params={'time_grain': time_grain})

        logger.info(f"Aggregated {len(df)} time-practice combinations")
        return df
