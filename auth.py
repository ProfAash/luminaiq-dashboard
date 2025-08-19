import bcrypt
import db

def ensure_default_admin():
    db.init_db()
    admin_email = "admin@luminaiq.co"
    admin = db.get_user_by_email(admin_email)
    if admin is None:
        password = "Admin#123"
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        db.insert_user(admin_email, "Admin", password_hash, role="admin", company="LuminaIQ")
        return True
    return False

def verify_credentials(email: str, password: str):
    user = db.get_user_by_email(email)
    if not user:
        return None
    stored_hash = user["password_hash"].encode("utf-8")
    if bcrypt.checkpw(password.encode("utf-8"), stored_hash):
        return user
    return None
