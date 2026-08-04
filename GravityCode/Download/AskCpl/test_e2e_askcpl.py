import sys
import os
import json
sys.path.append(r"c:\Users\12953 bao\Desktop\desktop\work\Project\Python\BasicLearnPython\W3schools\Python Tutorial\GravityCode\Download\AskCpl")
import tkinter as tk
from AskCpl import App
from auto_ai_worker import run_auto_ai
from settings import load_settings

def get_active_api_keys():
    state = load_settings()
    keys = state.get("gemini", {}).get("api_keys", [])
    active_keys = [k for k in keys if k.get("status") == "active"]
    return active_keys

def test_e2e_askcpl():
    out_dir = r"c:\Users\12953 bao\Desktop\desktop\work\Project\Python\BasicLearnPython\W3schools\Python Tutorial\GravityCode\Download\AskCpl\test_output"
    os.makedirs(out_dir, exist_ok=True)

    print("=== KHỞI TẠO ASK CPL ENGINE ===")
    root = tk.Tk()
    root.withdraw()
    app = App(root)

    # Ghi đè log để in ra console
    def mock_log(msg):
        print(f"[Engine] {msg}")
    app.roadmap_gen_log = mock_log

    # Chuẩn bị dữ liệu giống y hệt lúc nhập trên UI
    app.ai_roadmap_domain_var.set("Sango Heros 7")
    app.ai_roadmap_time_var.set("30 phút")
    app.ai_roadmap_days_var.set("2") # Chỉ tạo 2 ngày để test E2E cho nhanh
    app.ai_roadmap_save_var.set(out_dir)
    app.ai_roadmap_expand_mode.set("ai")
    
    context_text = """Bản yêu cầu đã chuẩn hóa:
1. Tổng quan & cơ chế cốt lõi
Các mốc thời gian (kịch bản) có thể chọn khi bắt đầu, đặc điểm mỗi mốc
Chu kỳ thiết triều (2 tháng/lần): phong thưởng, ban chức, ban vũ khí/thú cưỡi
Hệ thống nội chính thành trì (xây dựng, thu thuế, tuyển quân...)

2. Tướng lĩnh
Bảng chỉ số đầy đủ mọi tướng: Thống lĩnh, Võ lực, Trí lực, Chính trị, Mị lực + chỉ số ẩn
Cách chiêu mộ/thu phục tướng.

LỆNH TỐI THƯỢNG ĐẶC BIỆT (Exhaustiveness): 
BẮT BUỘC phải áp dụng khung lý thuyết vào thực tế. Khi thiết kế bài học hoặc yêu cầu AI trả lời, bạn PHẢI ép AI lập bảng liệt kê chi tiết, phân tích rõ ràng cho TỪNG mốc kịch bản lịch sử hoặc TỪNG tướng (tuyệt đối không được nói lý thuyết suông, không được gom nhóm qua loa, và không được chỉ lấy vài ví dụ đại diện)."""
    
    app.ai_roadmap_context_text.delete("1.0", tk.END)
    app.ai_roadmap_context_text.insert(tk.END, context_text)

    snapshot = app._roadmap_snapshot()
    
    print("\n=== [1/3] CHẠY BƯỚC 1: LÊN DÀN Ý LÕI (CORE) ===")
    try:
        app._roadmap_v5_step1(snapshot)
    except Exception as e:
        print(f"Lỗi bước 1: {e}")
        
    print("\n=== [2/3] CHẠY BƯỚC 2: PHẢN BIỆN & MỞ RỘNG (REVIEW) ===")
    try:
        snapshot = app._show_saved_plan_and_snapshot(snapshot, prefer_reviewed=False)
        app._roadmap_v5_step2(snapshot)
    except Exception as e:
        print(f"Lỗi bước 2: {e}")

    print("\n=== [3/3] CHẠY BƯỚC 3: SINH CHI TIẾT MASTER ROADMAP ===")
    try:
        snapshot = app._show_saved_plan_and_snapshot(snapshot, prefer_reviewed=True)
        app._roadmap_v5_step3(snapshot)
    except Exception as e:
        print(f"Lỗi bước 3: {e}")

    # Lấy đường dẫn file roadmap MD vừa sinh
    artifacts = app._roadmap_artifacts(snapshot)
    roadmap_path = artifacts["final"]
    print(f"\n=> Roadmap đã tạo tại: {roadmap_path}")
    
    if not os.path.exists(roadmap_path):
        print("Không tìm thấy file roadmap, quá trình tạo roadmap thất bại.")
        return

    print("\n=== [4] CHẠY AUTO AI WORKER BẰNG ROADMAP VỪA SINH ===")
    api_keys = get_active_api_keys()
    if not api_keys:
        print("Không tìm thấy API Key nào đang active.")
        return

    # Clean previous output
    session_file = os.path.join(out_dir, "session.json")
    if os.path.exists(session_file):
        os.remove(session_file)

    run_auto_ai(
        api_keys_list=api_keys, 
        roadmap_path=roadmap_path, 
        doc_dir=out_dir, 
        out_dir=out_dir, 
        log_callback=lambda msg: print(f"[AutoAI] {msg}"),
        force=True, 
        enable_followup=False, 
        max_followup=0, 
        start_day=1,
        adaptive_mode=False,
        generate_visuals=False
    )
    
    md_file = os.path.join(out_dir, "Day1.md")
    if os.path.exists(md_file):
        print("\n=== KẾT QUẢ CỦA BÀI HỌC DAY 1 ĐƯỢC AUTO AI SINH RA ===")
        with open(md_file, "r", encoding="utf-8") as f:
            print(f.read()[:2500] + "\n... [TRUNCATED] ...")
    else:
        print("\nKhông tìm thấy file Day1.md do Auto AI sinh ra.")

if __name__ == "__main__":
    test_e2e_askcpl()
