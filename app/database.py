import os
import sqlite3

APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
DATA_DIR = os.path.join(APP_ROOT, "data")
DATABASE_PATH = os.path.join(DATA_DIR, "Data.db")

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initializes all database tables and performs necessary schema migrations."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    conn = get_db_connection()
    
    # --- Perform MXH Schema Migration FIRST ---
    _migrate_mxh_schema(conn)

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

    # MXH Groups Table
    conn.execute(
        """CREATE TABLE IF NOT EXISTS mxh_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            color TEXT NOT NULL,
            icon TEXT DEFAULT 'bi-share-fill',
            created_at TEXT NOT NULL
        )"""
    )
    
    # --- NEW Simplified MXH Accounts (Card) Table ---
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

    # --- NEW Sub-Accounts Table ---
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
            
            -- WeChat Specific Fields
            wechat_created_day INTEGER,
            wechat_created_month INTEGER,
            wechat_created_year INTEGER,
            wechat_status TEXT DEFAULT 'available',
            muted_until TEXT,
            status TEXT DEFAULT 'active',
            die_date TEXT,
            wechat_scan_count INTEGER DEFAULT 0,
            wechat_last_scan_date TEXT,
            rescue_count INTEGER DEFAULT 0,
            rescue_success_count INTEGER DEFAULT 0,
            
            -- Other specific fields
            email_reset_date TEXT,
            notice TEXT,
            
            FOREIGN KEY (card_id) REFERENCES mxh_accounts (id) ON DELETE CASCADE
        )"""
    )

    conn.commit()
    conn.close()
    print("Database initialization and migration check complete.")

def _migrate_mxh_schema(conn):
    """
    Handles the one-time migration from the old single-table mxh_accounts
    to the new two-table (mxh_accounts, mxh_sub_accounts) structure.
    """
    cursor = conn.cursor()
    
    # Check if migration is needed by looking for a column from the OLD schema
    try:
        cursor.execute("PRAGMA table_info(mxh_accounts)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'secondary_username' not in columns:
            print("✅ Database already uses new schema or is fresh. No migration needed.")
            return
    except sqlite3.OperationalError:
        # Table mxh_accounts might not even exist yet, which is fine.
        print("✅ Fresh database. No migration needed.")
        return

    print("🔄 Old schema detected. Starting migration to new two-table structure...")
    
    try:
        # 1. Rename old table
        cursor.execute("ALTER TABLE mxh_accounts RENAME TO mxh_accounts_old")
        print("   - Step 1/5: Renamed old table to mxh_accounts_old.")

        # 2. Create the new (simplified) mxh_accounts and mxh_sub_accounts tables
        # Use the main init function's logic to create them fresh
        cursor.execute(
            """CREATE TABLE mxh_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT, card_name TEXT NOT NULL, group_id INTEGER NOT NULL,
                platform TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT,
                FOREIGN KEY (group_id) REFERENCES mxh_groups (id)
            )"""
        )
        cursor.execute(
            """CREATE TABLE mxh_sub_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT, card_id INTEGER NOT NULL, is_primary BOOLEAN DEFAULT 0,
                account_name TEXT, username TEXT, phone TEXT, url TEXT, login_username TEXT, login_password TEXT,
                created_at TEXT, updated_at TEXT, wechat_created_day INTEGER, wechat_created_month INTEGER,
                wechat_created_year INTEGER, wechat_status TEXT, muted_until TEXT, status TEXT, die_date TEXT,
                wechat_scan_count INTEGER, wechat_last_scan_date TEXT, rescue_count INTEGER, rescue_success_count INTEGER,
                email_reset_date TEXT, notice TEXT,
                FOREIGN KEY (card_id) REFERENCES mxh_accounts (id) ON DELETE CASCADE
            )"""
        )
        print("   - Step 2/5: Created new mxh_accounts and mxh_sub_accounts tables.")

        # 3. Transfer data
        cursor.execute("SELECT * FROM mxh_accounts_old")
        old_accounts = cursor.fetchall()
        
        for old_account in old_accounts:
            old_dict = dict(old_account)
            
            # Insert into new simplified mxh_accounts (the card)
            cursor.execute(
                "INSERT INTO mxh_accounts (id, card_name, group_id, platform, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (old_dict['id'], old_dict['card_name'], old_dict['group_id'], old_dict['platform'], old_dict['created_at'], old_dict.get('updated_at'))
            )
            card_id = old_dict['id']
            
            # Insert PRIMARY sub-account from old main fields
            cursor.execute(
                """INSERT INTO mxh_sub_accounts (card_id, is_primary, account_name, username, phone, url, login_username, login_password, created_at, updated_at, wechat_created_day, wechat_created_month, wechat_created_year, wechat_status, muted_until, status, die_date, wechat_scan_count, wechat_last_scan_date, rescue_count, rescue_success_count, notice)
                   VALUES (?, 1, 'Tài khoản chính', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (card_id, old_dict['username'], old_dict.get('phone'), old_dict.get('url'), old_dict.get('login_username'), old_dict.get('login_password'), old_dict['created_at'], old_dict.get('updated_at'), old_dict.get('wechat_created_day'), old_dict.get('wechat_created_month'), old_dict.get('wechat_created_year'), old_dict.get('wechat_status'), old_dict.get('muted_until'), old_dict.get('status'), old_dict.get('die_date'), old_dict.get('wechat_scan_count'), old_dict.get('wechat_last_scan_date'), old_dict.get('rescue_count'), old_dict.get('rescue_success_count'), old_dict.get('notice'))
            )
            
            # Insert SECONDARY sub-account if it exists
            if old_dict.get('secondary_username'):
                cursor.execute(
                    """INSERT INTO mxh_sub_accounts (card_id, is_primary, account_name, username, phone, url, login_username, login_password, created_at, updated_at, wechat_created_day, wechat_created_month, wechat_created_year, wechat_status, muted_until, status, die_date, wechat_scan_count, wechat_last_scan_date, rescue_count, rescue_success_count, notice)
                       VALUES (?, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (card_id, old_dict.get('secondary_card_name', 'Tài khoản phụ'), old_dict['secondary_username'], old_dict.get('secondary_phone'), old_dict.get('secondary_url'), old_dict.get('secondary_login_username'), old_dict.get('secondary_login_password'), old_dict['created_at'], old_dict.get('updated_at'), old_dict.get('secondary_wechat_created_day'), old_dict.get('secondary_wechat_created_month'), old_dict.get('secondary_wechat_created_year'), old_dict.get('secondary_wechat_status'), old_dict.get('secondary_muted_until'), old_dict.get('secondary_status'), old_dict.get('secondary_die_date'), old_dict.get('secondary_wechat_scan_count'), old_dict.get('secondary_wechat_last_scan_date'), old_dict.get('secondary_rescue_count'), old_dict.get('secondary_rescue_success_count'), None) # Notice field is not for secondary
                )

        print(f"   - Step 3/5: Migrated {len(old_accounts)} cards and their sub-accounts.")

        # 4. Drop the old table
        cursor.execute("DROP TABLE mxh_accounts_old")
        print("   - Step 4/5: Dropped old table.")
        
        # 5. Commit changes
        conn.commit()
        print("   - Step 5/5: Migration committed successfully!")

    except Exception as e:
        print(f"❌ MIGRATION FAILED: {e}. Rolling back changes.")
        conn.rollback()
        # Attempt to restore the original table if it exists
        try:
            cursor.execute("ALTER TABLE mxh_accounts_old RENAME TO mxh_accounts")
            conn.commit()
            print("   - Rollback: Restored original table.")
        except:
            print("   - Rollback: Could not restore original table. Manual intervention may be required.")
        raise e # Re-raise the exception to halt initialization if migration fails