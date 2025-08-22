# pages/2_Upload_Data.py
import io
from datetime import datetime

import pandas as pd
import streamlit as st

from db import insert_upload, list_uploads_for_user
from storage import upload_bytes

st.set_page_config(page_title="Upload Data • LuminaIQ", page_icon="📤", layout="wide")

user = st.session_state.get("user")
if not user:
    st.warning("Please sign in first.")
    st.stop()

st.title("📤 Upload Data")

uploaded = st.file_uploader("Upload a CSV file", type=["csv"], key="csv_uploader")

if uploaded is not None:
    try:
        # Read once for preview
        file_bytes = uploaded.read()
        df = pd.read_csv(io.BytesIO(file_bytes))

        st.success(f"Loaded **{uploaded.name}** — {df.shape[0]:,} rows × {df.shape[1]:,} cols")
        st.dataframe(df.head(10), use_container_width=True)

        # Upload to Supabase Storage
        path_in_bucket, public_url = upload_bytes(
            filename=uploaded.name,
            content=file_bytes,
            content_type="text/csv",
        )

        # Record in DB (store the public URL in `path` so the rest of the app can load it)
        insert_upload(
            user_id=user["id"],
            filename=uploaded.name,
            path=public_url,  # <- store public URL
            uploaded_at=datetime.utcnow().isoformat(timespec="seconds") + "Z",
            rows=int(df.shape[0]),
            cols=int(df.shape[1]),
        )

        st.success("✅ Upload saved to cloud storage.")
        st.toast("Upload recorded", icon="✅")
    except Exception as e:
        st.error(f"Failed to process file: {e}")

st.divider()
st.subheader("Your uploads")

records = list_uploads_for_user(user["id"])
df_up = pd.DataFrame(records)

if df_up.empty:
    st.info("No uploads yet.")
else:
    # Keep columns that exist
    cols = [c for c in ["filename", "uploaded_at", "rows", "cols"] if c in df_up.columns]
    st.dataframe(df_up[cols], use_container_width=True)



