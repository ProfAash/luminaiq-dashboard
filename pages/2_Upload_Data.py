import pandas as pd
import streamlit as st
from db import list_uploads_for_user

st.title("Your uploads")

user = st.session_state.get("user")
if not user:
    st.warning("Please sign in first.")
    st.stop()

uploads = list_uploads_for_user(user["id"])
df = pd.DataFrame(uploads)

if df.empty:
    st.info("No uploads yet.")
else:
    # Only show the columns that actually exist
    show_cols = [c for c in ["filename", "uploaded_at", "rows", "cols"] if c in df.columns]
    st.dataframe(df[show_cols])

