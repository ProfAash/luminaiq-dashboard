import os
import base64
import hashlib
import streamlit as st
from typing import Optional
from db import get_user_by_email, insert_user

def _hash_password(password: str, salt: Optional[bytes] = None) -> str:
    ITER = 200_000
    ALGO = "pbkdf2_sha256"
    if salt is None:
        salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITER)
    return f"{ALGO}${ITER}${base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}"

def reset_admin():
    st.title("🔑 Reset Admin Credentials")

    email = st.text_input("Admin Email")
    name = st.text_input("Admin Name")
    password = st.text_input("New Password", type="password")

    if st.button("Reset Admin"):
        if not email or not name or not password:
            st.error("⚠️ All fields are required")
            return

        # Hash password
        password_hash = _hash_password(password)

        # Insert or update admin user
        try:
            existing_user = get_user_by_email(email)
            if existing_user:
                st.warning("Admin already exists. Updating password only.")
                # Updating password for existing admin
                from db import get_conn
                conn = get_conn()
                cur = conn.cursor()
                cur.execute(
                    "UPDATE users SET password_hash = ?, role = 'admin' WHERE email = ?",
                    (password_hash, email.lower()),
                )
                conn.commit()
            else:
                insert_user(email, name, password_hash, role="admin")

            st.success("✅ Admin credentials reset successfully!")
        except Exception as e:
            st.error(f"Error resetting admin: {e}")

if __name__ == "__main__":
    reset_admin()

