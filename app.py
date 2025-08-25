# app.py
import os
import importlib.util
import importlib.metadata as md
import pkg_resources
import streamlit as st

from db import init_db
from auth import verify_credentials, ensure_default_admin

# ---------------------------------------------------------------------
# MUST be the first Streamlit call
st.set_page_config(
    page_title="LuminaIQ Dashboard",
    page_icon="📊",
    layout="wide",
)
# ---------------------------------------------------------------------

st.markdown("""
<style>
/* hide the hamburger & footer */
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
/* comfy sidebar width */
section[data-testid="stSidebar"] {width: 290px !important;}
/* less top padding for the main content */
.block-container {padding-top: 0.75rem;}
</style>
""", unsafe_allow_html=True)


# Optional diagnostics (AFTER set_page_config)
try:
    if importlib.util.find_spec("supabase"):
        st.sidebar.success(f"Supabase present: {md.version('supabase')}")
    else:
        st.sidebar.warning("Supabase missing")
except Exception as e:
    st.sidebar.warning(f"Diag error: {e}")

# (Optional) list installed packages (can remove if too noisy)
try:
    packages = sorted([f"{p.project_name}=={p.version}" for p in pkg_resources.working_set])
    st.sidebar.write("Installed packages:", packages)
except Exception:
    pass

# (Optional) quick dependency checks
try:
    import plotly  # noqa: F401
    import plotly.express as px  # noqa: F401
    import pandas as _pd  # noqa: F401
    st.sidebar.info(f"Plotly available: {md.version('plotly')}")
except Exception as e:
    st.error(f"Dependency import failed: {type(e).__name__}: {e}")

# Initialize DB and default admin
init_db()
created_admin = ensure_default_admin()

# State bootstrap
if "user" not in st.session_state:
    st.session_state.user = None

# ---------------- UI helpers ----------------
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
        u = st.session_state.get("user")
    if u:
        st.markdown(
            f"""
            <div style="
                padding:14px;border-radius:14px;
                background:rgba(255,255,255,0.03);
                border:1px solid rgba(255,255,255,.08);
                margin-bottom:10px">
                <div style="font-weight:700">{u.get('name','')}</div>
                <div style="opacity:.8">{u.get('company','')}</div>
                <div style="opacity:.6;font-size:.85rem">{u.get('email','')}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

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

# ---------------- Router ----------------
if st.session_state.user is None:
    login_form()
else:
    topbar()
    st.title("🏠 Home")
    if created_admin:
        st.info("Default admin created: admin@luminaiq.co / Admin#123 — please change it under Admin tools.")
    st.markdown(
        """
        **What you can do**
        - Upload a CSV and explore it with interactive charts.
        - Build quick KPIs and breakdowns by categories.
        - Run a baseline forecast on a time-series column.
        - Map any client CSV using the Client Template page.
        """
    )
