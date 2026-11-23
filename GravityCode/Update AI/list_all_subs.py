import sqlite3, json, datetime

con = sqlite3.connect('check2_lib.db')
cur = con.cursor()
print('=== ACCOUNTS WITH SUBSCRIPTIONS IN LIBRARY.DB ===')
for acc, doc, valid, data in cur.execute("select account, doc_id, subs_valid_until_time, inapp_purchase_data from ownership where doc_id like '%subs%'").fetchall():
    exp = ''
    if valid:
        try: exp = datetime.datetime.fromtimestamp(int(valid)/1000).strftime('%Y-%m-%d %H:%M:%S')
        except Exception: pass
    oid = ''
    if data:
        try: oid = json.loads(data).get('orderId', '')
        except Exception: pass
    print(f'{acc} | {doc} | {exp} | {oid}')
con.close()
