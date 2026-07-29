from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QWidget,
    QFormLayout, QLineEdit, QCheckBox, QPushButton, QMessageBox,
    QScrollArea, QSplitter
)
from PyQt6.QtCore import Qt
from core.page_config_mgr import PageConfigManager
from models.page_config import PageConfig

class ConfigManagerDialog(QDialog):
    def __init__(self, config_mgr: PageConfigManager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quản Lý Host (PageConfigManager)")
        self.resize(800, 600)
        self.setMinimumSize(700, 500)
        self.config_mgr = config_mgr
        self._configs = self.config_mgr.get_all_configs()
        self._current_config: PageConfig = None
        
        self._build_ui()
        self._populate_list()
        
    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left Panel (List)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        self.list_hosts = QListWidget()
        self.list_hosts.currentRowChanged.connect(self._on_host_selected)
        left_layout.addWidget(self.list_hosts)
        
        row_list_btn = QHBoxLayout()
        btn_add = QPushButton("Thêm")
        btn_add.clicked.connect(self._on_add)
        btn_del = QPushButton("Xóa")
        btn_del.clicked.connect(self._on_del)
        row_list_btn.addWidget(btn_add)
        row_list_btn.addWidget(btn_del)
        left_layout.addLayout(row_list_btn)
        
        # Right Panel (Form)
        right_panel = QScrollArea()
        right_panel.setWidgetResizable(True)
        form_container = QWidget()
        self.form_layout = QFormLayout(form_container)
        
        self.fields = {}
        
        # Text fields
        text_props = [
            ("page_code", "Page Code (Host URL):"),
            ("paging_pattern", "Paging Pattern:"),
            ("css_query_get_list_chapter", "CSS List Chapter:"),
            ("css_query_get_chapter_title", "CSS Title:"),
            ("css_query_get_chapter_content", "CSS Content:"),
            ("css_filter", "CSS Filter:"),
            ("url_page_test", "URL Test:"),
            ("text_guide", "Text Guide:"),
            ("ajax_list_chap_url", "AJAX List URL:"),
            ("ajax_list_chap_id", "AJAX List ID:"),
        ]
        
        for prop, label in text_props:
            txt = QLineEdit()
            self.form_layout.addRow(label, txt)
            self.fields[prop] = txt
            
        # Checkboxes
        bool_props = [
            ("by_pass_cloudflare", "Bypass Cloudflare"),
            ("is_vietnamese_host", "Vietnamese Host"),
            ("is_chapter_link_absolute", "Absolute Chapter Link"),
            ("is_use_jsoup_get", "Use Jsoup (HTML parser)"),
            ("is_forum_type", "Forum Type"),
            ("is_manual_get", "Manual Get"),
            ("is_enable_chapter_sign", "Enable Chapter Sign"),
            ("is_revert_chapter_list", "Revert Chapter List"),
            ("use_brute_force_method", "Brute Force Method")
        ]
        
        for prop, label in bool_props:
            chk = QCheckBox(label)
            self.form_layout.addRow("", chk)
            self.fields[prop] = chk
            
        right_panel.setWidget(form_container)
        
        # Add to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([250, 550])
        
        main_layout.addWidget(splitter, stretch=1)
        
        # Bottom Buttons
        row_bottom = QHBoxLayout()
        btn_apply = QPushButton("Cập nhật config hiện tại")
        btn_apply.clicked.connect(self._on_apply_current)
        btn_save_all = QPushButton("LƯU TẤT CẢ VÀO FILE")
        btn_save_all.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold;")
        btn_save_all.clicked.connect(self._on_save_all)
        
        row_bottom.addStretch()
        row_bottom.addWidget(btn_apply)
        row_bottom.addWidget(btn_save_all)
        main_layout.addLayout(row_bottom)
        
        self._enable_form(False)

    def _populate_list(self):
        self.list_hosts.clear()
        for pc in self._configs:
            self.list_hosts.addItem(pc.page_code)
            
    def _enable_form(self, enabled: bool):
        for w in self.fields.values():
            w.setEnabled(enabled)

    def _on_host_selected(self, idx: int):
        if idx < 0 or idx >= len(self._configs):
            self._enable_form(False)
            self._current_config = None
            return
            
        self._current_config = self._configs[idx]
        self._enable_form(True)
        
        # Load values
        for prop, widget in self.fields.items():
            val = getattr(self._current_config, prop)
            if isinstance(widget, QLineEdit):
                widget.setText(str(val or ""))
            elif isinstance(widget, QCheckBox):
                widget.setChecked(bool(val))

    def _on_apply_current(self):
        if not self._current_config:
            return
            
        for prop, widget in self.fields.items():
            if isinstance(widget, QLineEdit):
                setattr(self._current_config, prop, widget.text().strip())
            elif isinstance(widget, QCheckBox):
                setattr(self._current_config, prop, widget.isChecked())
                
        # Cập nhật list item tên nếu page_code thay đổi
        idx = self.list_hosts.currentRow()
        if idx >= 0:
            self.list_hosts.item(idx).setText(self._current_config.page_code)
            
        QMessageBox.information(self, "Thành công", "Đã cập nhật cấu hình tạm thời.\nNhấn 'LƯU TẤT CẢ' để lưu vào ghfuConfig.json.")

    def _on_add(self):
        new_pc = PageConfig(page_code="new_host.com")
        self._configs.append(new_pc)
        self.list_hosts.addItem(new_pc.page_code)
        self.list_hosts.setCurrentRow(self.list_hosts.count() - 1)

    def _on_del(self):
        idx = self.list_hosts.currentRow()
        if idx < 0:
            return
            
        ans = QMessageBox.question(self, "Xác nhận", f"Xóa config {self._configs[idx].page_code}?")
        if ans == QMessageBox.StandardButton.Yes:
            self._configs.pop(idx)
            self.list_hosts.takeItem(idx)

    def _on_save_all(self):
        if self.config_mgr.save_config():
            QMessageBox.information(self, "Thành công", "Đã lưu toàn bộ cấu hình vào ghfuConfig.json!")
            self.accept()
        else:
            QMessageBox.critical(self, "Lỗi", "Không thể lưu file cấu hình.")
