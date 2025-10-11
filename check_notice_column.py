import sqlite3
import os

# Path to database
APP_ROOT = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(APP_ROOT, "data")
DATABASE_PATH = os.path.join(DATA_DIR, "Data.db")

print(f"Checking database: {DATABASE_PATH}")

conn = sqlite3.connect(DATABASE_PATH)
cursor = conn.cursor()

# Check if notice column exists
cursor.execute("PRAGMA table_info(mxh_accounts)")
columns = cursor.fetchall()

print("\nAll columns in mxh_accounts:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

notice_exists = any(col[1] == 'notice' for col in columns)

if notice_exists:
    print("\n✅ Column 'notice' EXISTS")
    
    # Check if there are any accounts with notice set
    cursor.execute("SELECT id, card_name, notice FROM mxh_accounts WHERE notice IS NOT NULL AND notice != ''")
    accounts_with_notice = cursor.fetchall()
    
    if accounts_with_notice:
        print(f"\n📋 Found {len(accounts_with_notice)} accounts with notice data:")
        for acc in accounts_with_notice:
            print(f"  - Account {acc[0]} ({acc[1]}): {acc[2]}")
    else:
        print("\n📋 No accounts have notice data yet")
else:
    print("\n❌ Column 'notice' DOES NOT EXIST - Need to run migration!")

conn.close()
