import subprocess, time

adb = r'D:\LDPlayer\LDPlayer9\adb.exe'
serial = '127.0.0.1:5555'
subprocess.run([adb, 'connect', serial], capture_output=True)

# wake up display
subprocess.run([adb, '-s', serial, 'shell', 'input keyevent KEYCODE_WAKEUP'])
subprocess.run([adb, '-s', serial, 'shell', 'wm dismiss-keyguard'])
subprocess.run([adb, '-s', serial, 'shell', 'input keyevent 82'])
subprocess.run([adb, '-s', serial, 'shell', 'input keyevent 3'])
time.sleep(1)

p = subprocess.run([adb, '-s', serial, 'shell', 'dumpsys window windows'], capture_output=True, text=True)
for line in p.stdout.splitlines():
    if 'mCurrentFocus' in line or 'mFocusedApp' in line:
        print(line.strip())

# try uiautomator dump again
d = subprocess.run([adb, '-s', serial, 'shell', 'uiautomator dump /sdcard/ui.xml'], capture_output=True, text=True)
print("dump:", d.stdout, d.stderr)
