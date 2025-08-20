# auth.py — stdlib-only password hashing (PBKDF2-HMAC-SHA256)
import os, hmac, hashlib, base64
import db

# configurable defaults
_ITERATIONS = 200_000
_ALGO = "pbkdf2_sha256"

def _hash_password(password: str, salt: bytes | None = None) -> str:
    if salt is None:
        salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERATIONS)
    # store as: algo$iter$base64salt$base64dk
    return f"{_ALGO}${_ITERATIONS}${base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}"

def _verify_password(password: str, stored: str) -> bool:
    try:
        algo, iters_s, b64salt, b64dk = stored.split("$", 3)
        if algo != _ALGO:
            return False
        iters = int(iters_s)
        salt = base64.b64decode(b64salt.encode())
        expected = base64.b64decode(b64dk.encode())
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iters)
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False

def ensure_default_admin():
    db.init_db()
    admin_email = "admin@luminaiq.co"
    admin = db.get_user_by_email(admin_email)
    if admin is None:
        password_hash = _hash_password("Admin#123")
        db.insert_user(admin_email, "Admin", password_hash, role="admin", company="LuminaIQ")
        return True
    return False

def verify_credentials(email: str, password: str):
    user = db.get_user_by_email(email)
    if not user:
        return None
    if _verify_password(password, user["password_hash"]):
        return user
    return None

