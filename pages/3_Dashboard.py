# pages/3_Dashboard.py
import pandas as pd
import streamlit as st
from io import BytesIO
from db import list_uploads_for_user

# --- Plotly optional ---
try:
    import plotly.express as px
    HAS_PLOTLY = True
except Exception:
    HAS_PLOTLY = False

# --- Kaleido (for PNG export) optional ---
try:
    import kaleido  # noqa: F401
    import plotly.io as pio
    HAS_KALEIDO = True
except Exception:
    HAS_KALEIDO = False
    pio = None  # type: ignore

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
choice = st.selectbox("Choose a dataset", list(options.keys()), key="dash_dataset")
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
    sel_cat = colf1.selectbox("Category (optional)", ["—"] + cat_cols, key="dash_cat")
    sel_val = colf2.selectbox("Value (numeric)", num_cols if num_cols else [], key="dash_val")
    sel_dt  = colf3.selectbox("Date (optional)", ["—"] + dt_cols, key="dash_dt")

    if sel_dt != "—" and len(df):
        dmin, dmax = pd.to_datetime(df[sel_dt]).min(), pd.to_datetime(df[sel_dt]).max()
        drange = colf4.date_input("Date range", (dmin.date(), dmax.date()), key="dash_drange")
    else:
        drange = None

    # --- Searchable category values (server-side filtered) ---
    cat_query = ""
    keep_vals = []
    if sel_cat != "—":
        cat_query = st.text_input(
            f"Search {sel_cat} values",
            value=st.session_state.get("dash_cat_query", ""),
            key="dash_cat_query",
            placeholder="Type to filter category values…",
        )
        all_vals = sorted(v for v in df[sel_cat].dropna().astype(str).unique())
        if cat_query:
            q = cat_query.lower()
            all_vals = [v for v in all_vals if q in v.lower()]

        # Preserve previously selected values if still present
        default_sel = [v for v in st.session_state.get("dash_keep_vals", []) if v in all_vals]

        keep_vals = st.multiselect(
            f"Keep {sel_cat} values",
            options=all_vals,
            default=default_sel,
            key="dash_keep_vals",
        )

    # --- Optional numeric range filter for the selected value column ---
    num_range = None
    if sel_val:
        col_min = float(pd.to_numeric(df[sel_val], errors="coerce").min())
        col_max = float(pd.to_numeric(df[sel_val], errors="coerce").max())
        num_range = st.slider(
            f"{sel_val} range",
            min_value=float(col_min),
            max_value=float(col_max),
            value=st.session_state.get("dash_val_range", (float(col_min), float(col_max))),
            key="dash_val_range",
        )

# Apply filters
df_view = df.copy()

# Date range
if sel_dt != "—" and drange:
    d0, d1 = pd.to_datetime(drange[0]), pd.to_datetime(drange[1])
    sdt = pd.to_datetime(df_view[sel_dt], errors="coerce")
    df_view = df_view[(sdt.dt.date >= d0.date()) & (sdt.dt.date <= d1.date())]

# Category multiselect
if sel_cat != "—" and keep_vals:
    df_view = df_view[df_view[sel_cat].astype(str).isin(keep_vals)]

# Numeric range
if sel_val and num_range:
    v0, v1 = num_range
    sv = pd.to_numeric(df_view[sel_val], errors="coerce")
    df_view = df_view[(sv >= v0) & (sv <= v1)]

# ---------- KPIs ----------
from components import kpi
rows, cols = df_view.shape
c1, c2, c3 = st.columns(3)
with c1:
    kpi("Rows", f"{rows:,}")
with c2:
    kpi("Columns", f"{cols:,}")
with c3:
    if sel_val:
        kpi(f"Total {sel_val}", f"{pd.to_numeric(df_view[sel_val], errors='coerce').sum():,.2f}")
    else:
        kpi("Total", "—")

st.divider()

# ---------- Charts ----------
# Category breakdown
if sel_cat != "—" and sel_val:
    grp = (
        df_view.groupby(sel_cat, dropna=False)[sel_val]
               .apply(lambda s: pd.to_numeric(s, errors="coerce").sum())
               .reset_index()
               .sort_values(sel_val, ascending=False)
               .head(20)
    )
    if HAS_PLOTLY:
        fig_bar = px.bar(grp, x=sel_cat, y=sel_val, title=f"{sel_val} by {sel_cat} (Top 20)")
        st.plotly_chart(fig_bar, use_container_width=True)

        if HAS_KALEIDO and pio is not None:
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
        first_num = num_cols[0]
        if HAS_PLOTLY:
            fig_hist = px.histogram(df_view, x=first_num, title=f"Distribution of {first_num}")
            st.plotly_chart(fig_hist, use_container_width=True)

            if HAS_KALEIDO and pio is not None:
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
            st.bar_chart(df_view[first_num].value_counts().sort_index())

# Time series (if chosen)
if sel_dt != "—" and sel_val:
    ts = (
        df_view[[sel_dt, sel_val]]
        .dropna()
        .assign(**{sel_dt: pd.to_datetime(df_view[sel_dt], errors="coerce"),
                   sel_val: pd.to_numeric(df_view[sel_val], errors="coerce")})
        .dropna()
        .groupby(sel_dt, as_index=False)[sel_val].sum()
        .sort_values(sel_dt)
    )
    if len(ts):
        if HAS_PLOTLY:
            fig_line = px.line(ts, x=sel_dt, y=sel_val, title=f"{sel_val} over time")
            st.plotly_chart(fig_line, use_container_width=True)

            if HAS_KALEIDO and pio is not None:
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
