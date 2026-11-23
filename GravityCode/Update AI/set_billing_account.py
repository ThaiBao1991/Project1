import subprocess, sqlite3

adb = r'D:\LDPlayer\LDPlayer9\adb.exe'
serial = '127.0.0.1:5555'

def set_play_billing_account(email: str):
    print(f"Switching Google Play appstate account to: {email}")
    # Stop apps first
    subprocess.run([adb, '-s', serial, 'shell', 'am force-stop com.android.vending && am force-stop com.google.android.apps.subscriptions.red'])
    
    # Check and checkpoint WAL
    sql = f"UPDATE appstate SET account='{email}' WHERE package_name='com.google.android.apps.subscriptions.red'; PRAGMA wal_checkpoint(TRUNCATE);"
    p = subprocess.Popen([adb, '-s', serial, 'shell', 'sqlite3 /data/data/com.android.vending/databases/localappstate.db'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = p.communicate(input=sql)
    print("Output:", out, err)
    
    # Verify
    p2 = subprocess.Popen([adb, '-s', serial, 'shell', 'sqlite3 /data/data/com.android.vending/databases/localappstate.db "SELECT package_name, account FROM appstate WHERE package_name=\'com.google.android.apps.subscriptions.red\';"'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out2, err2 = p2.communicate()
    print("Verification:", out2.strip())

if __name__ == "__main__":
    set_play_billing_account("gamesvendn@gmail.com")
