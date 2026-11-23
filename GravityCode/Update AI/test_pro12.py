import ultra0, time

ultra0.ADB = ultra0.find_adb()
ultra0.SERIAL = "127.0.0.1:5555"

pid = ultra0.launch_app()
print(f"PID: {pid}")

fr = ultra0.run_trial(pid, plan="pro12", stack=False)
print("Launched:", fr["launched"])

for i in range(10):
    time.sleep(2)
    xml = ultra0.ui_xml()
    txt = " ".join(n["text"] for n in ultra0.nodes(xml) if n["text"])
    print(f"\n--- Round {i} ({len(txt)} chars) ---")
    print(txt[:250])
    if "Đăng ký" in txt or "AI" in txt or "Pro" in txt or "Google One" in txt:
        with open("pro12_sheet.xml", "w", encoding="utf-8") as f:
            f.write(xml)
        print("Captured sheet XML!")
        break
