import pandas as pd
import streamlit as st
from db import list_uploads_for_user

# Try Plotly, fall back to Streamlit charts if not available
try:
    import plotly.express as px
    HAS_PLOTLY = True
except Exception:
    HAS_PLOTLY = False

st.set_page_config(page_title="Dashboards • LuminaIQ", page_icon="📊", layout="wide")
user = st.session_state.get("user")
if not user:
    st.warning("Please sign in from the Home page.")
    st.stop()

st.title("📊 Dashboards")
uploads = list_uploads_for_user(user_id=user["id"])

if not uploads:
    st.info("Upload a dataset first.")
    st.stop()

options = {f"{u['uploaded_at']} — {u['filename']}": u for u in uploads}
choice = st.selectbox("Choose a dataset", list(options.keys()))
ds = options[choice]

try:
    df = pd.read_csv(ds["path"])
except Exception as e:
    st.error(f"Could not read dataset: {e}")
    st.stop()

with st.expander("Preview data"):
    st.dataframe(df.head())

num_cols = df.select_dtypes("number").columns.tolist()
cat_cols = df.select_dtypes("object").columns.tolist()

kpi_col = None
if num_cols:
    kpi_col = st.selectbox("Numeric column to sum (KPI)", num_cols, index=0)
    total_value = df[kpi_col].sum()
else:
    total_value = None

c1, c2, c3 = st.columns(3)
c1.metric("Rows", f"{len(df):,}")
c2.metric("Columns", f"{df.shape[1]}")
c3.metric(f"Total {kpi_col if kpi_col else ''}".strip(), f"{total_value:,.2f}" if total_value is not None else "—")

st.divider()

if cat_cols and num_cols:
    group_col = st.selectbox("Breakdown by category", cat_cols, index=0)
    value_col = st.selectbox("Value column", num_cols, index=0)
    grp = df.groupby(group_col)[value_col].sum().reset_index().sort_values(value_col, ascending=False).head(20)
    st.plotly_chart(px.bar(grp, x=group_col, y=value_col), use_container_width=True)
else:
    st.info("Need at least one numeric and one categorical column for breakdowns.")

date_cols = [c for c in df.columns if "date" in c.lower()] + list(df.select_dtypes("datetime").columns)
date_cols = list(dict.fromkeys(date_cols))

try:
    if date_cols:
        ts_col = st.selectbox("Time column (optional)", date_cols, index=0)
        ts = pd.to_datetime(df[ts_col], errors="coerce")
        df_ts = df.copy()
        df_ts[ts_col] = ts
        df_ts = df_ts.dropna(subset=[ts_col])
        if num_cols:
            val_ts = st.selectbox("Metric over time", num_cols, index=0)
            st.plotly_chart(px.line(df_ts.sort_values(ts_col), x=ts_col, y=val_ts), use_container_width=True)
    else:
        st.caption("Tip: add a 'date' column to unlock time-series views.")
except Exception as e:
    st.warning(f"Time-series view not available: {e}")
