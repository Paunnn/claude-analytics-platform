"""
Analytics API endpoints.

Provides endpoints for retrieving analytics, metrics, and insights.
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Dict, Any, List, Optional
from datetime import datetime, date
import logging

from analytics.metrics import MetricsEngine
from analytics.aggregations import AggregationEngine
from analytics.ml_models import AnomalyDetector, ForecastModel, UserClusterer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/metrics/token-usage")
async def get_token_usage_metrics(
    start_date: Optional[date] = Query(None, description="Start date for metrics"),
    end_date: Optional[date] = Query(None, description="End date for metrics"),
    group_by: Optional[str] = Query(None, description="Group by field (practice, level)")
) -> Dict[str, Any]:
    """
    Get token usage metrics.

    Returns:
        Dictionary with token usage statistics
    """
    try:
        metrics = MetricsEngine()

        # Convert dates to datetime
        start_dt = datetime.combine(start_date, datetime.min.time()) if start_date else None
        end_dt = datetime.combine(end_date, datetime.max.time()) if end_date else None

        # Get token trends by practice
        df = metrics.token_trends_by_practice(start_date=start_dt, end_date=end_dt)

        return {
            "data": df.to_dict(orient="records"),
            "total_records": len(df),
            "start_date": str(start_date) if start_date else None,
            "end_date": str(end_date) if end_date else None
        }
    except Exception as e:
        logger.error(f"Error fetching token usage metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/cost")
async def get_cost_metrics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    group_by: Optional[str] = Query(None, description="Group by field")
) -> Dict[str, Any]:
    """
    Get cost metrics and breakdowns.

    Returns:
        Dictionary with cost statistics
    """
    try:
        metrics = MetricsEngine()

        start_dt = datetime.combine(start_date, datetime.min.time()) if start_date else None
        end_dt = datetime.combine(end_date, datetime.max.time()) if end_date else None

        if group_by:
            df = metrics.calculate_total_cost(
                start_date=start_dt,
                end_date=end_dt,
                group_by=[group_by]
            )
        else:
            df = metrics.calculate_total_cost(start_date=start_dt, end_date=end_dt)

        return {
            "data": df.to_dict(orient="records"),
            "total_records": len(df)
        }
    except Exception as e:
        logger.error(f"Error fetching cost metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/performance")
async def get_performance_metrics(
    model_name: Optional[str] = Query(None, description="Filter by model")
) -> Dict[str, Any]:
    """
    Get performance metrics (latency, errors, etc.).

    Returns:
        Dictionary with performance statistics
    """
    try:
        metrics = MetricsEngine()

        # Get tool success rates
        tool_stats = metrics.tool_success_rates()

        # Get model usage distribution
        model_stats = metrics.model_usage_distribution()

        if model_name:
            model_stats = model_stats[model_stats['model_name'] == model_name]

        return {
            "tool_performance": tool_stats.to_dict(orient="records"),
            "model_performance": model_stats.to_dict(orient="records")
        }
    except Exception as e:
        logger.error(f"Error fetching performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/peak-hours")
async def get_peak_usage_hours() -> Dict[str, Any]:
    """
    Get peak usage hours analysis.

    Returns:
        Dictionary with hourly usage patterns
    """
    try:
        metrics = MetricsEngine()
        heatmap = metrics.peak_usage_heatmap()

        return {
            "data": heatmap.to_dict(orient="records"),
            "total_records": len(heatmap)
        }
    except Exception as e:
        logger.error(f"Error fetching peak hours: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/cache-efficiency")
async def get_cache_efficiency() -> Dict[str, Any]:
    """
    Get cache efficiency metrics by user.

    Returns:
        Dictionary with cache hit rates and efficiency
    """
    try:
        metrics = MetricsEngine()
        cache_df = metrics.cache_efficiency_by_user()

        return {
            "data": cache_df.to_dict(orient="records"),
            "total_users": len(cache_df),
            "avg_cache_hit_rate": float(cache_df['cache_hit_rate'].mean())
        }
    except Exception as e:
        logger.error(f"Error fetching cache efficiency: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/top-users")
async def get_top_users(
    n: int = Query(10, ge=1, le=100, description="Number of top users")
) -> Dict[str, Any]:
    """
    Get top N users by cost.

    Returns:
        Dictionary with top users by spending
    """
    try:
        metrics = MetricsEngine()
        top_users = metrics.top_users_by_cost(n=n)

        return {
            "data": top_users.to_dict(orient="records"),
            "total_users": len(top_users)
        }
    except Exception as e:
        logger.error(f"Error fetching top users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends/{metric}")
async def get_metric_trend(
    metric: str,
    time_grain: str = Query("day", description="Aggregation level (hour, day, week, month)"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
) -> Dict[str, Any]:
    """
    Get time-series trend for a specific metric.

    Returns:
        Time-series data for the metric
    """
    try:
        agg = AggregationEngine()

        start_dt = datetime.combine(start_date, datetime.min.time()) if start_date else None
        end_dt = datetime.combine(end_date, datetime.max.time()) if end_date else None

        df = agg.aggregate_by_time(
            metric=metric,
            time_grain=time_grain,
            start_date=start_dt,
            end_date=end_dt
        )

        return {
            "metric": metric,
            "time_grain": time_grain,
            "data": df.to_dict(orient="records"),
            "total_periods": len(df)
        }
    except Exception as e:
        logger.error(f"Error fetching metric trend: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/aggregations/user-cohorts")
async def get_user_cohort_analysis(
    cohort_field: str = Query("level", description="Cohort field (level, practice, location)")
) -> Dict[str, Any]:
    """
    Get user cohort analysis.

    Returns:
        Cohort-level aggregations
    """
    try:
        agg = AggregationEngine()
        cohorts = agg.aggregate_by_user_cohort(cohort_field=cohort_field)

        return {
            "cohort_field": cohort_field,
            "data": cohorts.to_dict(orient="records"),
            "total_cohorts": len(cohorts)
        }
    except Exception as e:
        logger.error(f"Error fetching cohort analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/aggregations/rolling-averages")
async def get_rolling_averages(
    metric: str = Query("cost", description="Metric to calculate"),
    window_days: int = Query(7, ge=1, le=90, description="Rolling window in days")
) -> Dict[str, Any]:
    """
    Get rolling averages for a metric.

    Returns:
        Time-series with rolling averages
    """
    try:
        agg = AggregationEngine()
        rolling = agg.calculate_rolling_averages(metric=metric, window_days=window_days)

        return {
            "metric": metric,
            "window_days": window_days,
            "data": rolling.to_dict(orient="records"),
            "total_periods": len(rolling)
        }
    except Exception as e:
        logger.error(f"Error calculating rolling averages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/aggregations/percentiles")
async def get_percentiles(
    metric: str = Query("cost_usd", description="Metric to analyze")
) -> Dict[str, Any]:
    """
    Get percentile distribution for a metric.

    Returns:
        Percentile values
    """
    try:
        agg = AggregationEngine()
        percentiles = agg.calculate_percentiles(
            metric=metric,
            percentiles=[0.25, 0.5, 0.75, 0.9, 0.95, 0.99]
        )

        return {
            "metric": metric,
            "percentiles": percentiles
        }
    except Exception as e:
        logger.error(f"Error calculating percentiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools/usage-stats")
async def get_tool_usage_stats() -> List[Dict[str, Any]]:
    """
    Get tool usage statistics.

    Returns:
        List of tool usage metrics
    """
    try:
        metrics = MetricsEngine()
        tool_stats = metrics.tool_success_rates()

        return tool_stats.to_dict(orient="records")
    except Exception as e:
        logger.error(f"Error fetching tool stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools/usage-patterns")
async def get_tool_usage_patterns() -> Dict[str, Any]:
    """
    Get tool usage patterns by user segment.

    Returns:
        Tool usage patterns
    """
    try:
        agg = AggregationEngine()
        patterns = agg.aggregate_tool_usage_patterns()

        return {
            "data": patterns.to_dict(orient="records"),
            "total_patterns": len(patterns)
        }
    except Exception as e:
        logger.error(f"Error fetching tool patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/comparison")
async def get_model_comparison() -> Dict[str, Any]:
    """
    Get comparative analysis of different models.

    Returns:
        Model comparison metrics
    """
    try:
        metrics = MetricsEngine()
        model_dist = metrics.model_usage_distribution()

        return {
            "data": model_dist.to_dict(orient="records"),
            "total_models": len(model_dist)
        }
    except Exception as e:
        logger.error(f"Error fetching model comparison: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ml/forecast")
async def get_usage_forecast(
    days: int = Query(7, ge=1, le=90, description="Number of days to forecast")
) -> Dict[str, Any]:
    """
    Get ML-based usage forecast.

    Returns:
        Forecasted values with confidence intervals
    """
    try:
        model = ForecastModel()
        model.fit()
        forecast = model.forecast(days=days)

        return {
            "days": days,
            "forecast": forecast.to_dict(orient="records"),
            "total_predictions": len(forecast)
        }
    except Exception as e:
        logger.error(f"Error generating forecast: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ml/anomalies")
async def get_anomalies() -> Dict[str, Any]:
    """
    Get detected anomalies in usage patterns.

    Returns:
        List of anomalous events
    """
    try:
        detector = AnomalyDetector()
        detector.fit()
        anomalies = detector.predict()

        # Filter only anomalies
        anomalies_only = anomalies[anomalies['is_anomaly']]

        return {
            "total_records": len(anomalies),
            "anomalies_detected": len(anomalies_only),
            "anomaly_rate": float(len(anomalies_only) / len(anomalies)) if len(anomalies) > 0 else 0,
            "data": anomalies_only.to_dict(orient="records")
        }
    except Exception as e:
        logger.error(f"Error detecting anomalies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ml/user-clusters")
async def get_user_clusters() -> Dict[str, Any]:
    """
    Get user segmentation clusters.

    Returns:
        User clusters with labels
    """
    try:
        clusterer = UserClusterer()
        clusters = clusterer.fit_predict()

        # Get cluster distribution
        cluster_dist = clusters['cluster_label'].value_counts().to_dict()

        return {
            "total_users": len(clusters),
            "cluster_distribution": cluster_dist,
            "data": clusters.to_dict(orient="records")
        }
    except Exception as e:
        logger.error(f"Error clustering users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary/overview")
async def get_overview_summary() -> Dict[str, Any]:
    """
    Get comprehensive overview summary.

    Returns:
        Overall metrics summary
    """
    try:
        metrics = MetricsEngine()

        # Get overall totals
        totals = metrics.calculate_total_cost()

        # Get daily active users
        dau = metrics.calculate_daily_active_users(days=30)

        total_row = totals.iloc[0] if not totals.empty else {}

        return {
            "overall": {
                "total_cost": float(total_row.get('total_cost', 0)),
                "total_requests": int(total_row.get('request_count', 0)),
                "avg_cost_per_request": float(total_row.get('avg_cost_per_request', 0)),
                "total_tokens": int(total_row.get('total_tokens', 0)),
                "unique_users": int(total_row.get('unique_users', 0)),
                "unique_sessions": int(total_row.get('unique_sessions', 0))
            },
            "daily_active_users": dau.to_dict(orient="records") if not dau.empty else []
        }
    except Exception as e:
        logger.error(f"Error generating overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))
