import json
import sqlite3
import os

# --- CONFIGURATION ---
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(APP_ROOT, "data")
DATABASE_PATH = os.path.join(DATA_DIR, "Data.db")
BACKUP_FILE_PATH = os.path.join(APP_ROOT, "data_backup.json")

def import_data():
    """
    Reads data from data_backup.json and inserts it into the new
    mxh_accounts and mxh_sub_accounts tables in Data.db.
    """
    # 1. Check if backup file exists
    if not os.path.exists(BACKUP_FILE_PATH):
        print(f"ERROR: Khong tim thay file backup tai '{BACKUP_FILE_PATH}'.")
        return

    # 2. Connect to the database and create tables
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        print("SUCCESS: Da ket noi toi database.")
        
        # Create tables first
        cursor.execute("CREATE TABLE IF NOT EXISTS notes (id TEXT PRIMARY KEY, title_html TEXT, content_html TEXT, due_time TEXT, status TEXT, modified_at TEXT, is_marked INTEGER DEFAULT 0)")
        cursor.execute("CREATE TABLE IF NOT EXISTS mxh_groups (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, color TEXT NOT NULL, icon TEXT, created_at TEXT NOT NULL)")
        cursor.execute("CREATE TABLE IF NOT EXISTS mxh_cards (id INTEGER PRIMARY KEY AUTOINCREMENT, card_name TEXT NOT NULL, group_id INTEGER NOT NULL, platform TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT, FOREIGN KEY (group_id) REFERENCES mxh_groups(id) ON DELETE CASCADE)")
        cursor.execute("CREATE TABLE IF NOT EXISTS mxh_accounts (id INTEGER PRIMARY KEY AUTOINCREMENT, card_id INTEGER NOT NULL, is_primary BOOLEAN DEFAULT 0, account_name TEXT DEFAULT 'Tài khoản phụ', username TEXT, phone TEXT, url TEXT, login_username TEXT, login_password TEXT, created_at TEXT NOT NULL, updated_at TEXT, wechat_created_day INTEGER, wechat_created_month INTEGER, wechat_created_year INTEGER, wechat_status TEXT DEFAULT 'available', muted_until TEXT, status TEXT DEFAULT 'active', die_date TEXT, wechat_scan_count INTEGER DEFAULT 0, wechat_last_scan_date TEXT, rescue_count INTEGER DEFAULT 0, rescue_success_count INTEGER DEFAULT 0, email_reset_date TEXT, notice TEXT, FOREIGN KEY (card_id) REFERENCES mxh_cards(id) ON DELETE CASCADE)")
        
        # Create default WeChat group
        cursor.execute("INSERT OR IGNORE INTO mxh_groups (id, name, color, icon, created_at) VALUES (4, 'WeChat', '#25D366', 'bi-wechat', '2025-10-18T06:00:00')")
        
        conn.commit()
        print("SUCCESS: Da tao cac bang va group mac dinh.")
        
    except Exception as e:
        print(f"ERROR: Khong the ket noi toi database: {e}")
        return

    # 3. Read data from JSON backup
    with open(BACKUP_FILE_PATH, 'r', encoding='utf-8') as f:
        backup_data = json.load(f)
    
    cards_to_import = backup_data.get('cards', [])
    sub_accounts_to_import = backup_data.get('sub_accounts', [])
    
    if not cards_to_import or not sub_accounts_to_import:
        print("ERROR: File backup khong chua du lieu 'cards' hoac 'sub_accounts'.")
        conn.close()
        return

    print(f"INFO: Tim thay {len(cards_to_import)} cards va {len(sub_accounts_to_import)} sub-accounts trong file backup.")

    try:
        # 4. Insert Cards into mxh_cards
        card_count = 0
        for card in cards_to_import:
            cursor.execute(
                "INSERT OR IGNORE INTO mxh_cards (id, card_name, group_id, platform, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (card['id'], card['card_name'], card['group_id'], card['platform'], card['created_at'], card.get('updated_at'))
            )
            if cursor.rowcount > 0:
                card_count += 1
        
        print(f"   -> Da import {card_count} cards vao bang mxh_cards.")

        # 5. Insert Accounts into mxh_accounts
        account_count = 0
        for sub in sub_accounts_to_import:
            # Using INSERT OR IGNORE to prevent errors if an account with the same ID already exists
            cursor.execute(
                """INSERT OR IGNORE INTO mxh_accounts (id, card_id, is_primary, account_name, username, phone, url, login_username, login_password, created_at, updated_at, wechat_created_day, wechat_created_month, wechat_created_year, wechat_status, muted_until, status, die_date, wechat_scan_count, wechat_last_scan_date, rescue_count, rescue_success_count, notice) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    sub.get('id'), sub.get('card_id'), sub.get('is_primary'), sub.get('account_name'), sub.get('username'), 
                    sub.get('phone'), sub.get('url'), sub.get('login_username'), sub.get('login_password'), 
                    sub.get('created_at'), sub.get('updated_at'), sub.get('wechat_created_day'), sub.get('wechat_created_month'), 
                    sub.get('wechat_created_year'), sub.get('wechat_status'), sub.get('muted_until'), sub.get('status'), 
                    sub.get('die_date'), sub.get('wechat_scan_count'), sub.get('wechat_last_scan_date'), 
                    sub.get('rescue_count'), sub.get('rescue_success_count'), sub.get('notice')
                )
            )
            if cursor.rowcount > 0:
                account_count += 1

        print(f"   -> Da import {account_count} accounts vao bang mxh_accounts.")

        # 6. Commit changes and close connection
        conn.commit()
        print("SUCCESS: Hoan tat! Du lieu da duoc import thanh cong.")

    except Exception as e:
        print(f"ERROR: Loi trong qua trinh import: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("\nBat dau qua trinh import...")
    print("NOTE: Khong xoa database hien tai, chi them du lieu moi.")
    import_data()
    print("\n--- HUONG DAN ---")
    print("1. Qua trinh import da xong.")
    print("2. Bay gio ban co the chay lai ung dung bang file 'run.pyw'.")
    print("3. Du lieu cu cua ban se duoc hien thi tren giao dien.")
