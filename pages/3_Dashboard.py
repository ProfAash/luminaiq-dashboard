# pages/3_Dashboard.py
import pandas as pd
import streamlit as st
from db import list_uploads_for_user

# Try Plotly; fall back to Streamlit charts if not available
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

# Pick a dataset
options = {f"{u['uploaded_at']} — {u['filename']}": u for u in uploads}
choice = st.selectbox("Choose a dataset", list(options.keys()))
ds = options[choice]

# Step 6 in action: read from Supabase URL (or local path if running locally)
path = ds.get("path", "")
try:
    if isinstance(path, str) and path.startswith(("http://", "https://")):
        df = pd.read_csv(path)
    else:
        # local path (useful for local dev; may not exist on Streamlit Cloud)
        df = pd.read_csv(path)
except Exception as e:
    st.error(
        "Could not read dataset.\n\n"
        f"Path: `{path}`\n\n"
        "If this is a local path from before we enabled cloud storage, "
        "re-upload the file so it’s stored in Supabase."
    )
    st.stop()

with st.expander("Preview data"):
    st.dataframe(df.head(), use_container_width=True)

num_cols = df.select_dtypes("number").columns.tolist()
cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

# KPIs
kpi_col = num_cols[0] if num_cols else None
total_value = df[kpi_col].sum() if kpi_col else None

c1, c2, c3 = st.columns(3)
c1.metric("Rows", f"{len(df):,}")
c2.metric("Columns", f"{df.shape[1]}")
c3.metric(f"Total {kpi_col if kpi_col else ''}".strip(),
          f"{total_value:,.2f}" if total_value is not None else "—")

st.divider()

# Category breakdown
if cat_cols and num_cols:
    group_col = st.selectbox("Breakdown by category", cat_cols, index=0)
    value_col = st.selectbox("Value column", num_cols, index=0)
    grp = (
        df.groupby(group_col, dropna=False)[value_col]
          .sum()
          .reset_index()
          .sort_values(value_col, ascending=False)
          .head(20)
    )
    if HAS_PLOTLY:
        st.plotly_chart(px.bar(grp, x=group_col, y=value_col), use_container_width=True)
    else:
        st.bar_chart(grp.set_index(group_col)[value_col])
else:
    st.info("Need at least one numeric and one categorical column for breakdowns.")

# Time series
# guess date-like columns by name or dtype
date_cols = [c for c in df.columns if "date" in c.lower()]
date_cols += [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
date_cols = list(dict.fromkeys(date_cols))  # dedupe, keep order

try:
    if date_cols:
        ts_col = st.selectbox("Time column (optional)", date_cols, index=0)
        df_ts = df[[ts_col] + (num_cols[:1] if num_cols else [])].copy()
        df_ts[ts_col] = pd.to_datetime(df_ts[ts_col], errors="coerce")
        df_ts = df_ts.dropna(subset=[ts_col]).sort_values(ts_col)
        if num_cols:
            val_ts = st.selectbox("Metric over time", num_cols, index=0)
            if HAS_PLOTLY:
                st.plotly_chart(px.line(df_ts, x=ts_col, y=val_ts), use_container_width=True)
            else:
                st.line_chart(df_ts.set_index(ts_col)[val_ts])
    else:
        st.caption("Tip: add a 'date' column to unlock time-series views.")
except Exception as e:
    st.warning(f"Time-series view not available: {e}")

