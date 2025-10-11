import requests

r = requests.get('http://localhost:5001/mxh/api/accounts')
data = r.json()

acc_with_notice = [a for a in data if a.get('notice') and a['notice'].get('enabled')]

print(f'Total accounts: {len(data)}')
print(f'Accounts with notice enabled: {len(acc_with_notice)}')

for a in acc_with_notice[:5]:
    print(f"ID {a['id']} ({a.get('card_name')}): {a['notice']}")

# Check specific accounts from database query
for id in [22, 23, 24]:
    acc = next((a for a in data if a['id'] == id), None)
    if acc:
        print(f"\nAccount {id} notice: {acc.get('notice')}")
