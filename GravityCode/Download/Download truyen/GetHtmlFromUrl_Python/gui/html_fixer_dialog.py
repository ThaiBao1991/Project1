import os
import re
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFileDialog, QMessageBox, QLineEdit, QProgressBar
)

class HtmlFixerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sửa lỗi font HTML (Fix Encoding)")
        self.resize(500, 150)
        self.setMinimumSize(450, 150)
        
        self._build_ui()
        
    def _build_ui(self):
        layout = QVBoxLayout(self)
        
        lbl_guide = QLabel("Công cụ này tự động chèn BOM và thẻ Meta chuẩn để sửa lỗi font khi convert HTML sang PRC/MOBI.\nChọn file HTML cũ của bạn để bắt đầu:")
        layout.addWidget(lbl_guide)
        
        row_file = QHBoxLayout()
        self.txt_file = QLineEdit()
        self.txt_file.setReadOnly(True)
        row_file.addWidget(self.txt_file, stretch=1)
        
        btn_browse = QPushButton("Chọn File HTML...")
        btn_browse.clicked.connect(self._on_browse)
        row_file.addWidget(btn_browse)
        layout.addLayout(row_file)
        
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        layout.addWidget(self.progress)
        
        row_btn = QHBoxLayout()
        btn_fix = QPushButton("Bắt đầu Sửa Lỗi")
        btn_fix.setStyleSheet("background-color: #1976d2; color: white; font-weight: bold;")
        btn_fix.clicked.connect(self._on_fix)
        
        btn_close = QPushButton("Đóng")
        btn_close.clicked.connect(self.reject)
        
        row_btn.addStretch()
        row_btn.addWidget(btn_fix)
        row_btn.addWidget(btn_close)
        layout.addLayout(row_btn)
        
    def _on_browse(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Chọn file HTML cần sửa", "", 
            "HTML Files (*.html *.htm);;All Files (*.*)"
        )
        if file_path:
            self.txt_file.setText(file_path)
            self.progress.setValue(0)

    def _on_fix(self):
        file_path = self.txt_file.text().strip()
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn một file HTML hợp lệ.")
            return
            
        try:
            self.progress.setValue(20)
            
            # Đọc file bằng utf-8 (bỏ qua BOM nếu có)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            self.progress.setValue(50)
            
            # Thay thế thẻ Meta cũ nếu có
            new_meta = '<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\" />'
            # Tìm và thay thế thẻ meta charset=UTF-8 cũ
            content = re.sub(r'<meta charset=[\'\"]?UTF-8[\'\"]?>', new_meta, content, flags=re.IGNORECASE)
            
            # Nếu thẻ meta mới chưa tồn tại trong file thì thêm vào sau <head>
            if new_meta not in content:
                content = re.sub(r'<head>', f'<head>\n{new_meta}', content, flags=re.IGNORECASE)
                
            self.progress.setValue(80)
            
            # Ghi đè file bằng định dạng utf-8-sig (chèn BOM vào đầu file)
            with open(file_path, 'w', encoding='utf-8-sig') as f:
                f.write(content)
                
            self.progress.setValue(100)
            QMessageBox.information(self, "Thành công", f"Đã sửa thành công file:\n{file_path}\n(Đã thêm BOM và thẻ Meta chuẩn)")
            
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể xử lý file:\n{e}")
            self.progress.setValue(0)
