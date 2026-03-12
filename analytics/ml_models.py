"""
Machine Learning models for predictive analytics.

This module provides ML models for:
- Anomaly detection using IsolationForest
- Time-series forecasting using Holt-Winters
- User clustering using KMeans
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
import logging

# ML libraries
from sklearn.ensemble import IsolationForest
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import warnings

from config import settings

logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore')


class AnomalyDetector:
    """
    Anomaly detection on daily token usage per user using IsolationForest.

    Detects unusual token consumption patterns that may indicate:
    - Unexpectedly high usage
    - Potential bugs or inefficiencies
    - Users who need optimization support
    """

    def __init__(self, contamination: float = 0.05, engine: Optional[Engine] = None):
        """
        Initialize anomaly detector.

        Args:
            contamination: Expected proportion of outliers (default 5%)
            engine: SQLAlchemy engine (sync). If None, creates one from settings.
        """
        self.contamination = contamination
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        self.is_fitted = False

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

        logger.info(f"AnomalyDetector initialized with contamination={contamination}")

    def _get_daily_user_tokens(self) -> pd.DataFrame:
        """
        Fetch daily token usage per user from database.

        Returns:
            DataFrame with date, user_email, practice, total_tokens
        """
        query = text("""
            SELECT
                DATE(ar.event_timestamp) as date,
                e.email as user_email,
                e.full_name,
                e.practice,
                SUM(ar.input_tokens + ar.output_tokens) as total_tokens,
                COUNT(*) as request_count,
                SUM(ar.cost_usd) as total_cost
            FROM api_requests ar
            JOIN user_accounts ua ON ar.user_id = ua.user_id
            JOIN employees e ON ua.employee_id = e.employee_id
            GROUP BY DATE(ar.event_timestamp), e.email, e.full_name, e.practice
            ORDER BY date, user_email
        """)

        df = pd.read_sql(query, self.engine)
        logger.info(f"Fetched {len(df)} daily user-token records")
        return df

    def fit(self, df: Optional[pd.DataFrame] = None) -> 'AnomalyDetector':
        """
        Train the anomaly detection model on daily token usage.

        Args:
            df: Optional DataFrame with 'total_tokens' column.
                If None, fetches from database.

        Returns:
            self (for method chaining)

        Example:
            >>> detector = AnomalyDetector()
            >>> detector.fit()
            >>> anomalies = detector.predict()
        """
        if df is None:
            df = self._get_daily_user_tokens()

        # Feature: total_tokens per day per user
        X = df[['total_tokens']].values

        # Fit model
        self.model.fit(X)
        self.is_fitted = True

        logger.info(f"AnomalyDetector fitted on {len(df)} records")
        return self

    def predict(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Detect anomalies in daily token usage.

        Args:
            df: Optional DataFrame with 'total_tokens' column.
                If None, fetches from database.

        Returns:
            DataFrame with columns:
            - date: Date of usage
            - user_email: User email
            - practice: User's practice
            - total_tokens: Total tokens used
            - is_anomaly: True if anomalous
            - anomaly_score: Anomaly score (lower = more anomalous)

        Example:
            >>> anomalies = detector.predict()
            >>> print(anomalies[anomalies['is_anomaly']])
        """
        if not self.is_fitted:
            logger.warning("Model not fitted. Calling fit() first.")
            self.fit()

        if df is None:
            df = self._get_daily_user_tokens()

        # Get features
        X = df[['total_tokens']].values

        # Predict: -1 for anomalies, 1 for normal
        predictions = self.model.predict(X)

        # Get anomaly scores (lower = more anomalous)
        scores = self.model.score_samples(X)

        # Add predictions to dataframe
        result = df.copy()
        result['is_anomaly'] = predictions == -1
        result['anomaly_score'] = scores

        # Select output columns
        result = result[[
            'date', 'user_email', 'practice', 'total_tokens',
            'is_anomaly', 'anomaly_score'
        ]]

        anomaly_count = result['is_anomaly'].sum()
        logger.info(f"Detected {anomaly_count} anomalies out of {len(result)} records")

        return result


class ForecastModel:
    """
    Time-series forecasting using Holt-Winters Exponential Smoothing.

    Forecasts future token usage to help with:
    - Capacity planning
    - Budget forecasting
    - Trend analysis
    """

    def __init__(self, engine: Optional[Engine] = None):
        """
        Initialize forecast model.

        Args:
            engine: SQLAlchemy engine (sync). If None, creates one from settings.
        """
        self.model = None
        self.is_fitted = False

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

        logger.info("ForecastModel initialized")

    def _get_daily_totals(self) -> pd.DataFrame:
        """
        Fetch daily total token usage from database.

        Returns:
            DataFrame with date and total_tokens
        """
        query = text("""
            SELECT
                DATE(event_timestamp) as date,
                SUM(input_tokens + output_tokens) as total_tokens
            FROM api_requests
            GROUP BY DATE(event_timestamp)
            ORDER BY date
        """)

        df = pd.read_sql(query, self.engine)
        logger.info(f"Fetched {len(df)} daily totals")
        return df

    def fit(self, daily_totals_df: Optional[pd.DataFrame] = None) -> 'ForecastModel':
        """
        Train the Holt-Winters forecasting model.

        Args:
            daily_totals_df: Optional DataFrame with 'date' and 'total_tokens' columns.
                             If None, fetches from database.

        Returns:
            self (for method chaining)

        Example:
            >>> model = ForecastModel()
            >>> model.fit()
            >>> forecast = model.forecast(days=7)
        """
        if daily_totals_df is None:
            daily_totals_df = self._get_daily_totals()

        # Prepare time series
        ts = daily_totals_df.set_index('date')['total_tokens']

        # Fit Holt-Winters Exponential Smoothing
        # Use additive model (suitable for stable variance)
        try:
            self.model = ExponentialSmoothing(
                ts,
                trend='add',
                seasonal=None,  # No seasonal pattern in 30 days of data
                seasonal_periods=None
            ).fit()
            self.is_fitted = True
            logger.info(f"ForecastModel fitted on {len(ts)} daily observations")
        except Exception as e:
            # Fallback to simple exponential smoothing if trend fails
            logger.warning(f"Holt-Winters with trend failed: {e}. Using simple exponential smoothing.")
            self.model = ExponentialSmoothing(
                ts,
                trend=None,
                seasonal=None
            ).fit()
            self.is_fitted = True

        return self

    def forecast(self, days: int = 7) -> pd.DataFrame:
        """
        Generate forecast for future days.

        Args:
            days: Number of days to forecast

        Returns:
            DataFrame with columns:
            - date: Forecast date
            - predicted_tokens: Predicted token usage
            - lower_bound: 95% confidence interval lower bound
            - upper_bound: 95% confidence interval upper bound

        Example:
            >>> forecast = model.forecast(days=7)
            >>> print(forecast)
        """
        if not self.is_fitted:
            logger.warning("Model not fitted. Calling fit() first.")
            self.fit()

        # Generate forecast
        forecast_result = self.model.forecast(steps=days)

        # Calculate confidence intervals (approximation: ±1.96 * std_error)
        # Use residual standard error as approximation
        std_error = np.std(self.model.resid)
        margin = 1.96 * std_error

        # Create result dataframe
        last_date = self.model.model.data.orig_endog.index[-1]
        forecast_dates = pd.date_range(
            start=last_date + timedelta(days=1),
            periods=days,
            freq='D'
        )

        result = pd.DataFrame({
            'date': forecast_dates,
            'predicted_tokens': forecast_result.values,
            'lower_bound': forecast_result.values - margin,
            'upper_bound': forecast_result.values + margin
        })

        # Ensure non-negative predictions
        result['predicted_tokens'] = result['predicted_tokens'].clip(lower=0)
        result['lower_bound'] = result['lower_bound'].clip(lower=0)
        result['upper_bound'] = result['upper_bound'].clip(lower=0)

        logger.info(f"Generated {days}-day forecast")
        return result


class UserClusterer:
    """
    User clustering using KMeans to segment users by behavior.

    Segments users into 4 clusters:
    - Power User: High usage, many sessions
    - Balanced: Average usage across all metrics
    - Tool-Heavy: High tool usage rate
    - Light User: Low usage overall
    """

    def __init__(self, n_clusters: int = 4, engine: Optional[Engine] = None):
        """
        Initialize user clusterer.

        Args:
            n_clusters: Number of clusters (default 4)
            engine: SQLAlchemy engine (sync). If None, creates one from settings.
        """
        self.n_clusters = n_clusters
        self.model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        self.scaler = StandardScaler()
        self.is_fitted = False

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

        logger.info(f"UserClusterer initialized with {n_clusters} clusters")

    def _get_user_features(self) -> pd.DataFrame:
        """
        Fetch user features from database.

        Returns:
            DataFrame with user features:
            - user_email, full_name, practice
            - avg_tokens_per_session
            - sessions_per_day
            - tool_usage_rate
            - cache_hit_rate
        """
        query = text("""
            WITH user_stats AS (
                SELECT
                    e.email as user_email,
                    e.full_name,
                    e.practice,
                    e.level,
                    -- Average tokens per session
                    AVG(ar.input_tokens + ar.output_tokens)::FLOAT as avg_tokens_per_request,
                    COUNT(DISTINCT ar.session_id)::FLOAT as total_sessions,
                    COUNT(*)::FLOAT as total_requests,
                    -- Date range for sessions per day calculation
                    EXTRACT(EPOCH FROM (MAX(ar.event_timestamp) - MIN(ar.event_timestamp))) / 86400.0 as days_active,
                    -- Cache hit rate
                    SUM(ar.cache_read_tokens)::FLOAT / NULLIF(SUM(ar.cache_read_tokens + ar.input_tokens), 0) as cache_hit_rate
                FROM api_requests ar
                JOIN user_accounts ua ON ar.user_id = ua.user_id
                JOIN employees e ON ua.employee_id = e.employee_id
                GROUP BY e.email, e.full_name, e.practice, e.level
            ),
            tool_stats AS (
                SELECT
                    e.email as user_email,
                    COUNT(*)::FLOAT as total_tool_executions
                FROM tool_results tr
                JOIN user_accounts ua ON tr.user_id = ua.user_id
                JOIN employees e ON ua.employee_id = e.employee_id
                GROUP BY e.email
            )
            SELECT
                us.user_email,
                us.full_name,
                us.practice,
                us.level,
                -- Feature 1: Average tokens per session
                (us.total_requests * us.avg_tokens_per_request / us.total_sessions) as avg_tokens_per_session,
                -- Feature 2: Sessions per day
                (us.total_sessions / NULLIF(us.days_active, 0)) as sessions_per_day,
                -- Feature 3: Tool usage rate (tools per request)
                COALESCE(ts.total_tool_executions / us.total_requests, 0) as tool_usage_rate,
                -- Feature 4: Cache hit rate
                COALESCE(us.cache_hit_rate, 0) as cache_hit_rate
            FROM user_stats us
            LEFT JOIN tool_stats ts ON us.user_email = ts.user_email
            WHERE us.total_sessions > 0 AND us.days_active > 0
        """)

        df = pd.read_sql(query, self.engine)

        # Handle any NaN or inf values
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.fillna(0)

        logger.info(f"Fetched features for {len(df)} users")
        return df

    def fit_predict(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Cluster users based on behavioral features.

        Args:
            df: Optional DataFrame with feature columns. If None, fetches from database.

        Returns:
            DataFrame with columns:
            - user_email: User email
            - full_name: User full name
            - practice: User's practice
            - cluster_label: Assigned cluster label
            - avg_tokens_per_session: Feature value
            - sessions_per_day: Feature value
            - tool_usage_rate: Feature value
            - cache_hit_rate: Feature value

        Example:
            >>> clusterer = UserClusterer()
            >>> clusters = clusterer.fit_predict()
            >>> print(clusters.groupby('cluster_label').size())
        """
        if df is None:
            df = self._get_user_features()

        # Extract features
        feature_cols = [
            'avg_tokens_per_session',
            'sessions_per_day',
            'tool_usage_rate',
            'cache_hit_rate'
        ]

        X = df[feature_cols].values

        # Normalize features
        X_scaled = self.scaler.fit_transform(X)

        # Fit KMeans
        cluster_ids = self.model.fit_predict(X_scaled)
        self.is_fitted = True

        # Assign meaningful labels based on cluster characteristics
        df_copy = df.copy()
        df_copy['cluster_id'] = cluster_ids

        # Calculate cluster centers in original scale
        cluster_stats = df_copy.groupby('cluster_id')[feature_cols].mean()

        # Assign labels based on characteristics
        labels = self._assign_cluster_labels(cluster_stats)

        # Map cluster IDs to labels
        df_copy['cluster_label'] = df_copy['cluster_id'].map(labels)

        # Select output columns
        result = df_copy[[
            'user_email', 'full_name', 'practice', 'cluster_label',
            'avg_tokens_per_session', 'sessions_per_day',
            'tool_usage_rate', 'cache_hit_rate'
        ]]

        logger.info(f"Clustered {len(result)} users into {self.n_clusters} clusters")
        logger.info(f"Cluster distribution:\n{result['cluster_label'].value_counts()}")

        return result

    def _assign_cluster_labels(self, cluster_stats: pd.DataFrame) -> Dict[int, str]:
        """
        Assign meaningful labels to clusters based on their characteristics.

        Args:
            cluster_stats: DataFrame with mean feature values per cluster

        Returns:
            Dictionary mapping cluster_id to label
        """
        labels = {}

        # Calculate relative metrics (normalized by max)
        for col in cluster_stats.columns:
            max_val = cluster_stats[col].max()
            if max_val > 0:
                cluster_stats[f'{col}_norm'] = cluster_stats[col] / max_val
            else:
                cluster_stats[f'{col}_norm'] = 0

        for cluster_id in cluster_stats.index:
            stats = cluster_stats.loc[cluster_id]

            # Determine label based on normalized feature values
            tokens = stats['avg_tokens_per_session_norm']
            sessions = stats['sessions_per_day_norm']
            tools = stats['tool_usage_rate_norm']
            cache = stats['cache_hit_rate_norm']

            # Power User: High tokens AND high sessions
            if tokens > 0.7 and sessions > 0.7:
                labels[cluster_id] = 'Power User'
            # Tool-Heavy: High tool usage
            elif tools > 0.7:
                labels[cluster_id] = 'Tool-Heavy'
            # Light User: Low on most metrics
            elif tokens < 0.4 and sessions < 0.4:
                labels[cluster_id] = 'Light User'
            # Balanced: Everything else
            else:
                labels[cluster_id] = 'Balanced'

        # Ensure all 4 labels are present (if we have 4 clusters)
        used_labels = set(labels.values())
        all_labels = {'Power User', 'Balanced', 'Tool-Heavy', 'Light User'}

        # If any label is missing, assign it to the cluster closest to that profile
        if len(used_labels) < 4 and len(labels) == 4:
            missing_labels = all_labels - used_labels
            for label in missing_labels:
                # Find unassigned cluster and assign missing label
                for cid in labels:
                    if labels[cid] in list(labels.values())[:-1]:  # Already assigned
                        continue
                    labels[cid] = label
                    break

        return labels
