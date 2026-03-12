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
    UsageForecastModel,
    AnomalyDetectionModel,
    CostOptimizationModel,
)

__all__ = [
    "MetricsEngine",
    "AggregationEngine",
    "InsightGenerator",
    "UsageForecastModel",
    "AnomalyDetectionModel",
    "CostOptimizationModel",
]
