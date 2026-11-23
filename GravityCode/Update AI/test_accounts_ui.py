import subprocess, time, xml.etree.ElementTree as ET

adb = r'D:\LDPlayer\LDPlayer9\adb.exe'
serial = '127.0.0.1:5555'

def run_adb(*args, timeout=10):
    subprocess.run([adb, 'connect', serial], capture_output=True, timeout=5)
    cmd = [adb, '-s', serial] + list(args)
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return res.stdout.strip()

def dump_ui():
    run_adb('shell', 'input keyevent KEYCODE_WAKEUP')
    run_adb('shell', 'wm dismiss-keyguard')
    run_adb('shell', 'uiautomator dump /sdcard/ui.xml')
    run_adb('pull', '/sdcard/ui.xml', 'current_ui.xml')
    try:
        tree = ET.parse('current_ui.xml')
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
    except Exception as e:
        print("dump error:", e)
        return []

def tap(x, y):
    print(f"Tap: {x}, {y}")
    run_adb('shell', f'input tap {x} {y}')
    time.sleep(1)

if __name__ == '__main__':
    print("Opening Sync Settings (Accounts)...")
    run_adb('shell', 'am start -a android.settings.SYNC_SETTINGS')
    time.sleep(2)
    nodes = dump_ui()
    print("Found UI nodes:")
    for n in nodes:
        if n['text'] or n['desc']:
            print(f" - text='{n['text']}' desc='{n['desc']}' at ({n['cx']}, {n['cy']})")
