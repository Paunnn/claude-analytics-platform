import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

API_URL = os.environ.get("API_URL", "http://api:8000")


def fetch(endpoint, params=None):
    try:
        r = requests.get(f"{API_URL}{endpoint}", params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error ({endpoint}): {e}")
        return None


def main():
    st.title("Cost Analysis")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Cost by Practice")
        cost = fetch("/analytics/metrics/cost", {"group_by": "practice"})
        if cost and cost.get("data"):
            df = pd.DataFrame(cost["data"])
            fig = px.bar(df, x="practice", y="total_cost", color="practice",
                         labels={"total_cost": "Total Cost ($)", "practice": "Practice"})
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Cost by Level")
        cost_level = fetch("/analytics/metrics/cost", {"group_by": "level"})
        if cost_level and cost_level.get("data"):
            df = pd.DataFrame(cost_level["data"])
            fig = px.pie(df, values="total_cost", names="level",
                         title="Cost Distribution by Level")
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Top 10 Users by Cost")
    top_users = fetch("/analytics/metrics/top-users", {"n": 10})
    if top_users and top_users.get("data"):
        df = pd.DataFrame(top_users["data"])
        fig = px.bar(df, x="full_name", y="total_cost", color="practice",
                     labels={"total_cost": "Total Cost ($)", "full_name": "User"})
        fig.update_xaxes(tickangle=30)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(
            df[["full_name", "practice", "level", "total_cost",
                "request_count", "avg_cost_per_request"]].rename(columns={
                    "full_name": "Name", "practice": "Practice", "level": "Level",
                    "total_cost": "Total Cost ($)", "request_count": "Requests",
                    "avg_cost_per_request": "Avg $/Req"
                }),
            hide_index=True, use_container_width=True
        )

    st.markdown("---")
    st.subheader("Cache Efficiency")
    cache = fetch("/analytics/metrics/cache-efficiency")
    if cache:
        avg_rate = cache.get("avg_cache_hit_rate", 0)
        st.metric("Average Cache Hit Rate", f"{avg_rate:.1%}")
        if cache.get("data"):
            df = pd.DataFrame(cache["data"])
            fig = px.bar(df.head(15), x="email", y="cache_hit_rate",
                         color="practice",
                         title="Cache Hit Rate — Top 15 Users",
                         labels={"cache_hit_rate": "Cache Hit Rate", "email": "User"})
            fig.update_xaxes(tickangle=30)
            fig.update_yaxes(tickformat=".0%")
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("7-Day Cost Forecast")
    forecast = fetch("/analytics/ml/forecast", {"days": 7})
    if forecast and forecast.get("forecast"):
        df = pd.DataFrame(forecast["forecast"])
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["date"], y=df["predicted_tokens"],
                                 mode="lines+markers", name="Forecast",
                                 line=dict(color="royalblue", width=2)))
        fig.add_trace(go.Scatter(x=df["date"], y=df["upper_bound"],
                                 mode="lines", name="Upper bound",
                                 line=dict(color="lightblue", dash="dash"), showlegend=False))
        fig.add_trace(go.Scatter(x=df["date"], y=df["lower_bound"],
                                 mode="lines", name="Lower bound",
                                 line=dict(color="lightblue", dash="dash"),
                                 fill="tonexty", fillcolor="rgba(173,216,230,0.2)",
                                 showlegend=False))
        fig.update_layout(title="Predicted Token Usage (next 7 days)",
                          xaxis_title="Date", yaxis_title="Tokens")
        st.plotly_chart(fig, use_container_width=True)


main()
