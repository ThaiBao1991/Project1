# excel/reader.py
from abc import ABC, abstractmethod

class ExcelReader(ABC):
    """Abstract class cho các định dạng Excel khác nhau"""
    
    @abstractmethod
    def get_sheet_names(self) -> list[str]:
        """Lấy danh sách tên sheet"""
        pass
    
    @abstractmethod
    def get_cell_value(self, sheet_name: str, row: int, col: int):
        """Lấy giá trị của ô (row, col là 1-index)"""
        pass
    
    @abstractmethod
    def get_cell_formula(self, sheet_name: str, row: int, col: int) -> str | None:
        """Lấy công thức của ô (nếu có)"""
        pass
    
    @abstractmethod
    def has_formula(self, sheet_name: str, row: int, col: int) -> bool:
        """Kiểm tra ô có chứa công thức không"""
        pass
    
    @abstractmethod
    def get_hyperlink(self, sheet_name: str, row: int, col: int) -> str | None:
        """Lấy hyperlink target (nếu có)"""
        pass
    
    @abstractmethod
    def get_max_row(self, sheet_name: str) -> int:
        """Lấy số dòng tối đa của sheet"""
        pass
    
    @abstractmethod
    def get_max_col(self, sheet_name: str) -> int:
        """Lấy số cột tối đa của sheet"""
        pass
    
    @abstractmethod
    def update_cell(self, sheet_name: str, row: int, col: int, value: str):
        """Cập nhật giá trị ô (dùng cho tab Update)"""
        pass
    
    @abstractmethod
    def save(self, filepath: str = None):
        """Lưu file Excel (nếu có thay đổi)"""
        pass
    
    @abstractmethod
    def close(self):
        """Đóng file"""
        pass