import subprocess, time, re, os, sqlite3, datetime, json, secrets
from pathlib import Path
import xml.etree.ElementTree as ET

ADB = r'D:\LDPlayer\LDPlayer9\adb.exe'
SERIAL = '127.0.0.1:5555'

CARD_1 = {
    "name": "Thẻ 1 (2646)",
    "holder": "PHAN THANH THAI BINH",
    "number": "4848041097772646",
    "exp": "0330",
    "cvc": "680",
    "last4": "2646"
}

CARD_2 = {
    "name": "Thẻ 2 (0841)",
    "holder": "PHAN THANH THAI BINH",
    "number": "4619300014630841",
    "exp": "1131",
    "cvc": "326",
    "last4": "0841"
}

PASSWORDS = ["satthubibon", "satthubibon01"]

TARGET_ACCOUNTS = [
    "gamesvendn20@gmail.com",
    "gamesvendn21@gmail.com",
    "gamesvendn22@gmail.com",
    "gamesvendn23@gmail.com",
    "gamesvendn24@gmail.com",
    "gamesvendn25@gmail.com",
    "gamesvendn26@gmail.com",
    "gamesvendn27@gmail.com",
    "gamesvendn29@gmail.com",
    "gamesvendn30@gmail.com"
]

PROGRESS_FILE = "batch_progress.json"

def sh(*args, timeout=40):
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

# ---------- ĐĂNG NHẬP ----------
def login_single(email):
    print(f"\n▶ [Đăng Nhập Tài Khoản]: {email}")
    if email.lower() in accounts_on_device():
        print(f"   ✅ Tài khoản {email} đã có sẵn trên thiết bị!")
        return True

    sh("shell", "am force-stop com.android.settings")
    sh("shell", "am start -a android.settings.ADD_ACCOUNT_SETTINGS")
    time.sleep(2)

    if not tap_text("Google", exact=True):
        tap(97, 99)
    time.sleep(4)

    email_entered = False
    for _ in range(15):
        xml = ui_xml()
        txt = " ".join(n["text"] for n in nodes(xml) if n["text"])
        if "Đang kiểm tra" in txt or "Checking" in txt:
            time.sleep(1.5)
            continue
        if "Đăng nhập" in txt or "Sign in" in txt or "TIẾP THEO" in txt or "Next" in txt:
            edits = [n for n in nodes(xml) if "EditText" in n["cls"]]
            pos = (edits[0]["x"], edits[0]["y"]) if edits else (480, 314)
            tap(pos[0], pos[1])
            time.sleep(0.5)
            sh("shell", f"input text '{email}'")
            time.sleep(0.8)
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
        print(f"   ❌ Không mở được trang nhập email cho {email}")
        return False

    pwd_entered = False
    for pwd in PASSWORDS:
        for _ in range(12):
            xml = ui_xml()
            txt = " ".join(n["text"] for n in nodes(xml) if n["text"])
            if "Chào mừng" in txt or "Welcome" in txt or "Nhập mật khẩu" in txt or "Enter your password" in txt:
                edits = [n for n in nodes(xml) if "EditText" in n["cls"]]
                pos = (edits[0]["x"], edits[0]["y"]) if edits else (480, 292)
                tap(pos[0], pos[1])
                time.sleep(0.5)
                sh("shell", f"input text '{pwd}'")
                time.sleep(0.8)
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
        if pwd_entered:
            break

    if not pwd_entered:
        print(f"   ❌ Không tìm thấy trường mật khẩu cho {email}")
        return False

    # Vượt qua các popup xác nhận, điều khoản
    for _ in range(25):
        if email.lower() in accounts_on_device():
            print(f"   ✅ Đã đăng nhập {email} thành công!")
            return True
        xml = ui_xml()
        txt = " ".join(n["text"] for n in nodes(xml) if n["text"])
        if "Tôi đồng ý" in txt or "I agree" in txt:
            tap_text("Tôi đồng ý", "I agree") or tap(889, 514)
            time.sleep(3)
            continue
        if "TIẾP THEO" in txt or "Next" in txt:
            tap_text("TIẾP THEO", "Next") or tap(889, 514)
            time.sleep(3)
            continue
        if "Bỏ qua" in txt or "Skip" in txt:
            tap_text("Bỏ qua", "Skip") or tap(100, 514)
            time.sleep(2)
            continue
        if "Chấp nhận" in txt or "Accept" in txt:
            tap_text("Chấp nhận", "Accept") or tap(889, 514)
            time.sleep(3)
            continue
        time.sleep(1.5)

    res_ok = email.lower() in accounts_on_device()
    if res_ok:
        print(f"   ✅ Đã đăng nhập {email} thành công!")
    else:
        print(f"   ⚠️ Hết thời gian chờ đăng nhập {email}")
    return res_ok

# ---------- CHỌN TÀI KHOẢN PLAY STORE & GOOGLE ONE ----------
def ensure_google_play_account(email):
    for _ in range(3):
        sh("shell", "am start -n com.android.vending/com.android.vending.AssetBrowserActivity")
        time.sleep(3)
        tap(908, 43) # Avatar top right
        time.sleep(2)
        xml = ui_xml()
        if email.lower() in xml.lower():
            if "Đã đăng nhập bằng" in xml and email.lower() in xml.lower().split("quản lý")[0]:
                tap(932, 48)
                return True
            if tap_text(email):
                time.sleep(2)
                return True
        # Mở rộng danh sách
        tap_text("Mở rộng danh sách tài khoản") or tap(450, 120)
        time.sleep(1.5)
        if tap_text(email):
            time.sleep(2)
            return True
        tap(932, 48)
    return False

def ensure_google_one_account(email):
    sh("shell", "am force-stop com.google.android.apps.subscriptions.red")
    time.sleep(1)
    sh("shell", "monkey -p com.google.android.apps.subscriptions.red -c android.intent.category.LAUNCHER 1")
    time.sleep(4)
    xml = ui_xml()
    if email.lower() in xml.lower():
        return True
    # Đổi account trong Google One
    tap(908, 43)
    time.sleep(2)
    tap_text(email)
    time.sleep(2)
    return True

# ---------- THÊM THẺ ----------
def add_card(card_info):
    last4 = card_info["last4"]
    print(f"\n▶ [Thêm Thẻ]: Đang thêm {card_info['name']} (đuôi {last4})...")
    sh("shell", "am force-stop com.android.vending && am start -a android.intent.action.VIEW -d https://play.google.com/store/paymentmethods")
    time.sleep(4)

    for _ in range(10):
        xml = ui_xml()
        if last4 in xml:
            print(f"   ✅ Google Play đã có sẵn {card_info['name']}!")
            return True
        if "Thêm phương thức" in xml or "Thêm thẻ" in xml:
            break
        time.sleep(1)

    print("   Bấm 'Thêm thẻ tín dụng hoặc thẻ ghi nợ'...")
    tap_text("Thêm thẻ tín dụng hoặc thẻ ghi nợ") or tap(480, 314)
    time.sleep(4)

    # Nếu có màn hình camera quét thẻ, bấm "Nhập thông tin theo cách thủ công"
    for _ in range(5):
        xml_scan = ui_xml()
        if "thủ công" in xml_scan or "manually" in xml_scan.lower():
            print("   Bấm 'Nhập thông tin theo cách thủ công'...")
            tap_text("Nhập thông tin theo cách thủ công", "Enter details manually") or tap(140, 297)
            time.sleep(3)
            break
        time.sleep(1)

    # Nhập thông tin thẻ trực tiếp theo layout SheetUiBuilderHostActivity
    print(f"   Điền thông tin thẻ {card_info['name']}...")
    tap(480, 190)
    time.sleep(0.5)
    sh("shell", f"input text {card_info['number']}")
    time.sleep(1.0)
    tap(240, 355)
    time.sleep(0.5)
    sh("shell", f"input text {card_info['exp']}")
    time.sleep(1.0)
    tap(700, 355)
    time.sleep(0.5)
    sh("shell", f"input text {card_info['cvc']}")
    time.sleep(1.0)

    # Ẩn bàn phím ảo trước khi bấm Lưu
    sh("shell", "input keyevent 111")
    time.sleep(0.5)
    print("   Bấm 'Lưu thẻ'...")
    tap_text("Lưu", "Save") or tap(480, 496)
    time.sleep(6)

    for _ in range(12):
        xml3 = ui_xml()
        if last4 in xml3:
            print(f"   ✅ Đã thêm thành công {card_info['name']}!")
            return True
        if "OR-REH-04" in xml3 or "lỗi" in xml3.lower():
            print(f"   ⚠️ Thêm thẻ gặp lỗi từ ngân hàng/Google: {xml3[:200]}")
            return False
        time.sleep(1)

    # Kiểm tra lại
    sh("shell", "am force-stop com.android.vending && am start -a android.intent.action.VIEW -d https://play.google.com/store/paymentmethods")
    time.sleep(4)
    xml_final = ui_xml()
    res = last4 in xml_final
    if res:
        print(f"   ✅ Đã xác nhận {card_info['name']} trong Google Play!")
    else:
        print(f"   ❌ Không thêm được {card_info['name']}!")
    return res

# ---------- GỠ THẺ TRIỆT ĐỂ (0 THẺ) ----------
def remove_all_cards_strictly(email):
    print(f"\n▶ [Gỡ Sạch Thẻ Bắt Buộc]: Đang mở payments.google.com cho {email}...")
    sh("shell", "am start -a android.intent.action.VIEW -d https://payments.google.com/gp/w/home/paymentmethods")
    time.sleep(5)

    # Nếu Chrome hỏi continue with account
    xml_c = ui_xml()
    if "Tiếp tục bằng tài khoản" in xml_c or "Tiếp tục" in xml_c:
        tap_text("Tiếp tục bằng tài khoản", "Tiếp tục") or tap(480, 453)
        time.sleep(5)

    # Lặp gỡ tất cả các thẻ có nút Remove
    for round_idx in range(5):
        xml = ui_xml()
        if "No payment methods" in xml or "chưa có phương thức" in xml.lower():
            print("   Web Google Payments: Không còn thẻ nào!")
            break
        # Tìm nút Remove
        print(f"   Tìm và bấm Remove thẻ (vòng {round_idx+1})...")
        tap_text("Remove", "Xóa") or tap(300, 405)
        time.sleep(2.5)
        # Bấm xác nhận Remove modal
        tap_text("Remove and save", "Remove", "Xóa") or tap(600, 355)
        time.sleep(4)

    # Đối chiếu lại trong Google Play Store
    sh("shell", "am force-stop com.android.vending")
    sh("shell", "am start -a android.intent.action.VIEW -d https://play.google.com/store/paymentmethods")
    time.sleep(4)

    xml_play = ui_xml()
    cards_remaining = [n.get('text') for n in nodes(xml_play) if n.get('text') and any(k in n.get('text') for k in ['Visa', '0841', '2646', 'Mastercard'])]
    if not cards_remaining:
        print(f"   ✅ XÁC MINH 100%: Tài khoản {email} đã SẠCH THẺ HOÀN TOÀN (0 thẻ)!")
        return True
    else:
        print(f"   ⚠️ Vẫn còn thẻ trong Google Play: {cards_remaining}")
        return False

# ---------- HỦY GIA HẠN GÓI THUÊ BAO ----------
def cancel_auto_renew_strictly(email):
    print(f"\n▶ [Hủy Gia Hạn Bắt Buộc]: Quản lý gói thuê bao của {email}...")
    sh("shell", "am force-stop com.android.vending && am start -a android.intent.action.VIEW -d https://play.google.com/store/account/subscriptions")
    time.sleep(4)

    for _ in range(5):
        xml = ui_xml()
        if "Khám phá đăng ký" in xml:
            print("   ✅ Không có gói đang hoạt động hoặc gói đã hủy hoàn toàn!")
            return True
        if "Google One" in xml or "Google AI Pro" in xml or "Đang hoạt động" in xml:
            print("   Bấm vào chi tiết gói thuê bao...")
            tap(480, 333)
            time.sleep(3)
            xml_det = ui_xml()
            if "Đã hủy" in xml_det or "Đăng ký lại" in xml_det:
                print("   ✅ Gói đã hủy gia hạn trước đó!")
                return True
            print("   Bấm 'Hủy gói thuê bao'...")
            tap_text("Hủy gói thuê bao", "Huỷ gói thuê bao") or tap(480, 516)
            time.sleep(2.5)
            # Chọn lý do
            tap(500, 440)
            time.sleep(1)
            tap(500, 130)
            time.sleep(1)
            tap(614, 516)
            time.sleep(3)
            xml_fin = ui_xml()
            if "Đã hủy" in xml_fin or "sẽ hết hạn vào" in xml_fin or "Đăng ký lại" in xml_fin:
                print("   ✅ XÁC NHẬN: Gói đã hủy gia hạn thành công (quyền lợi giữ nguyên đến 2028)!")
                return True
        time.sleep(2)
    return False

# ---------- XÓA TÀI KHOẢN KHỎI MÁY ----------
def remove_account_from_device(email):
    print(f"\n▶ [Xóa Tài Khoản Khỏi Thiết Bị]: Đang xóa {email}...")
    sh("shell", "am force-stop com.android.settings")
    sh("shell", "am start -a android.settings.SYNC_SETTINGS")
    time.sleep(2)

    found = False
    for _ in range(4):
        if tap_text(email):
            found = True
            break
        sh("shell", "input swipe 500 400 500 150")
        time.sleep(1)

    if not found:
        print(f"   ⚠️ Không tìm thấy {email} trong Cài đặt đồng bộ!")
        return False

    time.sleep(2)
    tap_text("XÓA TÀI KHOẢN", "REMOVE ACCOUNT") or tap(479, 358)
    time.sleep(1.5)
    tap_text("XÓA TÀI KHOẢN", "REMOVE ACCOUNT") or tap(652, 333)
    time.sleep(2)
    print(f"   ✅ Đã xóa an toàn {email} khỏi máy giả lập!")
    return True

# ---------- KIỂM TRA HẠN DÙNG TRONG DATABASE ----------
def get_current_sub_expiry(target_email=None):
    try:
        sh("shell", "su 0 cp /data/data/com.android.vending/databases/library.db* /data/local/tmp/ && su 0 chmod 666 /data/local/tmp/library.db*")
        sh("pull", "/data/local/tmp/library.db", "pipe_lib.db")
        sh("pull", "/data/local/tmp/library.db-wal", "pipe_lib.db-wal")
        con = sqlite3.connect("pipe_lib.db")
        cur = con.cursor()
        if target_email:
            rows = cur.execute("select account, subs_valid_until_time, inapp_purchase_data from ownership where account = ? and doc_id like '%subs_variant%'", (target_email,)).fetchall()
        else:
            rows = cur.execute("select account, subs_valid_until_time, inapp_purchase_data from ownership where doc_id like '%subs_variant%'").fetchall()
        con.close()
        for f in ["pipe_lib.db", "pipe_lib.db-wal", "pipe_lib.db-shm"]:
            if os.path.exists(f): os.remove(f)
        if rows:
            for acc, valid, data in rows:
                if valid:
                    exp = datetime.datetime.fromtimestamp(int(valid)/1000).strftime('%Y-%m-%d %H:%M:%S')
                    oid = ""
                    if data:
                        try: oid = json.loads(data).get('orderId', '')
                        except Exception: pass
                    return exp, oid, acc
    except Exception:
        pass
    return "", "", ""

def run_cmd(cmd_list, timeout=120):
    env = os.environ.copy()
    env["PATH"] += f";{r'D:\LDPlayer\LDPlayer9'}"
    p = subprocess.run(cmd_list, capture_output=True, text=True, timeout=timeout, env=env)
    return p.stdout + p.stderr

def run_ultra_step(plan, email, stack=False):
    cmd = ["python", "-X", "utf8", "ultra0.py", "--account", email, "--no-add", "--force", "--plan", plan]
    if stack:
        cmd.append("--stack")
    out = run_cmd(cmd, timeout=120)
    print(out[-350:] if len(out) > 350 else out)
    return out

# ---------- LƯU TRÌNH XỬ LÝ 1 TÀI KHOẢN (2 TẦNG THẺ) ----------
def process_one_account(email):
    print("\n" + "=" * 60)
    print(f"  BẮT ĐẦU XỬ LÝ: {email}")
    print("=" * 60)

    # 0. Quy tắc Bắt buộc: Độc tôn 1 Tài khoản Chính (Single Primary Account Rule)
    for existing in accounts_on_device():
        if existing != email.lower():
            print(f"   Dọn dẹp tài khoản cũ {existing} để {email} là Tài khoản Chính duy nhất...")
            remove_account_from_device(existing)

    # 1. Đảm bảo tài khoản có trên máy và được chọn
    if email.lower() not in accounts_on_device():
        login_ok = login_single(email)
        if not login_ok:
            return False, "login_failed", "Không đăng nhập được tài khoản"

    ensure_google_play_account(email)
    ensure_google_one_account(email)

    # Kiểm tra xem tài khoản đã có sẵn gói 24 tháng chưa
    exp, oid, acc = get_current_sub_expiry(email)
    if "2028" in exp and acc == email:
        print(f"🎉 Tài khoản {email} đã có sẵn gói 24 tháng (Hạn: {exp})!")
        cancel_auto_renew_strictly(email)
        remove_all_cards_strictly(email)
        remove_account_from_device(email)
        return True, "already_24m", f"Đã có 24m (Hạn: {exp})"

    cards_to_try = [CARD_1, CARD_2]
    subscribed = False
    active_card = None

    for card in cards_to_try:
        print(f"\n--- [Thử nghiệm {card['name']}] cho {email} ---")
        # Đảm bảo trước khi thêm thẻ mới thì gỡ sạch thẻ cũ
        remove_all_cards_strictly(email)

        # Thêm thẻ
        add_ok = add_card(card)
        if not add_ok:
            print(f"⚠️ Thêm {card['name']} không thành công, chuyển phương án...")
            continue

        # Thử kích hoạt pro12 (12 tháng)
        print(f"\n[Bước 1/3]: Kích hoạt 12 tháng miễn phí (pro12) với {card['name']}...")
        run_ultra_step("pro12", email, stack=False)
        time.sleep(3)

        exp, oid, acc = get_current_sub_expiry(email)
        if exp and acc == email:
            print(f"   ✅ KÍCH HOẠT THÀNH CÔNG BƯỚC 1 VỚI {card['name']}! (Hạn: {exp})")
            subscribed = True
            active_card = card
            break
        else:
            print(f"   ❌ {card['name']} không kích hoạt được pro12!")

    # Nếu cả 2 thẻ đều không kích hoạt được
    if not subscribed:
        print(f"\n⛔ CẢ 2 THẺ ĐỀU KHÔNG KÍCH HOẠT ĐƯỢC CHO {email}!")
        remove_all_cards_strictly(email)
        remove_account_from_device(email)
        return False, "both_cards_failed", "Cả Thẻ 1 và Thẻ 2 đều bị từ chối"

    # Đã kích hoạt Bước 1 thành công -> Tiếp tục cộng dồn lên 24 tháng
    print(f"\n[Bước 2/3]: Cộng dồn +6 tháng lên 18 tháng (pro6)...")
    run_ultra_step("pro6", email, stack=True)
    time.sleep(3)
    exp, oid, acc = get_current_sub_expiry(email)

    print(f"\n[Bước 3/3]: Cộng dồn thêm +6 tháng lên 24 tháng (pro6b)...")
    run_ultra_step("pro6b", email, stack=True)
    time.sleep(3)
    exp, oid, acc = get_current_sub_expiry(email)

    print(f"\n[Kết quả SQLite Play Store]: Acc={acc}, Expiry={exp}, OrderId={oid}")
    if "2028" in exp and acc == email:
        print(f"🎉 CHÚC MỪNG: {email} ĐÃ HOÀN TẤT ĐỦ 24 THÁNG (Hạn: {exp}) VỚI {active_card['name']}!")
        # Hủy gia hạn
        cancel_auto_renew_strictly(email)
        # Gỡ sạch thẻ
        remove_all_cards_strictly(email)
        # Xóa account khỏi máy
        remove_account_from_device(email)
        return True, "success_24m", f"Hoàn tất 24m (Hạn: {exp}, {active_card['name']})"
    else:
        print(f"⚠️ {email} mới đạt mốc {exp}, chưa đủ 24 tháng!")
        cancel_auto_renew_strictly(email)
        remove_all_cards_strictly(email)
        remove_account_from_device(email)
        return False, "partial_sub", f"Chưa đủ 24m (Hạn: {exp})"

# ---------- TIẾN TRÌNH CHÍNH ----------
def load_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_progress(data):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    print("=" * 60)
    print("  KHỞI ĐỘNG PIPELINE TỰ ĐỘNG CHUẨN HÓA: gamesvendn20 ➔ 30")
    print("=" * 60)

    progress = load_progress()

    for idx, email in enumerate(TARGET_ACCOUNTS, 1):
        if progress.get(email, {}).get("status") in ["success_24m", "both_cards_failed"]:
            print(f"⏭️ Bỏ qua {email} vì đã xử lý trước đó: {progress[email]}")
            continue

        print(f"\n>>>> TIẾN ĐỘ TỔNG THỂ: [{idx}/{len(TARGET_ACCOUNTS)}] - {email} <<<<")
        ok, code, note_msg = process_one_account(email)

        progress[email] = {
            "status": code,
            "success": ok,
            "note": note_msg,
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_progress(progress)

        # Cập nhật ProjectLog.md
        with open("projectLog.md", "a", encoding="utf-8") as f:
            status_symbol = "✅" if ok else "❌"
            f.write(f"\n- **{email}**: {status_symbol} {code} - {note_msg} ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n")

        time.sleep(3)

    print("\n" + "=" * 60)
    print("  HOÀN THÀNH TOÀN BỘ DANH SÁCH 20 ➔ 30!")
    print("=" * 60)
    for acc, p in progress.items():
        print(f"  {acc:<28} : {p.get('status')} | {p.get('note')}")

if __name__ == "__main__":
    main()
