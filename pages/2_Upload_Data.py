import os
from datetime import datetime

import pandas as pd
import streamlit as st

from db import insert_upload, list_uploads_for_user

st.set_page_config(page_title="Upload Data • LuminaIQ", page_icon="📤", layout="wide")

user = st.session_state.get("user")
if not user:
    st.warning("Please sign in first.")
    st.stop()

st.title("📤 Upload Data")

# --- Uploader ---
uploaded = st.file_uploader("Upload a CSV file", type=["csv"], key="csv_uploader")

if uploaded is not None:
    try:
        df = pd.read_csv(uploaded)
        st.success(f"Loaded **{uploaded.name}** — {df.shape[0]:,} rows × {df.shape[1]:,} cols")
        st.dataframe(df.head(10))

        # Ensure an uploads directory exists
        save_dir = os.path.join(os.path.dirname(__file__), "..", "uploads")
        save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))
        os.makedirs(save_dir, exist_ok=True)

        # Save file to disk
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        safe_name = f"{ts}__{uploaded.name.replace(' ', '_')}"
        save_path = os.path.join(save_dir, safe_name)
        df.to_csv(save_path, index=False)

        # Record in DB
        insert_upload(
            user_id=user["id"],
            filename=uploaded.name,
            path=save_path,
            uploaded_at=datetime.utcnow().isoformat(timespec="seconds") + "Z",
            rows=int(df.shape[0]),
            cols=int(df.shape[1]),
        )

        st.success("✅ Upload saved.")
        st.toast("Upload recorded", icon="✅")
    except Exception as e:
        st.error(f"Failed to process file: {e}")

st.divider()

# --- Past uploads ---
st.subheader("Your uploads")

records = list_uploads_for_user(user["id"])
df_up = pd.DataFrame(records)

if df_up.empty:
    st.info("No uploads yet.")
else:
    # Show only columns that exist
    cols = [c for c in ["filename", "uploaded_at", "rows", "cols"] if c in df_up.columns]
    st.dataframe(df_up[cols], use_container_width=True)


