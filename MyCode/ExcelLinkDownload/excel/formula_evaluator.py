# excel/formula_evaluator.py
import re
from .reader import ExcelReader

class FormulaEvaluator:
    """Đánh giá công thức Excel, đặc biệt là HYPERLINK có tham chiếu ô"""
    
    def __init__(self, reader: ExcelReader, sheet_name: str):
        self.reader = reader
        self.sheet_name = sheet_name
    
    def extract_hyperlink_path(self, formula: str) -> str | None:
        """
        Trích xuất và evaluate đường dẫn từ HYPERLINK trong công thức
        Hỗ trợ biểu thức nối chuỗi kiểu Excel: "text" & A1 & "text" & $B$2
        """
        if not formula:
            return None
        
        try:
            # 1. Tìm vị trí "HYPERLINK("
            start = formula.find("HYPERLINK(")
            if start == -1:
                return None
            
            # 2. Đếm ngoặc để tìm vị trí kết thúc của HYPERLINK(...)
            i = start + 10  # len("HYPERLINK(")
            paren_count = 1
            while i < len(formula) and paren_count > 0:
                if formula[i] == '(':
                    paren_count += 1
                elif formula[i] == ')':
                    paren_count -= 1
                i += 1
            
            if paren_count != 0:
                return None
            
            # 3. Nội dung bên trong HYPERLINK(...)
            inner = formula[start + 10:i-1]
            
            # 4. Tìm dấu phẩy đầu tiên (ngăn cách path và display text)
            comma_pos = inner.find(',')
            if comma_pos == -1:
                return None
            
            # 5. Lấy phần path (trước dấu phẩy)
            path_expr = inner[:comma_pos].strip()
            
            print(f"DEBUG - Path expression: {path_expr}")
            
            # 6. Evaluate biểu thức nối chuỗi
            result = self._evaluate_concatenation(path_expr)
            
            print(f"DEBUG - Evaluated result: {result}")
            
            # 7. Dọn dẹp kết quả
            result = self._clean_path(result)
            
            print(f"DEBUG - Final result: {result}")
            
            return result
            
        except Exception as e:
            print(f"Warning: extract_hyperlink_path failed: {e}")
            return None
    
    def _evaluate_concatenation(self, expr: str) -> str:
        """
        Evaluate biểu thức nối chuỗi kiểu Excel
        Ví dụ: "\\path\"&B365&"-"&$G$9&".PDF"
        -> "\\path\Z04-2-V.PDF"
        """
        if not expr:
            return ""
        
        # Tách các thành phần bằng dấu &
        # Nhưng cẩn thận: trong string literal có thể có &?
        # Trong Excel, & trong string literal được viết là &&, nhưng hiếm gặp
        parts = expr.split('&')
        
        result_parts = []
        
        for part in parts:
            part = part.strip()
            
            if not part:
                continue
            
            # Trường hợp 1: String literal (nằm trong dấu ngoặc kép)
            if part.startswith('"') and part.endswith('"'):
                # Lấy nội dung bên trong, bỏ dấu ngoặc kép
                text = part[1:-1]
                result_parts.append(text)
                print(f"DEBUG - String literal: '{text}'")
            
            # Trường hợp 2: Tham chiếu ô (có chữ cái và số)
            elif re.match(r'^\$?[A-Za-z]+\$?[0-9]+$', part.upper()):
                # Lấy giá trị từ ô
                value = self._get_cell_value_from_ref(part)
                result_parts.append(str(value) if value else "")
                print(f"DEBUG - Cell reference {part} = '{value}'")
            
            # Trường hợp 3: Số
            elif part.isdigit():
                result_parts.append(part)
                print(f"DEBUG - Number: '{part}'")
            
            # Trường hợp 4: Text thường (không có dấu ngoặc kép)
            else:
                result_parts.append(part)
                print(f"DEBUG - Plain text: '{part}'")
        
        # Nối tất cả
        return ''.join(result_parts)
    
    def _get_cell_value_from_ref(self, ref: str):
        """
        Lấy giá trị từ tham chiếu ô
        Hỗ trợ: A1, $A$1, B365, $G$9
        """
        # Loại bỏ $ để lấy cột
        col_part = ''.join([c for c in ref if c.isalpha()])
        # Loại bỏ $ để lấy số dòng
        row_part = ''.join([c for c in ref if c.isdigit()])
        
        if not row_part:
            return None
        
        try:
            row = int(row_part)
            col = self._col_to_index(col_part)
            
            value = self.reader.get_cell_value(self.sheet_name, row, col)
            return value
        except Exception as e:
            print(f"Warning: _get_cell_value_from_ref failed for {ref}: {e}")
            return None
    
    def _clean_path(self, path: str) -> str:
        """
        Dọn dẹp đường dẫn sau khi evaluate
        """
        if not path:
            return path
        
        # Xóa dấu " thừa (nếu còn)
        path = path.replace('"', '')
        
        # Chuẩn hóa dấu \: thay \\ bằng \
        # Nhưng giữ nguyên \\ đầu nếu là UNC path
        if path.startswith('\\\\'):
            # Giữ 2 dấu \ đầu
            prefix = '\\\\'
            rest = path[2:]
            rest = rest.replace('\\\\', '\\')
            path = prefix + rest
        else:
            path = path.replace('\\\\', '\\')
        
        # Xóa khoảng trắng đầu cuối
        path = path.strip()
        
        return path
    
    def _col_to_index(self, col_str: str) -> int:
        """Chuyển đổi 'A' -> 1, 'Z' -> 26, 'AA' -> 27"""
        result = 0
        for c in col_str.upper():
            if c == '$':
                continue
            result = result * 26 + (ord(c) - ord('A') + 1)
        return result


def get_link_from_cell(reader: ExcelReader, sheet_name: str, row: int, col: int) -> str | None:
    """
    Lấy link thực từ ô Excel (hỗ trợ mọi định dạng và công thức phức tạp)
    """
    # Cách 1: Hyperlink object (nếu có) - ưu tiên nhất
    try:
        link = reader.get_hyperlink(sheet_name, row, col)
        if link:
            print(f"DEBUG - Found hyperlink object: {link[:100]}...")
            return link
    except Exception as e:
        print(f"Warning: get_hyperlink failed: {e}")
    
    # Cách 2: Công thức có HYPERLINK
    try:
        if reader.has_formula(sheet_name, row, col):
            formula = reader.get_cell_formula(sheet_name, row, col)
            if formula:
                print(f"DEBUG - Found formula: {formula[:200]}...")
                evaluator = FormulaEvaluator(reader, sheet_name)
                link = evaluator.extract_hyperlink_path(formula)
                if link:
                    print(f"DEBUG - Extracted link: {link[:100]}...")
                    return link
    except Exception as e:
        print(f"Warning: get_cell_formula/has_formula failed: {e}")
    
    # Cách 3: Giá trị text thuần (UNC, local path, http)
    try:
        value = reader.get_cell_value(sheet_name, row, col)
        if isinstance(value, str):
            # UNC path
            if value.startswith('\\\\'):
                return value
            # Local path
            if ':\\' in value:
                return value
            # HTTP/HTTPS
            if value.startswith(('http://', 'https://')):
                return value
    except Exception as e:
        print(f"Warning: get_cell_value failed: {e}")
    
    return None