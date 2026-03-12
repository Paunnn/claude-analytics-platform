"""
Reusable chart components for dashboard.

Provides pre-configured Plotly charts for common visualizations.
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Optional, List


def create_metric_card(
    title: str,
    value: float,
    unit: str = "",
    delta: Optional[float] = None,
    delta_unit: str = "%"
):
    """
    Create a metric card component.

    Args:
        title: Card title
        value: Main metric value
        unit: Value unit (e.g., "$", "tokens")
        delta: Change value (for trend indicator)
        delta_unit: Delta unit

    Example:
        >>> create_metric_card("Total Cost", 1234.56, "$", 15.2, "%")
    """
    pass


def create_line_chart(
    data: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color: Optional[str] = None,
    height: int = 400
) -> go.Figure:
    """
    Create a line chart.

    Args:
        data: DataFrame with data
        x: Column for x-axis
        y: Column for y-axis
        title: Chart title
        color: Optional column for color grouping
        height: Chart height in pixels

    Returns:
        Plotly Figure object
    """
    pass


def create_bar_chart(
    data: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    orientation: str = "v",
    color: Optional[str] = None
) -> go.Figure:
    """
    Create a bar chart.

    Args:
        data: DataFrame with data
        x: Column for x-axis
        y: Column for y-axis
        title: Chart title
        orientation: 'v' for vertical, 'h' for horizontal
        color: Optional column for color grouping

    Returns:
        Plotly Figure object
    """
    pass


def create_pie_chart(
    data: pd.DataFrame,
    names: str,
    values: str,
    title: str,
    hole: float = 0.3
) -> go.Figure:
    """
    Create a pie/donut chart.

    Args:
        data: DataFrame with data
        names: Column for slice labels
        values: Column for slice values
        title: Chart title
        hole: Hole size (0 for pie, 0.3-0.5 for donut)

    Returns:
        Plotly Figure object
    """
    pass


def create_heatmap(
    data: pd.DataFrame,
    x: str,
    y: str,
    z: str,
    title: str,
    colorscale: str = "Viridis"
) -> go.Figure:
    """
    Create a heatmap.

    Args:
        data: DataFrame with data
        x: Column for x-axis
        y: Column for y-axis
        z: Column for cell values
        title: Chart title
        colorscale: Plotly colorscale name

    Returns:
        Plotly Figure object
    """
    pass


def create_scatter_plot(
    data: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    size: Optional[str] = None,
    color: Optional[str] = None,
    hover_data: Optional[List[str]] = None
) -> go.Figure:
    """
    Create a scatter plot.

    Args:
        data: DataFrame with data
        x: Column for x-axis
        y: Column for y-axis
        title: Chart title
        size: Optional column for bubble size
        color: Optional column for color grouping
        hover_data: Additional columns to show on hover

    Returns:
        Plotly Figure object
    """
    pass


def create_forecast_chart(
    historical: pd.DataFrame,
    forecast: pd.DataFrame,
    date_col: str,
    value_col: str,
    title: str
) -> go.Figure:
    """
    Create a forecast chart with historical and predicted values.

    Args:
        historical: Historical data DataFrame
        forecast: Forecast data DataFrame with yhat, yhat_lower, yhat_upper
        date_col: Date column name
        value_col: Value column name
        title: Chart title

    Returns:
        Plotly Figure object with historical + forecast
    """
    pass
