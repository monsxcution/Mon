import sqlite3
from datetime import datetime, timezone

DB_PATH = "data/Data.db"
account_id = 5

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

# Before
before = conn.execute("SELECT id, username, phone, status, rescue_count FROM mxh_accounts WHERE id = ?", (account_id,)).fetchone()
print(f"BEFORE: user={before['username']}, phone={before['phone']}, status={before['status']}, rescue={before['rescue_count']}")

# UPDATE
now_iso = datetime.now(timezone.utc).astimezone().isoformat()
cursor = conn.execute("""
    UPDATE mxh_accounts
    SET username = '.',
        phone = '.',
        status = 'active',
        die_date = NULL,
        wechat_scan_count = 0,
        wechat_last_scan_date = NULL,
        rescue_count = 0,
        rescue_success_count = 0,
        notice = NULL,
        muted_until = NULL,
        updated_at = ?
    WHERE id = ?
""", (now_iso, account_id))

print(f"UPDATE affected {cursor.rowcount} rows")
conn.commit()

# After
after = conn.execute("SELECT id, username, phone, status, rescue_count FROM mxh_accounts WHERE id = ?", (account_id,)).fetchone()
print(f"AFTER:  user={after['username']}, phone={after['phone']}, status={after['status']}, rescue={after['rescue_count']}")

conn.close()
print("✅ Test completed!")
