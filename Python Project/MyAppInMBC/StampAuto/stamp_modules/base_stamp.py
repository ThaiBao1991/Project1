import fitz
import os
import traceback

class BaseStamp:
    """Class base cho các module đóng dấu"""
    
    def __init__(self, stamp_image_path, settings):
        self.stamp_image_path = stamp_image_path
        self.settings = settings
        
    def stamp_pdf(self, pdf_path, output_path=None):
        """
        Đóng dấu vào file PDF
        Nếu output_path là None, sẽ lưu đè lên file gốc
        """
        try:
            # Kiểm tra file tồn tại
            if not os.path.exists(pdf_path):
                return False, f"Không tìm thấy file PDF: {pdf_path}", 0
                
            if not os.path.exists(self.stamp_image_path):
                return False, f"Không tìm thấy ảnh đóng dấu: {self.stamp_image_path}", 0
            
            # Mở file PDF
            doc = fitz.open(pdf_path)
            
            # Lấy kích thước ảnh
            img = fitz.Pixmap(self.stamp_image_path)
            img_width = img.width
            img_height = img.height
            
            # Lấy thông số từ settings
            scale = self.settings.get('scale', 0.1)
            search_text = self.settings.get('search_text', 'Xác nhận')
            
            # Offset mặc định (có thể được override trong subclass)
            y_bottom_offset = self.settings.get('position_offset', {}).get('y_bottom_offset', 1)
            height_offset = self.settings.get('position_offset', {}).get('height_offset', 5)
            x_offset = self.settings.get('position_offset', {}).get('x_offset', 0)
            
            total_stamps = 0
            
            # Duyệt từng trang
            for page_num, page in enumerate(doc, 1):
                text_instances = page.search_for(search_text)
                
                for inst in text_instances:
                    x0, y0, x1, y1 = inst
                    
                    width = img_width * scale
                    height = img_height * scale
                    
                    # Tính vị trí đóng dấu (có thể override trong subclass)
                    stamp_rect = self.calculate_position(
                        x0, y0, x1, y1, width, height, 
                        x_offset, y_bottom_offset, height_offset
                    )
                    
                    # Chèn ảnh
                    page.insert_image(stamp_rect, filename=self.stamp_image_path)
                    total_stamps += 1
                    
                    print(f"Đã chèn dấu tại trang {page_num}, vị trí: ({stamp_rect.x0}, {stamp_rect.y0})")
            
            # Lưu file
            if output_path:
                doc.save(output_path)
                result_path = output_path
                print(f"Đã lưu file mới: {output_path}")
            else:
                doc.save(pdf_path, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
                result_path = pdf_path
                print(f"Đã lưu đè lên file gốc: {pdf_path}")
            
            doc.close()
            
            if total_stamps > 0:
                return True, result_path, total_stamps
            else:
                return False, f"Không tìm thấy text '{search_text}' trong file PDF", 0
            
        except Exception as e:
            traceback.print_exc()
            return False, str(e), 0
    
    def calculate_position(self, x0, y0, x1, y1, width, height, x_offset, y_bottom_offset, height_offset):
        """Tính toán vị trí đóng dấu - sẽ được override trong subclass"""
        return fitz.Rect(
            x0 + x_offset,
            y1 + y_bottom_offset,
            x0 + x_offset + width,
            y1 + height_offset + height
        )