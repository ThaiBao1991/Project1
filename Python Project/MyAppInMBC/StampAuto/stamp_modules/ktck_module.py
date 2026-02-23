from .base_stamp import BaseStamp
import fitz

class KTCKStamp(BaseStamp):
    """
    Module đóng dấu kiểm tra cơ khí
    Đặc điểm: Đóng dấu ngay sát bên dưới text "Kiểm tra cơ khí"
    """
    
    def __init__(self, stamp_image_path, settings):
        super().__init__(stamp_image_path, settings)
    
    def calculate_position(self, x0, y0, x1, y1, width, height, x_offset, y_bottom_offset, height_offset):
        """
        Tính vị trí cho dấu KTCK:
        - Không dịch ngang (x_offset = 0)
        - Đặt sát bên dưới text
        """
        # Đảm bảo các giá trị offset đặc trưng cho KTCK
        y_bottom = 2  # Khoảng cách từ text đến dấu
        height_add = 6  # Khoảng cách thêm phía dưới
        
        return fitz.Rect(
            x0,  # Không dịch phải
            y1 + y_bottom,
            x0 + width,
            y1 + height_add + height
        )