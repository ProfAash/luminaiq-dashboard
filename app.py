# --- ensure plotly is available (temporary fallback for Streamlit Cloud) ---

# ---------------------------------------------------------------------------
import streamlit as st

# TEMP DIAG
try:
    import importlib.metadata as md
    import supabase  # noqa
    st.sidebar.success(f"Supabase present: {md.version('supabase')}")
except Exception as e:
    st.sidebar.error(f"Supabase import failed in app.py: {e}")

from db import init_db
from auth import verify_credentials, ensure_default_admin

import importlib.metadata as md

# Debug: verify critical deps once at startup
try:
    import plotly, plotly.express as px  # noqa
    import pandas as _pd  # noqa
except Exception as _e:
    import streamlit as _st
    _st.error(f"Dependency import failed: {_e}")

# --- startup dependency check (temporary) ---
try:
    import importlib.metadata as md
    import plotly
    _plotly_ver = md.version("plotly")
    import streamlit as st  # if not already imported above
    _st.info(f"Plotly available: {_plotly_ver}")
except Exception as _e:
    import streamlit as _st
    _st.error(f"Dependency import failed: {type(_e).__name__}: {_e}")
# --------------------------------------------

st.set_page_config(page_title="LuminaIQ Dashboard", page_icon="📊", layout="wide")

init_db()
created_admin = ensure_default_admin()

if "user" not in st.session_state:
    st.session_state.user = None

def login_form():
    st.title("LuminaIQ Client Dashboard")
    st.caption("Secure analytics workspace for clients")
    with st.form("login"):
        email = st.text_input("Email", placeholder="you@company.com")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Sign in"):
            user = verify_credentials(email, password)
            if user:
                st.session_state.user = dict(user)
                st.success(f"Welcome {user['name']}!")
                st.rerun()
            else:
                st.error("Invalid email or password.")

def topbar():
    with st.sidebar:
        st.markdown("### LuminaIQ")
        if st.session_state.user:
            st.write(f"**Signed in as**: {st.session_state.user['name']}")
            st.write(f"**Company**: {st.session_state.user['company']}")
            if st.button("Sign out"):
                st.session_state.user = None
                st.rerun()
        st.divider()
        st.page_link("app.py", label="🏠 Home", icon="🏠")
        st.page_link("pages/1_Overview.py", label="📈 Overview")
        st.page_link("pages/2_Upload_Data.py", label="⬆️ Upload Data")
        st.page_link("pages/3_Dashboard.py", label="📊 Dashboards")
        st.page_link("pages/4_Predictive_Forecasting.py", label="🔮 Predictive Forecasting")
        st.page_link("pages/6_Client_Template.py", label="🧩 Client Template")

if st.session_state.user is None:
    login_form()
else:
    topbar()
    st.title("🏠 Home")
    if created_admin:
        st.info("Default admin created: admin@luminaiq.co / Admin#123 — please change it under Admin tools.")
    st.markdown("""
    **What you can do**
    - Upload a CSV and explore it with interactive charts.
    - Build quick KPIs and breakdowns by categories.
    - Run a baseline forecast on a time-series column.
    - Map any client CSV using the Client Template page.
    """)
