import sqlite3

conn = sqlite3.connect('data/Data.db')
cursor = conn.cursor()

# Check table columns
cursor.execute('PRAGMA table_info(mxh_accounts)')
cols = cursor.fetchall()

print('mxh_accounts table columns:')
for col in cols:
    print(f'  {col[1]} ({col[2]})')

# Check if email_reset_date exists
has_column = any(col[1] == 'email_reset_date' for col in cols)
print(f'\n✅ email_reset_date column exists: {has_column}')

# If column exists, check Telegram account
if has_column:
    cursor.execute('SELECT id, card_name, platform, email_reset_date FROM mxh_accounts WHERE platform = "telegram"')
    telegram_accounts = cursor.fetchall()
    print(f'\nTelegram accounts:')
    for acc in telegram_accounts:
        print(f'  ID: {acc[0]}, Name: {acc[1]}, email_reset_date: {acc[3]}')

conn.close()
