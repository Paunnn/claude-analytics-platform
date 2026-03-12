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
    col_title, col_btn = st.columns([6, 1])
    col_title.title("Overview")
    if col_btn.button("Refresh", use_container_width=True):
        st.cache_data.clear()

    data = fetch("/analytics/summary/overview")
    if data:
        overall = data.get("overall", {})
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Cost", f"${overall.get('total_cost', 0):,.2f}")
        c2.metric("Total Requests", f"{overall.get('total_requests', 0):,}")
        c3.metric("Active Users", overall.get("unique_users", 0))
        c4.metric("Avg Cost / Request", f"${overall.get('avg_cost_per_request', 0):.4f}")

        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            dau = data.get("daily_active_users", [])
            if dau:
                df = pd.DataFrame(dau)
                fig = px.line(df, x="date", y="daily_active_users",
                              title="Daily Active Users",
                              labels={"daily_active_users": "Users", "date": "Date"})
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            models = fetch("/analytics/models/comparison")
            if models and models.get("data"):
                df = pd.DataFrame(models["data"])
                fig = px.pie(df, values="request_count", names="model_name",
                             title="Requests by Model")
                st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Cost by Practice")
    cost = fetch("/analytics/metrics/cost", {"group_by": "practice"})
    if cost and cost.get("data"):
        df = pd.DataFrame(cost["data"])
        fig = px.bar(df, x="practice", y="total_cost", color="practice",
                     labels={"total_cost": "Total Cost ($)", "practice": "Practice"})
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)


main()
