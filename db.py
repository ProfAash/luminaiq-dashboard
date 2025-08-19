import os, sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "luminaiq.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'client',
        company TEXT DEFAULT ''
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS uploads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        filename TEXT NOT NULL,
        path TEXT NOT NULL,
        uploaded_at TEXT NOT NULL,
        rows INTEGER DEFAULT 0,
        cols INTEGER DEFAULT 0,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    conn.commit()
    return conn

def get_user_by_email(email: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (email.lower(),))
    return cur.fetchone()

def insert_user(email: str, name: str, password_hash: str, role: str = "client", company: str = "") -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (email, name, password_hash, role, company) VALUES (?, ?, ?, ?, ?)",
        (email.lower(), name, password_hash, role, company)
    )
    conn.commit()
    return cur.lastrowid

def list_uploads_for_user(user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM uploads WHERE user_id = ? ORDER BY uploaded_at DESC", (user_id,))
    return cur.fetchall()

def insert_upload(user_id: int, filename: str, path: str, uploaded_at: str, rows: int, cols: int) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO uploads (user_id, filename, path, uploaded_at, rows, cols) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, filename, path, uploaded_at, rows, cols)
    )
    conn.commit()
    return cur.lastrowid
