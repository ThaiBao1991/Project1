import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import json
from PyPDF2 import PdfReader
import re
import os

# Hàm trích xuất dữ liệu từ PDF với giao diện trực quan
def extract_vocab_from_pdf(pdf_path, log_text):
    try:
        pdf_reader = PdfReader(pdf_path)
        vocab_dict = {}
        
        # Xóa nội dung log trước khi bắt đầu
        log_text.delete(1.0, tk.END)
        log_text.insert(tk.END, "Bắt đầu trích xuất dữ liệu...\n")
        log_text.update()

        # Duyệt qua từng trang
        for page_num, page in enumerate(pdf_reader.pages, 1):
            text = page.extract_text()
            if not text:  # Bỏ qua trang trống
                log_text.insert(tk.END, f"Trang {page_num}: Trống, bỏ qua.\n")
                log_text.update()
                continue
            lines = text.split('\n')
            
            # Biểu thức chính quy khớp với định dạng: No. Word Type Pronounce Meaning
            pattern = r"^\d+\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?(?:\s+[a-zA-Z]+)?)\s+([nva]\b|adj\b|adv\b|pron\b|det\b|conj\b|prep\b|exclamation\b(?:,\s*[nva]\b|,\s*adj\b|,\s*adv\b|,\s*pron\b|,\s*det\b|,\s*conj\b|,\s*prep\b|,\s*exclamation\b)?)\s*([əæeɪioʊuʌʃʒθðŋɒɔʌʊʔˈ][əæeɪioʊuʌʃʒθðŋɒɔʌʊʔˈ:]*?)?\s+(.+)$"
            
            for line in lines:
                line = line.strip()
                if not line or not re.match(r"^\d+", line):  # Bỏ qua dòng không bắt đầu bằng số
                    continue
                
                # Loại bỏ tiêu đề hoặc dòng không phải từ vựng trước khi xử lý
                if re.search(r"(TỪ\s*VỰNG|THÔNG\s*DỤNG|Oxford|Effortless|Trang|\bT\b\s*$|3000)", line, re.IGNORECASE):
                    log_text.insert(tk.END, f"Trang {page_num}: Bỏ qua dòng tiêu đề: {line}\n")
                    log_text.update()
                    continue
                
                # Thay nhiều khoảng trắng bằng một khoảng trắng để chuẩn hóa
                line = re.sub(r"\s+", " ", line)
                log_text.insert(tk.END, f"Trang {page_num}: Đọc dòng: {line}\n")
                log_text.update()
                
                match = re.match(pattern, line)
                if match:
                    word, word_type, pronounce, meaning = match.groups()
                    
                    # Chuẩn hóa dữ liệu
                    word = word.strip() if word else ""
                    word_type = word_type.strip() if word_type else "N/A"
                    pronounce = pronounce.strip() if pronounce and re.match(r"[əæeɪioʊuʌʃʒθðŋɒɔʌʊʔˈ:].*", pronounce) else "N/A"
                    meaning = meaning.strip() if meaning else "N/A"
                    
                    # Tách pronounce nếu nó bị lẫn vào meaning
                    pronounce_pattern = r"([a-zəæeɪioʊuʌʃʒθðŋɒɔʌʊʔˈ:][a-zəæeɪioʊuʌʃʒθðŋɒɔʌʊʔˈ:]*)\s+(.+)"
                    pronounce_match = re.match(pronounce_pattern, meaning)
                    if pronounce_match:
                        pronounce, meaning = pronounce_match.groups()
                    elif pronounce == "N/A" and meaning:
                        meaning_parts = meaning.split()
                        if meaning_parts and re.match(r"[a-zəæeɪioʊuʌʃʒθðŋɒɔʌʊʔˈ:].*", meaning_parts[0]):
                            pronounce = meaning_parts[0]
                            meaning = " ".join(meaning_parts[1:]) if len(meaning_parts) > 1 else "N/A"
                    
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
                    log_text.insert(tk.END, f"  => Xử lý: word={word}, type={word_type}, pronounce={pronounce}, meaning={meaning}\n")
                    log_text.update()
                else:
                    # Xử lý thủ công nếu regex không khớp
                    parts = re.split(r"\s+", line)
                    if len(parts) >= 3 and parts[0].isdigit():  # Đảm bảo có ít nhất 3 phần tử (số, từ, loại từ)
                        word = parts[1]
                        # Tìm type trong danh sách từ loại
                        type_idx = next((i for i, p in enumerate(parts[2:]) if re.match(r"^[nva]$|^adj$|^adv$|^pron$|^det$|^conj$|^prep$|^exclamation(?:,\s*[nva]\b|,\s*adj\b|,\s*adv\b|,\s*pron\b|,\s*det\b|,\s*conj\b|,\s*prep\b|,\s*exclamation\b)?$", p)), None)
                        if type_idx is not None and type_idx + 2 < len(parts):
                            type_idx += 2
                            word_type = parts[type_idx]
                            # Tìm pronounce và meaning
                            meaning_start_idx = type_idx + 1
                            meaning_parts = parts[meaning_start_idx:]
                            pronounce = "N/A"
                            meaning = " ".join(meaning_parts) if meaning_parts else "N/A"
                            if meaning_parts and re.match(r"[a-zəæeɪioʊuʌʃʒθðŋɒɔʌʊʔˈ:].*", meaning_parts[0]):
                                pronounce = meaning_parts[0]
                                meaning = " ".join(meaning_parts[1:]) if len(meaning_parts) > 1 else "N/A"
                        else:
                            word_type = "N/A"
                            pronounce = "N/A"
                            meaning = " ".join(parts[2:]) if len(parts) > 2 else "N/A"
                            if parts[2:] and re.match(r"[a-zəæeɪioʊuʌʃʒθðŋɒɔʌʊʔˈ:].*", parts[2]):
                                pronounce = parts[2]
                                meaning = " ".join(parts[3:]) if len(parts) > 3 else "N/A"
                        
                        # Kiểm tra lại meaning nếu pronounce vẫn là N/A
                        if pronounce == "N/A" and meaning:
                            meaning_parts = meaning.split()
                            if meaning_parts and re.match(r"[a-zəæeɪioʊuʌʃʒθðŋɒɔʌʊʔˈ:].*", meaning_parts[0]):
                                pronounce = meaning_parts[0]
                                meaning = " ".join(meaning_parts[1:]) if len(meaning_parts) > 1 else "N/A"
                        
                        vocab_dict[word] = {
                            "type": word_type,
                            "pronounce": pronounce,
                            "meaning": meaning,
                            "correct_count": 0,
                            "completed_date": None
                        }
                        log_text.insert(tk.END, f"  => Xử lý thủ công: word={word}, type={word_type}, pronounce={pronounce}, meaning={meaning}\n")
                        log_text.update()
        
        log_text.insert(tk.END, "Hoàn tất trích xuất dữ liệu.\n")
        log_text.update()
        return vocab_dict
    except Exception as e:
        log_text.insert(tk.END, f"Lỗi: Không thể trích xuất dữ liệu từ PDF: {str(e)}\n")
        log_text.update()
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
def choose_file(entry_file):
    file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
    if file_path:
        entry_file.delete(0, tk.END)
        entry_file.insert(0, file_path)

# Hàm xử lý khi nhấn nút "Xuất JSON"
def export_json(entry_file, log_text):
    input_pdf = entry_file.get()
    if not input_pdf:
        messagebox.showwarning("Cảnh báo", "Vui lòng chọn file PDF trước!")
        return
    
    output_json = os.path.splitext(input_pdf)[0] + "_vocab.json"
    
    vocab_dict = extract_vocab_from_pdf(input_pdf, log_text)
    if vocab_dict:
        if export_to_json(vocab_dict, output_json):
            messagebox.showinfo("Thành công", f"File JSON đã được xuất tại: {output_json}\nTổng số từ: {len(vocab_dict)}")
        else:
            messagebox.showerror("Thất bại", "Không thể xuất file JSON.")

# Tạo giao diện GUI
root = tk.Tk()
root.title("Xuất từ vựng PDF sang JSON")
root.geometry("600x400")

# Frame chứa các thành phần nhập liệu
frame_input = tk.Frame(root)
frame_input.pack(pady=10)

label_file = tk.Label(frame_input, text="Chọn file PDF:")
label_file.grid(row=0, column=0, padx=5)

entry_file = tk.Entry(frame_input, width=40)
entry_file.grid(row=0, column=1, padx=5)

btn_choose = tk.Button(frame_input, text="Chọn file PDF", command=lambda: choose_file(entry_file))
btn_choose.grid(row=0, column=2, padx=5)

btn_export = tk.Button(root, text="Xuất JSON", command=lambda: export_json(entry_file, log_text))
btn_export.pack(pady=10)

# Thêm cửa sổ log để hiển thị quá trình xử lý
log_text = scrolledtext.ScrolledText(root, width=70, height=20)
log_text.pack(pady=10)

root.mainloop()