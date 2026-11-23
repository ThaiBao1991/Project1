import subprocess, time, xml.etree.ElementTree as ET

adb = r'D:\LDPlayer\LDPlayer9\adb.exe'
serial = '127.0.0.1:5555'

def run_adb(*args, timeout=10):
    subprocess.run([adb, 'connect', serial], capture_output=True, timeout=5)
    cmd = [adb, '-s', serial] + list(args)
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return res.stdout.strip()

def dump_ui(save_name='ui.xml'):
    run_adb('shell', 'input keyevent KEYCODE_WAKEUP')
    run_adb('shell', 'wm dismiss-keyguard')
    time.sleep(1)
    run_adb('shell', f'uiautomator dump /sdcard/{save_name}')
    run_adb('pull', f'/sdcard/{save_name}', save_name)
    try:
        tree = ET.parse(save_name)
        nodes = []
        for n in tree.getroot().iter('node'):
            b = n.attrib.get('bounds', '')
            t = n.attrib.get('text', '')
            d = n.attrib.get('content-desc', '')
            res = n.attrib.get('resource-id', '')
            if b.startswith('['):
                parts = b.replace('][', ',').replace('[', '').replace(']', '').split(',')
                x1, y1, x2, y2 = map(int, parts)
                nodes.append({'text': t, 'desc': d, 'id': res, 'cx': (x1+x2)//2, 'cy': (y1+y2)//2, 'b': b})
        return nodes
    except Exception as e:
        print("dump error:", e)
        return []

def tap(x, y):
    print(f"Tap: {x}, {y}")
    run_adb('shell', f'input tap {x} {y}')
    time.sleep(2)

if __name__ == '__main__':
    print("Opening Sync Settings...")
    run_adb('shell', 'am start -a android.settings.SYNC_SETTINGS')
    time.sleep(2)
    nodes = dump_ui('sync_settings.xml')
    google_node = None
    for n in nodes:
        if n['text'] == 'Google':
            google_node = n
            break
    
    if not google_node:
        print("Could not find Google in Sync Settings")
    else:
        print(f"Clicking Google at ({google_node['cx']}, {google_node['cy']})...")
        tap(google_node['cx'], google_node['cy'])
        time.sleep(2)
        nodes = dump_ui('google_accounts.xml')
        print("Accounts on screen:")
        for n in nodes:
            if '@' in n['text'] or 'svendn' in n['text'] or 'Xóa' in n['text'] or 'Remove' in n['text']:
                print(f" - text='{n['text']}' at ({n['cx']}, {n['cy']})")
