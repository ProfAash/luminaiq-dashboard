# pages/6_Client_Template.py
import os
import io
import yaml
import pandas as pd
import streamlit as st
from db import list_uploads_for_user  # not used yet but handy for future reuse

# Plotly optional
try:
    import plotly.express as px
    HAS_PLOTLY = True
except Exception:
    HAS_PLOTLY = False

st.set_page_config(page_title="Client Template • LuminaIQ", page_icon="🧩", layout="wide")

user = st.session_state.get("user")
if not user:
    st.warning("Please sign in from the Home page.")
    st.stop()

st.title("🧩 Client Template & Column Mapping")
st.caption("Upload the client's CSV and (optionally) a YAML mapping to wire up dashboards in minutes.")

# --- Example downloads (guard against missing files in Cloud) ---
with st.expander("Step 1 — Download examples"):
    try:
        demo_csv_path = os.path.join("templates", "client_demo_retail.csv")
        with open(demo_csv_path, "rb") as f:
            st.download_button("Download demo CSV", data=f.read(), file_name="client_demo_retail.csv")
    except Exception:
        st.info("Demo CSV not found in this build.")

    try:
        cfg_path = os.path.join("config", "client_config.yaml")
        with open(cfg_path, "rb") as f:
            st.download_button("Download mapping YAML", data=f.read(), file_name="client_config.yaml")
    except Exception:
        st.info("Mapping YAML not found in this build.")

st.divider()

# --- Uploads ---
colA, colB = st.columns(2)
with colA:
    data_file = st.file_uploader("Upload client dataset (CSV)", type=["csv"], key="client_csv")
with colB:
    map_file = st.file_uploader("Upload mapping (YAML, optional)", type=["yaml", "yml"], key="client_yaml")

if data_file is None:
    st.info("Upload a CSV to continue.")
    st.stop()

# Read CSV (BytesIO keeps it reusable)
data_bytes = data_file.read()
df = pd.read_csv(io.BytesIO(data_bytes))

# Load default mapping if present
mapping: dict | None = None
default_map_path = os.path.join("config", "client_config.yaml")
if os.path.exists(default_map_path):
    try:
        with open(default_map_path, "r") as f:
            mapping = yaml.safe_load(f) or {}
    except Exception as e:
        st.warning(f"Could not load default mapping: {e}")

# Merge uploaded mapping if provided
if map_file is not None:
    try:
        uploaded_map = yaml.safe_load(map_file.read()) or {}
        mapping = {**(mapping or {}), **uploaded_map}
    except Exception as e:
        st.warning(f"Could not parse uploaded YAML: {e}")

# Ensure mapping is a dict
mapping = mapping or {}

st.subheader("Preview (first 10 rows)")
st.dataframe(df.head(10), use_container_width=True)

def get_col(key_name: str) -> str | None:
    """Return mapped column if it exists in df, else None."""
    col = mapping.get(key_name)
    return col if isinstance(col, str) and col in df.columns else None

# Resolve columns from mapping with sensible fallbacks
date_col = get_col("date")

# time-series metric
value_key = mapping.get("charts", {}).get("time_series", {}).get("metric") or "amount"
value_col = get_col(value_key) or get_col("amount")

# breakdown metric
category_key = mapping.get("charts", {}).get("breakdown", {}).get("by") or "category"
category_col = get_col(category_key) or get_col("category")
break_val_key = mapping.get("charts", {}).get("breakdown", {}).get("value") or "amount"
break_val_col = get_col(break_val_key) or get_col("amount")

st.divider()
st.subheader("KPIs")

try:
    kpi_items = mapping.get("kpis", [])
    cols = st.columns(min(4, max(1, len(kpi_items)))) if kpi_items else st.columns(1)
    for i, k in enumerate(kpi_items):
        env = {"df": df, "pd": pd}
        formula = k.get("formula", "None")
        val = eval(formula, {"__builtins__": {}}, env)  # guarded: no builtins
        label = k.get("label", k.get("id", "KPI"))
        cols[i if i < len(cols) else -1].metric(label, f"{val:,.2f}" if isinstance(val, (int, float)) else f"{val}")
except Exception as e:
    st.warning(f"KPI evaluation issue: {e}")

# --- Time-series ---
st.divider()
st.subheader("Time-series")
if date_col and value_col:
    try:
        df_ts = df[[date_col, value_col]].copy()
        df_ts[date_col] = pd.to_datetime(df_ts[date_col], errors="coerce")
        df_ts = df_ts.dropna(subset=[date_col])
        df_ts = df_ts.groupby(date_col, as_index=False)[value_col].sum().sort_values(date_col)

        if HAS_PLOTLY:
            st.plotly_chart(px.line(df_ts, x=date_col, y=value_col), use_container_width=True)
        else:
            st.line_chart(df_ts.set_index(date_col)[value_col])
    except Exception as e:
        st.warning(f"Time-series not available: {e}")
else:
    st.info("Provide a 'date' column and a numeric 'amount' (e.g., revenue) in the mapping.")

# --- Category breakdown ---
st.divider()
st.subheader("Category breakdown")
if category_col and break_val_col:
    try:
        grp = (
            df.groupby(category_col, dropna=False)[break_val_col]
              .sum()
              .reset_index()
              .sort_values(break_val_col, ascending=False)
              .head(20)
        )
        if HAS_PLOTLY:
            st.plotly_chart(px.bar(grp, x=category_col, y=break_val_col), use_container_width=True)
        else:
            st.bar_chart(grp.set_index(category_col)[break_val_col])
    except Exception as e:
        st.warning(f"Breakdown not available: {e}")
else:
    st.info("Specify a categorical column (e.g., category/region) and a numeric value to aggregate.")

