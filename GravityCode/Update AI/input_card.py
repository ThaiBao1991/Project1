import subprocess, time

adb = r'D:\LDPlayer\LDPlayer9\adb.exe'

def tap(x, y):
    subprocess.run([adb, 'shell', f'input tap {x} {y}'])

def type_text(text):
    subprocess.run([adb, 'shell', f'input text {text}'])

print("Filling card number...")
tap(452, 197)
time.sleep(1)
type_text("4848041097772646")
time.sleep(1.5)

print("Filling expiry date...")
tap(232, 285)
time.sleep(1)
type_text("0330")
time.sleep(1.5)

print("Filling CVV...")
tap(672, 285)
time.sleep(1)
type_text("680")
time.sleep(1.5)

print("Tapping Lưu thẻ...")
tap(480, 496)
time.sleep(5)
print("Done filling and saving card.")
