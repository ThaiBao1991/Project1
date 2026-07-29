from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QSpinBox, QCheckBox, QPushButton, QComboBox, 
    QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt, QSettings

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cài Đặt")
        self.resize(350, 300)
        self.settings = QSettings("Mkbyme", "GetHtmlFromUrl")
        
        self._build_ui()
        self._load_settings()
        
    def _build_ui(self):
        layout = QVBoxLayout(self)
        
        # Group: Tải xuống
        grp_download = QGroupBox("Cấu hình Tải xuống")
        form_dl = QFormLayout(grp_download)
        
        self.spn_timeout = QSpinBox()
        self.spn_timeout.setRange(5, 120)
        self.spn_timeout.setSuffix(" giây")
        form_dl.addRow("Thời gian chờ (Timeout):", self.spn_timeout)
        
        self.spn_delay = QSpinBox()
        self.spn_delay.setRange(0, 10000)
        self.spn_delay.setSuffix(" ms")
        self.spn_delay.setSingleStep(100)
        form_dl.addRow("Khoảng nghỉ giữa các chương:", self.spn_delay)
        
        self.spn_max_conn = QSpinBox()
        self.spn_max_conn.setRange(1, 32)
        form_dl.addRow("Số kết nối tối đa:", self.spn_max_conn)
        
        layout.addWidget(grp_download)
        
        # Group: Tùy chọn khác
        grp_other = QGroupBox("Giao diện / Khác")
        form_other = QFormLayout(grp_other)
        
        self.cbo_lang = QComboBox()
        self.cbo_lang.addItems(["Tiếng Việt", "English"])
        form_other.addRow("Ngôn ngữ:", self.cbo_lang)
        
        self.chk_show_img_warning = QCheckBox("Cảnh báo chương có chứa hình ảnh")
        form_other.addRow("", self.chk_show_img_warning)
        
        layout.addWidget(grp_other)
        layout.addStretch()
        
        # Buttons
        row_btn = QHBoxLayout()
        btn_save = QPushButton("Lưu cấu hình")
        btn_save.clicked.connect(self._on_save)
        btn_cancel = QPushButton("Hủy")
        btn_cancel.clicked.connect(self.reject)
        
        row_btn.addStretch()
        row_btn.addWidget(btn_save)
        row_btn.addWidget(btn_cancel)
        layout.addLayout(row_btn)
        
    def _load_settings(self):
        self.spn_timeout.setValue(self.settings.value("download/timeout", 30, type=int))
        self.spn_delay.setValue(self.settings.value("download/delay_ms", 300, type=int))
        self.spn_max_conn.setValue(self.settings.value("download/max_connection", 1, type=int))
        self.cbo_lang.setCurrentText(self.settings.value("ui/language", "Tiếng Việt", type=str))
        self.chk_show_img_warning.setChecked(self.settings.value("ui/show_img_warning", True, type=bool))
        
    def _on_save(self):
        self.settings.setValue("download/timeout", self.spn_timeout.value())
        self.settings.setValue("download/delay_ms", self.spn_delay.value())
        self.settings.setValue("download/max_connection", self.spn_max_conn.value())
        self.settings.setValue("ui/language", self.cbo_lang.currentText())
        self.settings.setValue("ui/show_img_warning", self.chk_show_img_warning.isChecked())
        self.accept()
