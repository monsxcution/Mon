import sqlite3
import json
import os
from datetime import datetime, timezone

# Path to database
APP_ROOT = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(APP_ROOT, "data")
DATABASE_PATH = os.path.join(DATA_DIR, "Data.db")

print(f"Updating database: {DATABASE_PATH}\n")

conn = sqlite3.connect(DATABASE_PATH)
cursor = conn.cursor()

# Get all accounts with notice data
cursor.execute("SELECT id, card_name, notice FROM mxh_accounts WHERE notice IS NOT NULL AND notice != ''")
accounts = cursor.fetchall()

print(f"Found {len(accounts)} accounts with notice data\n")

updated_count = 0

for acc_id, card_name, notice_str in accounts:
    try:
        notice_obj = json.loads(notice_str)
        start_at = notice_obj.get('start_at')
        
        if start_at:
            print(f"Account {acc_id} ({card_name}):")
            print(f"  Old: {start_at}")
            
            # Convert to new format
            try:
                dt = datetime.fromisoformat(start_at.replace('Z', '+00:00'))
                new_start_at = dt.astimezone(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
                
                notice_obj['start_at'] = new_start_at
                new_notice_str = json.dumps(notice_obj)
                
                # Update in database
                cursor.execute("UPDATE mxh_accounts SET notice = ? WHERE id = ?", (new_notice_str, acc_id))
                
                print(f"  New: {new_start_at}")
                print(f"  ✅ Updated!\n")
                updated_count += 1
            except Exception as e:
                print(f"  ❌ Error converting: {e}\n")
        else:
            print(f"Account {acc_id} ({card_name}): No start_at (skipped)\n")
            
    except Exception as e:
        print(f"Account {acc_id} ({card_name}): Error parsing JSON: {e}\n")

conn.commit()
conn.close()

print(f"\n{'='*60}")
print(f"✅ Migration complete! Updated {updated_count} accounts")
print(f"{'='*60}")
