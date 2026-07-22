# excel/xlrd_reader.py
import xlrd
from .reader import ExcelReader

class XlrdReader(ExcelReader):
    """Hỗ trợ .xls (cũ) - dùng xlrd 1.2.0 để đọc được hyperlink"""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        # on_demand=True để đọc nhanh hơn
        self.wb = xlrd.open_workbook(filepath, formatting_info=True, on_demand=True)
        self._modified = False
        self._changes = []
    
    def get_sheet_names(self) -> list[str]:
        return self.wb.sheet_names()
    
    def _get_sheet(self, sheet_name: str):
        return self.wb.sheet_by_name(sheet_name)
    
    def get_cell_value(self, sheet_name: str, row: int, col: int):
        sheet = self._get_sheet(sheet_name)
        cell = sheet.cell(row-1, col-1)
        return cell.value
    
    def get_cell_formula(self, sheet_name: str, row: int, col: int) -> str | None:
        sheet = self._get_sheet(sheet_name)
        cell = sheet.cell(row-1, col-1)
        # xlrd 1.2.0: nếu là formula, cell.ctype == 2 (XL_CELL_FORMULA)
        if cell.ctype == 2:  # XL_CELL_FORMULA
            # Lấy công thức gốc
            if hasattr(cell, 'formula') and cell.formula:
                return cell.formula
            # Hoặc lấy từ value nếu là string
            return str(cell.value) if cell.value else None
        return None
    
    def has_formula(self, sheet_name: str, row: int, col: int) -> bool:
        sheet = self._get_sheet(sheet_name)
        cell = sheet.cell(row-1, col-1)
        return cell.ctype == 2
    
    def get_hyperlink(self, sheet_name: str, row: int, col: int) -> str | None:
        """
        Đọc hyperlink từ file .xls
        xlrd 1.2.0 hỗ trợ hyperlink qua cell.hyperlink
        """
        sheet = self._get_sheet(sheet_name)
        
        # Lấy hyperlink từ sheet (xlrd lưu hyperlink riêng)
        if hasattr(sheet, 'hyperlink_map') and sheet.hyperlink_map:
            # Tìm hyperlink tại vị trí (row, col)
            for hyperlink in sheet.hyperlink_map.values():
                # Kiểm tra tọa độ
                if (hyperlink.rowx == row-1 and hyperlink.colx == col-1):
                    if hasattr(hyperlink, 'url_or_path'):
                        return hyperlink.url_or_path
                    elif hasattr(hyperlink, 'rel_url'):
                        return hyperlink.rel_url
        
        # Nếu không tìm thấy, thử lấy từ cell
        cell = sheet.cell(row-1, col-1)
        if hasattr(cell, 'hyperlink') and cell.hyperlink:
            if hasattr(cell.hyperlink, 'url_or_path'):
                return cell.hyperlink.url_or_path
        
        # Thử lấy từ giá trị nếu là UNC hoặc local path
        value = self.get_cell_value(sheet_name, row, col)
        if isinstance(value, str):
            if value.startswith('\\\\') or ':\\' in value or value.startswith('http'):
                return value
        
        return None
    
    def get_max_row(self, sheet_name: str) -> int:
        sheet = self._get_sheet(sheet_name)
        return sheet.nrows
    
    def get_max_col(self, sheet_name: str) -> int:
        sheet = self._get_sheet(sheet_name)
        return sheet.ncols
    
    def update_cell(self, sheet_name: str, row: int, col: int, value: str):
        """Lưu thay đổi để ghi sau"""
        self._changes.append({
            'sheet': sheet_name,
            'row': row,
            'col': col,
            'value': value
        })
        self._modified = True
    
    def save(self, filepath: str = None):
        """Ghi file .xls bằng xlwt"""
        if not self._modified:
            return
        
        import xlwt
        
        # Tạo workbook mới
        wb_new = xlwt.Workbook(encoding='utf-8')
        
        for sheet_name in self.get_sheet_names():
            ws_new = wb_new.add_sheet(sheet_name)
            max_row = self.get_max_row(sheet_name)
            max_col = self.get_max_col(sheet_name)
            
            # Ghi dữ liệu
            for r in range(1, max_row + 1):
                for c in range(1, max_col + 1):
                    # Kiểm tra xem có change không
                    changed = False
                    for change in self._changes:
                        if change['sheet'] == sheet_name and change['row'] == r and change['col'] == c:
                            ws_new.write(r-1, c-1, change['value'])
                            changed = True
                            break
                    if not changed:
                        value = self.get_cell_value(sheet_name, r, c)
                        if value is not None:
                            ws_new.write(r-1, c-1, value)
        
        if filepath is None:
            filepath = self.filepath
        
        wb_new.save(filepath)
    
    def close(self):
        self.wb.release_resources()
        del self.wb