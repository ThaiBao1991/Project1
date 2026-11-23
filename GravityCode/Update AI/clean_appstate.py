import subprocess

adb = r'D:\LDPlayer\LDPlayer9\adb.exe'
serial = '127.0.0.1:5555'

sql = "DELETE FROM appstate WHERE package_name='com.android.vending'; PRAGMA wal_checkpoint(TRUNCATE);"
p = subprocess.Popen([adb, '-s', serial, 'shell', 'sqlite3 /data/data/com.android.vending/databases/localappstate.db'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
out, err = p.communicate(input=sql)
print("Output:", out, err)
