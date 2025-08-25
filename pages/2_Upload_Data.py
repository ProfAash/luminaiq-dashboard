# pages/2_Upload_Data.py
import os
import io
from datetime import datetime

import pandas as pd
import streamlit as st

from db import insert_upload, list_uploads_for_user
from storage import upload_bytes

# ✅ MUST be the first Streamlit call
st.set_page_config(page_title="Upload Data • LuminaIQ", page_icon="📤", layout="wide")

# (Optional) show a small diagnostic after page_config
try:
    import importlib.util, importlib.metadata as md
    if importlib.util.find_spec("supabase"):
        st.sidebar.success(f"Supabase present: {md.version('supabase')}")
    else:
        st.sidebar.warning("Supabase not detected; uploads will save locally.")
except Exception as _e:
    st.sidebar.warning(f"Diag error: {_e}")

# ---------------------------------------------------------------------
# Auth gate
# ---------------------------------------------------------------------
user = st.session_state.get("user")
if not user:
    st.warning("Please sign in first.")
    st.stop()

st.title("📤 Upload Data")

# ---------------------------------------------------------------------
# Uploader
# ---------------------------------------------------------------------
uploaded = st.file_uploader("Upload a CSV file", type=["csv"], key="csv_uploader")

if uploaded is not None:
    try:
        # Read file bytes once; reuse them
        file_bytes = uploaded.getvalue()

        # Preview
        df = pd.read_csv(io.BytesIO(file_bytes))
        st.success(f"Loaded **{uploaded.name}** — {df.shape[0]:,} rows × {df.shape[1]:,} cols")
        st.dataframe(df.head(10), use_container_width=True)

        # -----------------------------------------------------------------
        # Try cloud upload via Supabase; fall back to local storage
        # -----------------------------------------------------------------
        try:
            path_in_bucket, public_url = upload_bytes(
                filename=uploaded.name,
                content=file_bytes,
                content_type="text/csv",
            )
            save_path_for_db = public_url
            st.success("✅ Upload saved to cloud storage.")
        except Exception as e:
            st.warning(f"Cloud storage unavailable ({e}). Saving locally for now.")
            os.makedirs("uploads", exist_ok=True)
            safe_name = uploaded.name.replace(" ", "_")
            local_path = os.path.join("uploads", safe_name)
            with open(local_path, "wb") as f:
                f.write(file_bytes)
            save_path_for_db = local_path
            st.info(f"Saved locally: `{local_path}`")

        # -----------------------------------------------------------------
        # Record in DB (store the public URL or local path so the app can load it)
        # -----------------------------------------------------------------
        insert_upload(
            user_id=user["id"],
            filename=uploaded.name,
            path=save_path_for_db,
            uploaded_at=datetime.utcnow().isoformat(timespec="seconds") + "Z",
            rows=int(df.shape[0]),
            cols=int(df.shape[1]),
        )

        st.toast("Upload recorded", icon="✅")

    except Exception as e:
        st.error(f"Failed to process file: {e}")

st.divider()
st.subheader("Your uploads")

records = list_uploads_for_user(user["id"])
# SQLite row objects -> dicts for DataFrame
try:
    df_up = pd.DataFrame([dict(r) for r in records]) if records else pd.DataFrame()
except Exception:
    df_up = pd.DataFrame(records)  # fallback if they're already dict-like

if df_up.empty:
    st.info("No uploads yet.")
else:
    cols = [c for c in ["filename", "uploaded_at", "rows", "cols"] if c in df_up.columns]
    st.dataframe(df_up[cols], use_container_width=True)
