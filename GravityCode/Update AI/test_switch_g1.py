import subprocess, time, xml.etree.ElementTree as ET

adb = r'D:\LDPlayer\LDPlayer9\adb.exe'
serial = '127.0.0.1:5555'

def run_adb(*args):
    cmd = [adb, '-s', serial] + list(args)
    return subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def ui_nodes():
    run_adb('shell', 'uiautomator dump /sdcard/ui_g1.xml')
    run_adb('pull', '/sdcard/ui_g1.xml', 'temp_g1.xml')
    try:
        tree = ET.parse('temp_g1.xml')
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
    run_adb('shell', f'input tap {x} {y}')

def switch_google_one_account(target_email: str) -> bool:
    print(f"\n--- Chuyển Google One sang {target_email} ---")
    run_adb('shell', 'am force-stop com.google.android.apps.subscriptions.red')
    run_adb('shell', 'monkey -p com.google.android.apps.subscriptions.red -c android.intent.category.LAUNCHER 1')
    time.sleep(5)
    
    # tap avatar at top right
    tap(932, 56)
    time.sleep(2)
    
    nodes = ui_nodes()
    # Check if already active
    for n in nodes:
        if target_email.lower() in (n['text'] + ' ' + n['desc']).lower() and 'đã đăng nhập' in (n['text'] + ' ' + n['desc']).lower():
            print(f"✅ Google One đã đăng nhập sẵn {target_email}")
            run_adb('shell', 'input keyevent 4')
            return True
            
    # Look for target account in list
    for n in nodes:
        if target_email.lower() in (n['text'] + ' ' + n['desc']).lower() and 'đã đăng nhập' not in (n['text'] + ' ' + n['desc']).lower():
            print(f"👉 Tìm thấy {target_email} trong Google One tại ({n['cx']}, {n['cy']}), đang chọn...")
            tap(n['cx'], n['cy'])
            time.sleep(4)
            return True
            
    # Try scroll down
    run_adb('shell', 'input swipe 480 400 480 150 300')
    time.sleep(1)
    nodes = ui_nodes()
    for n in nodes:
        if target_email.lower() in (n['text'] + ' ' + n['desc']).lower():
            print(f"👉 Tìm thấy sau khi cuộn trong Google One: {target_email} tại ({n['cx']}, {n['cy']}), đang chọn...")
            tap(n['cx'], n['cy'])
            time.sleep(4)
            return True
            
    print(f"❌ Không tìm thấy {target_email} trong Google One")
    subprocess.run([adb, 'shell', 'input keyevent 4'])
    return False

if __name__ == '__main__':
    switch_google_one_account('gamesvendn09@gmail.com')
