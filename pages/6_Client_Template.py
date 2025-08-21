try:
    import plotly.express as px
    HAS_PLOTLY = True
except Exception:
    HAS_PLOTLY = False

import pandas as pd
import streamlit as st
from db import list_uploads_for_user
import os, yaml

# Try Plotly, fall back to Streamlit charts if not available
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

with st.expander("Step 1 — Download examples"):
    st.download_button("Download demo CSV", data=open(os.path.join('templates', 'client_demo_retail.csv'), 'rb').read(), file_name="client_demo_retail.csv")
    st.download_button("Download mapping YAML", data=open(os.path.join('config', 'client_config.yaml'), 'rb').read(), file_name="client_config.yaml")

st.divider()

colA, colB = st.columns(2)
with colA:
    data_file = st.file_uploader("Upload client dataset (CSV)", type=["csv"], key="client_csv")
with colB:
    map_file = st.file_uploader("Upload mapping (YAML, optional)", type=["yaml", "yml"], key="client_yaml")

if data_file is None:
    st.info("Upload a CSV to continue.")
    st.stop()

df = pd.read_csv(data_file)

default_map_path = os.path.join("config", "client_config.yaml")
with open(default_map_path, "r") as f:
    mapping = yaml.safe_load(f)

if map_file is not None:
    mapping = {**mapping, **yaml.safe_load(map_file.read())}

st.subheader("Preview (first 10 rows)")
st.dataframe(df.head(10))

def get_col(name):
    col = mapping.get(name)
    return col if col in df.columns else None

date_col = get_col("date")
value_key = mapping.get("charts", {}).get("time_series", {}).get("metric") or "amount"
value_col = get_col(value_key) or get_col("amount")

category_key = mapping.get("charts", {}).get("breakdown", {}).get("by") or "category"
category_col = get_col(category_key) or get_col("category")
break_val_key = mapping.get("charts", {}).get("breakdown", {}).get("value") or "amount"
break_val_col = get_col(break_val_key) or get_col("amount")

st.divider()
st.subheader("KPIs")
try:
    kpi_items = mapping.get("kpis", [])
    cols = st.columns(min(4, max(1, len(kpi_items))))
    for i, k in enumerate(kpi_items):
        env = {"df": df, "pd": pd}
        val = eval(k.get("formula", "None"), {"__builtins__": {}}, env)
        if isinstance(val, float):
            cols[i].metric(k.get("label", k["id"]), f"{val:,.2f}")
        else:
            cols[i].metric(k.get("label", k["id"]), f"{val}")
except Exception as e:
    st.warning(f"KPI evaluation issue: {e}")

st.divider()
st.subheader("Time-series")
if date_col and value_col:
    try:
        df_ts = df[[date_col, value_col]].copy()
        df_ts[date_col] = pd.to_datetime(df_ts[date_col], errors="coerce")
        df_ts = df_ts.dropna(subset=[date_col])
        df_ts = df_ts.groupby(date_col, as_index=False)[value_col].sum()

        if HAS_PLOTLY:
            st.plotly_chart(px.line(df_ts.sort_values(date_col), x=date_col, y=value_col), use_container_width=True)
        else:
            st.line_chart(df_ts.set_index(date_col)[value_col])

    except Exception as e:
        st.warning(f"Time-series not available: {e}")
else:
    st.info("Provide a 'date' column and a numeric 'amount' (e.g., revenue) in the mapping.")

st.divider()
st.subheader("Category breakdown")
if category_col and break_val_col:
    try:
        grp = (
            df.groupby(category_col, as_index=False)[break_val_col]
            .sum()
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
