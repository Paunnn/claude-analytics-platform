"""
Analytics module for Claude Analytics Platform.

This module provides:
- Metric calculations and aggregations
- Statistical analysis
- Insight generation
- ML-based forecasting and anomaly detection
"""

from .metrics import MetricsEngine
from .aggregations import AggregationEngine
from .insights import InsightGenerator
from .ml_models import (
    ForecastModel,
    AnomalyDetector,
    UserClusterer,
)

__all__ = [
    "MetricsEngine",
    "AggregationEngine",
    "InsightGenerator",
    "ForecastModel",
    "AnomalyDetector",
    "UserClusterer",
]
