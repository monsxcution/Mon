import sqlite3

conn = sqlite3.connect('data/Data.db')
conn.row_factory = sqlite3.Row

# Set test data
conn.execute('UPDATE mxh_accounts SET username=?, phone=?, rescue_count=? WHERE id=?', 
             ("Test User", "0123456789", 5, 5))
conn.commit()

row = conn.execute('SELECT username, phone, rescue_count FROM mxh_accounts WHERE id=5').fetchone()
print(f'✅ Set test data for account 5:')
print(f'   Username: {row["username"]}')
print(f'   Phone: {row["phone"]}')
print(f'   Rescue count: {row["rescue_count"]}')

conn.close()
