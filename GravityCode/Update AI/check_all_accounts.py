import subprocess, sqlite3, json, datetime

adb = r'D:\LDPlayer\LDPlayer9\adb.exe'
subprocess.run([adb, 'connect', '127.0.0.1:5555'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
device_cmd = [adb, '-s', '127.0.0.1:5555']

# Get all accounts on device
out = subprocess.check_output(device_cmd + ['shell', 'dumpsys account'], text=True, errors='ignore')
accounts = []
for line in out.splitlines():
    if 'Account {' in line and 'type=com.google' in line:
        m = line.split('name=')[1].split(',')[0]
        accounts.append(m)

print(f"Total accounts on device: {len(accounts)}")
for a in accounts:
    print(" -", a)

# Pull latest library.db
subprocess.run(device_cmd + ['shell', 'su 0 cp /data/data/com.android.vending/databases/library.db* /data/local/tmp/ && su 0 chmod 666 /data/local/tmp/library.db*'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run(device_cmd + ['pull', '/data/local/tmp/library.db', 'status_lib.db'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run(device_cmd + ['pull', '/data/local/tmp/library.db-wal', 'status_lib.db-wal'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run(device_cmd + ['pull', '/data/local/tmp/library.db-shm', 'status_lib.db-shm'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

con = sqlite3.connect('status_lib.db')
cur = con.cursor()

print("\n=== SUBSCRIPTIONS IN GOOGLE PLAY DATABASE ===")
sub_records = {}
for acc, doc, valid, data in cur.execute("select account, doc_id, subs_valid_until_time, inapp_purchase_data from ownership where doc_id like '%subs_variant%'").fetchall():
    exp = ''
    if valid:
        try: exp = datetime.datetime.fromtimestamp(int(valid)/1000).strftime('%Y-%m-%d %H:%M:%S')
        except Exception: pass
    oid = ''
    if data:
        try: oid = json.loads(data).get('orderId', '')
        except Exception: pass
    sub_records[acc] = (exp, oid)
    print(f"[{acc}] Expiry: {exp} | Order: {oid}")

print("\n=== STATUS BY ACCOUNT ===")
for acc in accounts:
    if acc in sub_records:
        exp, oid = sub_records[acc]
        print(f"✅ {acc}: ĐÃ KÍCH HOẠT (Hạn: {exp}, OrderId: {oid})")
    else:
        print(f"⏳ {acc}: CHƯA KÍCH HOẠT")

con.close()
