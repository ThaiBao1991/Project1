import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, 
    QComboBox, QPushButton, QLabel, QProgressBar, 
    QMessageBox, QFileDialog, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSlot

from core.page_config_mgr import PageConfigManager
from models.page_config import PageConfig
from gui.workers import DownloadWorker

class ManualGetUI(QDialog):
    def __init__(self, config_mgr: PageConfigManager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manual GET - Tải thủ công danh sách Link")
        self.resize(600, 500)
        self.setMinimumSize(500, 400)
        self.config_mgr = config_mgr
        self.worker: DownloadWorker | None = None
        
        self._build_ui()
        self._populate_host_combo()
        
    def _build_ui(self):
        layout = QVBoxLayout(self)
        
        # Hướng dẫn
        lbl_guide = QLabel("Dán danh sách các link chương vào đây (Mỗi link 1 dòng):")
        layout.addWidget(lbl_guide)
        
        # Ô nhập URLs
        self.txt_urls = QTextEdit()
        self.txt_urls.setPlaceholderText("https://truyenyy.com/truyen/abc/chuong-1\nhttps://truyenyy.com/truyen/abc/chuong-2")
        layout.addWidget(self.txt_urls, stretch=2)
        
        # Chọn Host
        row_host = QHBoxLayout()
        row_host.addWidget(QLabel("Chọn Cấu Hình (Host):"))
        self.cbo_host = QComboBox()
        row_host.addWidget(self.cbo_host, stretch=1)
        layout.addLayout(row_host)
        
        # Nơi lưu
        row_save = QHBoxLayout()
        row_save.addWidget(QLabel("Lưu tại:"))
        self.txt_save_path = QLineEdit()
        self.txt_save_path.setReadOnly(True)
        row_save.addWidget(self.txt_save_path, stretch=1)
        
        self.btn_browse = QPushButton("Chọn...")
        self.btn_browse.clicked.connect(self._on_browse)
        row_save.addWidget(self.btn_browse)
        layout.addLayout(row_save)
        
        # Logs
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        layout.addWidget(self.txt_log, stretch=1)
        
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Nút điều khiển
        row_btn = QHBoxLayout()
        self.btn_download = QPushButton("Tải Xuống")
        self.btn_download.clicked.connect(self._on_download)
        self.btn_cancel = QPushButton("Hủy")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self._on_cancel)
        
        row_btn.addStretch()
        row_btn.addWidget(self.btn_download)
        row_btn.addWidget(self.btn_cancel)
        layout.addLayout(row_btn)
        
    def _populate_host_combo(self):
        configs = self.config_mgr.get_all_configs()
        for c in configs:
            self.cbo_host.addItem(c.page_code, userData=c)
            
    def _on_browse(self):
        ext_filter = "HTML Files (*.html);;Text Files (*.txt)"
        save_path, _ = QFileDialog.getSaveFileName(self, "Chọn nơi lưu file", "", ext_filter)
        if save_path:
            self.txt_save_path.setText(save_path)
            
    def _on_download(self):
        raw_text = self.txt_urls.toPlainText().strip()
        if not raw_text:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập ít nhất 1 URL.")
            return
            
        links = [url.strip() for url in raw_text.split('\n') if url.strip()]
        if not links:
            QMessageBox.warning(self, "Lỗi", "Không có URL hợp lệ.")
            return
            
        save_path = self.txt_save_path.text().strip()
        if not save_path:
            self._on_browse()
            save_path = self.txt_save_path.text().strip()
            if not save_path:
                return
                
        page_config: PageConfig = self.cbo_host.currentData()
        if not page_config:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn Host cấu hình.")
            return
            
        # UI State
        self.btn_download.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.txt_urls.setEnabled(False)
        self.cbo_host.setEnabled(False)
        self.progress_bar.setMaximum(len(links))
        self.progress_bar.setValue(0)
        self.txt_log.clear()
        
        # Khởi tạo Worker với manual_links
        # Truyền dummy url vào worker, config_mgr không dùng tới detect nữa vì có forced_page_config
        self.worker = DownloadWorker(
            url=links[0], # Dummy base url
            config_mgr=self.config_mgr,
            save_path=save_path,
            is_divide_file=False,
            manual_links=links,
            page_config=page_config
        )
        
        self.worker.log_signal.connect(self.txt_log.append)
        self.worker.progress_signal.connect(self._on_progress)
        self.worker.finished_signal.connect(self._on_finished)
        
        self.worker.start()
        
    def _on_progress(self, idx: int, status: str, err: str):
        self.progress_bar.setValue(idx + 1)
        
    def _on_cancel(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.txt_log.append("⏹️ Đang hủy...")
            self.btn_cancel.setEnabled(False)
            
    def _on_finished(self, msg: str):
        self.txt_log.append(f"\n🎉 HOÀN THÀNH: {msg}")
        self.btn_download.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.txt_urls.setEnabled(True)
        self.cbo_host.setEnabled(True)
        
    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
        event.accept()
