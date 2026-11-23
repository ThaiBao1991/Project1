import subprocess, time, xml.etree.ElementTree as ET

adb = r'D:\LDPlayer\LDPlayer9\adb.exe'
serial = '127.0.0.1:5555'

def run_adb(*args):
    cmd = [adb, 'connect', serial]
    subprocess.run(cmd, capture_output=True)
    full_cmd = [adb, '-s', serial] + list(args)
    return subprocess.run(full_cmd, capture_output=True, text=True)

def ui_nodes():
    run_adb('shell', 'uiautomator dump /sdcard/ui_pm.xml')
    run_adb('pull', '/sdcard/ui_pm.xml', 'ui_pm.xml')
    try:
        tree = ET.parse('ui_pm.xml')
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

print("Starting Google Play...")
run_adb('shell', 'am force-stop com.android.vending')
run_adb('shell', 'am start -n com.android.vending/com.google.android.finsky.activities.MainActivity')
time.sleep(3)

# Go to payment methods
print("Opening payment methods...")
run_adb('shell', 'am start -a android.intent.action.VIEW -d "https://play.google.com/store/paymentmethods"')
time.sleep(4)

nodes = ui_nodes()
print("=== PAYMENT METHODS ON SCREEN ===")
for n in nodes:
    t = n['text']
    d = n['desc']
    if t or d:
        print(f"{t} | {d} | ({n['cx']}, {n['cy']})")
