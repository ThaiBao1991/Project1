import subprocess, time

adb = r'D:\LDPlayer\LDPlayer9\adb.exe'
serial = '127.0.0.1:5555'

def run_adb(*args):
    cmd = [adb, '-s', serial] + list(args)
    return subprocess.run(cmd, capture_output=True, text=True)

print("Setting com.android.vending to svendn03@gmail.com...")
run_adb('shell', 'am force-stop com.android.vending')
sql = "UPDATE appstate SET account='svendn03@gmail.com' WHERE package_name='com.android.vending'; PRAGMA wal_checkpoint(TRUNCATE);"
p = subprocess.Popen([adb, '-s', serial, 'shell', 'sqlite3 /data/data/com.android.vending/databases/localappstate.db'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
p.communicate(input=sql)

print("Starting Google Play with svendn03...")
run_adb('shell', 'am start -n com.android.vending/com.google.android.finsky.activities.MainActivity --es authAccount svendn03@gmail.com')
time.sleep(3)

print("Opening payment methods...")
run_adb('shell', 'am start -a android.intent.action.VIEW -d https://play.google.com/store/paymentmethods')
time.sleep(3)

run_adb('shell', 'screencap -p /sdcard/svendn03_pm_real.png')
run_adb('pull', '/sdcard/svendn03_pm_real.png', 'svendn03_pm_real.png')
print("Captured svendn03_pm_real.png")
