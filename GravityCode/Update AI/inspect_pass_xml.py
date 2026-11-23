import subprocess, re
adb = r'D:\LDPlayer\LDPlayer9\adb.exe'
subprocess.run([adb, '-s', '127.0.0.1:5555', 'shell', 'uiautomator dump /sdcard/pass.xml'])
res = subprocess.check_output([adb, '-s', '127.0.0.1:5555', 'shell', 'cat /sdcard/pass.xml']).decode('utf-8', errors='ignore')

nodes = re.findall(r'<node[^>]*>', res)
for n in nodes:
    t = re.search(r'text="([^"]*)"', n)
    d = re.search(r'content-desc="([^"]*)"', n)
    c = re.search(r'class="([^"]*)"', n)
    b = re.search(r'bounds="([^"]*)"', n)
    val = (t.group(1) if t else '') or (d.group(1) if d else '')
    cls = c.group(1) if c else ''
    bnd = b.group(1) if b else ''
    if val or 'Edit' in cls or 'Button' in cls:
        print(f"{cls} | {val!r} | {bnd}")
