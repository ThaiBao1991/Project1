# -*- coding: utf-8 -*-
"""
Module: run_cli.py
Giao diện điều khiển dòng lệnh (CLI) tương tác cho hệ thống tạo đề thi MBC DeThi.

Menu chính:
  1. Đóng gói toàn bộ PDF → Prompt cho NotebookLM (Bước 1)
  2. Nhập câu hỏi từ NotebookLM / JSON → Thẩm định và lưu vào ngân hàng (Bước 2)
  3. Xem báo cáo tiến độ 409 file (Bước 3)
  4. Xuất file Word Đề thi & Đáp án hoàn chỉnh (Bước 4)
  5. Test nhanh: Pack + Demo thẩm định câu hỏi mẫu (Bước 5 - phục vụ kiểm chứng)
  0. Thoát
"""

import os
import sys
import json
import glob

sys.stdout.reconfigure(encoding='utf-8')

from pdf_extractor import scan_all_sources
from notebooklm_packager import package_pdf_to_file, parse_notebooklm_response
from question_validator import QuestionValidator
from exam_word_merger import (
    merge_and_export,
    export_folder_exam_and_answer,
    export_all_individual_folders,
    export_all_single_files_all_folders,
    export_all_single_files_by_folder
)
from auto_question_generator import AutoQuestionGenerator

CONFIG_PATH = "config.json"


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def step1_pack_all_pdfs(config: dict):
    """BƯỚC 1: Đóng gói toàn bộ PDF thành file prompt sẵn sàng nạp vào NotebookLM."""
    source_dir = config.get("source_dir", "Source")
    prompts_dir = config.get("prompts_dir", "KetQua/prompts_for_notebooklm")
    folder_order = config.get("folder_order", [])

    print("\n📦 BƯỚC 1: ĐÓNG GÓI PDF → PROMPT NOTEBOOKLM")
    print("=" * 60)

    all_sources = scan_all_sources(source_dir, folder_order)

    # Cho phép lọc theo thư mục cụ thể
    print("Chọn thư mục cần xử lý:")
    print("  0 = Tất cả (409 file)")
    for i, fn in enumerate(folder_order, start=1):
        slug = fn.split()[0]
        count = len([x for x in all_sources if x["folder_name"] == fn])
        print(f"  {i} = {fn} ({count} file)")
    choice = input("Nhập lựa chọn (0-8): ").strip()

    if choice == "0":
        selected = all_sources
    elif choice.isdigit() and 1 <= int(choice) <= len(folder_order):
        target_folder = folder_order[int(choice) - 1]
        selected = [x for x in all_sources if x["folder_name"] == target_folder]
    else:
        print("Lựa chọn không hợp lệ, mặc định xử lý tất cả.")
        selected = all_sources

    # Hỏi có bỏ qua file đã có prompt chưa
    overwrite_str = input("\nBỏ qua file đã có prompt (y/n) [mặc định y]: ").strip().lower()
    skip_existing = overwrite_str != "n"

    done = 0
    skipped = 0
    errors = 0

    print(f"\nĐang đóng gói {len(selected)} file PDF...")
    for idx, item in enumerate(selected, start=1):
        folder_slug = item["folder_name"].split()[0]
        base_name = os.path.splitext(item["filename"])[0]
        expected_prompt = os.path.join(prompts_dir, folder_slug, f"{base_name}_prompt.txt")

        if skip_existing and os.path.exists(expected_prompt):
            skipped += 1
            continue

        try:
            out_path = package_pdf_to_file(item["full_path"], item["folder_name"], prompts_dir)
            done += 1
            if idx % 10 == 0 or idx == len(selected):
                print(f"  [{idx}/{len(selected)}] {done} xong, {skipped} bỏ qua, {errors} lỗi")
        except Exception as e:
            errors += 1
            print(f"  ⚠️ Lỗi {item['filename']}: {e}")

    print(f"\n✅ Hoàn thành! Đã tạo {done} file prompt tại: {os.path.abspath(prompts_dir)}")
    print(f"   Bỏ qua (đã có): {skipped} | Lỗi: {errors}")
    print("\n📋 HƯỚNG DẪN TIẾP THEO:")
    print("   1. Mở Google NotebookLM (notebooklm.google.com).")
    print("   2. Tạo notebook mới, upload các file *_prompt.txt từng lô (mỗi lô 1 thư mục).")
    print("   3. Hỏi NotebookLM bằng nội dung trong file prompt, copy phản hồi JSON.")
    print("   4. Quay lại menu này, chọn Bước 2 để nhập câu hỏi vào ngân hàng.")
    input("\nNhấn Enter để quay về menu...")


def step2_import_question(config: dict, validator: QuestionValidator):
    """BƯỚC 2: Nhập câu hỏi (JSON từ NotebookLM hoặc dán trực tiếp) → Thẩm định → Lưu."""
    print("\n📥 BƯỚC 2: NHẬP CÂU HỎI → NGÂN HÀNG CÂU HỎI")
    print("=" * 60)
    print("Phương thức nhập:")
    print("  1 = Nhập từ file JSON đã có (trong thư mục KetQua/prompts_for_notebooklm hoặc bất kỳ)")
    print("  2 = Dán trực tiếp text JSON từ NotebookLM vào terminal")
    mode = input("Chọn phương thức (1/2): ").strip()

    raw_text = ""
    if mode == "1":
        json_path = input("Nhập đường dẫn đến file JSON: ").strip().strip('"')
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                raw_text = f.read()
        else:
            print(f"❌ Không tìm thấy file: {json_path}")
            input("Nhấn Enter để quay lại...")
            return
    elif mode == "2":
        print("\nDán nội dung JSON từ NotebookLM vào đây (kết thúc bằng dòng '###END###'):")
        lines = []
        while True:
            ln = input()
            if ln.strip() == "###END###":
                break
            lines.append(ln)
        raw_text = "\n".join(lines)
    else:
        print("Lựa chọn không hợp lệ.")
        input("Nhấn Enter để quay lại...")
        return

    print("\n🔍 Đang phân tích và thẩm định câu hỏi...")
    data = parse_notebooklm_response(raw_text)

    if not data:
        print("❌ Không parse được JSON. Kiểm tra lại định dạng phản hồi từ NotebookLM.")
        input("Nhấn Enter để quay lại...")
        return

    is_valid, errors = validator.validate_data(data)
    file_name = data.get("file_name", "unknown.pdf")

    if is_valid:
        print(f"\n✅ HỢP LỆ! Bộ câu hỏi cho file '{file_name}' đạt chuẩn.")
    else:
        print(f"\n⚠️ CÓ LỖI trong bộ câu hỏi cho file '{file_name}':")
        for err in errors:
            print(f"   - {err}")
        save_choice = input("Vẫn lưu vào ngân hàng với trạng thái INVALID để chỉnh sửa sau? (y/n): ").strip().lower()
        if save_choice != "y":
            input("Nhấn Enter để quay lại...")
            return

    saved_path = validator.save_questions(data)
    print(f"\n💾 Đã lưu: {saved_path} (Trạng thái: {'OK' if is_valid else 'INVALID'})")
    input("Nhấn Enter để quay lại...")


def step2b_batch_import_jsons(config: dict, validator: QuestionValidator):
    """BƯỚC 2B: Tự động nạp hàng loạt các file JSON có sẵn trong thư mục."""
    print("\n📥 BƯỚC 2B: IMPORT HÀng LOẠT FILE JSON → NGÂN HÀNG CÂU HỎI")
    print("=" * 60)
    scan_dir = input("Nhập đường dẫn thư mục chứa các file JSON câu hỏi: ").strip().strip('"')
    if not os.path.exists(scan_dir):
        print(f"❌ Không tìm thấy thư mục: {scan_dir}")
        input("Nhấn Enter để quay lại...")
        return

    json_files = glob.glob(os.path.join(scan_dir, "**", "*.json"), recursive=True)
    print(f"Tìm thấy {len(json_files)} file JSON.")
    done = 0
    invalid = 0
    errors = 0

    for jf in json_files:
        try:
            with open(jf, "r", encoding="utf-8") as f:
                raw = f.read()
            data = parse_notebooklm_response(raw)
            if not data:
                print(f"  ⚠️ Bỏ qua (parse lỗi): {jf}")
                errors += 1
                continue
            is_valid, _ = validator.validate_data(data)
            validator.save_questions(data)
            if is_valid:
                done += 1
            else:
                invalid += 1
        except Exception as e:
            print(f"  ❌ Lỗi {jf}: {e}")
            errors += 1

    print(f"\n✅ Đã nạp: {done} OK | {invalid} INVALID | {errors} lỗi / {len(json_files)} file")
    input("Nhấn Enter để quay lại...")


def step3_show_progress(validator: QuestionValidator):
    """BƯỚC 3: Hiển thị báo cáo tiến độ toàn diện."""
    print("\n📊 BƯỚC 3: BÁO CÁO TIẾN ĐỘ NGÂN HÀNG CÂU HỎI")
    print("=" * 60)
    validator.print_progress()
    input("\nNhấn Enter để quay về menu...")


def step4_export_word(config: dict):
    """BƯỚC 4: Nối câu hỏi OK và xuất file Word (Đề thi & Đáp án)."""
    print("\n📄 BƯỚC 4: XUẤT FILE WORD ĐỀ THI & ĐÁP ÁN")
    print("=" * 60)
    print("Chọn hình thức xuất:")
    print("  1 = 📦 Gộp toàn bộ (Tất cả thư mục 2-000 đến 9-Z00 vào 1 đề & 1 đáp án tổng hợp)")
    print("  2 = 📑 Xuất file Word riêng biệt cho TỪNG BẢN TIÊU CHUẨN (từng file PDF)")
    print("  3 = 📑 Xuất riêng cho TẤT CẢ các thư mục tiêu chuẩn")
    print("  4 = 📑 Xuất riêng cho 1 thư mục cụ thể")
    sub_choice = input("Nhập lựa chọn (1-4, mặc định 1): ").strip()

    if sub_choice == "2":
        all_res = export_all_single_files_all_folders(CONFIG_PATH)
        total_files = sum(len(v) for v in all_res.values())
        print(f"\n✅ Đã xuất {total_files} bản tiêu chuẩn riêng biệt:")
        for fn, r_list in all_res.items():
            if r_list:
                print(f"  📁 {fn.split()[0]}: {len(r_list)} bản tại KetQua/{fn.split()[0]}/tung_ban/")
    elif sub_choice == "3":
        results = export_all_individual_folders(CONFIG_PATH)
        for fn, res in results.items():
            if "error" not in res:
                print(f"  ✅ {fn.split()[0]}: {res.get('total_questions')} câu → {os.path.basename(res.get('exam'))}")
            else:
                print(f"  ⚪ {fn.split()[0]}: {res.get('error')}")
    elif sub_choice == "4":
        folder_order = config.get("folder_order", [])
        for i, fn in enumerate(folder_order, 1):
            print(f"  {i} = {fn}")
        f_idx = input("Chọn thư mục (1-8): ").strip()
        if f_idx.isdigit() and 1 <= int(f_idx) <= len(folder_order):
            target_fn = folder_order[int(f_idx) - 1]
            res = export_folder_exam_and_answer(target_fn, CONFIG_PATH)
            if "error" in res:
                print(f"  ⚠ {res['error']}")
            else:
                print(f"  ✅ Đã xuất {target_fn.split()[0]}: {res.get('total_questions')} câu")
                print(f"     Đề thi: {res.get('exam')}")
                print(f"     Đáp án: {res.get('answer')}")
    else:
        result = merge_and_export(CONFIG_PATH)
        if result:
            print(f"\n✅ Hoàn thành xuất file tổng hợp!")
            print(f"   📝 Đề thi: {result.get('exam', 'N/A')}")
            print(f"   📋 Đáp án: {result.get('answer', 'N/A')}")
    input("\nNhấn Enter để quay lại...")


def step7_launch_gui():
    """Khởi động Giao diện Desktop Đồ họa (CustomTkinter GUI)."""
    import subprocess
    print("\n🖥 Đang khởi động Giao diện Desktop DeThi GUI...")
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_gui.py")
    subprocess.Popen([sys.executable, script_path])
    print("✅ Đã mở cửa sổ giao diện đồ họa thành công.")


def step5_demo_validate(config: dict, validator: QuestionValidator):
    """BƯỚC 5: Demo - Sinh mẫu dữ liệu câu hỏi thử nghiệm và thẩm định nó."""
    print("\n🧪 BƯỚC 5: DEMO THẨM ĐỊNH MẪU DỮ LIỆU CÂU HỎI")
    print("=" * 60)

    demo_data = {
        "file_name": "000-0-V.pdf",
        "folder_name": "2-000 Ban V IT HOA",
        "doc_title": "Bản tiêu chuẩn điểm kiểm hàng ngày dùng chung cho dụng cụ đo",
        "doc_code": "000-0",
        "target_audience": "Đội trưởng và nhân viên LK, TP, HC, ĐGSP, GCCK",
        "questions": [
            {
                "question_number": 1,
                "is_key": False,
                "question_text": "Tiến độ điểm kiểm của dụng cụ đo theo Bản tiêu chuẩn 000-0 là như thế nào?",
                "options": {
                    "A": "Mỗi lần sử dụng",
                    "B": "1 tuần/lần",
                    "C": "1 tháng/lần",
                    "D": "1 năm/lần"
                },
                "correct_answer": "A",
                "reference_note": "Căn cứ: Mục 'Tiến độ điểm kiểm: Mỗi lần sử dụng'"
            },
            {
                "question_number": 2,
                "is_key": True,
                "question_text": "◎ Khi phát hiện gỉ sét trên bề mặt kim loại của dụng cụ đo, dù rất nhỏ, cần xử lý như thế nào?",
                "options": {
                    "A": "Tiếp tục sử dụng nếu gỉ nhỏ không ảnh hưởng",
                    "B": "Lau sạch và tự ý điều chỉnh",
                    "C": "Loại bỏ vết gỉ đó và báo cáo người có trách nhiệm",
                    "D": "Bảo quản thêm dầu và tiếp tục dùng"
                },
                "correct_answer": "C",
                "reference_note": "Căn cứ: Mục 3 Ngoại quan (3): Có gỉ dù rất nhỏ cũng phải loại bỏ"
            },
            {
                "question_number": 3,
                "is_key": False,
                "question_text": "Theo Bản tiêu chuẩn 000-0, khi kết quả điểm kiểm dị thường thì cần xử lý như thế nào?",
                "options": {
                    "A": "Tự xử lý và không cần ghi chép",
                    "B": "Xử lý theo chỉ thị của người có trách nhiệm quản lý",
                    "C": "Tiếp tục sử dụng và báo cáo sau",
                    "D": "Thay thế dụng cụ ngay lập tức mà không cần báo cáo"
                },
                "correct_answer": "B",
                "reference_note": "Căn cứ: Phần giới thiệu bản tiêu chuẩn: 'Trường hợp kết quả điểm kiểm dị thường thì xử lý theo chỉ thị của người có trách nhiệm quản lý'"
            }
        ]
    }

    is_valid, errors = validator.validate_data(demo_data)
    print("📋 Kết quả thẩm định bộ câu hỏi demo (000-0-V.pdf):")
    if is_valid:
        print("  ✅ HỢP LỆ - Đạt chuẩn OK!")
    else:
        print(f"  ❌ INVALID - Có {len(errors)} lỗi:")
        for e in errors:
            print(f"     - {e}")

    save = input("\nLưu bộ câu hỏi demo vào ngân hàng? (y/n): ").strip().lower()
    if save == "y":
        saved = validator.save_questions(demo_data)
        print(f"  💾 Đã lưu: {saved}")

    input("\nNhấn Enter để quay lại...")


def step6_auto_generate(config: dict):
    """BƯỚC 6: Tự động sinh câu hỏi hoàn toàn bằng Gemini Files API."""
    print("\n⚡ BƯỚC 6: TỰ ĐỘNG SINH CÂU HỎI BẰNG GEMINI API")
    print("=" * 60)
    print("Ưu điểm: Gemini đọc PDF trực tiếp (Files API) — không cần NotebookLM thủ công.")
    print()

    try:
        gen = AutoQuestionGenerator(CONFIG_PATH, log_fn=print)
    except RuntimeError as e:
        print(str(e))
        input("\nNhấn Enter để quay lại...")
        return

    folder_order = config.get("folder_order", [])
    print("Chọn thư mục cần xử lý:")
    print("  0 = Tất cả (409 file, ~35-40 phút)")
    for i, fn in enumerate(folder_order, start=1):
        print(f"  {i} = {fn}")
    choice = input("Nhập lựa chọn (0-8): ").strip()

    if choice == "0":
        selected = folder_order
    elif choice.isdigit() and 1 <= int(choice) <= len(folder_order):
        selected = [folder_order[int(choice) - 1]]
    else:
        print("Lựa chọn không hợp lệ, mặc định xử lý tất cả.")
        selected = folder_order

    # Chọn chế độ chạy: Bổ sung vs Làm lại từ đầu
    print("\nChọn chế độ thực hiện:")
    print("  1 = ⚡ Chạy tiếp tục / Bổ sung (Chỉ xử lý file mới hoặc chưa có - Mặc định)")
    print("  2 = 🔄 Chạy lại từ đầu (Sinh mới và ghi đè toàn bộ câu hỏi)")
    mode_choice = input("Nhập lựa chọn (1-2, mặc định 1): ").strip()
    force_regen = (mode_choice == "2")

    if force_regen:
        print("⚠️ CẢNH BÁO: Bạn đang chọn LÀM LẠI TỪ ĐẦU.")
        confirm_fresh = input("Xác nhận ghi đè toàn bộ dữ liệu cũ? (yes/no): ").strip().lower()
        if confirm_fresh not in ("yes", "y"):
            print("Đã huỷ.")
            input("\nNhấn Enter để quay lại...")
            return

    # Đối chiếu file mới / còn thiếu
    detect = gen.detect_new_and_missing_files(selected)
    print(f"\n🔍 Thống kê đối chiếu:")
    print(f"   • Tổng số file: {detect['total_count']}")
    print(f"   • Đã hoàn thành OK: {detect['done_count']}")
    print(f"   • Cần xử lý: {detect['missing_count'] if not force_regen else detect['total_count']}")

    confirm = input("\nXác nhận bắt đầu vòng lặp? (y/n): ").strip().lower()
    if confirm != "y":
        input("Đã huỷ. Nhấn Enter để quay lại...")
        return

    _stop = [False]
    try:
        result = gen.run_loop_until_complete(
            selected_folders=selected,
            stop_check=lambda: _stop[0],
            force_regenerate=force_regen
        )
        print(f"\n✅ Hoàn thành! Tổng: {result['total']} | Đã xong: {result['done']} | Còn thiếu: {result['missing']}")
    except KeyboardInterrupt:
        _stop[0] = True
        print("\n⛔ Đã dừng bởi người dùng.")

    input("\nNhấn Enter để quay về menu...")


def main():
    print("=" * 72)
    print("  🏭  HỆ THỐNG TẠO ĐỀ THI & ĐÁP ÁN NHẬN ĐỊNH TƯ CÁCH NHÂN VIÊN/ĐỘI TRƯỞNG")
    print("  📍  MBC DeThi MVP — Mabuchi Motor Vietnam")
    print("=" * 72)

    config = load_config()
    validator = QuestionValidator(CONFIG_PATH)

    while True:
        print("\n===== MENU CHÍNH =====")
        print("  🖥 --- GIAO DIỆN ĐỒ HỌA DESKTOP ---")
        print("  7. 🖥 Khởi động Giao diện đồ họa (GUI)         [GIAO DIỆN]")
        print("  ---")
        print("  ⚡ --- HOÀN TOÀN TỰ ĐỘNG (Không cần NotebookLM) ---")
        print("  6. ⚡ Tự động sinh câu hỏi (Gemini Files API)  [BƯỚC 6]")
        print("  ---")
        print("  1. 📦 Đóng gói PDF → Prompt NotebookLM        [BƯỚC 1]")
        print("  2. 📥 Nhập câu hỏi từ NotebookLM (1 file)      [BƯỚC 2]")
        print("  2b. 📥 Import hàng loạt file JSON               [BƯỚC 2B]")
        print("  ---")
        print("  3. 📊 Xem báo cáo tiến độ 409 file             [BƯỚC 3]")
        print("  4. 📄 Xuất file Word Đề thi & Đáp án            [BƯỚC 4]")
        print("  5. 🧪 Demo: Thẩm định câu hỏi mẫu              [TEST]")
        print("  0. 🚪 Thoát")
        print("=" * 25)

        choice = input("Nhập lựa chọn: ").strip().lower()

        if choice == "7":
            step7_launch_gui()
        elif choice == "6":
            step6_auto_generate(config)
        elif choice == "1":
            step1_pack_all_pdfs(config)
        elif choice == "2":
            step2_import_question(config, validator)
        elif choice in ("2b", "2B"):
            step2b_batch_import_jsons(config, validator)
        elif choice == "3":
            step3_show_progress(validator)
        elif choice == "4":
            step4_export_word(config)
        elif choice == "5":
            step5_demo_validate(config, validator)
        elif choice == "0":
            print("\n✅ Thoát. Chúc công việc thuận lợi!")
            break
        else:
            print("⚠️ Lựa chọn không hợp lệ. Vui lòng nhập lại.")


if __name__ == "__main__":
    main()
