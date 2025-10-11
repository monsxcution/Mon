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
    
    # MXH Tables
    # Groups table to organize social media accounts
    conn.execute(
        """CREATE TABLE IF NOT EXISTS mxh_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            color TEXT NOT NULL,
            icon TEXT DEFAULT 'bi-share-fill',
            created_at TEXT NOT NULL
        )"""
    )
    
    # Accounts table with full WeChat support
    conn.execute(
        """CREATE TABLE IF NOT EXISTS mxh_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_name TEXT NOT NULL,
            group_id INTEGER NOT NULL,
            platform TEXT NOT NULL,
            username TEXT NOT NULL,
            phone TEXT,
            url TEXT,
            login_username TEXT,
            login_password TEXT,
            created_at TEXT NOT NULL,
            
            -- WeChat Primary Account Fields
            wechat_created_day INTEGER DEFAULT 1,
            wechat_created_month INTEGER DEFAULT 1,
            wechat_created_year INTEGER DEFAULT 2024,
            wechat_scan_create INTEGER DEFAULT 0,
            wechat_scan_rescue INTEGER DEFAULT 0,
            wechat_status TEXT DEFAULT 'available',
            muted_until TEXT,
            status TEXT DEFAULT 'active',
            die_date TEXT,
            wechat_scan_count INTEGER DEFAULT 0,
            wechat_last_scan_date TEXT,
            rescue_count INTEGER DEFAULT 0,
            rescue_success_count INTEGER DEFAULT 0,
            
            -- WeChat Secondary Account Fields
            secondary_card_name TEXT,
            secondary_username TEXT,
            secondary_phone TEXT,
            secondary_url TEXT,
            secondary_login_username TEXT,
            secondary_login_password TEXT,
            secondary_wechat_created_day INTEGER,
            secondary_wechat_created_month INTEGER,
            secondary_wechat_created_year INTEGER,
            secondary_wechat_status TEXT,
            secondary_muted_until TEXT,
            secondary_status TEXT DEFAULT 'active',
            secondary_die_date TEXT,
            secondary_wechat_scan_count INTEGER DEFAULT 0,
            secondary_wechat_last_scan_date TEXT,
            secondary_rescue_count INTEGER DEFAULT 0,
            secondary_rescue_success_count INTEGER DEFAULT 0,
            
            FOREIGN KEY (group_id) REFERENCES mxh_groups (id)
        )"""
    )
    
    # Migration: Add email_reset_date column for Telegram accounts
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(mxh_accounts)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'email_reset_date' not in columns:
            conn.execute("ALTER TABLE mxh_accounts ADD COLUMN email_reset_date TEXT")
            print("✅ Added email_reset_date column to mxh_accounts table")
        
        if 'notice' not in columns:
            conn.execute("ALTER TABLE mxh_accounts ADD COLUMN notice TEXT")
            print("✅ Added notice column to mxh_accounts table")
    except Exception as e:
        print(f"Migration note: {e}")
    
    conn.commit()
    conn.close()
    print("Database initialized successfully.")
