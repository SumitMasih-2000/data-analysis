import sqlite3
import hashlib
import io
import pandas as pd

DB_FILE = "retailiq.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    return conn

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    # Datasets table (stores data as CSV string per user)
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_datasets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            data_csv TEXT NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()

def create_user(username, password):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                  (username.strip().lower(), hash_password(password)))
        conn.commit()
        return True, "Account created successfully!"
    except sqlite3.IntegrityError:
        return False, "Username already exists. Please choose another."
    finally:
        conn.close()

def authenticate_user(username, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, username FROM users WHERE username = ? AND password = ?", 
              (username.strip().lower(), hash_password(password)))
    user = c.fetchone()
    conn.close()
    if user:
        return {"id": user[0], "username": user[1]}
    return None

def save_user_dataset(user_id: int, filename: str, df: pd.DataFrame):
    conn = get_connection()
    c = conn.cursor()
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_text = csv_buffer.getvalue()
    
    # Store or update current dataset for user
    c.execute("DELETE FROM user_datasets WHERE user_id = ?", (user_id,))
    c.execute("INSERT INTO user_datasets (user_id, filename, data_csv) VALUES (?, ?, ?)", 
              (user_id, filename, csv_text))
    conn.commit()
    conn.close()

def load_user_dataset(user_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT filename, data_csv FROM user_datasets WHERE user_id = ? ORDER BY uploaded_at DESC LIMIT 1", (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        filename, data_csv = row
        df = pd.read_csv(io.StringIO(data_csv))
        return filename, df
    return None, None
