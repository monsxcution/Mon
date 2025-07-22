# memory_manager.py
import sqlite3
import os
from datetime import datetime

# --- Create absolute path for the database ---
basedir = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(basedir, "memory.db")

def initialize_memory():
    """Creates the memory database and table if they don't exist."""
    try:
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL UNIQUE,
                timestamp TEXT NOT NULL
            )
        """)
        con.commit()
        con.close()
    except Exception as e:
        print(f"Error initializing memory DB: {e}")

def add_memory(text: str):
    """Adds a new piece of information to the AI's memory."""
    try:
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute("INSERT OR IGNORE INTO memories (content, timestamp) VALUES (?, ?)", 
                    (text, datetime.now().isoformat()))
        con.commit()
        con.close()
        return True
    except Exception as e:
        print(f"Error adding memory: {e}")
        return False

def get_all_memories(limit: int = 15) -> list[str]:
    """Retrieves the most recent memories."""
    try:
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute("SELECT content FROM memories ORDER BY id DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        con.close()
        return [row[0] for row in rows]
    except Exception as e:
        print(f"Error getting memories: {e}")
        return []

def clear_all_memories():
    """Deletes all memories from the database."""
    try:
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute("DELETE FROM memories")
        con.commit()
        con.close()
        return True
    except Exception as e:
        print(f"Error clearing memories: {e}")
        return False 