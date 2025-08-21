try:
    import plotly.express as px
    HAS_PLOTLY = True
except Exception:
    HAS_PLOTLY = False

import pandas as pd
import streamlit as st
from db import list_uploads_for_user

# Try Plotly, fall back to Streamlit charts if not available
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

c1, c2, c3 = st.columns(3)
c1.metric("Total datasets", f"{len(uploads)}")
rows_total = sum(u["rows"] for u in uploads) if uploads else 0
c2.metric("Total rows", f"{rows_total:,}")
c3.metric("Last upload", uploads[0]["uploaded_at"] if uploads else "—")

st.divider()
st.subheader("Recent uploads")
if not uploads:
    st.info("No uploads yet. Go to **Upload Data** to get started.")
else:
    st.dataframe(pd.DataFrame(uploads)[["filename","uploaded_at","rows","cols"]])
    latest = uploads[0]
    try:
        df = pd.read_csv(latest["path"])
        st.subheader(f"Quick glance: {latest['filename']}")
        st.write(df.head())
        numeric_cols = df.select_dtypes("number").columns.tolist()
        if numeric_cols:
            st.plotly_chart(px.histogram(df, x=numeric_cols[0]), use_container_width=True)
        cat_cols = df.select_dtypes("object").columns.tolist()
        if cat_cols:
            top_counts = df[cat_cols[0]].value_counts().head(10).reset_index()
            top_counts.columns = [cat_cols[0], "count"]
            if HAS_PLOTLY:
                st.plotly_chart(px.bar(grp, x=category_col, y=break_val_col), use_container_width=True)
            else:
                st.bar_chart(grp.set_index(category_col)[break_val_col])

    except Exception as e:
        st.warning(f"Could not preview latest dataset: {e}")
