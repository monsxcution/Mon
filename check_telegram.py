import sqlite3

conn = sqlite3.connect('data/Data.db')
cursor = conn.cursor()

# Check all platforms
cursor.execute('SELECT id, card_name, platform, username FROM mxh_accounts')
rows = cursor.fetchall()

print(f"Total accounts: {len(rows)}")
print("\nAll platforms:")
platforms = {}
for row in rows:
    platform = row[2]
    if platform not in platforms:
        platforms[platform] = []
    platforms[platform].append(row)

for platform, accounts in platforms.items():
    print(f"\n{platform.upper()}: {len(accounts)} cards")
    for acc in accounts[:3]:  # Show first 3
        print(f"  - ID: {acc[0]}, Name: {acc[1]}, User: {acc[3]}")

conn.close()
