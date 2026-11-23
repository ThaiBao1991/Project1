import subprocess, sqlite3

adb = r'D:\LDPlayer\LDPlayer9\adb.exe'
serial = '127.0.0.1:5555'
subprocess.run([adb, '-s', serial, 'shell', 'su 0 cp /data/data/com.android.vending/databases/localappstate.db* /data/local/tmp/ && su 0 chmod 666 /data/local/tmp/localappstate.db*'], stdout=subprocess.DEVNULL)
subprocess.run([adb, '-s', serial, 'pull', '/data/local/tmp/localappstate.db', 'temp_local.db'], stdout=subprocess.DEVNULL)
subprocess.run([adb, '-s', serial, 'pull', '/data/local/tmp/localappstate.db-wal', 'temp_local.db-wal'], stdout=subprocess.DEVNULL)

con = sqlite3.connect('temp_local.db')
cur = con.cursor()
for table in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
    tname = table[0]
    print('Table:', tname)
    try:
        cols = [c[1] for c in cur.execute(f"PRAGMA table_info({tname})").fetchall()]
        print('  Cols:', cols)
        rows = cur.execute(f"SELECT * FROM {tname} WHERE package_name LIKE '%subscriptions%'").fetchall()
        for r in rows:
            print('  ROW:', r)
    except Exception as e:
        print(' ', e)
con.close()
