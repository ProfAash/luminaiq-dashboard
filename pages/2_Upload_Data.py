import os, time
import pandas as pd
import streamlit as st
from db import insert_upload, list_uploads_for_user

st.set_page_config(page_title="Upload • LuminaIQ", page_icon="⬆️", layout="wide")
user = st.session_state.get("user")
if not user:
    st.warning("Please sign in from the Home page.")
    st.stop()

st.title("⬆️ Upload Data")
st.caption("CSV files only. Your data stays private to your account.")

uploaded = st.file_uploader("Choose a CSV file", type=["csv"])

if uploaded:
    try:
        df = pd.read_csv(uploaded)
        rows, cols = df.shape
        st.success(f"Parsed **{rows} rows × {cols} columns**")
        st.dataframe(df.head())

        safe_name = os.path.basename(uploaded.name)
        user_dir = os.path.join(os.path.dirname(__file__), "..", "uploads", str(user["id"]))
        os.makedirs(user_dir, exist_ok=True)
        ts = int(time.time())
        out_path = os.path.abspath(os.path.join(user_dir, f"{ts}_{safe_name}"))
        df.to_csv(out_path, index=False)

        insert_upload(user_id=user["id"], filename=safe_name, path=out_path, uploaded_at=time.strftime("%Y-%m-%d %H:%M:%S"), rows=rows, cols=cols)
        st.success("✅ Upload saved")
        st.toast("Upload complete. Go to Dashboards to analyze.", icon="📊")

    except Exception as e:
        st.error(f"Upload failed: {e}")

st.divider()
st.subheader("Your uploads")
uploads = list_uploads_for_user(user_id=user["id"])
if uploads:
    st.dataframe(pd.DataFrame(uploads)[["filename","uploaded_at","rows","cols"]])
else:
    st.info("No files uploaded yet.")
