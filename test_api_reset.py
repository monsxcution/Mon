import requests
import json

# Test reset API
account_id = 5
url = f"http://localhost:5000/mxh/api/accounts/{account_id}/reset"

print(f"Testing reset API for account {account_id}...")
print(f"URL: {url}\n")

try:
    response = requests.post(url, headers={'Content-Type': 'application/json'})
    print(f"Status Code: {response.status_code}")
    print(f"Response:\n{json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ API returned:")
        print(f"   Username: {data.get('username')}")
        print(f"   Phone: {data.get('phone')}")
        print(f"   Status: {data.get('status')}")
        print(f"   Rescue count: {data.get('rescue_count')}")
except Exception as e:
    print(f"❌ Error: {e}")

# Now check database directly
import sqlite3
conn = sqlite3.connect('data/Data.db')
conn.row_factory = sqlite3.Row
row = conn.execute('SELECT username, phone, status, rescue_count FROM mxh_accounts WHERE id = ?', (account_id,)).fetchone()
print(f"\n📊 Database actual values:")
print(f"   Username: {row['username']}")
print(f"   Phone: {row['phone']}")
print(f"   Status: {row['status']}")
print(f"   Rescue count: {row['rescue_count']}")
conn.close()
