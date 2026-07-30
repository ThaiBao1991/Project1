import os
import json
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QTextEdit, QPushButton, QFileDialog, QMessageBox, QLineEdit
)

class ResumeDialog(QDialog):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quản Lý Resume (Tải tiếp file lỗi)")
        self.resize(600, 450)
        self.setMinimumSize(500, 350)
        self.main_window = main_window
        self.failed_links = []
        self.resume_data = None
        
        self._build_ui()
        
    def _build_ui(self):
        layout = QVBoxLayout(self)
        
        lbl_guide = QLabel("Chọn file <b>_Resume.json</b> hoặc <b>_ErrorLog.txt</b> được tạo ra trong quá trình tải:")
        layout.addWidget(lbl_guide)
        
        row_file = QHBoxLayout()
        self.txt_file = QLineEdit()
        self.txt_file.setReadOnly(True)
        row_file.addWidget(self.txt_file, stretch=1)
        
        btn_browse = QPushButton("Chọn File...")
        btn_browse.clicked.connect(self._on_browse)
        row_file.addWidget(btn_browse)
        layout.addLayout(row_file)
        
        self.lbl_status = QLabel("Trạng thái: Chưa chọn file.")
        self.lbl_status.setStyleSheet("color: blue;")
        layout.addWidget(self.lbl_status)
        
        layout.addWidget(QLabel("Danh sách các link bị lỗi / thiếu:"))
        self.txt_links = QTextEdit()
        layout.addWidget(self.txt_links, stretch=1)
        
        row_btn = QHBoxLayout()
        self.btn_resume = QPushButton("Tải bù và gộp lại file gốc")
        self.btn_resume.setStyleSheet("background-color: #f57c00; color: white; font-weight: bold;")
        self.btn_resume.clicked.connect(self._on_resume)
        
        btn_close = QPushButton("Đóng")
        btn_close.clicked.connect(self.reject)
        
        row_btn.addStretch()
        row_btn.addWidget(self.btn_resume)
        row_btn.addWidget(btn_close)
        layout.addLayout(row_btn)
        
    def _on_browse(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Chọn file Resume/ErrorLog", "", 
            "JSON/TXT Files (*.json *.txt);;All Files (*.*)"
        )
        if not file_path:
            return
            
        self.txt_file.setText(file_path)
        self.failed_links.clear()
        self.resume_data = None
        
        try:
            if file_path.endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.resume_data = json.load(f)
                    self.failed_links = self.resume_data.get("failed_links", [])
                    total = len(self.resume_data.get("all_links", [])) or self.resume_data.get("total_links", 0)
                    self.lbl_status.setText(f"Trạng thái: Phát hiện {len(self.failed_links)} / {total} chương bị lỗi.")
                    self.btn_resume.setText("Tải bù và gộp lại file gốc")
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.read().splitlines()
                    self.failed_links = [l for l in lines if l.strip()]
                    self.lbl_status.setText(f"Trạng thái: Đã tải {len(self.failed_links)} link lỗi từ file TXT.")
                    self.btn_resume.setText("Mở Manual GET để tải bù")
                    
            self.txt_links.setPlainText("\n".join(self.failed_links))
            
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể đọc file:\n{e}")
            self.lbl_status.setText("Trạng thái: Lỗi đọc file.")

    def _on_resume(self):
        raw_text = self.txt_links.toPlainText().strip()
        if not raw_text:
            QMessageBox.warning(self, "Thông báo", "Không có link nào để tải bù.")
            return
            
        self.accept()
        
        if self.resume_data and "save_dir" in self.resume_data:
            # File JSON chuẩn mới, chuyển thẳng sang main_window
            if hasattr(self.main_window, '_on_resume_from_data'):
                self.main_window._on_resume_from_data(self.resume_data)
            else:
                QMessageBox.warning(self.main_window, "Lỗi", "Chức năng tải bù chưa được hỗ trợ trên phiên bản này.")
        else:
            # File TXT cũ hoặc file JSON bản cũ, dùng Manual Get UI thông qua main_window
            try:
                self.main_window._on_manual_get()
                if hasattr(self.main_window, 'manual_get_ui') and self.main_window.manual_get_ui:
                    self.main_window.manual_get_ui.txt_urls.setPlainText(raw_text)
                    self.main_window.manual_get_ui.txt_log.append("📌 Đã tự động điền danh sách chương tải thiếu từ file log.")
            except Exception as e:
                pass

