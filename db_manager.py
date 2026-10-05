import sqlite3
from pathlib import Path

# SQLite database stored in the same folder as this file
DB_PATH = Path(__file__).resolve().parent / "retailiq.db"


def _get_connection():
    """Create a connection to the local SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS user_data (
            username TEXT PRIMARY KEY,
            csv_data TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def save_data(username, csv_string):
    """
    Save or replace CSV data for a user.

    Parameters:
        username: Logged-in user's username/ID.
        csv_string: CSV content as a string.
    """
    if not username:
        raise ValueError("Username is required.")

    if csv_string is None:
        raise ValueError("CSV data cannot be empty.")

    conn = _get_connection()
    try:
        conn.execute(
            """
            INSERT INTO user_data (username, csv_data)
            VALUES (?, ?)
            ON CONFLICT(username)
            DO UPDATE SET csv_data = excluded.csv_data
            """,
            (str(username), str(csv_string)),
        )
        conn.commit()
    finally:
        conn.close()


def get_data(username):
    """
    Retrieve the CSV data stored for a user.

    Returns:
        CSV string if data exists, otherwise None.
    """
    if not username:
        return None

    conn = _get_connection()
    try:
        cursor = conn.execute(
            "SELECT csv_data FROM user_data WHERE username = ?",
            (str(username),),
        )
        row = cursor.fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def delete_data(username):
    """Delete all stored data for a user."""
    if not username:
        return

    conn = _get_connection()
    try:
        conn.execute(
            "DELETE FROM user_data WHERE username = ?",
            (str(username),),
        )
        conn.commit()
    finally:
        conn.close()
