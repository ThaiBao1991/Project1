import sqlite3, json, os
from pathlib import Path
roaming = Path(os.environ.get('APPDATA', '')) / 'Antigravity IDE' / 'User'
db = roaming / 'globalStorage' / 'state.vscdb'
conn = sqlite3.connect(db)
c = conn.cursor()
c.execute("SELECT value FROM ItemTable WHERE key='Davissss2.antigravity-account'")
row = c.fetchone()
if row:
    data = json.loads(row[0])
    accs = data.get('antigravity.accounts.list', [])
    if accs: 
        print("Keys:", list(accs[0].keys()))
        print("Sample:", json.dumps(accs[0], indent=2))
