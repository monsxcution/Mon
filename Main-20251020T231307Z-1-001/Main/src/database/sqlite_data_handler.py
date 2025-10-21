"""
SQLite Data Handler Module
This module contains all SQLite database operations to replace JSON file operations.
"""

import sqlite3
import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

# Database path
DATABASE_PATH = os.path.join("data", "Data.db")

def create_health_tables():
    """Create tables for the Healthy Dashboard if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Goals Table (stores one row of goals)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS health_goals (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            target_weight REAL,
            target_kcal INTEGER,
            tdee INTEGER,
            height REAL,
            updated_at TEXT NOT NULL
        )
        """)

        # Weight History Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS health_weight_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_date TEXT NOT NULL UNIQUE,
            weight REAL NOT NULL,
            created_at TEXT NOT NULL
        )
        """)

        # Food Library Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS health_food_library (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            kcal INTEGER NOT NULL,
            protein REAL NOT NULL,
            carbs REAL NOT NULL,
            fat REAL NOT NULL,
            default_serving_g REAL DEFAULT 100
        )
        """)

        # Daily Food Log Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS health_food_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_date TEXT NOT NULL,
            meal_category TEXT NOT NULL,
            food_id INTEGER,
            custom_name TEXT,
            amount_g REAL NOT NULL,
            kcal INTEGER NOT NULL,
            protein REAL NOT NULL,
            carbs REAL NOT NULL,
            fat REAL NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (food_id) REFERENCES health_food_library (id)
        )
        """)
        conn.commit()
        print("✅ Health tables checked/created successfully.")
    except sqlite3.Error as e:
        print(f"Error creating health tables: {e}")
    finally:
        conn.close()

def init_database():
    """Initialize the SQLite database with all required tables."""
    db_dir = os.path.dirname(DATABASE_PATH)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
        
    conn = get_db_connection()
    # Database will be created automatically by SQLite if it doesn't exist.
    conn.close()
    
    # Create health-specific tables
    create_health_tables()
    
    print("✅ Database initialized")


def get_db_connection():
    """Get SQLite database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
    return conn

# Alias functions for consistent naming
def get_accounts():
    """Get all password accounts."""
    return load_accounts()

def get_password_types():
    """Get all password types."""
    return load_types()

def get_notes():
    """Get all notes."""
    return load_notes()

def get_reminders():
    """Get all reminders."""
    # Return empty list for now - reminders are not fully implemented
    return []

def get_proxies():
    """Get all proxies."""
    # Return empty list for now - proxies are not fully implemented
    return []

def get_telegram_sessions():
    """Get all Telegram sessions from uploaded_sessions directory."""
    sessions_data = []
    sessions_base_path = os.path.join("data", "uploaded_sessions")
    
    if not os.path.exists(sessions_base_path):
        return sessions_data
    
    try:
        # Scan all subdirectories in uploaded_sessions
        for folder_name in os.listdir(sessions_base_path):
            folder_path = os.path.join(sessions_base_path, folder_name)
            
            if os.path.isdir(folder_path):
                # Count session files in this folder
                session_files = [f for f in os.listdir(folder_path) if f.endswith('.session')]
                
                sessions_data.append({
                    "folder_name": folder_name,
                    "session_count": len(session_files),
                    "sessions": [
                        {
                            "filename": session_file,
                            "phone": session_file.replace('.session', '').replace('_', '+'),
                            "status": "active",  # Default status
                            "last_seen": "Unknown"
                        }
                        for session_file in sorted(session_files)
                    ]
                })
        
        return sessions_data
    except Exception as e:
        print(f"Error loading Telegram sessions: {e}")
        return []

def get_db_connection():
    """Get SQLite database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
    return conn

# --- PASSWORD MANAGEMENT FUNCTIONS ---

def load_accounts() -> List[Dict[str, Any]]:
    """Load password accounts from SQLite database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
        SELECT id, type, username, password, notes, two_fa as "2fa", 
               created_at, updated_at 
        FROM password_accounts 
        ORDER BY id
        """)
        accounts = [dict(row) for row in cursor.fetchall()]
        return accounts
    except sqlite3.Error as e:
        print(f"Error loading accounts: {e}")
        return []
    finally:
        conn.close()

def save_accounts(accounts: List[Dict[str, Any]]) -> bool:
    """Save password accounts to SQLite database. (This is now handled by individual operations)"""
    # This function is kept for compatibility but individual operations should be used
    return True

def get_next_id(accounts: List[Dict[str, Any]]) -> int:
    """Get next available ID for password accounts."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT MAX(id) FROM password_accounts")
        max_id = cursor.fetchone()[0]
        return (max_id or 0) + 1
    except sqlite3.Error:
        return 1
    finally:
        conn.close()

def add_password_account(account_data: Dict[str, Any]) -> bool:
    """Add a new password account to database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
        INSERT INTO password_accounts (type, username, password, notes, two_fa)
        VALUES (?, ?, ?, ?, ?)
        """, (
            account_data.get('type', ''),
            account_data.get('username', ''),
            account_data.get('password', ''),
            account_data.get('notes', ''),
            account_data.get('2fa', '')
        ))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error adding account: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def update_password_account(account_id: int, account_data: Dict[str, Any]) -> bool:
    """Update an existing password account."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
        UPDATE password_accounts 
        SET type = ?, username = ?, password = ?, notes = ?, two_fa = ?, 
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """, (
            account_data.get('type', ''),
            account_data.get('username', ''),
            account_data.get('password', ''),
            account_data.get('notes', ''),
            account_data.get('2fa', ''),
            account_id
        ))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Error updating account: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def delete_password_account(account_id: int) -> bool:
    """Delete a password account."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM password_accounts WHERE id = ?", (account_id,))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Error deleting account: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# --- PASSWORD TYPES MANAGEMENT ---

def load_types() -> List[Dict[str, str]]:
    """Load password types from SQLite database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT name, color FROM password_types ORDER BY name")
        types = [dict(row) for row in cursor.fetchall()]
        return types
    except sqlite3.Error as e:
        print(f"Error loading types: {e}")
        return []
    finally:
        conn.close()

def save_types(types: List[Dict[str, str]]) -> bool:
    """Save password types to SQLite database. (This is now handled by individual operations)"""
    # This function is kept for compatibility but individual operations should be used
    return True

def add_password_type(name: str, color: str = "#6c757d") -> bool:
    """Add a new password type."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
        INSERT INTO password_types (name, color)
        VALUES (?, ?)
        """, (name, color))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Type already exists
        return False
    except sqlite3.Error as e:
        print(f"Error adding type: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def delete_password_type(name: str) -> bool:
    """Delete a password type."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM password_types WHERE name = ?", (name,))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Error deleting type: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def update_password_type_color(name: str, color: str) -> bool:
    """Update password type color."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
        UPDATE password_types 
        SET color = ?, updated_at = CURRENT_TIMESTAMP
        WHERE name = ?
        """, (color, name))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Error updating type color: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# --- NOTES MANAGEMENT ---

def load_notes() -> List[Dict[str, Any]]:
    """Load notes from SQLite database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
        SELECT id, title_html, content_html, due_time, status, 
               created_at, modified_at 
        FROM notes 
        ORDER BY modified_at DESC
        """)
        notes = [dict(row) for row in cursor.fetchall()]
        return notes
    except sqlite3.Error as e:
        print(f"Error loading notes: {e}")
        return []
    finally:
        conn.close()

def save_notes(notes: List[Dict[str, Any]]) -> bool:
    """Save notes to SQLite database. (This is now handled by individual operations)"""
    # This function is kept for compatibility but individual operations should be used
    return True

def add_note(note_data: Dict[str, Any]) -> bool:
    """Add a new note to database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        note_id = note_data.get('id') or str(uuid.uuid4())
        cursor.execute("""
        INSERT INTO notes (id, title_html, content_html, due_time, status, modified_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            note_id,
            note_data.get('title_html', ''),
            note_data.get('content_html', ''),
            note_data.get('due_time'),
            note_data.get('status', 'none'),
            note_data.get('modified_at', datetime.now().isoformat())
        ))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error adding note: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def update_note(note_id: str, note_data: Dict[str, Any]) -> bool:
    """Update an existing note."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Build update query dynamically based on provided fields
        update_fields = []
        update_values = []
        
        if 'title_html' in note_data:
            update_fields.append("title_html = ?")
            update_values.append(note_data['title_html'])
            
        if 'content_html' in note_data:
            update_fields.append("content_html = ?")
            update_values.append(note_data['content_html'])
            
        if 'due_time' in note_data:
            update_fields.append("due_time = ?")
            update_values.append(note_data['due_time'])
            
        if 'status' in note_data:
            update_fields.append("status = ?")
            update_values.append(note_data['status'])
            
        # Always update modified_at
        update_fields.append("modified_at = ?")
        update_values.append(note_data.get('modified_at', datetime.now().isoformat()))
        
        # Add note_id for WHERE clause
        update_values.append(note_id)
        
        if not update_fields:
            return False
            
        query = f"UPDATE notes SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(query, update_values)
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Error updating note: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def delete_note(note_id: str) -> bool:
    """Delete a note."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Error deleting note: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# --- PROXY SETTINGS MANAGEMENT ---

def load_proxy_settings() -> Dict[str, Any]:
    """Load proxy settings from SQLite database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT enabled, proxy_list FROM proxy_settings ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            return {
                'enabled': bool(row['enabled']),
                'proxies': json.loads(row['proxy_list'])
            }
        return {'enabled': True, 'proxies': []}
    except sqlite3.Error as e:
        print(f"Error loading proxy settings: {e}")
        return {'enabled': True, 'proxies': []}
    finally:
        conn.close()

def save_proxy_settings(settings: Dict[str, Any]) -> bool:
    """Save proxy settings to SQLite database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Clear existing settings and insert new ones
        cursor.execute("DELETE FROM proxy_settings")
        cursor.execute("""
        INSERT INTO proxy_settings (enabled, proxy_list)
        VALUES (?, ?)
        """, (
            settings.get('enabled', True),
            json.dumps(settings.get('proxies', []))
        ))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error saving proxy settings: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# --- DASHBOARD SETTINGS MANAGEMENT ---

def load_dashboard_settings() -> Dict[str, Any]:
    """Load dashboard settings from SQLite database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT setting_key, setting_value FROM dashboard_settings")
        rows = cursor.fetchall()
        settings = {}
        for row in rows:
            key = row['setting_key']
            value = row['setting_value']
            # Try to parse JSON, otherwise use as string
            try:
                settings[key] = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                settings[key] = value
        return settings
    except sqlite3.Error as e:
        print(f"Error loading dashboard settings: {e}")
        return {}
    finally:
        conn.close()

def save_dashboard_settings(settings: Dict[str, Any]) -> bool:
    """Save dashboard settings to SQLite database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Clear existing settings
        cursor.execute("DELETE FROM dashboard_settings")
        
        # Insert new settings
        for key, value in settings.items():
            value_str = json.dumps(value) if not isinstance(value, str) else value
            cursor.execute("""
            INSERT INTO dashboard_settings (setting_key, setting_value)
            VALUES (?, ?)
            """, (key, value_str))
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error saving dashboard settings: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_dashboard_setting(key: str, default: Any = None) -> Any:
    """Get a specific dashboard setting."""
    settings = load_dashboard_settings()
    return settings.get(key, default)

def set_dashboard_setting(key: str, value: Any) -> bool:
    """Set a specific dashboard setting."""
    settings = load_dashboard_settings()
    settings[key] = value
    return save_dashboard_settings(settings)

# --- HEALTHY DASHBOARD DATA FUNCTIONS ---

def get_health_goals() -> Optional[Dict[str, Any]]:
    """Load health goals from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM health_goals WHERE id = 1")
        row = cursor.fetchone()
        return dict(row) if row else None
    except sqlite3.Error as e:
        print(f"Error loading health goals: {e}")
        return None
    finally:
        conn.close()

def save_health_goals(goals: Dict[str, Any]) -> bool:
    """Save or update health goals in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT OR REPLACE INTO health_goals (id, target_weight, target_kcal, tdee, height, updated_at)
        VALUES (1, ?, ?, ?, ?, ?)
        """, (
            goals.get('target_weight'),
            goals.get('target_kcal'),
            goals.get('tdee'),
            goals.get('height'),
            datetime.now().isoformat()
        ))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error saving health goals: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_weight_history() -> List[Dict[str, Any]]:
    """Load all weight history entries, ordered by date."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT entry_date, weight FROM health_weight_history ORDER BY entry_date ASC")
        history = [dict(row) for row in cursor.fetchall()]
        return history
    except sqlite3.Error as e:
        print(f"Error loading weight history: {e}")
        return []
    finally:
        conn.close()

def add_weight_entry(entry_date: str, weight: float) -> bool:
    """Add or update a weight entry for a specific date."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT OR REPLACE INTO health_weight_history (entry_date, weight, created_at)
        VALUES (?, ?, ?)
        """, (entry_date, weight, datetime.now().isoformat()))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error adding weight entry: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_food_log_for_date(entry_date: str) -> List[Dict[str, Any]]:
    """Get all food log entries for a specific date."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT l.*, f.name as food_name 
            FROM health_food_log l
            LEFT JOIN health_food_library f ON l.food_id = f.id
            WHERE l.entry_date = ?
        """, (entry_date,))
        log = [dict(row) for row in cursor.fetchall()]
        return log
    except sqlite3.Error as e:
        print(f"Error getting food log: {e}")
        return []
    finally:
        conn.close()

def add_food_log_entry(log_data: Dict[str, Any]) -> bool:
    """Add an entry to the food log."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO health_food_log 
            (entry_date, meal_category, food_id, custom_name, amount_g, kcal, protein, carbs, fat, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            log_data['entry_date'],
            log_data['meal_category'],
            log_data.get('food_id'),
            log_data.get('custom_name'),
            log_data['amount_g'],
            log_data['kcal'],
            log_data['protein'],
            log_data['carbs'],
            log_data['fat'],
            datetime.now().isoformat()
        ))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error adding food log entry: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def search_food_library(query: str) -> List[Dict[str, Any]]:
    """Search the food library by name."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT * FROM health_food_library WHERE name LIKE ? LIMIT 20", 
            (f'%{query}%',)
        )
        results = [dict(row) for row in cursor.fetchall()]
        return results
    except sqlite3.Error as e:
        print(f"Error searching food library: {e}")
        return []
    finally:
        conn.close()
