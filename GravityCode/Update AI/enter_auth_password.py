import subprocess, time, re

adb = r'D:\LDPlayer\LDPlayer9\adb.exe'
serial = '127.0.0.1:5555'

def adb_cmd(*args):
    cmd = [adb, '-s', serial] + list(args)
    return subprocess.run(cmd, capture_output=True, text=True)

import os

pass_file = os.path.join('AdminData', 'Pass.txt') if os.path.exists(os.path.join('AdminData', 'Pass.txt')) else 'Pass.txt'
with open(pass_file, encoding='utf-8') as f:
    passwords = [l.strip() for l in f if l.strip()]

print(f"Loaded passwords from Pass.txt: {passwords}")

# Check current UI
adb_cmd('shell', 'uiautomator dump /sdcard/auth.xml')
xml = adb_cmd('shell', 'cat /sdcard/auth.xml').stdout

if 'Xác minh' not in xml and 'Nhập mật khẩu' not in xml:
    print("Not on verification screen!")
    print(xml[:500])
    exit(0)

print("Found verification screen! Processing...")

for pwd in passwords:
    print(f"Trying password: {pwd}")
    # Tap password EditText (center around 480, 345)
    adb_cmd('shell', 'input tap 480 345')
    time.sleep(0.5)
    
    # Select all / clear
    adb_cmd('shell', 'input keyevent 29 --meta 113') # Ctrl+A
    adb_cmd('shell', 'input keyevent 67') # Backspace
    time.sleep(0.3)
    
    # Enter password
    adb_cmd('shell', f'input text "{pwd}"')
    time.sleep(0.5)
    
    # Tap "Nhớ thông tin đăng nhập" checkbox (bounds [264,390][696,422] -> tap 280, 405)
    adb_cmd('shell', 'input tap 280 405')
    time.sleep(0.3)
    
    # Tap "Xác minh" button (bounds [264,490][696,526] -> tap 480, 508)
    adb_cmd('shell', 'input tap 480 508')
    print("Tapped Xác minh! Waiting 5s...")
    time.sleep(5)
    
    # Dump UI to check outcome
    adb_cmd('shell', 'uiautomator dump /sdcard/result.xml')
    res_xml = adb_cmd('shell', 'cat /sdcard/result.xml').stdout
    
    texts = re.findall(r'text="([^"]*)"', res_xml)
    print("Texts after submit:", [t for t in texts if t][:10])
    
    if any(k in res_xml.lower() for k in ['sai mật khẩu', 'incorrect password', 'không đúng']):
        print(f"Password '{pwd}' was INCORRECT! Trying next...")
        continue
    else:
        print(f"Password '{pwd}' ACCEPTED or screen moved forward!")
        break
