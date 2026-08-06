import os
import re
import sys
import codecs
import requests
from bs4 import BeautifulSoup
import time
import json
import urllib.parse
# from google import genai # (Uncomment nếu dùng Gemini API thật)

# Fix Unicode console output on Windows
if sys.platform.startswith('win'):
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())


# Các file dữ liệu cần quét
TARGET_FILES = [
    "data_Tuong.md",
    "data_ChucQuan.md",
    "data_Linh.md",
    "data_Meo.md",
    "data_VuKhi_Do.md",
    "data_Skill.md"
]

# Regex để tìm dòng có chứa link. Ví dụ:
# 28. **[Gamersky]** Giải ảo: Cầm nhiều tướng có đặc tính "Kiếp Lược" có cộng dồn vàng không? *https://www.gamersky.com/handbook/200712/89355.shtml*
LINK_PATTERN = re.compile(r'^(.*?)\*(https?://[^\*]+)\*$')

def check_if_already_answered(lines, current_idx):
    """
    Kiểm tra xem dưới dòng link (current_idx) đã có khối blockquote `> ` trả lời chưa.
    """
    if current_idx + 1 < len(lines):
        next_line = lines[current_idx + 1].strip()
        if next_line.startswith(">"):
            return True
    return False

def check_semantic_existence(question, full_text):
    """
    (Nâng cao) Dùng AI hoặc Regex để check xem câu hỏi đã được giải đáp ở phần khác trong file chưa.
    Ở đây dùng mô phỏng cơ bản: tìm keyword chính trong file.
    """
    # Ví dụ: lấy từ trong ngoặc kép
    keywords = re.findall(r'"([^"]*)"', question)
    for kw in keywords:
        # Nếu keyword xuất hiện > 2 lần (1 lần ở bảng, 1 lần ở link), có thể nó đã có giải thích
        if full_text.count(kw) > 2:
            pass # TODO: Implement deep semantic check with LLM
            
    return False # Mặc định giả định là chưa có giải thích chi tiết

def fetch_and_summarize_content(url, question):
    """
    Cào dữ liệu từ URL và dùng AI tóm tắt trả lời đúng câu hỏi.
    """
    print(f"      [FETCHING] Đang cào dữ liệu từ: {url} ...")
    try:
        # Giả lập Anti-bot Header
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            text_content = soup.get_text(separator=' ', strip=True)
            
            # TODO: Gửi `text_content` và `question` vào Gemini API để tóm tắt.
            # client = genai.Client(api_key=GEMINI_API_KEY)
            # prompt = f"Đọc nội dung sau và trả lời ngắn gọn câu hỏi: {question}\nNội dung: {text_content[:3000]}"
            # response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
            # return f"> **Chi tiết:** {response.text}"
            
            return f"> **Chi tiết:** [Dữ liệu mô phỏng từ {url}. Cần mở comment code dùng API Gemini để tóm tắt thực tế]"
        else:
            return f"> **Lỗi:** Không thể truy cập link (HTTP {response.status_code}). Trang web có thể đã chết."
    except Exception as e:
        return f"> **Lỗi:** Request thất bại (URL chết hoặc bị chặn). Chi tiết: {type(e).__name__}"

def process_file(filepath):
    print(f"\n--- Bắt đầu quét file: {os.path.basename(filepath)} ---")
    if not os.path.exists(filepath):
        print(f"  [ERROR] File không tồn tại.")
        return

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        full_text = "".join(lines)

    new_lines = []
    changes_made = 0

    i = 0
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)
        match = LINK_PATTERN.match(line.strip())
        
        if match:
            question_text = match.group(1).strip()
            url = match.group(2).strip()
            
            print(f"  [LINK FOUND] {question_text[:50]}...")
            
            # 1. Kiểm tra xem ngay dưới link đã có dòng `>` chưa?
            if check_if_already_answered(lines, i):
                print("    -> [SKIPPED] Đã có blockquote giải đáp ở ngay dưới.")
            else:
                # 2. (Tùy chọn) Kiểm tra ngữ nghĩa toàn file xem có chưa
                if check_semantic_existence(question_text, full_text):
                    print("    -> [SKIPPED] Thông tin đã có sẵn trong file (Semantic Check).")
                else:
                    # 3. Tiến hành cào dữ liệu & Bổ sung
                    summary = fetch_and_summarize_content(url, question_text)
                    new_lines.append(summary + "\n")
                    changes_made += 1
                    print("    -> [ADDED] Đã bổ sung nội dung mới.")
        i += 1

    if changes_made > 0:
        # ⚠️ CHÚ Ý: LUÔN DÙNG MÃ HÓA 2 CHIỀU ĐỒNG BỘ KHI CẦN THIẾT. Ở đây là ghi file text trơn.
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"  [DONE] Đã lưu {changes_made} thay đổi vào {os.path.basename(filepath)}.")
    else:
        print(f"  [DONE] Không có link nào cần cập nhật thêm.")

def main():
    print("=== BẮT ĐẦU LUỒNG KIỂM TRA & TẢI DỮ LIỆU TỰ ĐỘNG ===")
    for filename in TARGET_FILES:
        filepath = os.path.join(os.path.dirname(__file__), filename)
        process_file(filepath)
    print("=== HOÀN TẤT ===")

if __name__ == "__main__":
    main()
