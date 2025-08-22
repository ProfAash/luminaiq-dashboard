# pages/1_Overview.py
import pandas as pd
import streamlit as st
from db import list_uploads_for_user

# Try Plotly; fall back to Streamlit charts if not available
try:
    import plotly.express as px
    HAS_PLOTLY = True
except Exception:
    HAS_PLOTLY = False

st.set_page_config(page_title="Overview • LuminaIQ", page_icon="📈", layout="wide")

user = st.session_state.get("user")
if not user:
    st.warning("Please sign in from the Home page.")
    st.stop()

st.title("📈 Overview")

uploads = list_uploads_for_user(user_id=user["id"])

# KPIs
c1, c2, c3 = st.columns(3)
c1.metric("Total datasets", f"{len(uploads)}")
rows_total = sum(u.get("rows", 0) for u in uploads) if uploads else 0
c2.metric("Total rows", f"{rows_total:,}")
last_up = uploads[0]["uploaded_at"] if uploads else "—"
c3.metric("Last upload", last_up)

st.divider()
st.subheader("Recent uploads")

if not uploads:
    st.info("No uploads yet. Go to **Upload Data** to get started.")
else:
    # show only columns that exist
    up_df = pd.DataFrame(uploads)
    show_cols = [c for c in ["filename", "uploaded_at", "rows", "cols"] if c in up_df.columns]
    st.dataframe(up_df[show_cols], use_container_width=True)

    # Quick glance of the latest dataset
    latest = uploads[0]
    st.subheader(f"Quick glance: {latest.get('filename', 'latest dataset')}")
    try:
        path = latest.get("path", "")
        df = pd.read_csv(path)  # works with Supabase public URL or local path
        st.write(df.head())

        # One quick numeric distribution
        numeric_cols = df.select_dtypes("number").columns.tolist()
        if numeric_cols:
            st.caption(f"Distribution of **{numeric_cols[0]}**")
            if HAS_PLOTLY:
                st.plotly_chart(px.histogram(df, x=numeric_cols[0]), use_container_width=True)
            else:
                st.bar_chart(df[numeric_cols[0]].value_counts().sort_index())

        # Top categories for first categorical column
        cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        if cat_cols:
            st.caption(f"Top values for **{cat_cols[0]}**")
            top_counts = df[cat_cols[0]].value_counts(dropna=False).head(10).reset_index()
            top_counts.columns = [cat_cols[0], "count"]
            if HAS_PLOTLY:
                st.plotly_chart(px.bar(top_counts, x=cat_cols[0], y="count"), use_container_width=True)
            else:
                st.bar_chart(top_counts.set_index(cat_cols[0])["count"])

    except Exception as e:
        st.warning(f"Could not preview latest dataset: {e}")

