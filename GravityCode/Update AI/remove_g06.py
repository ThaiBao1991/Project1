import subprocess, time, re

adb = r'D:\LDPlayer\LDPlayer9\adb.exe'
serial = '127.0.0.1:5555'

def adb_cmd(*args):
    return subprocess.run([adb, '-s', serial] + list(args), capture_output=True, text=True)

# Open Sync Settings
adb_cmd('shell', 'am start -a android.settings.SYNC_SETTINGS')
time.sleep(2)

# Dump UI to find gamesvendn06@gmail.com
adb_cmd('shell', 'uiautomator dump /sdcard/accs.xml')
xml = adb_cmd('shell', 'cat /sdcard/accs.xml').stdout

# Parse nodes
import xml.etree.ElementTree as ET
tree = ET.fromstring(xml)

target_btn = None
for node in tree.iter('node'):
    text = node.attrib.get('text', '')
    if 'gamesvendn06@gmail.com' in text:
        b = node.attrib.get('bounds')
        m = re.findall(r'\d+', b)
        if m:
            x = (int(m[0]) + int(m[2])) // 2
            y = (int(m[1]) + int(m[3])) // 2
            target_btn = (x, y)
            break

if not target_btn:
    print("Could not find gamesvendn06 in current view, scrolling down...")
    adb_cmd('shell', 'input swipe 500 400 500 150')
    time.sleep(1)
    adb_cmd('shell', 'uiautomator dump /sdcard/accs.xml')
    xml = adb_cmd('shell', 'cat /sdcard/accs.xml').stdout
    tree = ET.fromstring(xml)
    for node in tree.iter('node'):
        text = node.attrib.get('text', '')
        if 'gamesvendn06@gmail.com' in text:
            b = node.attrib.get('bounds')
            m = re.findall(r'\d+', b)
            if m:
                x = (int(m[0]) + int(m[2])) // 2
                y = (int(m[1]) + int(m[3])) // 2
                target_btn = (x, y)
                break

if target_btn:
    print(f"Clicking gamesvendn06 at {target_btn}")
    adb_cmd('shell', f'input tap {target_btn[0]} {target_btn[1]}')
    time.sleep(2)
    
    # In Account Detail, click "XÓA TÀI KHOẢN" / "REMOVE ACCOUNT"
    adb_cmd('shell', 'uiautomator dump /sdcard/detail.xml')
    d_xml = adb_cmd('shell', 'cat /sdcard/detail.xml').stdout
    d_tree = ET.fromstring(d_xml)
    del_btn = None
    for node in d_tree.iter('node'):
        text = node.attrib.get('text', '')
        if 'XÓA TÀI KHOẢN' in text.upper() or 'REMOVE ACCOUNT' in text.upper():
            b = node.attrib.get('bounds')
            m = re.findall(r'\d+', b)
            if m:
                x = (int(m[0]) + int(m[2])) // 2
                y = (int(m[1]) + int(m[3])) // 2
                del_btn = (x, y)
                break
    
    if del_btn:
        print(f"Clicking Remove Account at {del_btn}")
        adb_cmd('shell', f'input tap {del_btn[0]} {del_btn[1]}')
        time.sleep(1.5)
        
        # Confirm dialog: click "XÓA TÀI KHOẢN" / "REMOVE ACCOUNT"
        adb_cmd('shell', 'uiautomator dump /sdcard/confirm.xml')
        c_xml = adb_cmd('shell', 'cat /sdcard/confirm.xml').stdout
        c_tree = ET.fromstring(c_xml)
        for node in c_tree.iter('node'):
            text = node.attrib.get('text', '')
            cls = node.attrib.get('class', '')
            if 'Button' in cls and ('XÓA' in text.upper() or 'REMOVE' in text.upper()):
                b = node.attrib.get('bounds')
                m = re.findall(r'\d+', b)
                if m:
                    x = (int(m[0]) + int(m[2])) // 2
                    y = (int(m[1]) + int(m[3])) // 2
                    print(f"Confirming remove at {x}, {y}")
                    adb_cmd('shell', f'input tap {x} {y}')
                    time.sleep(2)
                    break
        print("Successfully removed gamesvendn06 from device!")
    else:
        print("Remove button not found in detail screen!")
else:
    print("gamesvendn06 not found on device!")
