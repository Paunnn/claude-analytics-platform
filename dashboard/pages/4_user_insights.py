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
    st.title("User Insights")

    # Cohort comparison
    st.subheader("Practice Cohort Comparison")
    cohorts = fetch("/analytics/aggregations/user-cohorts", {"cohort_field": "practice"})
    if cohorts and cohorts.get("data"):
        df = pd.DataFrame(cohorts["data"])
        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(df, x="cohort", y="total_cost", color="cohort",
                         title="Total Cost by Practice",
                         labels={"total_cost": "Cost ($)", "cohort": "Practice"})
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.bar(df, x="cohort", y="cache_hit_rate", color="cohort",
                         title="Cache Hit Rate by Practice",
                         labels={"cache_hit_rate": "Cache Hit Rate", "cohort": "Practice"})
            fig.update_layout(showlegend=False)
            fig.update_yaxes(tickformat=".0%")
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Level cohort
    st.subheader("Level Cohort Comparison")
    cohorts_level = fetch("/analytics/aggregations/user-cohorts", {"cohort_field": "level"})
    if cohorts_level and cohorts_level.get("data"):
        df = pd.DataFrame(cohorts_level["data"])
        fig = px.scatter(df, x="requests_per_user", y="avg_cost_per_request",
                         size="user_count", color="cohort", text="cohort",
                         title="Cost Efficiency vs Usage Volume by Level",
                         labels={"requests_per_user": "Requests / User",
                                 "avg_cost_per_request": "Avg Cost / Request ($)",
                                 "cohort": "Level"})
        fig.update_traces(textposition="top center")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # User directory with filter
    st.subheader("User Directory")
    practices = fetch("/users/practices")
    filter_practice = None
    if practices:
        options = ["All"] + practices
        selected = st.selectbox("Filter by practice", options)
        if selected != "All":
            filter_practice = selected

    params = {}
    if filter_practice:
        params["practice"] = filter_practice
    users = fetch("/users/", params)
    if users and users.get("data"):
        df = pd.DataFrame(users["data"])
        cols = [c for c in ["full_name", "email", "practice", "level", "location"]
                if c in df.columns]
        st.dataframe(df[cols], hide_index=True, use_container_width=True)
        st.caption(f"{len(df)} users")

    st.markdown("---")

    # ML user clusters
    st.subheader("User Segmentation (KMeans)")
    clusters = fetch("/analytics/ml/user-clusters")
    if clusters:
        dist = clusters.get("cluster_distribution", {})
        if dist:
            col1, col2 = st.columns(2)
            with col1:
                fig = px.pie(values=list(dist.values()), names=list(dist.keys()),
                             title="User Cluster Distribution")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                if clusters.get("cluster_details"):
                    df = pd.DataFrame(clusters["cluster_details"])
                    st.dataframe(df, hide_index=True, use_container_width=True)


main()
