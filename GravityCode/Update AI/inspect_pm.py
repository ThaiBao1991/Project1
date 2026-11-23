import subprocess, time, xml.etree.ElementTree as ET

adb = r'D:\LDPlayer\LDPlayer9\adb.exe'
serial = '127.0.0.1:5555'

def adb_cmd(*args):
    subprocess.run([adb, 'connect', serial], capture_output=True)
    cmd = [adb, '-s', serial] + list(args)
    return subprocess.run(cmd, capture_output=True, text=True)

def dump_ui():
    adb_cmd('shell', 'uiautomator dump /sdcard/ui_check.xml')
    adb_cmd('pull', '/sdcard/ui_check.xml', 'ui_check.xml')
    try:
        tree = ET.parse('ui_check.xml')
        items = []
        for n in tree.getroot().iter('node'):
            t = n.attrib.get('text', '')
            d = n.attrib.get('content-desc', '')
            b = n.attrib.get('bounds', '')
            if t or d:
                items.append({'text': t, 'desc': d, 'bounds': b})
        return items
    except Exception as e:
        print("dump error:", e)
        return []

print("Opening payment methods on Play Store...")
adb_cmd('shell', 'am start -a android.intent.action.VIEW -d "https://play.google.com/store/paymentmethods"')
time.sleep(4)

items = dump_ui()
for item in items:
    print(item['text'], '|', item['desc'], '|', item['bounds'])
