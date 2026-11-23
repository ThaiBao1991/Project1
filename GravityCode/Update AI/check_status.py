import subprocess, sqlite3, json, datetime

adb = r'D:\LDPlayer\LDPlayer9\adb.exe'
subprocess.run([adb, 'shell', 'cp /data/data/com.android.vending/databases/library.db* /data/local/tmp/ && chmod 666 /data/local/tmp/library.db*'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run([adb, 'pull', '/data/local/tmp/library.db', 'check2_lib.db'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run([adb, 'pull', '/data/local/tmp/library.db-wal', 'check2_lib.db-wal'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

con = sqlite3.connect('check2_lib.db')
cur = con.cursor()
rows = cur.execute("select account, doc_id, subs_valid_until_time, inapp_purchase_data from ownership where doc_id like '%subs_variant%'").fetchall()
for acc, doc, valid, data in rows:
    exp = ''
    if valid:
        try:
            exp = datetime.datetime.fromtimestamp(int(valid)/1000).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            pass
    order_id = ''
    if data:
        try:
            order_id = json.loads(data).get('orderId', '')
        except Exception:
            pass
    print(f'Account: {acc} | Expiry: {valid} ({exp}) | OrderId: {order_id}')
con.close()
