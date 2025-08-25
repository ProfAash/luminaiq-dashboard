# pages/3_Dashboard.py
import pandas as pd
import streamlit as st
from db import list_uploads_for_user

# --- Plotly optional ---
try:
    import plotly.express as px
    HAS_PLOTLY = True
except Exception:
    HAS_PLOTLY = False

# --- Kaleido (for PNG export) optional ---
try:
    import plotly.io as pio  # requires kaleido for static image export
    HAS_KALEIDO = True
except Exception:
    HAS_KALEIDO = False

from io import BytesIO

st.set_page_config(page_title="Dashboards • LuminaIQ", page_icon="📊", layout="wide")

# ---------- Auth ----------
user = st.session_state.get("user")
if not user:
    st.warning("Please sign in from the Home page.")
    st.stop()

st.title("📊 Dashboards")

# ---------- Dataset picker ----------
uploads = list_uploads_for_user(user_id=user["id"])
if not uploads:
    st.info("Upload a dataset first.")
    st.stop()

options = {f"{u['uploaded_at']} — {u['filename']}": u for u in uploads}
choice = st.selectbox("Choose a dataset", list(options.keys()))
ds = options[choice]

# ---------- Load data (URL or local path) ----------
path = ds.get("path", "")
try:
    df = pd.read_csv(path)
except Exception as e:
    st.error(f"Could not read dataset: {e}")
    st.stop()

# Try to coerce any date-like columns
for c in df.columns:
    if any(k in c.lower() for k in ("date", "day", "time")):
        try:
            df[c] = pd.to_datetime(df[c], errors="ignore")
        except Exception:
            pass

num_cols = df.select_dtypes("number").columns.tolist()
cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
dt_cols  = df.select_dtypes(include=["datetime", "datetimetz"]).columns.tolist()

# ---------- Filters ----------
with st.expander("Filters", True):
    colf1, colf2, colf3, colf4 = st.columns(4)
    sel_cat = colf1.selectbox("Category (optional)", ["—"] + cat_cols)
    sel_val = colf2.selectbox("Value (numeric)", num_cols if num_cols else [])
    sel_dt  = colf3.selectbox("Date (optional)", ["—"] + dt_cols)

    if sel_dt != "—" and len(df):
        dmin, dmax = pd.to_datetime(df[sel_dt]).min(), pd.to_datetime(df[sel_dt]).max()
        drange = colf4.date_input("Date range", (dmin.date(), dmax.date()))
    else:
        drange = None

# Apply filters
df_view = df.copy()
if sel_dt != "—" and drange:
    d0, d1 = pd.to_datetime(drange[0]), pd.to_datetime(drange[1])
    sdt = pd.to_datetime(df_view[sel_dt], errors="coerce")
    df_view = df_view[(sdt.dt.date >= d0.date()) & (sdt.dt.date <= d1.date())]

if sel_cat != "—":
    keep_vals = st.multiselect("Keep categories", sorted(df_view[sel_cat].dropna().unique()))
    if keep_vals:
        df_view = df_view[df_view[sel_cat].isin(keep_vals)]

# ---------- KPIs ----------
rows, cols = df_view.shape
c1, c2, c3 = st.columns(3)
c1.metric("Rows", f"{rows:,}")
c2.metric("Columns", f"{cols:,}")
if sel_val:
    c3.metric(f"Total {sel_val}", f"{df_view[sel_val].sum():,.2f}")
else:
    c3.metric("Total", "—")

st.divider()

# ---------- Charts ----------
# Category breakdown
if sel_cat != "—" and sel_val:
    grp = (
        df_view.groupby(sel_cat, dropna=False)[sel_val]
               .sum()
               .reset_index()
               .sort_values(sel_val, ascending=False)
               .head(20)
    )
    if HAS_PLOTLY:
        fig_bar = px.bar(grp, x=sel_cat, y=sel_val, title=f"{sel_val} by {sel_cat} (Top 20)")
        st.plotly_chart(fig_bar, use_container_width=True)

        # PNG export (requires kaleido)
        if HAS_KALEIDO:
            buf = BytesIO()
            try:
                pio.write_image(fig_bar, buf, format="png", scale=2)
                st.download_button("Download bar chart PNG", buf.getvalue(),
                                   "category_chart.png", "image/png")
            except Exception as e:
                st.caption(f"PNG export unavailable: {e}")
        else:
            st.caption("Tip: add `kaleido==0.2.1` to requirements.txt to enable PNG export.")
    else:
        st.bar_chart(grp.set_index(sel_cat)[sel_val])

else:
    # Fallback: simple histogram of first numeric
    if num_cols:
        if HAS_PLOTLY:
            fig_hist = px.histogram(df_view, x=num_cols[0], title=f"Distribution of {num_cols[0]}")
            st.plotly_chart(fig_hist, use_container_width=True)

            if HAS_KALEIDO:
                buf = BytesIO()
                try:
                    pio.write_image(fig_hist, buf, format="png", scale=2)
                    st.download_button("Download histogram PNG", buf.getvalue(),
                                       "histogram.png", "image/png")
                except Exception as e:
                    st.caption(f"PNG export unavailable: {e}")
            else:
                st.caption("Tip: add `kaleido==0.2.1` to requirements.txt to enable PNG export.")
        else:
            st.bar_chart(df_view[num_cols[0]].value_counts().sort_index())

# Time series (if chosen)
if sel_dt != "—" and sel_val:
    ts = (
        df_view[[sel_dt, sel_val]]
        .dropna()
        .assign(**{sel_dt: pd.to_datetime(df_view[sel_dt], errors="coerce")})
        .dropna()
        .groupby(sel_dt, as_index=False)[sel_val].sum()
        .sort_values(sel_dt)
    )
    if len(ts):
        if HAS_PLOTLY:
            fig_line = px.line(ts, x=sel_dt, y=sel_val, title=f"{sel_val} over time")
            st.plotly_chart(fig_line, use_container_width=True)

            if HAS_KALEIDO:
                buf = BytesIO()
                try:
                    pio.write_image(fig_line, buf, format="png", scale=2)
                    st.download_button("Download time-series PNG", buf.getvalue(),
                                       "timeseries.png", "image/png")
                except Exception as e:
                    st.caption(f"PNG export unavailable: {e}")
            else:
                st.caption("Tip: add `kaleido==0.2.1` to requirements.txt to enable PNG export.")
        else:
            st.line_chart(ts.set_index(sel_dt)[sel_val])

st.divider()

# ---------- Downloads ----------
csv_bytes = df_view.to_csv(index=False).encode()
st.download_button("Download filtered CSV", csv_bytes, "filtered.csv", "text/csv")

