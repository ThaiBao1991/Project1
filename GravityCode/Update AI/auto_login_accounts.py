import subprocess, time, re
import xml.etree.ElementTree as ET

ADB = r'D:\LDPlayer\LDPlayer9\adb.exe'
SERIAL = '127.0.0.1:5555'

PASSWORDS = ["satthubibon", "satthubibon01"]

TARGET_ACCOUNTS = [
    "gamesvendn26@gmail.com",
    "gamesvendn27@gmail.com",
    "gamesvendn28@gmail.com",
    "gamesvendn29@gmail.com",
    "gamesvendn30@gmail.com"
]

def sh(*args, timeout=30):
    cmd = [ADB, '-s', SERIAL] + list(args)
    p = subprocess.run(cmd, capture_output=True, timeout=timeout, text=True, errors='ignore')
    return p.stdout.strip()

def accounts_on_device():
    out = sh("shell", "dumpsys account")
    res = []
    for line in out.splitlines():
        if "Account {" in line and "type=com.google" in line:
            m = re.search(r"name=([^,]+)", line)
            if m:
                res.append(m.group(1).strip().lower())
    return res

def ui_xml():
    sh("shell", "uiautomator dump /data/local/tmp/ui.xml")
    return sh("shell", "cat /data/local/tmp/ui.xml")

def nodes(xml_text):
    for m in re.finditer(r"<node[^>]*>", xml_text):
        s = m.group(0)
        t = re.search(r'text="([^"]*)"', s)
        d = re.search(r'content-desc="([^"]*)"', s)
        b = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', s)
        c = re.search(r'class="([^"]*)"', s)
        if not b:
            continue
        yield {
            "text": (t.group(1) if t else "") or "",
            "desc": (d.group(1) if d else "") or "",
            "cls": (c.group(1) if c else "") or "",
            "x": (int(b.group(1)) + int(b.group(3))) // 2,
            "y": (int(b.group(2)) + int(b.group(4))) // 2,
        }

def tap(x, y):
    sh("shell", f"input tap {x} {y}")

def tap_text(*needles, exact=False):
    for n in nodes(ui_xml()):
        label = n["text"] or n["desc"]
        if not label:
            continue
        hit = (label == needles[0]) if exact and needles else any(k in label for k in needles)
        if hit and (n["x"] or n["y"]):
            tap(n["x"], n["y"])
            return True
    return False

def login_single(email):
    print(f"\n==========================================")
    print(f"▶ Bắt đầu đăng nhập tài khoản: {email}")
    print(f"==========================================")

    if email.lower() in accounts_on_device():
        print(f"✅ Tài khoản {email} đã có sẵn trên thiết bị!")
        return True

    # 1. Mở màn hình Thêm tài khoản
    sh("shell", "am force-stop com.android.settings")
    sh("shell", "am start -a android.settings.ADD_ACCOUNT_SETTINGS")
    time.sleep(2)

    # Chọn Google
    if not tap_text("Google", exact=True):
        tap(97, 99)
    time.sleep(4)

    # Đợi màn hình đăng nhập xuất hiện
    email_entered = False
    for _ in range(15):
        xml = ui_xml()
        txt = " ".join(n["text"] for n in nodes(xml) if n["text"])
        if "Đang kiểm tra" in txt or "Checking" in txt:
            time.sleep(1.5)
            continue
        if "Đăng nhập" in txt or "Sign in" in txt or "TIẾP THEO" in txt or "Next" in txt:
            # Tìm trường nhập email
            edits = [n for n in nodes(xml) if "EditText" in n["cls"]]
            pos = (edits[0]["x"], edits[0]["y"]) if edits else (480, 314)
            print(f"Nhập email {email} tại {pos}...")
            tap(pos[0], pos[1])
            time.sleep(0.5)
            sh("shell", f"input text '{email}'")
            time.sleep(0.8)
            # Bấm Tiếp theo
            btn_next = None
            for n in nodes(xml):
                if n["text"].strip() in ["TIẾP THEO", "Tiếp theo", "Next", "NEXT"]:
                    btn_next = (n["x"], n["y"])
                    break
            if not btn_next:
                btn_next = (889, 514)
            tap(btn_next[0], btn_next[1])
            email_entered = True
            time.sleep(3)
            break
        time.sleep(1.5)

    if not email_entered:
        print(f"❌ Không mở được trang nhập email cho {email}")
        return False

    # 2. Nhập mật khẩu
    pwd_entered = False
    pwd_idx = 0
    for _ in range(15):
        xml = ui_xml()
        txt = " ".join(n["text"] for n in nodes(xml) if n["text"])
        if "Chào mừng" in txt or "Welcome" in txt or "Nhập mật khẩu" in txt or "Enter your password" in txt:
            edits = [n for n in nodes(xml) if "EditText" in n["cls"]]
            pos = (edits[0]["x"], edits[0]["y"]) if edits else (480, 292)
            curr_pwd = PASSWORDS[pwd_idx]
            print(f"Nhập mật khẩu ({curr_pwd}) tại {pos}...")
            tap(pos[0], pos[1])
            time.sleep(0.5)
            sh("shell", f"input text '{curr_pwd}'")
            time.sleep(0.8)
            # Bấm Tiếp theo
            btn_next = None
            for n in nodes(xml):
                if n["text"].strip() in ["TIẾP THEO", "Tiếp theo", "Next", "NEXT"]:
                    btn_next = (n["x"], n["y"])
                    break
            if not btn_next:
                btn_next = (889, 514)
            tap(btn_next[0], btn_next[1])
            pwd_entered = True
            time.sleep(4)
            break
        time.sleep(1.5)

    if not pwd_entered:
        print(f"❌ Không tìm thấy trường mật khẩu cho {email}")
        return False

    # 3. Vòng lặp xử lý các màn hình chuyển tiếp (Bỏ qua số đt, nhà, đồng ý điều khoản)
    for step_num in range(25):
        if email.lower() in accounts_on_device():
            print(f"✅ Google xác nhận tài khoản {email} đã được thêm thành công!")
            return True

        xml = ui_xml()
        txt = " ".join(n["text"] for n in nodes(xml) if n["text"])

        # Kiểm tra mật khẩu sai -> thử pass 2
        if "Mật khẩu không chính xác" in txt or "Wrong password" in txt:
            if pwd_idx + 1 < len(PASSWORDS):
                pwd_idx += 1
                curr_pwd = PASSWORDS[pwd_idx]
                print(f"⚠️ Mật khẩu đầu tiên sai, thử mật khẩu thứ 2: {curr_pwd}...")
                edits = [n for n in nodes(xml) if "EditText" in n["cls"]]
                pos = (edits[0]["x"], edits[0]["y"]) if edits else (480, 292)
                tap(pos[0], pos[1])
                time.sleep(0.5)
                # Xóa sạch text cũ
                for _ in range(25):
                    sh("shell", "input keyevent 67")
                sh("shell", f"input text '{curr_pwd}'")
                time.sleep(0.5)
                tap(889, 514)
                time.sleep(4)
                continue
            else:
                print(f"❌ Cả 2 mật khẩu đều không đúng cho {email}")
                return False

        # Bỏ qua khôi phục (Số điện thoại / email khôi phục)
        if "Đảm bảo rằng bạn luôn có thể đăng nhập" in txt or "Account Recovery" in txt or "thông tin khôi phục" in txt:
            print("Phát hiện màn hình hỏi thông tin khôi phục -> Cuộn xuống và bấm Huỷ...")
            sh("shell", "input swipe 500 500 500 100")
            time.sleep(1)
            tap_text("Huỷ", "Hủy", "Cancel") or tap(308, 495)
            time.sleep(3)
            continue

        # Bỏ qua địa chỉ nhà riêng
        if "Đặt địa chỉ nhà riêng" in txt or "Home address" in txt:
            print("Phát hiện màn hình hỏi địa chỉ nhà riêng -> Bấm Bỏ qua...")
            tap_text("Bỏ qua", "Skip") or tap(780, 504)
            time.sleep(3)
            continue

        # Đồng ý điều khoản
        if "Tôi đồng ý" in txt or "I agree" in txt:
            print("Bấm 'Tôi đồng ý'...")
            tap_text("Tôi đồng ý", "I agree") or tap(717, 492)
            time.sleep(4)
            continue

        # Google Services (Sao lưu)
        if "Dịch vụ của Google" in txt or "Google Services" in txt:
            print("Xử lý màn hình Dịch vụ Google (Xem thêm / Chấp nhận)...")
            tap_text("Xem thêm", "More") or tap_text("Chấp nhận", "Accept")
            time.sleep(2)
            tap_text("Chấp nhận", "Accept")
            time.sleep(3)
            continue

        # Bỏ qua chung (Skip / Để sau / Không)
        if tap_text("Bỏ qua", "Skip", "Để sau", "Not now"):
            print("Bấm Bỏ qua / Để sau...")
            time.sleep(2)
            continue

        # Kiểm tra lỗi bảo mật
        if any(err in txt for err in ["OR-REH-04", "Không thể xác minh", "Xác minh danh tính"]):
            print(f"⚠️ Phát hiện kiểm soát bảo mật từ Google cho {email}, dừng và bỏ qua!")
            return False

        time.sleep(2)

    if email.lower() in accounts_on_device():
        print(f"✅ Hoàn tất thêm {email}")
        return True
    else:
        print(f"⚠️ Quá thời gian chờ thêm {email}")
        return False

def main():
    print("==========================================")
    print("CHƯƠNG TRÌNH TỰ ĐỘNG ĐĂNG NHẬP TÀI KHOẢN")
    print(f"Tổng số tài khoản: {len(TARGET_ACCOUNTS)}")
    print("==========================================")
    
    success_count = 0
    for acc in TARGET_ACCOUNTS:
        ok = login_single(acc)
        if ok:
            success_count += 1
        time.sleep(2)

    print(f"\n==========================================")
    print(f"KẾT QUẢ: Đã đăng nhập thành công {success_count}/{len(TARGET_ACCOUNTS)} tài khoản.")
    print("==========================================")

if __name__ == "__main__":
    main()
