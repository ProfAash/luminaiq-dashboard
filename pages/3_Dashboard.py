# pages/3_Dashboard.py
import json
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED

import pandas as pd
import streamlit as st

from db import list_uploads_for_user, save_view, list_views, delete_view

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

# Deep-link support via query params
qp = st.query_params
if "dataset" in qp and qp["dataset"] in options:
    default_dataset = qp["dataset"]
else:
    default_dataset = list(options.keys())[0]

choice = st.selectbox("Choose a dataset", list(options.keys()), key="dash_dataset", index=list(options.keys()).index(default_dataset))
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

    # Searchable category values
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

    # Numeric range filter for selected value
    num_range = None
    if sel_val:
        series_numeric = pd.to_numeric(df[sel_val], errors="coerce")
        col_min = float(series_numeric.min())
        col_max = float(series_numeric.max())
        num_range = st.slider(
            f"{sel_val} range",
            min_value=float(col_min),
            max_value=float(col_max),
            value=st.session_state.get("dash_val_range", (float(col_min), float(col_max))),
            key="dash_val_range",
        )

# ---------- Apply filters ----------
df_view = df.copy()

# Date
if sel_dt != "—" and drange:
    d0, d1 = pd.to_datetime(drange[0]), pd.to_datetime(drange[1])
    sdt = pd.to_datetime(df_view[sel_dt], errors="coerce")
    df_view = df_view[(sdt.dt.date >= d0.date()) & (sdt.dt.date <= d1.date())]

# Category
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
bar_fig = None
line_fig = None

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
        bar_fig = px.bar(grp, x=sel_cat, y=sel_val, title=f"{sel_val} by {sel_cat} (Top 20)")
        st.plotly_chart(bar_fig, use_container_width=True)
    else:
        st.bar_chart(grp.set_index(sel_cat)[sel_val])
else:
    # Fallback: simple histogram of first numeric
    if num_cols and HAS_PLOTLY:
        first_num = num_cols[0]
        bar_fig = px.histogram(df_view, x=first_num, title=f"Distribution of {first_num}")
        st.plotly_chart(bar_fig, use_container_width=True)
    elif num_cols:
        st.bar_chart(df_view[num_cols[0]].value_counts().sort_index())

# Time series
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
            line_fig = px.line(ts, x=sel_dt, y=sel_val, title=f"{sel_val} over time")
            st.plotly_chart(line_fig, use_container_width=True)
        else:
            st.line_chart(ts.set_index(sel_dt)[sel_val])

st.divider()

# ---------- 6) Saved Views ----------
st.subheader("Saved views")

# Compose payload (what defines this view)
view_payload = {
    "dataset": choice,
    "sel_cat": sel_cat,
    "sel_val": sel_val,
    "sel_dt": sel_dt,
    "drange": [str(d) for d in st.session_state.get("dash_drange", [])] if sel_dt != "—" and st.session_state.get("dash_drange") else None,
    "keep_vals": st.session_state.get("dash_keep_vals", []),
    "cat_query": st.session_state.get("dash_cat_query", ""),
    "num_range": st.session_state.get("dash_val_range", None),
}

# Buttons row
csa, csb, csc = st.columns([2,2,3])

with csa:
    new_name = st.text_input("View name", placeholder="e.g., Q1 · Region=Gauteng · Sales", key="dash_view_name")
    if st.button("Save view", type="primary", use_container_width=True):
        try:
            save_view(user_id=user["id"], page="dashboard", name=new_name.strip(), payload_json=json.dumps(view_payload))
            st.success(f"Saved view “{new_name}”.")
        except Exception as e:
            st.error(f"Could not save view: {e}")

with csb:
    all_views = list_views(user["id"], "dashboard")
    labels = [v["name"] for v in all_views]
    pick = st.selectbox("Load view", ["—"] + labels, index=0, key="dash_pick_view")
    if pick != "—":
        chosen = next(v for v in all_views if v["name"] == pick)
        payload = json.loads(chosen["payload"])

        # Restore session state
        st.session_state["dash_dataset"] = payload.get("dataset", choice)
        st.session_state["dash_cat"] = payload.get("sel_cat", "—")
        st.session_state["dash_val"] = payload.get("sel_val", "")
        st.session_state["dash_dt"] = payload.get("sel_dt", "—")
        if payload.get("drange"):
            from datetime import date
            try:
                d0 = pd.to_datetime(payload["drange"][0]).date()
                d1 = pd.to_datetime(payload["drange"][1]).date()
                st.session_state["dash_drange"] = (d0, d1)
            except Exception:
                st.session_state["dash_drange"] = None
        st.session_state["dash_keep_vals"] = payload.get("keep_vals", [])
        st.session_state["dash_cat_query"] = payload.get("cat_query", "")
        if payload.get("num_range") is not None:
            st.session_state["dash_val_range"] = tuple(payload["num_range"])

        # Update query params for deep link
        qp.update({"dataset": st.session_state["dash_dataset"]})
        st.rerun()

with csc:
    del_pick = st.selectbox("Delete view", ["—"] + labels, index=0, key="dash_del_view")
    if del_pick != "—" and st.button("Delete", use_container_width=True):
        try:
            delete_view(user["id"], "dashboard", del_pick)
            st.success(f"Deleted view “{del_pick}”.")
            st.rerun()
        except Exception as e:
            st.error(f"Could not delete: {e}")

# Offer raw JSON and deep-link helper
dl_json = json.dumps(view_payload, indent=2).encode()
st.download_button("Download view JSON", dl_json, "dashboard_view.json", "application/json")

# Also reflect current dataset in query params for sharable link
qp.update({"dataset": choice})

st.caption("Tip: copy the URL from your browser after setting filters — it includes the selected dataset. Saved views restore all filters, not just dataset.")

st.divider()

# ---------- 7) One-click Export (ZIP) ----------
st.subheader("Export")
exp_note = []
if not HAS_PLOTLY:
    exp_note.append("Plotly not available → charts PNGs will be skipped.")
if HAS_PLOTLY and not HAS_KALEIDO:
    exp_note.append("kaleido not installed → charts PNGs will be skipped.")
if exp_note:
    st.info(" ".join(exp_note))

if st.button("Download ZIP (filtered CSV + charts PNGs)", type="primary"):
    mem = BytesIO()
    with ZipFile(mem, mode="w", compression=ZIP_DEFLATED) as zf:
        # CSV
        zf.writestr("filtered.csv", df_view.to_csv(index=False))

        # Charts (if possible)
        if HAS_PLOTLY and HAS_KALEIDO and pio is not None:
            try:
                if bar_fig is not None:
                    buf = BytesIO()
                    pio.write_image(bar_fig, buf, format="png", scale=2)
                    zf.writestr("chart_bar.png", buf.getvalue())
                if line_fig is not None:
                    buf = BytesIO()
                    pio.write_image(line_fig, buf, format="png", scale=2)
                    zf.writestr("chart_timeseries.png", buf.getvalue())
            except Exception as e:
                zf.writestr("export_warning.txt", f"PNG export failed: {e}")

    st.download_button(
        "Download export.zip",
        data=mem.getvalue(),
        file_name="export.zip",
        mime="application/zip",
    )
