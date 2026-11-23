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
    time.sleep(1)
    run_adb('shell', 'uiautomator dump /sdcard/ui_pm.xml')
    run_adb('pull', '/sdcard/ui_pm.xml', 'ui_pm.xml')
    try:
        tree = ET.parse('ui_pm.xml')
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

if __name__ == '__main__':
    print("Launching Google Play payment methods...")
    run_adb('shell', 'am force-stop com.android.vending')
    run_adb('shell', 'am start -n com.android.vending/com.google.android.finsky.activities.MainActivity --es authAccount svendn03@gmail.com')
    time.sleep(3)
    run_adb('shell', 'am start -a android.intent.action.VIEW -d "https://play.google.com/store/paymentmethods"')
    time.sleep(4)
    nodes = dump_ui()
    print("Found UI nodes on Payment Methods screen:")
    for n in nodes:
        if n['text'] or n['desc']:
            print(f" - text='{n['text']}' desc='{n['desc']}' id='{n['id']}' at ({n['cx']}, {n['cy']})")
