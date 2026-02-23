from .base_stamp import BaseStamp
import fitz

class HieuChinhStamp(BaseStamp):
    """
    Module đóng dấu hiệu chỉnh
    Đặc điểm: Dịch sang phải 50 đơn vị so với text "Hiệu chỉnh"
    """
    
    def __init__(self, stamp_image_path, settings):
        super().__init__(stamp_image_path, settings)
    
    def calculate_position(self, x0, y0, x1, y1, width, height, x_offset, y_bottom_offset, height_offset):
        """
        Tính vị trí cho dấu Hiệu chỉnh:
        - Dịch sang phải 20 đơn vị
        - Giữ nguyên offset dọc
        """
        # Đặc thù của dấu hiệu chỉnh: dịch phải 20 đơn vị
        x_offset = 20
        y_bottom = 1
        height_add = 5
        
        return fitz.Rect(
            x0 + x_offset,  # Dịch phải 20 đơn vị
            y1 + y_bottom,
            x0 + x_offset + width,
            y1 + height_add + height
        )