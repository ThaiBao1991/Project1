import subprocess, time, xml.etree.ElementTree as ET

adb = r'D:\LDPlayer\LDPlayer9\adb.exe'
serial = '127.0.0.1:5555'

def adb_cmd(*args):
    subprocess.run([adb, 'connect', serial], capture_output=True)
    cmd = [adb, '-s', serial] + list(args)
    return subprocess.run(cmd, capture_output=True, text=True)

print("Starting Google Play with svendn03@gmail.com...")
adb_cmd('shell', 'am force-stop com.android.vending')
adb_cmd('shell', 'am start -n com.android.vending/com.google.android.finsky.activities.MainActivity --es authAccount svendn03@gmail.com')
time.sleep(4)

print("Opening payment methods...")
adb_cmd('shell', 'am start -a android.intent.action.VIEW -d "https://play.google.com/store/paymentmethods"')
time.sleep(5)

adb_cmd('shell', 'uiautomator dump /sdcard/svendn03_pm.xml')
adb_cmd('pull', '/sdcard/svendn03_pm.xml', 'svendn03_pm.xml')

tree = ET.parse('svendn03_pm.xml')
for n in tree.getroot().iter('node'):
    t = n.attrib.get('text', '')
    d = n.attrib.get('content-desc', '')
    b = n.attrib.get('bounds', '')
    if t or d:
        print(t, '|', d, '|', b)
