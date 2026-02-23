import fitz
import sys
import os
import json
import traceback
from pathlib import Path
from datetime import datetime

# File log để ghi lỗi
LOG_FILE = r"C:\Users\12953 bao\Desktop\desktop\work\Project\Python\BasicLearnPython\W3schools\Python Tutorial\Python Project\MyAppInMBC\StampAuto\stamp_log.txt"

def write_log(message):
    """Ghi log chi tiết"""
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] {message}\n")
    except:
        pass

def main():
    try:
        write_log("=== BẮT ĐẦU ĐÓNG DẤU HIỆU CHỈNH ===")
        
        if len(sys.argv) < 2:
            write_log("LỖI: Thiếu đường dẫn file PDF")
            print("Thiếu đường dẫn file PDF")
            sys.exit(1)
        
        pdf_path = sys.argv[1]
        write_log(f"File PDF nhận được: {pdf_path}")
        
        pdf_path = pdf_path.replace('/', '\\')
        write_log(f"File PDF sau chuẩn hóa: {pdf_path}")
        
        if not os.path.exists(pdf_path):
            write_log(f"LỖI: File PDF không tồn tại: {pdf_path}")
            print(f"File PDF không tồn tại: {pdf_path}")
            sys.exit(1)
        
        write_log("✓ File PDF tồn tại")
        
        script_dir = Path(__file__).parent
        setting_dir = script_dir / "setting"
        stamps_dir = setting_dir / "stamps"
        settings_file = setting_dir / "settings.json"
        
        # Kiểm tra các thư mục và file
        if not setting_dir.exists():
            write_log(f"LỖI: Thư mục setting không tồn tại: {setting_dir}")
            print(f"Thư mục setting không tồn tại")
            sys.exit(1)
        
        if not stamps_dir.exists():
            write_log(f"LỖI: Thư mục stamps không tồn tại: {stamps_dir}")
            print(f"Thư mục stamps không tồn tại")
            sys.exit(1)
        
        if not settings_file.exists():
            write_log(f"LỖI: File settings không tồn tại: {settings_file}")
            print(f"File settings không tồn tại")
            sys.exit(1)
        
        # Đọc settings
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            write_log("✓ Đọc settings thành công")
        except Exception as e:
            write_log(f"LỖI đọc settings: {str(e)}")
            print(f"Lỗi đọc settings: {str(e)}")
            sys.exit(1)
        
        # Tìm loại đóng dấu Hiệu chỉnh
        stamp_type = None
        for stamp in settings.get('stamp_types', []):
            if stamp['id'] == 'hieuchinh' or stamp.get('module') == 'StamptHieuChinh':
                stamp_type = stamp
                break
        
        if not stamp_type:
            write_log("LỖI: Không tìm thấy cấu hình đóng dấu Hiệu chỉnh")
            print("Không tìm thấy cấu hình đóng dấu Hiệu chỉnh")
            sys.exit(1)
        
        # Đường dẫn ảnh đóng dấu
        stamp_image = stamps_dir / stamp_type.get('image', 'condauHieuChinh.png')
        write_log(f"Đường dẫn ảnh đóng dấu: {stamp_image}")
        
        if not stamp_image.exists():
            write_log(f"LỖI: Không tìm thấy ảnh đóng dấu: {stamp_image}")
            print(f"Không tìm thấy ảnh đóng dấu: {stamp_image}")
            sys.exit(1)
        
        # Thực hiện đóng dấu
        try:
            write_log("Bắt đầu mở file PDF...")
            doc = fitz.open(pdf_path)
            write_log(f"✓ Mở file PDF thành công. Số trang: {len(doc)}")
            
            img = fitz.Pixmap(str(stamp_image))
            img_width = img.width
            img_height = img.height
            write_log(f"✓ Kích thước ảnh: {img_width}x{img_height}")
            
            scale = stamp_type.get('scale', 0.1)
            y_bottom_offset = stamp_type.get('position_offset', {}).get('y_bottom_offset', 1)
            height_offset = stamp_type.get('position_offset', {}).get('height_offset', 5)
            
            total_stamps = 0
            
            for page_num, page in enumerate(doc, 1):
                text_instances = page.search_for(stamp_type.get('search_text', 'Hiệu chỉnh'))
                write_log(f"Tìm thấy {len(text_instances)} vị trí text trên trang {page_num}")
                
                for inst_num, inst in enumerate(text_instances, 1):
                    x0, y0, x1, y1 = inst
                    
                    width = img_width * scale
                    height = img_height * scale
                    
                    stamp_rect = fitz.Rect(
                        x0 + 20,
                        y1 + y_bottom_offset,
                        x0 + 20 + width,
                        y1 + height_offset + height
                    )
                    
                    page.insert_image(stamp_rect, filename=str(stamp_image))
                    total_stamps += 1
            
            write_log(f"✓ Đã chèn {total_stamps} dấu vào file PDF")
            
            # LƯU TRỰC TIẾP VÀO FILE GỐC
            write_log("Lưu thay đổi vào file gốc...")
            doc.save(pdf_path, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
            doc.close()
            
            write_log(f"✓ ĐÃ ĐÓNG DẤU THÀNH CÔNG vào file gốc: {pdf_path}")
            print(f"Đã đóng dấu thành công vào file gốc: {pdf_path}")
            
        except Exception as e:
            write_log(f"LỖI khi xử lý PDF: {str(e)}")
            write_log(traceback.format_exc())
            print(f"Lỗi xử lý PDF: {str(e)}")
            sys.exit(1)
        
        write_log("=== KẾT THÚC ĐÓNG DẤU HIỆU CHỈNH ===\n")
        
    except Exception as e:
        write_log(f"LỖI CHUNG: {str(e)}")
        write_log(traceback.format_exc())
        print(f"Lỗi chung: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()