import tkinter as tk
from tkinter import filedialog, messagebox
import json
from PyPDF2 import PdfReader
import re
import os

# Hàm trích xuất dữ liệu từ PDF
def extract_vocab_from_pdf(pdf_path):
    try:
        pdf_reader = PdfReader(pdf_path)
        vocab_dict = {}
        
        # Duyệt qua từng trang
        for page in pdf_reader.pages:
            text = page.extract_text()
            if not text:  # Bỏ qua trang trống
                continue
            lines = text.split('\n')
            
            # Biểu thức chính quy khớp với định dạng: No. Word Type Pronounce Meaning
            pattern = r"^\d+\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?(?:\s+[a-zA-Z]+)?)\s+([nva]\b|adj\b|adv\b|pron\b|det\b|conj\b|prep\b|exclamation\b(?:,\s*[nva]\b|,\s*adj\b|,\s*adv\b|,\s*pron\b|,\s*det\b|,\s*conj\b|,\s*prep\b|,\s*exclamation\b)?)\s*([əæeɪioʊuʌʃʒθðŋɒɔʌʊʔˈ][əæeɪioʊuʌʃʒθðŋɒɔʌʊʔˈ:]*?)?\s+(.+)$"
            
            for line in lines:
                line = line.strip()
                if not line or not re.match(r"^\d+", line):  # Bỏ qua dòng không bắt đầu bằng số
                    continue
                
                # Loại bỏ tiêu đề hoặc dòng không phải từ vựng
                if re.search(r"(TỪ\s*VỰNG|THÔNG\s*DỤNG|Oxford|Effortless|Trang|\bT\b\s*$)", line, re.IGNORECASE):
                    continue
                
                # Thay nhiều khoảng trắng bằng một khoảng trắng để chuẩn hóa
                line = re.sub(r"\s+", " ", line)
                
                match = re.match(pattern, line)
                if match:
                    word, word_type, pronounce, meaning = match.groups()
                    
                    # Chuẩn hóa dữ liệu
                    word = word.strip() if word else ""
                    word_type = word_type.strip() if word_type else "N/A"
                    pronounce = pronounce.strip() if pronounce and re.match(r"[əæeɪioʊuʌʃʒθðŋɒɔʌʊʔˈ].*", pronounce) else "N/A"
                    meaning = meaning.strip() if meaning else "N/A"
                    
                    # Tách pronounce nếu nó bị lẫn vào meaning
                    pronounce_pattern = r"([əæeɪioʊuʌʃʒθðŋɒɔʌʊʔˈ][əæeɪioʊuʌʃʒθðŋɒɔʌʊʔˈ:]*)\s+(.+)"
                    pronounce_match = re.match(pronounce_pattern, meaning)
                    if pronounce_match:
                        pronounce, meaning = pronounce_match.groups()
                    elif pronounce == "N/A" and meaning and re.match(r"[əæeɪioʊuʌʃʒθðŋɒɔʌʊʔˈ].*", meaning.split()[0] if meaning.split() else ""):
                        pronounce = meaning.split()[0]
                        meaning = " ".join(meaning.split()[1:]) if len(meaning.split()) > 1 else "N/A"
                    
                    # Đảm bảo word không lẫn type
                    if re.search(r"\s+(n|v|adj|adv|pron|det|conj|prep|exclamation)$", word):
                        word_parts = word.split()
                        word = " ".join(word_parts[:-1])
                        word_type = word_parts[-1]
                    
                    vocab_dict[word] = {
                        "type": word_type,
                        "pronounce": pronounce,
                        "meaning": meaning,
                        "correct_count": 0,
                        "completed_date": None
                    }
                else:
                    # Xử lý thủ công nếu regex không khớp
                    parts = re.split(r"\s+", line)
                    if len(parts) >= 4 and parts[0].isdigit():  # Đảm bảo có ít nhất 4 phần tử và bắt đầu bằng số
                        word = parts[1]
                        # Tìm type trong danh sách từ loại
                        type_idx = next((i for i, p in enumerate(parts[2:]) if re.match(r"^[nva]$|^adj$|^adv$|^pron$|^det$|^conj$|^prep$|^exclamation$", p)), None)
                        if type_idx is not None and type_idx + 2 < len(parts):  # Kiểm tra chỉ số hợp lệ
                            type_idx += 2  # Điều chỉnh chỉ số
                            word_type = parts[type_idx]
                            # Tìm pronounce
                            pronounce_idx = next((i for i, p in enumerate(parts[type_idx+1:]) if re.match(r"[əæeɪioʊuʌʃʒθðŋɒɔʌʊʔˈ].*", p)), None)
                            if pronounce_idx is not None and pronounce_idx + type_idx + 1 < len(parts):  # Kiểm tra chỉ số hợp lệ
                                pronounce_idx += type_idx + 1
                                pronounce = parts[pronounce_idx]
                                meaning = " ".join(parts[pronounce_idx+1:]) if pronounce_idx + 1 < len(parts) else "N/A"
                            else:
                                pronounce = "N/A"
                                meaning = " ".join(parts[type_idx+1:]) if type_idx + 1 < len(parts) else "N/A"
                        else:
                            word_type = "N/A"
                            pronounce = "N/A"
                            meaning = " ".join(parts[2:]) if len(parts) > 2 else "N/A"
                        
                        # Tách pronounce nếu cần
                        pronounce_pattern = r"([əæeɪioʊuʌʃʒθðŋɒɔʌʊʔˈ][əæeɪioʊuʌʃʒθðŋɒɔʌʊʔˈ:]*)\s+(.+)"
                        pronounce_match = re.match(pronounce_pattern, meaning)
                        if pronounce_match:
                            pronounce, meaning = pronounce_match.groups()
                        elif pronounce == "N/A" and meaning and re.match(r"[əæeɪioʊuʌʃʒθðŋɒɔʌʊʔˈ].*", meaning.split()[0] if meaning.split() else ""):
                            pronounce = meaning.split()[0]
                            meaning = " ".join(meaning.split()[1:]) if len(meaning.split()) > 1 else "N/A"
                        
                        vocab_dict[word] = {
                            "type": word_type,
                            "pronounce": pronounce,
                            "meaning": meaning,
                            "correct_count": 0,
                            "completed_date": None
                        }
        
        return vocab_dict
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể trích xuất dữ liệu từ PDF: {str(e)}")
        return None

# Hàm xuất dữ liệu ra file JSON
def export_to_json(vocab_dict, output_json):
    try:
        with open(output_json, 'w', encoding='utf-8') as json_file:
            json.dump(vocab_dict, json_file, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể xuất file JSON: {str(e)}")
        return False

# Hàm chọn file PDF
def choose_file():
    file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
    if file_path:
        entry_file.delete(0, tk.END)
        entry_file.insert(0, file_path)

# Hàm xử lý khi nhấn nút "Xuất JSON"
def export_json():
    input_pdf = entry_file.get()
    if not input_pdf:
        messagebox.showwarning("Cảnh báo", "Vui lòng chọn file PDF trước!")
        return
    
    output_json = os.path.splitext(input_pdf)[0] + "_vocab.json"
    
    vocab_dict = extract_vocab_from_pdf(input_pdf)
    if vocab_dict:
        if export_to_json(vocab_dict, output_json):
            messagebox.showinfo("Thành công", f"File JSON đã được xuất tại: {output_json}\nTổng số từ: {len(vocab_dict)}")
        else:
            messagebox.showerror("Thất bại", "Không thể xuất file JSON.")

# Tạo giao diện GUI
root = tk.Tk()
root.title("Xuất từ vựng PDF sang JSON")
root.geometry("400x250")

label_file = tk.Label(root, text="Chọn file PDF:")
label_file.pack(pady=10)

entry_file = tk.Entry(root, width=40)
entry_file.pack(pady=5)

btn_choose = tk.Button(root, text="Chọn file PDF", command=choose_file)
btn_choose.pack(pady=10)

btn_export = tk.Button(root, text="Xuất JSON", command=export_json)
btn_export.pack(pady=10)

root.mainloop()