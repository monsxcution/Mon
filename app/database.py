import os
import sqlite3

# Correctly define APP_ROOT as the project's root directory
APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
DATA_DIR = os.path.join(APP_ROOT, "data")
DATABASE_PATH = os.path.join(DATA_DIR, "Data.db")

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    # Using check_same_thread=False for web app context, but be mindful of thread safety.
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Creates the data directory and initializes all database tables if they don't exist."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    conn = get_db_connection()
    # Notes Table
    conn.execute(
        """CREATE TABLE IF NOT EXISTS notes (
            id TEXT PRIMARY KEY,
            title_html TEXT,
            content_html TEXT,
            due_time TEXT,
            status TEXT,
            modified_at TEXT,
            is_marked INTEGER DEFAULT 0
        )"""
    )
    # Add other table creation statements here in the future
    conn.commit()
    conn.close()
    print("Database initialized successfully.")
