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
    st.title("Tool Analytics")

    tools = fetch("/analytics/tools/usage-stats")
    if tools:
        df = pd.DataFrame(tools)

        # Summary metrics
        total_exec = int(df["total_executions"].sum())
        overall_sr = df["successful"].sum() / df["total_executions"].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Executions", f"{total_exec:,}")
        c2.metric("Overall Success Rate", f"{overall_sr:.1%}")
        c3.metric("Distinct Tools", len(df))

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            fig = px.bar(df.sort_values("total_executions", ascending=True),
                         x="total_executions", y="tool_name",
                         orientation="h", title="Executions by Tool",
                         labels={"total_executions": "Executions", "tool_name": "Tool"})
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.bar(df.sort_values("success_rate", ascending=True),
                         x="success_rate", y="tool_name",
                         orientation="h", title="Success Rate by Tool",
                         labels={"success_rate": "Success Rate", "tool_name": "Tool"},
                         color="success_rate", color_continuous_scale="RdYlGn",
                         range_color=[0.8, 1.0])
            fig.update_xaxes(tickformat=".0%")
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("Latency by Tool")
        fig = px.bar(df.sort_values("avg_duration_ms", ascending=False),
                     x="tool_name", y=["avg_duration_ms", "p95_duration_ms"],
                     barmode="group", title="Average and P95 Latency (ms)",
                     labels={"value": "Duration (ms)", "tool_name": "Tool",
                             "variable": "Metric"})
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("Full Table")
        display_df = df[["tool_name", "total_executions", "successful", "failed",
                          "success_rate", "avg_duration_ms", "p95_duration_ms"]].copy()
        display_df["success_rate"] = display_df["success_rate"].map("{:.1%}".format)
        display_df["avg_duration_ms"] = display_df["avg_duration_ms"].map("{:.0f}ms".format)
        display_df["p95_duration_ms"] = display_df["p95_duration_ms"].map("{:.0f}ms".format)
        st.dataframe(display_df.rename(columns={
            "tool_name": "Tool", "total_executions": "Executions",
            "successful": "Success", "failed": "Failed",
            "success_rate": "Success Rate", "avg_duration_ms": "Avg Latency",
            "p95_duration_ms": "P95 Latency"
        }), hide_index=True, use_container_width=True)

    st.markdown("---")
    st.subheader("Anomaly Detection")
    anomalies = fetch("/analytics/ml/anomalies")
    if anomalies:
        c1, c2 = st.columns(2)
        c1.metric("Anomalies Detected", anomalies.get("anomalies_detected", 0))
        c2.metric("Anomaly Rate", f"{anomalies.get('anomaly_rate', 0):.1%}")
        if anomalies.get("data"):
            df_a = pd.DataFrame(anomalies["data"])
            st.dataframe(
                df_a[["date", "user_email", "practice", "total_tokens", "anomaly_score"]].head(15),
                hide_index=True, use_container_width=True
            )


main()
