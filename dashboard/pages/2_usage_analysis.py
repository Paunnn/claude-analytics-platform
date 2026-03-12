import os
import streamlit as st
import pandas as pd
import plotly.express as px
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
    st.title("Usage Analysis")

    st.subheader("Token Usage by Practice")
    token_data = fetch("/analytics/metrics/token-usage")
    if token_data and token_data.get("data"):
        df = pd.DataFrame(token_data["data"])
        # Aggregate to practice level for the trend chart
        if "practice" in df.columns and "date" in df.columns:
            fig = px.line(df, x="date", y="total_input_tokens", color="practice",
                          title="Daily Input Tokens by Practice",
                          labels={"total_input_tokens": "Input Tokens", "date": "Date"})
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Peak Usage Heatmap")
    peak = fetch("/analytics/metrics/peak-hours")
    if peak and peak.get("data"):
        df = pd.DataFrame(peak["data"])
        day_names = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}
        df["day_name"] = df["day_of_week"].map(day_names)
        pivot = df.pivot_table(index="day_name", columns="hour_of_day",
                               values="request_count", aggfunc="sum")
        day_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        pivot = pivot.reindex([d for d in day_order if d in pivot.index])
        fig = px.imshow(pivot, title="Requests by Hour and Day",
                        labels={"x": "Hour of Day", "y": "Day", "color": "Requests"},
                        color_continuous_scale="Blues")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Usage by Practice Cohort")
    cohorts = fetch("/analytics/aggregations/user-cohorts", {"cohort_field": "practice"})
    if cohorts and cohorts.get("data"):
        df = pd.DataFrame(cohorts["data"])
        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(df, x="cohort", y="total_requests", color="cohort",
                         title="Total Requests by Practice",
                         labels={"total_requests": "Requests", "cohort": "Practice"})
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.bar(df, x="cohort", y="requests_per_user", color="cohort",
                         title="Requests per User by Practice",
                         labels={"requests_per_user": "Requests / User", "cohort": "Practice"})
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            df[["cohort", "user_count", "total_requests", "requests_per_user",
                "avg_tokens_per_request", "cache_hit_rate"]].rename(columns={
                    "cohort": "Practice", "user_count": "Users",
                    "total_requests": "Requests", "requests_per_user": "Req/User",
                    "avg_tokens_per_request": "Tokens/Req", "cache_hit_rate": "Cache Hit Rate"
                }),
            hide_index=True, use_container_width=True
        )


main()
