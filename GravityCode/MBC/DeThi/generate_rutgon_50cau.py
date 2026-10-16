# -*- coding: utf-8 -*-
"""
Module: generate_rutgon_50cau.py  (PHIÊN BẢN 4.0 - ĐỀ THI RÚT GỌN 60 CÂU - 80% TIÊU CHUẨN 1-A)
Mục đích:
- Chọn lọc chính xác 60 câu hỏi trắc nghiệm rút gọn cho Hệ thống Đề thi MBC:
  + 80% là tiêu chuẩn 1-A00 (mục tiêu 48 câu).
  + Nếu 1-A00 qua kiểm tra nghiêm ngặt không đủ 48 câu (do loại bỏ câu SI, câu generic, câu tra mã số),
    hệ thống tự động lấy bù từ các tiêu chuẩn thiết bị còn lại (2-000 đến 9-Z00) để đảm bảo đủ 60 câu.
  + Tự động làm sạch 100% ký tự tiếng Nhật còn sót lại (như 【校正】, 判定法...).
  + Lược bỏ tham chiếu số trang gây khó hiểu (tại trang 4, trang 2...).
  + Loại bỏ câu hỏi tra cứu mã số hình thức, chỉ giữ lại câu hỏi về nội dung, quy trình, yêu cầu thực tế.
  + Cơ chế chống file lock an toàn khi lưu file Word.
"""

import os
import sys
import json
import glob
import re
from typing import List, Dict, Any, Tuple, Set

try:
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BANK_BASE = os.path.join(ROOT_DIR, "KetQua", "questions_bank")
OUTPUT_DIR = os.path.join(ROOT_DIR, "KetQua")
CONFIG_PATH = os.path.join(ROOT_DIR, "config.json")

from exam_word_merger import build_exam_doc, build_answer_doc
from generate_rutgon import should_exclude_question, strip_vietnamese_accents

# ─────────────────────────────────────────────────────────────────────────────
# HAM LAM SACH KY TU TIENG NHAT VA THAM CHIEU SO TRANG
# ─────────────────────────────────────────────────────────────────────────────
def clean_text_content(text: str) -> str:
    """Loai bo ky tu tieng Nhat, ngoac tieng Nhat va tham chieu so trang gay kho hieu."""
    if not text:
        return ""
    # 1. Xoa cac cum tieng Nhat trong ngoac don hoac ngoac vuong
    # Vi du: (【校正】), (判定法), 【点検】, (【Kiểm điểm】)
    text = re.sub(r'[\(（]?【[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff66-\uff9f\s\w]+】[\)）]?', '', text)
    text = re.sub(r'[\(（][\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff66-\uff9f\s]+[\)）]', '', text)
    # 2. Xoa cac ky tu tieng Nhat don le neu con
    text = re.sub(r'[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff66-\uff9f]', '', text)
    # 3. Xoa dau ngoac vuong dac biet 【】
    text = text.replace("【", "").replace("】", "")
    # 4. Xoa tham chieu so trang gay kho hieu nhu "tai trang 4,", "(trang 2),", "tai trang 4"
    text = re.sub(r'\s*\(?trang\s*\d+\)?\s*,?', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*tai\s+trang\s*\d+\s*,?', ' ', text, flags=re.IGNORECASE)
    # 5. Chuan hoa khoang trang
    text = re.sub(r'\s{2,}', ' ', text).strip()
    return text


# ─────────────────────────────────────────────────────────────────────────────
# BANG BO LOC "GENERIC ABNORMAL" - Loai bo cau hoi khuon mau chung
# ─────────────────────────────────────────────────────────────────────────────
_GENERIC_ABNORMAL_QT_PATTERNS = [
    r"(di thuong|bat thuong).*(phai xu ly|lam gi|xu ly the nao|xu ly nhu the nao|quy dinh nao duoi day|thao tac the nao)",
    r"(phat hien|truong hop|ket qua).*(di thuong|bat thuong).*(nhan vien|thao tac|thuc hien).*(phai|lam gi|xu ly)",
    r"(diem kiem|kiem tra|su dung|hieu chinh).*(co |phat hien |thay )?(di thuong|bat thuong).*(nhan vien|nguoi|phai |lam gi|xu ly)",
    r"truong hop.*(di thuong|bat thuong).*(phai xu ly|xu ly nhu the nao|lam gi)",
    r"khi ket qua diem kiem phat hien co di thuong",
    r"sau khi kiem tra.*phat hien truong hop bat thuong.*xu ly nhu the nao",
]


def is_generic_abnormal(q: Dict[str, Any]) -> bool:
    """Phat hien cau hoi khuon mau 'phat hien di thuong/bat thuong thi lam gi'."""
    qt = q.get("question_text", "")
    norm_qt = strip_vietnamese_accents(qt.lower())
    for p in _GENERIC_ABNORMAL_QT_PATTERNS:
        if re.search(p, norm_qt):
            return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# HAM PHAN LOAI VA CHAM DIEM CAU HOI
# ─────────────────────────────────────────────────────────────────────────────
def analyze_and_tag_question(q: Dict[str, Any], doc_title: str = "") -> Tuple[int, List[str], str]:
    """Phan tich, cham diem va gan the chu de cho cau hoi."""
    qt = q.get("question_text", "").strip()
    opts = q.get("options", {})
    opts_str = " ".join(str(v) for v in opts.values())
    full_norm = strip_vietnamese_accents((qt + " " + opts_str).lower())

    score = 0
    tags = []
    main_topic = "Nghiep vu chung"

    # 1. Nhan & Mau sac (Quy dinh dan nhan, chu ky 12 thang)
    if any(k in full_norm for k in ["dan nhan", "mau sac", "mau nen", "phong mau",
                                      "nhan chung nhan", "nhan so", "nhan dan"]) or \
       ("nhan" in full_norm and any(c in full_norm for c in ["mau", "xanh", "do", "vang", "trang"])):
        score += 45
        tags.append("Nhan & Mau sac")
        main_topic = "Quy dinh dan nhan & Mau sac"

    # 2. Thoi gian luu tru tai lieu
    if any(k in full_norm for k in ["luu tru", "ky han luu tru", "thoi gian luu tru", "ho so hieu chinh"]):
        score += 40
        tags.append("Luu tru ho so")
        if main_topic == "Nghiep vu chung":
            main_topic = "Thoi gian luu tru tai lieu"

    # 3. May nghi & Han dinh
    if any(k in full_norm for k in ["may nghi", "giai tru may nghi", "han dinh", "su dung co han dinh"]):
        score += 40
        tags.append("May nghi & Han dinh")
        if main_topic == "Nghiep vu chung":
            main_topic = "Dac diem may nghi & Han dinh"

    # 4. Quy trinh bat hop cach (co noi dung cu the)
    if any(k in full_norm for k in ["bat hop cach", "khong hop cach", "xu ly motor",
                                      "thong bao khach hang", "bao cao truong phong"]):
        score += 35
        tags.append("Bat hop cach")
        if main_topic == "Nghiep vu chung":
            main_topic = "Quy trinh xu ly bat hop cach"

    # 5. Xac nhan & Dieu kien moi truong
    if any(k in full_norm for k in ["xac nhan may do", "dieu kien moi truong",
                                      "nhiet do", "do am", "truoc khi su dung"]):
        score += 30
        tags.append("Xac nhan & Moi truong")
        if main_topic == "Nghiep vu chung":
            main_topic = "Noi dung can xac nhan & Dieu kien moi truong"

    # 6. Luu trinh / Trach nhiem / Ai thuc hien
    if any(k in full_norm for k in ["quy trinh", "trinh tu", "luu do", "ai la nguoi",
                                      "trach nhiem", "phuong phap xu ly", "tham quyen"]):
        score += 25
        tags.append("Luu trinh / Trach nhiem")
        if main_topic == "Nghiep vu chung":
            main_topic = "Luu trinh & Trach nhiem"

    # 7. Thong so ky thuat / Dung sai / Chu ky / Ten thiet bi cu the
    if any(k in full_norm for k in ["dung sai", "do chinh xac", "phan dinh", "chu ky", "cham dau", "dien ap", "sensor", "dong ho", "can dien tu", "laser"]):
        score += 30
        tags.append("Ky thuat dac thu")
        if main_topic == "Nghiep vu chung":
            main_topic = "Thong so & Quy cach ky thuat"

    # 8. Co con so cu the (thoi gian, chu ky, dien ap)
    has_number = bool(re.search(r'\d+\s*(lan|thang|nam|gio|phut|nen|ngay|%|mm|um|µm|kg|v|mv|hz|khz)', full_norm))
    if has_number:
        score += 20
        tags.append("Co con so cu the")

    # 9. Cau chu chot (◎)
    if "◎" in qt or q.get("is_key", False):
        score += 15
        tags.append("Chu chot")

    # 10. PHAT TRIET DE cau khuon mau "bat thuong diem kiem" generic
    if is_generic_abnormal(q):
        score -= 500
        tags.append("GENERIC_ABNORMAL")
        main_topic = "Khuon mau chung - can tranh"

    # 11. PHAT cau chi hoi ma so hinh thuc
    if any(k in full_norm for k in ["ung voi ten thuong goi nao", "ma so cua", "phan ky hieu"]):
        score -= 500
        tags.append("MA_SO_LOOKUP")

    return score, tags, main_topic


# ─────────────────────────────────────────────────────────────────────────────
# CHUAN HOA CAU HOI VA LAM SACH DU LIEU
# ─────────────────────────────────────────────────────────────────────────────
def sanitize_question_dict(q: Dict[str, Any], doc_title: str) -> Dict[str, Any]:
    """Tao ban sao sach cua cau hoi: xoa tieng Nhat, xoa trang X, lam ro thiet bi."""
    q_clean = dict(q)
    raw_qt = clean_text_content(q.get("question_text", ""))

    # Neu cau hoi hoi diem 0 hoac kiem tra ma chua noi ro thiet bi nao, bo sung ten thiet bi
    norm_qt = strip_vietnamese_accents(raw_qt.lower())
    if "xac nhan diem 0" in norm_qt and not any(k in norm_qt for k in ["dong ho", "may do", "can", "sensor"]):
        clean_title = clean_text_content(doc_title)
        raw_qt = raw_qt.replace("xác nhận điểm 0", f"xác nhận điểm 0 ({clean_title})")

    q_clean["question_text"] = raw_qt

    opts = q.get("options", {})
    opts_clean = {}
    for k, v in opts.items():
        opts_clean[k] = clean_text_content(str(v))
    q_clean["options"] = opts_clean

    if "explanation" in q_clean:
        q_clean["explanation"] = clean_text_content(q_clean.get("explanation", ""))
    if "reference_note" in q_clean:
        q_clean["reference_note"] = clean_text_content(q_clean.get("reference_note", ""))

    return q_clean


# ─────────────────────────────────────────────────────────────────────────────
# CHON CAU HOI TU 1-A00 (MUC TIEU 80% = 48 CAU)
# ─────────────────────────────────────────────────────────────────────────────
def select_questions_1a(target_count: int = 48) -> List[Dict[str, Any]]:
    """Chon loc cau hoi tu 1-A00:
    - 0 cau SI, 0 cau generic, 0 cau ma so hinh thuc.
    - Moi file lay 1-2 cau chat luong cao (khac chu de).
    - Tra ve danh sach cau thuc te dat chuan.
    """
    a100_dir = os.path.join(BANK_BASE, "1-A00")
    files_data: Dict[str, List[Dict]] = {}

    for jf in sorted(glob.glob(os.path.join(a100_dir, "*.json"))):
        fname = os.path.basename(jf)
        with open(jf, "r", encoding="utf-8") as f:
            d = json.load(f)

        doc_title = clean_text_content(d.get("doc_title", ""))
        candidates = []
        for q in d.get("questions", []):
            exc, _ = should_exclude_question(fname, q)
            if exc:
                continue
            if is_generic_abnormal(q):
                continue

            sc, tags, topic = analyze_and_tag_question(q, doc_title)
            if sc <= 0:
                continue

            q_sanitized = sanitize_question_dict(q, doc_title)
            candidates.append({
                "folder_name": "1-A00 Ban V IT HOA",
                "folder_slug": "1-A00",
                "file_name": fname,
                "doc_code": d.get("doc_code", fname.replace(".json", "")),
                "doc_title": doc_title,
                "target_audience": d.get("target_audience", "Doi truong va nhan vien LK, TP, HC, DGSP, GCCK"),
                "score": sc,
                "tags": tags,
                "topic": topic,
                "is_generic": False,
                "is_key": "◎" in q_sanitized.get("question_text", "") or q.get("is_key", False),
                "question": q_sanitized
            })

        if candidates:
            candidates.sort(key=lambda x: (x["score"], x["is_key"]), reverse=True)
            files_data[fname] = candidates

    print(f"📊 [1-A00] Co {len(files_data)} ban tieu chuan hop le sau khi loc nghiem ngat.")

    selected: List[Dict] = []
    used_doc_codes: Set[str] = set()

    # Vong 1: Moi file lay 1 cau tot nhat (unique doc_code)
    for fname in sorted(files_data.keys()):
        cands = files_data[fname]
        for c in cands:
            if c["doc_code"] not in used_doc_codes:
                selected.append(c)
                used_doc_codes.add(c["doc_code"])
                break

    print(f"  -> Vong 1 (1-A00): Da chon {len(selected)} cau (moi file 1 cau).")

    # Vong 2: Bo sung cau thu 2 tu cac file co cau hay khac chu de (toi da 2 cau/file)
    used_files_for_2nd_pick: Set[str] = set()
    if len(selected) < target_count:
        file_to_selected_topics: Dict[str, Set[str]] = {}
        for s in selected:
            fn2 = s["file_name"]
            if fn2 not in file_to_selected_topics:
                file_to_selected_topics[fn2] = set()
            file_to_selected_topics[fn2].add(s["topic"])

        second_pool = []
        for fname, cands in files_data.items():
            if fname not in file_to_selected_topics:
                continue
            already_chosen_topics = file_to_selected_topics[fname]
            for c in cands[1:]:
                if c["topic"] not in already_chosen_topics:
                    second_pool.append(c)
                    break

        second_pool.sort(key=lambda x: (x["score"], x["is_key"]), reverse=True)
        needed = target_count - len(selected)
        for c in second_pool:
            if needed <= 0:
                break
            fn2 = c["file_name"]
            if fn2 in used_files_for_2nd_pick:
                continue
            selected.append(c)
            used_files_for_2nd_pick.add(fn2)
            needed -= 1

        print(f"  -> Vong 2 (1-A00): Bo sung {len(used_files_for_2nd_pick)} cau thu 2. Hien co {len(selected)} cau.")

    final = selected[:target_count]
    print(f"  -> Hoan tat chon {len(final)}/{target_count} cau tu 1-A00.")
    return final


# ─────────────────────────────────────────────────────────────────────────────
# CHON CAU HOI TU CAC PHAN CON LAI (2-000 den 9-Z00)
# ─────────────────────────────────────────────────────────────────────────────
def select_questions_other(target_count: int = 12) -> List[Dict[str, Any]]:
    """Chon loc cau hoi tu cac tieu chuan con lai (2-000 den 9-Z00):
    - 0 cau generic, sach 100% tieng Nhat, moi doc_code chi 1 cau.
    - Uu tien da dang thu muc: 2-000, 3-400, 4-500, 5-600, 6-900, 7-S00, 8-T00, 9-Z00.
    """
    folder_list = [
        "2-000",
        "4-500",
        "5-600",
        "7-S00",
        "9-Z00",
        "6-900",
        "8-T00",
        "3-400",
    ]

    folder_candidates: Dict[str, List[Dict]] = {}
    for fld in folder_list:
        fdir = os.path.join(BANK_BASE, fld)
        if not os.path.isdir(fdir):
            continue

        cands = []
        for jf in sorted(glob.glob(os.path.join(fdir, "*.json"))):
            fname = os.path.basename(jf)
            with open(jf, "r", encoding="utf-8") as f:
                d = json.load(f)

            doc_title = clean_text_content(d.get("doc_title", ""))
            for q in d.get("questions", []):
                exc, _ = should_exclude_question(fname, q)
                if exc:
                    continue
                if is_generic_abnormal(q):
                    continue

                sc, tags, topic = analyze_and_tag_question(q, doc_title)
                if sc <= 0:
                    continue

                q_sanitized = sanitize_question_dict(q, doc_title)
                doc_code = d.get("doc_code", fname.replace(".json", ""))
                cands.append({
                    "folder_name": f"{fld} Ban V IT HOA",
                    "folder_slug": fld,
                    "file_name": fname,
                    "doc_code": doc_code,
                    "doc_title": doc_title,
                    "target_audience": d.get("target_audience", "Doi truong va nhan vien LK, TP, HC, DGSP, GCCK"),
                    "score": sc,
                    "tags": tags,
                    "topic": topic,
                    "is_generic": False,
                    "is_key": "◎" in q_sanitized.get("question_text", "") or q.get("is_key", False),
                    "question": q_sanitized
                })

        if cands:
            cands.sort(key=lambda x: (x["score"], x["is_key"]), reverse=True)
            folder_candidates[fld] = cands

    selected: List[Dict] = []
    used_doc_codes: Set[str] = set()

    # Vong 1: Moi thu muc lay 1 cau tot nhat (phu deu tat ca thu muc)
    for fld in folder_list:
        if fld not in folder_candidates:
            continue
        for c in folder_candidates[fld]:
            if c["doc_code"] not in used_doc_codes:
                selected.append(c)
                used_doc_codes.add(c["doc_code"])
                break

    print(f"  -> Vong 1 (Cac phan khac): Da chon {len(selected)} cau (phu deu {len(folder_candidates)} thu muc).")

    # Vong 2: Bo sung theo han muc cac thu muc nhieu file (2-000, 4-500, 5-600, 7-S00)
    quota_v2 = {
        "2-000": 8,
        "4-500": 8,
        "5-600": 5,
        "7-S00": 4,
        "9-Z00": 3,
        "6-900": 3,
        "8-T00": 2,
        "3-400": 1,
    }

    for fld, quota in quota_v2.items():
        if len(selected) >= target_count:
            break
        if fld not in folder_candidates:
            continue
        cur_fld_count = sum(1 for it in selected if it["folder_slug"] == fld)
        for c in folder_candidates[fld]:
            if cur_fld_count >= quota or len(selected) >= target_count:
                break
            if c["doc_code"] in used_doc_codes:
                continue
            selected.append(c)
            used_doc_codes.add(c["doc_code"])
            cur_fld_count += 1

    # Vong 3: Neu van chua du target_count, gom tat ca ung vien con lai va chon theo diem cao nhat
    if len(selected) < target_count:
        all_remaining = []
        for fld, cands in folder_candidates.items():
            for c in cands:
                if c["doc_code"] not in used_doc_codes:
                    all_remaining.append(c)
        all_remaining.sort(key=lambda x: (x["score"], x["is_key"]), reverse=True)

        for c in all_remaining:
            if len(selected) >= target_count:
                break
            selected.append(c)
            used_doc_codes.add(c["doc_code"])

    final = selected[:target_count]
    print(f"  -> Hoan tat chon {len(final)}/{target_count} cau tu cac tieu chuan con lai (100% non-generic).")
    return final


# ─────────────────────────────────────────────────────────────────────────────
# HAM GOM NHOM THEO FILE
# ─────────────────────────────────────────────────────────────────────────────
def group_questions_by_file(selected_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Gom cac cau hoi lai theo tung file tai lieu theo cau truc cua exam_word_merger."""
    grouped: Dict = {}
    for item in selected_items:
        key = (item["folder_name"], item["file_name"])
        if key not in grouped:
            grouped[key] = {
                "folder_name": item["folder_name"],
                "file_name": item["file_name"],
                "doc_code": item["doc_code"],
                "doc_title": clean_text_content(item["doc_title"]),
                "target_audience": item["target_audience"],
                "status": "OK",
                "questions": []
            }
        grouped[key]["questions"].append(item["question"])

    return list(grouped.values())


# ─────────────────────────────────────────────────────────────────────────────
# HAM PIPELINE CHINH - XUAT DE THI VA DAP AN 60 CAU
# ─────────────────────────────────────────────────────────────────────────────
def generate_exam_and_answer_60_questions(total_target: int = 60, ratio_1a: float = 0.8):
    """Ham pipeline chinh V4.0: Chon loc 60 cau (80% 1-A00, linh dong bu) va xuat 2 file Word."""
    print("=" * 70)
    print(f" BAT DAU CHON LOC V4.0 - DE THI TONG HOP {total_target} CAU RUT GON")
    print(f" (Muc tieu: {int(total_target * ratio_1a)} cau 1-A00 [{int(ratio_1a*100)}%], linh hoat bu cau neu thieu)")
    print(" (Sach 100% tieng Nhat, khong so trang mo ho, khong cau hoi ma so)")
    print("=" * 70)

    target_1a = int(total_target * ratio_1a)
    list_1a = select_questions_1a(target_count=target_1a)
    needed_other = total_target - len(list_1a)

    print(f"\n📌 1-A00 chon duoc: {len(list_1a)} cau (dat {len(list_1a)/total_target*100:.1f}%).")
    print(f"📌 Can lay tu cac tieu chuan con lai: {needed_other} cau.")

    list_other = select_questions_other(target_count=needed_other)

    total_60 = list_1a + list_other
    print(f"\n✅ TONG CONG DA CHON: {len(total_60)} CAU ({len(list_1a)} cau 1-A00 + {len(list_other)} cau cac phan khac).")

    # Kiem tra file_name trung > 2 lan
    all_files = [it["file_name"] for it in total_60]
    dup_files_3plus = [fn for fn in set(all_files) if all_files.count(fn) > 2]
    dup_files_2 = [fn for fn in set(all_files) if all_files.count(fn) == 2]
    if dup_files_3plus:
        print(f"⚠ CANH BAO: {len(dup_files_3plus)} file bi chon > 2 cau: {dup_files_3plus}")
    else:
        print(f"✅ Kiem tra file uniqueness: OK ({len(dup_files_2)} file duoc chon 2 cau khac chu de).")

    # Kiem tra tieng Nhat con sot lai
    jp_regex = re.compile(r'[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff66-\uff9f【】]')
    jp_count = 0
    for it in total_60:
        qt = it["question"].get("question_text", "")
        opts = " ".join(str(v) for v in it["question"].get("options", {}).values())
        if jp_regex.search(qt + " " + opts):
            jp_count += 1
    print(f"📌 Kiem tra ky tu tieng Nhat: {jp_count} / {len(total_60)} cau co tieng Nhat (Muc tieu: 0).")

    # Kiem tra cau generic
    generic_list = [it for it in total_60 if is_generic_abnormal(it["question"])]
    print(f"📌 Cau khuon mau 'bat thuong diem kiem': {len(generic_list)} / {len(total_60)} cau.")

    # Kiem tra cau SI
    si_count = sum(1 for it in total_60 if "don vi si" in strip_vietnamese_accents(it["question"].get("question_text", "").lower()))
    print(f"📌 Cau hoan doi don vi SI: {si_count} / {len(total_60)} cau.")

    key_count = sum(1 for it in total_60 if it["is_key"])
    print(f"⭐ Tong so cau chu chot (ky hieu ◎): {key_count} / {len(total_60)} cau.")

    grouped_data = group_questions_by_file(total_60)

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    config_60 = dict(config)
    exam_settings = dict(config.get("exam_settings", {}))
    exam_settings["title"] = f"BAI TEST NHAN DINH TU CACH NHAN VIEN VA DOI TRUONG (DE RUT GON {len(total_60)} CAU)"
    exam_settings["revision"] = f"REV 14 (2026) - BAN TRONG DIEM {len(total_60)} CAU V4.0 (80% 1-A00)"
    config_60["exam_settings"] = exam_settings

    # Xuat file Word De thi
    exam_filename = f"DE THI TONG HOP {len(total_60)} CAU RUT GON.docx"
    exam_path = os.path.join(OUTPUT_DIR, exam_filename)
    print(f"\n📝 Dang tao file Word De thi: {exam_filename}...")
    exam_doc = build_exam_doc(config_60, grouped_data)
    try:
        exam_doc.save(exam_path)
        print(f"✅ Da luu file De thi: {exam_path}")
    except PermissionError:
        fallback_name = f"DE THI TONG HOP {len(total_60)} CAU RUT GON_Moi.docx"
        exam_path = os.path.join(OUTPUT_DIR, fallback_name)
        exam_doc.save(exam_path)
        print(f"⚠ File goc bi khoa boi Word, da luu file De thi sang: {exam_path}")

    # Xuat file Word Dap An
    ans_filename = f"DAP AN TONG HOP {len(total_60)} CAU RUT GON.docx"
    ans_path = os.path.join(OUTPUT_DIR, ans_filename)
    print(f"📋 Dang tao file Word Dap An: {ans_filename}...")
    ans_doc = build_answer_doc(config_60, grouped_data)
    try:
        ans_doc.save(ans_path)
        print(f"✅ Da luu file Dap An: {ans_path}")
    except PermissionError:
        fallback_ans = f"DAP AN TONG HOP {len(total_60)} CAU RUT GON_Moi.docx"
        ans_path = os.path.join(OUTPUT_DIR, fallback_ans)
        ans_doc.save(ans_path)
        print(f"⚠ File goc bi khoa boi Word, da luu file Dap An sang: {ans_path}")

    # Xuat file JSON snapshot
    json_filename = f"DE THI TONG HOP {len(total_60)} CAU RUT GON_questions.json"
    json_path = os.path.join(OUTPUT_DIR, json_filename)
    json_output = {
        "exam_title": exam_settings["title"],
        "revision": exam_settings["revision"],
        "total_questions": len(total_60),
        "total_1a_questions": len(list_1a),
        "total_other_questions": len(list_other),
        "total_key_questions": key_count,
        "generic_abnormal_count": len(generic_list),
        "japanese_character_count": jp_count,
        "questions_summary": [
            {
                "stt": idx + 1,
                "folder": it["folder_name"],
                "file": it["file_name"],
                "doc_code": it["doc_code"],
                "doc_title": it["doc_title"],
                "topic": it["topic"],
                "is_generic": is_generic_abnormal(it["question"]),
                "is_key": it["is_key"],
                "question_text": it["question"].get("question_text", ""),
                "correct_answer": it["question"].get("correct_answer", ""),
                "options": it["question"].get("options", {}),
                "explanation": it["question"].get("explanation", "")
            }
            for idx, it in enumerate(total_60)
        ],
        "files": grouped_data
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_output, f, ensure_ascii=False, indent=2)
    print(f"💾 Da luu du lieu JSON: {json_path}")

    print("\n" + "=" * 70)
    print(f" HOAN THANH XUAT BO DE RUT GON {len(total_60)} CAU V4.0!")
    print(f"  * De thi: {exam_path}")
    print(f"  * Dap An: {ans_path}")
    print(f"  * Du lieu JSON: {json_path}")
    print("=" * 70)

    return {
        "exam_path": exam_path,
        "ans_path": ans_path,
        "json_path": json_path,
        "total": len(total_60),
        "count_1a": len(list_1a),
        "count_other": len(list_other),
        "key_count": key_count,
        "generic_abnormal_count": len(generic_list),
        "japanese_count": jp_count
    }


if __name__ == "__main__":
    generate_exam_and_answer_60_questions(total_target=60, ratio_1a=0.8)
