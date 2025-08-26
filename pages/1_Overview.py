# pages/1_Overview.py
import pandas as pd
import streamlit as st
from db import list_uploads_for_user
from components import kpi

try:
    from components import kpi
except Exception:
    import streamlit as st
    def kpi(label, value, delta=None, help=None):
        st.metric(label, value, delta=delta, help=help)


# Plotly optional
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
rows_total = sum(u.get("rows", 0) or 0 for u in uploads) if uploads else 0
last_upload = uploads[0]["uploaded_at"] if uploads else "—"

# --- KPI header ---
c1, c2, c3 = st.columns(3)
with c1: kpi("Total datasets", f"{len(uploads):,}")
with c2: kpi("Total rows", f"{rows_total:,}")
with c3: kpi("Last upload", f"{last_upload}")

st.divider()
st.subheader("Recent uploads")

if not uploads:
    st.info("No uploads yet. Go to **Upload Data** to get started.")
    st.stop()

df_up = pd.DataFrame(uploads)
keep_cols = [c for c in ["filename","uploaded_at","rows","cols","path"] if c in df_up.columns]
st.dataframe(df_up[keep_cols], use_container_width=True)

# Quick glance of latest file
latest = uploads[0]
st.subheader(f"Quick glance: {latest['filename']}")

try:
    # Read from URL or local path
    path = latest.get("path", "")
    df = pd.read_csv(path)

    st.dataframe(df.head(10), use_container_width=True)

    # Try a quick chart if any numeric column exists
    num_cols = df.select_dtypes("number").columns.tolist()
    if num_cols:
        if HAS_PLOTLY:
            fig = px.histogram(df, x=num_cols[0])
            st.plotly_chart(fig, use_container_width=True)
            # PNG export button (enabled in section B below)
            from io import BytesIO
            buf = BytesIO()
            try:
                import plotly.io as pio
                pio.write_image(fig, buf, format="png", scale=2)  # requires kaleido
                st.download_button("Download chart PNG", data=buf.getvalue(),
                                   file_name="overview_chart.png", mime="image/png")
            except Exception as e:
                st.caption("Tip: add `kaleido` to requirements.txt to enable PNG export.")
        else:
            st.bar_chart(df[num_cols[0]])
except Exception as e:
    st.warning(f"Could not preview latest dataset: {e}")
