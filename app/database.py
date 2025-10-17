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

    # Main cards table (simplified to only contain card identification)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS mxh_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_name TEXT NOT NULL,
            group_id INTEGER NOT NULL,
            platform TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            
            FOREIGN KEY (group_id) REFERENCES mxh_groups (id)
        )"""
    )

    # Sub-accounts table (contains all account details)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS mxh_sub_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id INTEGER NOT NULL,
            is_primary BOOLEAN DEFAULT 0,
            account_name TEXT DEFAULT 'Tài khoản phụ',
            username TEXT,
            phone TEXT,
            url TEXT,
            login_username TEXT,
            login_password TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            
            -- WeChat Account Fields
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
            
            -- Telegram specific fields
            email_reset_date TEXT,
            notice TEXT,
            
            FOREIGN KEY (card_id) REFERENCES mxh_accounts (id) ON DELETE CASCADE
        )"""
    )

    # Migration: Handle schema changes from old structure to new structure
    try:
        cursor = conn.cursor()
        
        # Check if mxh_sub_accounts table exists (indicates new schema)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='mxh_sub_accounts'")
        sub_accounts_exists = cursor.fetchone() is not None
        
        if not sub_accounts_exists:
            print("🔄 Migrating from old schema to new schema...")
            
            # Create the new sub_accounts table
            conn.execute(
                """CREATE TABLE mxh_sub_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    card_id INTEGER NOT NULL,
                    is_primary BOOLEAN DEFAULT 0,
                    account_name TEXT DEFAULT 'Tài khoản phụ',
                    username TEXT,
                    phone TEXT,
                    url TEXT,
                    login_username TEXT,
                    login_password TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    
                    -- WeChat Account Fields
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
                    
                    -- Telegram specific fields
                    email_reset_date TEXT,
                    notice TEXT,
                    
                    FOREIGN KEY (card_id) REFERENCES mxh_accounts (id) ON DELETE CASCADE
                )"""
            )
            
            # Migrate existing data from old mxh_accounts to new structure
            cursor.execute("SELECT * FROM mxh_accounts")
            old_accounts = cursor.fetchall()
            
            for account in old_accounts:
                # Create primary sub-account with all the old data
                conn.execute(
                    """INSERT INTO mxh_sub_accounts (
                        card_id, is_primary, account_name, username, phone, url, 
                        login_username, login_password, created_at, updated_at,
                        wechat_created_day, wechat_created_month, wechat_created_year,
                        wechat_scan_create, wechat_scan_rescue, wechat_status,
                        muted_until, status, die_date, wechat_scan_count,
                        wechat_last_scan_date, rescue_count, rescue_success_count,
                        email_reset_date, notice
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        account['id'], 1, 'Tài khoản chính', account.get('username'), 
                        account.get('phone'), account.get('url'), account.get('login_username'),
                        account.get('login_password'), account.get('created_at'), account.get('updated_at'),
                        account.get('wechat_created_day', 1), account.get('wechat_created_month', 1),
                        account.get('wechat_created_year', 2024), account.get('wechat_scan_create', 0),
                        account.get('wechat_scan_rescue', 0), account.get('wechat_status', 'available'),
                        account.get('muted_until'), account.get('status', 'active'), account.get('die_date'),
                        account.get('wechat_scan_count', 0), account.get('wechat_last_scan_date'),
                        account.get('rescue_count', 0), account.get('rescue_success_count', 0),
                        account.get('email_reset_date'), account.get('notice')
                    )
                )
            
            # Now we need to recreate the mxh_accounts table with the new simplified structure
            # First, backup the old table
            conn.execute("ALTER TABLE mxh_accounts RENAME TO mxh_accounts_old")
            
            # Create new simplified mxh_accounts table
            conn.execute(
                """CREATE TABLE mxh_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    card_name TEXT NOT NULL,
                    group_id INTEGER NOT NULL,
                    platform TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    
                    FOREIGN KEY (group_id) REFERENCES mxh_groups (id)
                )"""
            )
            
            # Copy only the essential fields from old table to new table
            conn.execute(
                """INSERT INTO mxh_accounts (id, card_name, group_id, platform, created_at, updated_at)
                   SELECT id, card_name, group_id, platform, created_at, updated_at 
                   FROM mxh_accounts_old"""
            )
            
            # Drop the old table
            conn.execute("DROP TABLE mxh_accounts_old")
            
            print("✅ Successfully migrated to new schema")
        else:
            print("✅ Database already uses new schema")
            
    except Exception as e:
        print(f"Migration error: {e}")

    conn.commit()
    conn.close()
    print("Database initialized successfully.")
