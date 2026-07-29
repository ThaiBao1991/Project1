from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QTextEdit, QPushButton, QComboBox, QMessageBox
)
from core.page_config_mgr import PageConfigManager

class QuickLoginDialog(QDialog):
    def __init__(self, config_mgr: PageConfigManager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Đăng nhập nhanh từ Cookies")
        self.resize(500, 350)
        self.config_mgr = config_mgr
        
        self._build_ui()
        self._populate_hosts()
        
    def _build_ui(self):
        layout = QVBoxLayout(self)
        
        # Hướng dẫn
        lbl_guide = QLabel("Chọn Host và dán chuỗi Cookies của bạn vào bên dưới:\n(Định dạng: name1=value1; name2=value2)")
        layout.addWidget(lbl_guide)
        
        row_host = QHBoxLayout()
        row_host.addWidget(QLabel("Cấu hình Host:"))
        self.cbo_host = QComboBox()
        row_host.addWidget(self.cbo_host, stretch=1)
        layout.addLayout(row_host)
        
        self.txt_cookies = QTextEdit()
        self.txt_cookies.setPlaceholderText("Paste cookies string here...")
        layout.addWidget(self.txt_cookies, stretch=1)
        
        # Buttons
        row_btn = QHBoxLayout()
        btn_apply = QPushButton("Áp dụng Cookies")
        btn_apply.clicked.connect(self._on_apply)
        btn_cancel = QPushButton("Đóng")
        btn_cancel.clicked.connect(self.reject)
        
        row_btn.addStretch()
        row_btn.addWidget(btn_apply)
        row_btn.addWidget(btn_cancel)
        layout.addLayout(row_btn)
        
    def _populate_hosts(self):
        for c in self.config_mgr.get_all_configs():
            self.cbo_host.addItem(c.page_code, userData=c)
            
    def _on_apply(self):
        raw = self.txt_cookies.toPlainText().strip()
        if not raw:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập chuỗi Cookies!")
            return
            
        page_config = self.cbo_host.currentData()
        if not page_config:
            return
            
        # Parse cookies
        cookie_dict = {}
        for item in raw.split(';'):
            if '=' in item:
                k, v = item.split('=', 1)
                cookie_dict[k.strip()] = v.strip()
                
        # Lưu vào một biến toàn cục trong config_mgr hoặc PageConfig để truyền cho Engine
        # Tạm thời gán thuộc tính động _custom_cookies vào page_config
        setattr(page_config, '_custom_cookies', cookie_dict)
        
        QMessageBox.information(self, "Thành công", f"Đã áp dụng {len(cookie_dict)} cookies cho host {page_config.page_code}!")
        self.accept()
