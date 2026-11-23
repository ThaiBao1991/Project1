import time, os, sys, subprocess

sys.path.insert(0, os.getcwd())
import ultra0

ultra0.ADB = ultra0.find_adb()
ultra0.pick_device()
ultra0.ensure_root()
ultra0.ensure_frida_server()
ultra0.ensure_module_apk()
ultra0.ensure_vending()

pid = ultra0.launch_app()
print(f'Google One PID: {pid}')

# Launch billing flow
fr = ultra0.run_trial(pid, plan='pro12', list_only=False, stack=False)
print('Frida result:', fr.get('launched'))

# Wait for billing sheet
clicked = False
for attempt in range(15):
    time.sleep(2)
    xml = ultra0.ui_xml()
    for n in ultra0.nodes(xml):
        if n['cls'] == 'android.widget.Button' and any(k in n['text'] for k in ['Đăng ký', 'Subscribe']):
            print(f"Found Subscribe button at ({n['x']}, {n['y']}), tapping!")
            ultra0.tap(n['x'], n['y'])
            clicked = True
            break
    if clicked:
        break

if not clicked:
    print('Failed to find subscribe button!')
    sys.exit(1)

# Now wait and monitor what happens
print('Monitoring screen after clicking Subscribe...')
passwords = ['satthubibon', 'satthubibon01']
pass_idx = 0

for i in range(20):
    time.sleep(2)
    xml = ultra0.ui_xml()
    texts = [n['text'] for n in ultra0.nodes(xml) if n['text']]
    cur_text = ' | '.join(texts[:8])
    print(f'[{i*2}s]', cur_text)
    
    # Check if password prompt appears
    if any('mật khẩu' in t.lower() for t in texts):
        print('-> Password prompt detected!')
        # find EditText
        edits = [n for n in ultra0.nodes(xml) if 'EditText' in n['cls']]
        if edits and pass_idx < len(passwords):
            pwd = passwords[pass_idx]
            pass_idx += 1
            print(f'-> Entering password: {pwd}')
            ultra0.tap(edits[0]['x'], edits[0]['y'])
            time.sleep(0.5)
            subprocess.run([ultra0.ADB, '-s', '127.0.0.1:5555', 'shell', f'input text "{pwd}"'])
            time.sleep(0.5)
            # Find OK button
            for n in ultra0.nodes(xml):
                if n['cls'] == 'android.widget.Button' and n['text'] in ['OK', 'Xác nhận']:
                    ultra0.tap(n['x'], n['y'])
                    print(f"-> Tapped {n['text']}")
                    break
            time.sleep(3)
            continue
            
    if any(k in t.lower() for t in texts for k in ['đã đăng ký', 'subscribed', 'thành công']):
        print('SUCCESS: Detected subscribed message!')
        break
    if any(k in t.lower() for t in texts for k in ['lỗi', 'error', 'or-']):
        print('ERROR: Payment error detected!')
        break

print('Done monitoring.')
