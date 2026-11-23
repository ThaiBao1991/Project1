import subprocess, time, xml.etree.ElementTree as ET

adb = r'D:\LDPlayer\LDPlayer9\adb.exe'
serial = '127.0.0.1:5555'

def adb_cmd(*args):
    subprocess.run([adb, 'connect', serial], capture_output=True)
    cmd = [adb, '-s', serial] + list(args)
    return subprocess.run(cmd, capture_output=True, text=True)

def ui_nodes():
    adb_cmd('shell', 'uiautomator dump /sdcard/ui.xml')
    adb_cmd('pull', '/sdcard/ui.xml', 'temp_ui.xml')
    try:
        tree = ET.parse('temp_ui.xml')
        nodes = []
        for n in tree.getroot().iter('node'):
            b = n.attrib.get('bounds', '')
            t = n.attrib.get('text', '')
            d = n.attrib.get('content-desc', '')
            if b.startswith('['):
                parts = b.replace('][', ',').replace('[', '').replace(']', '').split(',')
                x1, y1, x2, y2 = map(int, parts)
                nodes.append({'text': t, 'desc': d, 'cx': (x1+x2)//2, 'cy': (y1+y2)//2, 'b': b})
        return nodes
    except Exception:
        return []

def tap(x, y):
    adb_cmd('shell', f'input tap {x} {y}')

def switch_play_account(target_email: str) -> bool:
    print(f"\n--- Chuyển Google Play sang {target_email} ---")
    adb_cmd('shell', 'am force-stop com.android.vending')
    adb_cmd('shell', 'am start -n com.android.vending/com.google.android.finsky.activities.MainActivity')
    time.sleep(3)
    
    # tap 'Bạn' tab
    tap(710, 508)
    time.sleep(1.5)
    # tap avatar
    tap(924, 56)
    time.sleep(2)
    
    nodes = ui_nodes()
    # Check if already active
    for n in nodes:
        if target_email.lower() in (n['text'] + ' ' + n['desc']).lower() and 'đã đăng nhập' in (n['text'] + ' ' + n['desc']).lower():
            print(f"✅ Đã đăng nhập sẵn {target_email}")
            adb_cmd('shell', 'input keyevent 4') # close menu
            return True
            
    # Need to expand list
    expanded = False
    for n in nodes:
        if 'mở rộng danh sách tài khoản' in (n['text'] + ' ' + n['desc']).lower():
            tap(n['cx'], n['cy'])
            time.sleep(1.5)
            expanded = True
            break
    if not expanded:
        tap(440, 118)
        time.sleep(1.5)
        
    nodes = ui_nodes()
    for n in nodes:
        if target_email.lower() in (n['text'] + ' ' + n['desc']).lower() and 'thu gọn' not in (n['text'] + ' ' + n['desc']).lower():
            print(f"👉 Tìm thấy {target_email} tại ({n['cx']}, {n['cy']}), đang chọn...")
            tap(n['cx'], n['cy'])
            time.sleep(3)
            return True
            
    # Try scroll down
    adb_cmd('shell', 'input swipe 480 400 480 150 300')
    time.sleep(1.5)
    nodes = ui_nodes()
    for n in nodes:
        if target_email.lower() in (n['text'] + ' ' + n['desc']).lower() and 'thu gọn' not in (n['text'] + ' ' + n['desc']).lower():
            print(f"👉 Tìm thấy sau khi cuộn: {target_email} tại ({n['cx']}, {n['cy']}), đang chọn...")
            tap(n['cx'], n['cy'])
            time.sleep(3)
            return True
            
    print(f"❌ Không tìm thấy {target_email} trong danh sách")
    adb_cmd('shell', 'input keyevent 4')
    return False

if __name__ == '__main__':
    switch_play_account('svendn03@gmail.com')
