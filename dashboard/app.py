"""
Claude Analytics Platform — Streamlit dashboard entry point.
"""

import os
import streamlit as st
import requests
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings

API_URL = os.environ.get("API_URL", getattr(settings, "api_url", "http://api:8000"))

st.set_page_config(
    page_title="Claude Analytics Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Claude Analytics Platform")
st.markdown("Analytics platform for Claude Code telemetry data.")
st.markdown("Use the sidebar to navigate between pages.")

st.markdown("---")

# Quick health check
try:
    r = requests.get(f"{API_URL}/health/", timeout=5)
    if r.status_code == 200:
        st.success(f"API connected — {API_URL}")
    else:
        st.warning(f"API returned {r.status_code}")
except Exception as e:
    st.error(f"Cannot reach API at {API_URL}: {e}")

st.markdown("---")

st.markdown("""
- **1 Overview** — key metrics, daily active users, model distribution
- **2 Usage Analysis** — token trends, peak-hours heatmap, practice cohorts
- **3 Cost Analysis** — cost by practice/level, top users, cache efficiency, forecast
- **4 User Insights** — cohort comparison, user directory, KMeans clusters
- **5 Tool Analytics** — execution counts, success rates, latency, anomalies
""")
