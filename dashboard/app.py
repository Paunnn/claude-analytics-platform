"""
Main Streamlit dashboard application.

Entry point for the Claude Analytics Platform dashboard.
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings

# API URL
API_URL = settings.api_url if hasattr(settings, 'api_url') else "http://api:8000"


def configure_page():
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title="Claude Analytics Platform",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if 'date_range' not in st.session_state:
        st.session_state.date_range = 30


def render_sidebar():
    """Render the dashboard sidebar with filters and navigation."""
    st.sidebar.title("🎯 Claude Analytics")
    st.sidebar.markdown("---")

    # Navigation
    page = st.sidebar.radio(
        "Navigation",
        ["📊 Overview", "💰 Cost Analysis", "👥 Users", "🤖 ML Insights"]
    )

    st.sidebar.markdown("---")

    # Filters
    st.sidebar.subheader("Filters")
    date_range = st.sidebar.slider(
        "Last N Days",
        min_value=7,
        max_value=90,
        value=30,
        step=1
    )
    st.session_state.date_range = date_range

    st.sidebar.markdown("---")
    st.sidebar.caption(f"Environment: {settings.environment}")

    return page


def fetch_api(endpoint: str):
    """Fetch data from API endpoint."""
    try:
        response = requests.get(f"{API_URL}{endpoint}", timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None


def render_overview():
    """Render overview page."""
    st.title("📊 Overview Dashboard")

    # Fetch overview data
    overview = fetch_api("/analytics/summary/overview")

    if overview:
        overall = overview.get('overall', {})

        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total Cost",
                f"${overall.get('total_cost', 0):,.2f}",
                delta=None
            )

        with col2:
            st.metric(
                "Total Requests",
                f"{overall.get('total_requests', 0):,}",
                delta=None
            )

        with col3:
            st.metric(
                "Unique Users",
                f"{overall.get('unique_users', 0)}",
                delta=None
            )

        with col4:
            st.metric(
                "Avg Cost/Request",
                f"${overall.get('avg_cost_per_request', 0):.4f}",
                delta=None
            )

        st.markdown("---")

        # Charts
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Daily Active Users")
            dau_data = overview.get('daily_active_users', [])
            if dau_data:
                df = pd.DataFrame(dau_data)
                fig = px.line(
                    df,
                    x='date',
                    y='daily_active_users',
                    title='Daily Active Users Over Time'
                )
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Model Distribution")
            models = fetch_api("/analytics/models/comparison")
            if models and models.get('data'):
                df = pd.DataFrame(models['data'])
                fig = px.pie(
                    df,
                    values='request_count',
                    names='model_name',
                    title='Request Distribution by Model'
                )
                st.plotly_chart(fig, use_container_width=True)


def render_cost_analysis():
    """Render cost analysis page."""
    st.title("💰 Cost Analysis")

    # Cost by practice
    st.subheader("Cost by Practice & Level")
    cost_data = fetch_api("/analytics/metrics/cost?group_by=practice")

    if cost_data and cost_data.get('data'):
        df = pd.DataFrame(cost_data['data'])
        fig = px.bar(
            df,
            x='practice',
            y='total_cost',
            title='Total Cost by Practice',
            labels={'total_cost': 'Total Cost ($)', 'practice': 'Practice'}
        )
        st.plotly_chart(fig, use_container_width=True)

    # Top users by cost
    st.subheader("Top 10 Users by Cost")
    top_users = fetch_api("/analytics/metrics/top-users?n=10")

    if top_users and top_users.get('data'):
        df = pd.DataFrame(top_users['data'])
        st.dataframe(
            df[['full_name', 'practice', 'total_cost', 'request_count', 'avg_cost_per_request']],
            hide_index=True,
            use_container_width=True
        )

    # Cache efficiency
    st.subheader("Cache Efficiency")
    cache_data = fetch_api("/analytics/metrics/cache-efficiency")

    if cache_data:
        avg_hit_rate = cache_data.get('avg_cache_hit_rate', 0)
        st.metric("Average Cache Hit Rate", f"{avg_hit_rate:.1%}")

        if cache_data.get('data'):
            df = pd.DataFrame(cache_data['data'])
            fig = px.bar(
                df.head(15),
                x='email',
                y='cache_hit_rate',
                title='Cache Hit Rate by User (Top 15)',
                labels={'cache_hit_rate': 'Cache Hit Rate', 'email': 'User'}
            )
            st.plotly_chart(fig, use_container_width=True)


def render_users():
    """Render users page."""
    st.title("👥 User Analytics")

    # User cohorts
    st.subheader("User Cohorts by Practice")
    cohorts = fetch_api("/analytics/aggregations/user-cohorts?cohort_field=practice")

    if cohorts and cohorts.get('data'):
        df = pd.DataFrame(cohorts['data'])
        st.dataframe(
            df[['cohort', 'user_count', 'total_cost', 'total_requests', 'requests_per_user']],
            hide_index=True,
            use_container_width=True
        )

    # Practices and levels
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Practices")
        practices = fetch_api("/users/practices")
        if practices:
            st.write(practices)

    with col2:
        st.subheader("Levels")
        levels = fetch_api("/users/levels")
        if levels:
            st.write(levels)


def render_ml_insights():
    """Render ML insights page."""
    st.title("🤖 Machine Learning Insights")

    # Forecast
    st.subheader("7-Day Usage Forecast")
    forecast = fetch_api("/analytics/ml/forecast?days=7")

    if forecast and forecast.get('forecast'):
        df = pd.DataFrame(forecast['forecast'])
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['predicted_tokens'],
            mode='lines+markers',
            name='Predicted',
            line=dict(color='blue', width=2)
        ))

        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['upper_bound'],
            mode='lines',
            name='Upper Bound',
            line=dict(color='lightblue', width=1, dash='dash'),
            fill=None
        ))

        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['lower_bound'],
            mode='lines',
            name='Lower Bound',
            line=dict(color='lightblue', width=1, dash='dash'),
            fill='tonexty'
        ))

        fig.update_layout(title='Token Usage Forecast', xaxis_title='Date', yaxis_title='Tokens')
        st.plotly_chart(fig, use_container_width=True)

    # Anomalies
    st.subheader("Detected Anomalies")
    anomalies = fetch_api("/analytics/ml/anomalies")

    if anomalies:
        st.metric("Anomalies Detected", anomalies.get('anomalies_detected', 0))
        st.metric("Anomaly Rate", f"{anomalies.get('anomaly_rate', 0):.1%}")

        if anomalies.get('data'):
            df = pd.DataFrame(anomalies['data'])
            st.dataframe(
                df[['date', 'user_email', 'practice', 'total_tokens', 'anomaly_score']].head(10),
                hide_index=True,
                use_container_width=True
            )

    # User clusters
    st.subheader("User Segmentation")
    clusters = fetch_api("/analytics/ml/user-clusters")

    if clusters and clusters.get('cluster_distribution'):
        cluster_dist = clusters['cluster_distribution']
        fig = px.pie(
            values=list(cluster_dist.values()),
            names=list(cluster_dist.keys()),
            title='User Cluster Distribution'
        )
        st.plotly_chart(fig, use_container_width=True)


def main():
    """Main dashboard application."""
    configure_page()
    initialize_session_state()

    page = render_sidebar()

    # Render selected page
    if page == "📊 Overview":
        render_overview()
    elif page == "💰 Cost Analysis":
        render_cost_analysis()
    elif page == "👥 Users":
        render_users()
    elif page == "🤖 ML Insights":
        render_ml_insights()


if __name__ == "__main__":
    main()
