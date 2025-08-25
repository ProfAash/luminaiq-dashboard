# pages/2_Upload_Data.py
from __future__ import annotations
import io, os, hashlib
from datetime import datetime

import pandas as pd
import streamlit as st

from db import insert_upload, list_uploads_for_user

# Try storage upload (Supabase); if not available we fall back to local
try:
    from storage import upload_bytes  # (filename, content: bytes, content_type) -> (path_in_bucket, public_url)
    HAS_CLOUD = True
except Exception:
    HAS_CLOUD = False

st.set_page_config(page_title="Upload Data • LuminaIQ", page_icon="📤", layout="wide")

# ---------- auth guard ----------
user = st.session_state.get("user")
if not user:
    st.warning("Please sign in from the Home page.")
    st.stop()

st.title("📤 Upload Data")

# ---------- helpers ----------
@st.cache_data(show_spinner=False, ttl=600)
def _read_csv_bytes(b: bytes) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(b))

def _md5_digest(b: bytes) -> str:
    return hashlib.md5(b).hexdigest()[:8]

# (optional) enforce schema here if needed
REQUIRED_COLUMNS: list[str] = []   # e.g. ["Year", "Median_Value_ZAR"]

# ---------- uploader ----------
uploaded = st.file_uploader("Upload a CSV file", type=["csv"], key="csv_uploader")

if uploaded is not None:
    try:
        # read once
        file_bytes = uploaded.read()
        df = _read_csv_bytes(file_bytes)

        # metadata for user feedback
        digest = _md5_digest(file_bytes)
        rows, cols = df.shape
        st.success(f"Loaded **{uploaded.name}** — {rows:,} rows × {cols:,} cols · id `{digest}`")
        st.dataframe(df.head(10), use_container_width=True)

        # schema guard (optional)
        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            st.error(f"Missing required columns: {', '.join(missing)}")
            st.stop()

        # try cloud first
        save_path_for_db: str
        if HAS_CLOUD:
            try:
                _, public_url = upload_bytes(
                    filename=uploaded.name,
                    content=file_bytes,
                    content_type="text/csv",
                )
                save_path_for_db = public_url
                st.toast("✅ Upload saved to cloud storage", icon="✅")
            except Exception as e:
                st.warning(f"Cloud storage unavailable ({e}). Saving locally for now.")
                os.makedirs("uploads", exist_ok=True)
                local_path = os.path.join("uploads", uploaded.name.replace(" ", "_"))
                # Reconstruct CSV bytes to disk
                pd.read_csv(io.BytesIO(file_bytes)).to_csv(local_path, index=False)
                save_path_for_db = local_path
        else:
            # local fallback
            os.makedirs("uploads", exist_ok=True)
            local_path = os.path.join("uploads", uploaded.name.replace(" ", "_"))
            pd.read_csv(io.BytesIO(file_bytes)).to_csv(local_path, index=False)
            save_path_for_db = local_path
            st.info("Saving locally (cloud storage not configured).")

        # record in DB (path will be public URL or local path as above)
        insert_upload(
            user_id=user["id"],
            filename=uploaded.name,
            path=save_path_for_db,
            uploaded_at=datetime.utcnow().isoformat(timespec="seconds") + "Z",
            rows=int(rows),
            cols=int(cols),
        )
        st.toast("Upload recorded", icon="📦")

    except Exception as e:
        st.error(f"Failed to process file: {e}")

st.divider()
st.subheader("Your uploads")

records = list_uploads_for_user(user_id=user["id"])
if not records:
    st.info("No uploads yet.")
else:
    # show common columns if present
    df_up = pd.DataFrame(records)
    keep_cols = [c for c in ["filename", "uploaded_at", "rows", "cols", "path"] if c in df_up.columns]
    st.dataframe(df_up[keep_cols], use_container_width=True)
