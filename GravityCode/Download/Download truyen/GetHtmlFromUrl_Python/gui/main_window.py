"""
main_window.py — Cửa sổ chính ứng dụng GetHtmlFromUrl
Clone 1:1 giao diện UI.java từ bản Java gốc (GetTextFromHtml-V1.5.6 by Mkbyme).
"""

import os
import time
import webbrowser
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QComboBox, QTextEdit, QProgressBar, QCheckBox, QGroupBox,
    QGridLayout, QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox,
    QMenuBar, QMenu, QStatusBar, QFrame, QSizePolicy, QToolButton
)
from PyQt6.QtGui import QAction, QColor, QFont, QPalette, QIcon
from PyQt6.QtCore import Qt, pyqtSlot, QSettings

from core.page_config_mgr import PageConfigManager
from gui.workers import DownloadWorker
from gui.dialogs import DownloadRangeDialog, EbookInfoDialog
from gui.manual_get_ui import ManualGetUI
from gui.settings_dialog import SettingsDialog
from gui.quick_login_dialog import QuickLoginDialog
from gui.config_mgr_dialog import ConfigManagerDialog
from gui.resume_dialog import ResumeDialog
from gui.html_fixer_dialog import HtmlFixerDialog


class MainWindow(QMainWindow):
    """
    Cửa sổ chính — tương đương UI.java
    """

    APP_TITLE = "GetTextFromHtml - Python Edition by Mkbyme"
    SETTINGS_KEY_ONE_PER_FILE = "ui/one_per_file"
    SETTINGS_KEY_ADD_EBOOK_INFO = "ui/add_ebook_info"
    SETTINGS_KEY_USE_RANGE = "ui/use_range"

    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.APP_TITLE)
        self.setMinimumSize(600, 440)
        self.resize(650, 480)

        # Nạp cấu hình sites
        cfg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "ghfuConfig.json")
        self.config_mgr = PageConfigManager(cfg_path)
        self._all_configs = self.config_mgr.get_all_configs()

        # QSettings để lưu UX state
        self.settings = QSettings("Mkbyme", "GetHtmlFromUrl")

        self.worker: DownloadWorker | None = None
        self._download_range = (0, -1)   # (start_idx, end_idx)
        self._ebook_info_html = ""
        self._total_chapters = 0  # set khi nhận chapter_list_ready signal

        self._build_menu()
        self._build_ui()
        self._restore_settings()
        self._populate_host_combo()

    # ---------------------------------------------------------------
    # Menu Bar (tương đương JMenuBar Java)
    # ---------------------------------------------------------------
    def _build_menu(self):
        mb: QMenuBar = self.menuBar()

        # Tệp
        menu_file = QMenu("Tệp", self)
        
        act_new_window = QAction("Cửa Sổ Mới", self)
        act_new_window.triggered.connect(self._on_new_window)
        menu_file.addAction(act_new_window)
        
        act_open_browser = QAction("Mở trình duyệt", self)
        act_open_browser.triggered.connect(self._on_open_browser)
        menu_file.addAction(act_open_browser)
        
        act_host_manager = QAction("Quản Lý Host", self)
        act_host_manager.triggered.connect(self._on_host_manager)
        menu_file.addAction(act_host_manager)
        
        act_settings = QAction("Cài Đặt", self)
        act_settings.triggered.connect(self._on_settings)
        menu_file.addAction(act_settings)
        
        act_manual_get = QAction("Manual GET(*)", self)
        act_manual_get.triggered.connect(self._on_manual_get)
        menu_file.addAction(act_manual_get)
        
        menu_file.addSeparator()
        
        act_exit = QAction("Thoát", self)
        act_exit.triggered.connect(self.close)
        menu_file.addAction(act_exit)
        mb.addMenu(menu_file)

        # Thông Tin
        menu_info = QMenu("Thông Tin", self)
        
        act_author = QAction("Tác Giả", self)
        act_author.triggered.connect(self._on_about_author)
        menu_info.addAction(act_author)
        
        act_help = QAction("Trợ Giúp", self)
        act_help.triggered.connect(self._on_about_help)
        menu_info.addAction(act_help)
        
        act_check_update = QAction("Kiểm tra cập nhật", self)
        act_check_update.triggered.connect(self._on_check_update)
        menu_info.addAction(act_check_update)
        
        act_homepage = QAction("Trang Chủ", self)
        act_homepage.triggered.connect(lambda: webbrowser.open("https://github.com/mkbyme"))
        menu_info.addAction(act_homepage)
        
        act_fanpage = QAction("Fanpage", self)
        act_fanpage.triggered.connect(lambda: webbrowser.open("https://fb.com/mkbyme"))
        menu_info.addAction(act_fanpage)
        
        mb.addMenu(menu_info)

        # Đường Dẫn Trợ Giúp
        menu_help = QMenu("Đường Dẫn Trợ Giúp", self)
        
        act_guide_use = QAction("Hướng Dẫn Sử Dụng", self)
        act_guide_use.triggered.connect(lambda: webbrowser.open("https://mkbyme.com"))
        menu_help.addAction(act_guide_use)
        
        act_guide_convert = QAction("Hướng Dẫn Convert", self)
        act_guide_convert.triggered.connect(lambda: webbrowser.open("https://mkbyme.com"))
        menu_help.addAction(act_guide_convert)
        
        act_guide_add_host = QAction("Hướng Dẫn Thêm Host", self)
        act_guide_add_host.triggered.connect(lambda: webbrowser.open("https://mkbyme.com"))
        menu_help.addAction(act_guide_add_host)
        
        act_download_config = QAction("Tải File Config", self)
        act_download_config.triggered.connect(self._on_download_config)
        menu_help.addAction(act_download_config)
        
        mb.addMenu(menu_help)

        # Công cụ
        menu_tools = QMenu("Công cụ", self)
        
        act_login_to = QAction("Login tới trang", self)
        act_login_to.triggered.connect(self._on_login_to)
        menu_tools.addAction(act_login_to)
        
        act_quick_login = QAction("Đăng nhập nhanh từ cookies", self)
        act_quick_login.triggered.connect(self._on_quick_login)
        menu_tools.addAction(act_quick_login)
        
        menu_tools.addSeparator()
        
        act_resume = QAction("Quản lý Resume (Tải tiếp file lỗi)", self)
        act_resume.triggered.connect(self._on_resume_manager)
        menu_tools.addAction(act_resume)
        
        act_fix_html = QAction("Sửa lỗi font HTML", self)
        act_fix_html.triggered.connect(self._on_fix_html)
        menu_tools.addAction(act_fix_html)
        
        mb.addMenu(menu_tools)

    # ---------------------------------------------------------------
    # Main UI Layout (clone bố cục Java Swing)
    # ---------------------------------------------------------------
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(8, 6, 8, 6)
        root.setSpacing(4)

        # ── Hàng 1: URL + Nút Tải Xuống ─────────────────────────────
        row1 = QHBoxLayout()
        lbl_url = QLabel("URL (CTRL+V):")
        lbl_url.setFixedWidth(100)
        self.txt_url = QLineEdit()
        self.txt_url.setPlaceholderText("Dán link truyện vào đây...")
        self.txt_url.textChanged.connect(self._on_url_changed)

        self.btn_download = QPushButton("Tải Xuống")
        self.btn_download.setFixedWidth(90)
        self.btn_download.clicked.connect(self._on_start_download)

        row1.addWidget(lbl_url)
        row1.addWidget(self.txt_url)
        row1.addWidget(self.btn_download)
        root.addLayout(row1)

        # ── Hàng 1b: Lưu tại ──────────────────────────────────
        row_save = QHBoxLayout()
        lbl_save = QLabel("Lưu tại:")
        lbl_save.setFixedWidth(100)
        self.txt_save_path = QLineEdit()
        self.txt_save_path.setPlaceholderText("Chọn đường dẫn lưu file...")
        self.txt_save_path.setReadOnly(False)
        self.btn_browse = QPushButton("📂 Chọn...")
        self.btn_browse.setFixedWidth(90)
        self.btn_browse.clicked.connect(self._on_browse_save)
        row_save.addWidget(lbl_save)
        row_save.addWidget(self.txt_save_path)
        row_save.addWidget(self.btn_browse)
        root.addLayout(row_save)

        # ── Hàng 2: Tìm kiếm host ────────────────────────────────────
        row2 = QHBoxLayout()
        lbl_filter = QLabel("Tìm kiếm host:")
        lbl_filter.setFixedWidth(100)

        self.cbo_host_type = QComboBox()
        self.cbo_host_type.setFixedWidth(130)
        self.cbo_host_type.addItems(["Tất cả host", "Web: Việt Nam", "Web: Trung Quốc", "Web: Khác"])
        self.cbo_host_type.currentIndexChanged.connect(self._filter_host_list)

        self.txt_filter = QLineEdit()
        self.txt_filter.setPlaceholderText("Nhập tên host cần tìm hoặc nhận diện, nhập...")
        self.txt_filter.textChanged.connect(self._filter_host_list)

        self.btn_clear_filter = QPushButton("✕")
        self.btn_clear_filter.setFixedWidth(28)
        self.btn_clear_filter.setToolTip("Xóa bộ lọc")
        self.btn_clear_filter.clicked.connect(lambda: self.txt_filter.clear())

        self.btn_cancel = QPushButton("Hủy")
        self.btn_cancel.setFixedWidth(70)
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self._on_cancel)

        row2.addWidget(lbl_filter)
        row2.addWidget(self.cbo_host_type)
        row2.addWidget(self.txt_filter)
        row2.addWidget(self.btn_clear_filter)
        row2.addWidget(self.btn_cancel)
        root.addLayout(row2)

        # ── Hàng 3: Số Host + Dropdown Host + Nút Tải Tiếp ──────────
        row3 = QHBoxLayout()
        self.btn_host_count = QPushButton("0 Host")
        self.btn_host_count.setFixedWidth(80)
        self.btn_host_count.setStyleSheet("color: green; font-weight: bold; border: none;")
        self.btn_host_count.setFlat(True)
        self.btn_host_count.setToolTip("Tổng số host đang được hỗ trợ")

        self.cbo_page_config = QComboBox()
        self.cbo_page_config.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.cbo_page_config.currentIndexChanged.connect(self._on_host_selected)

        self.btn_resume = QPushButton("Tải Tiếp/T...")
        self.btn_resume.setFixedWidth(100)
        self.btn_resume.setEnabled(False)
        self.btn_resume.setToolTip("Tiếp tục tải từ chương bị dừng")
        self.btn_resume.clicked.connect(self._on_resume)

        row3.addWidget(self.btn_host_count)
        row3.addWidget(self.cbo_page_config)
        row3.addWidget(self.btn_resume)
        root.addLayout(row3)

        # ── Hàng 4: Link hướng dẫn ───────────────────────────────────
        self.lbl_guide = QLabel()
        self.lbl_guide.setTextFormat(Qt.TextFormat.RichText)
        self.lbl_guide.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self.lbl_guide.setOpenExternalLinks(True)
        self.lbl_guide.setText('🔴 <a href="">Hướng dẫn tải truyện</a>')
        root.addWidget(self.lbl_guide)

        # ── Separator ────────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        root.addWidget(sep)

        # ── Tùy chọn: 2 GroupBox song song ──────────────────────────
        options_row = QHBoxLayout()

        grp_download = QGroupBox("Tùy Chọn Tải Xuống")
        vbox_dl = QVBoxLayout(grp_download)
        self.chk_download_range = QCheckBox("Chọn Phạm Vi Tải...")
        self.chk_download_range.stateChanged.connect(self._on_range_checked)
        self.chk_add_ebook_info = QCheckBox("Chèn Thông Tin Ebook...")
        self.chk_add_ebook_info.stateChanged.connect(self._on_ebook_info_checked)
        vbox_dl.addWidget(self.chk_download_range)
        vbox_dl.addWidget(self.chk_add_ebook_info)

        grp_save = QGroupBox("Tùy Chỉnh Lưu Tệp")
        vbox_sv = QVBoxLayout(grp_save)
        self.chk_one_file_per = QCheckBox("Mỗi chương thành 1 tệp")
        vbox_sv.addWidget(self.chk_one_file_per)

        options_row.addWidget(grp_download)
        options_row.addWidget(grp_save)
        root.addLayout(options_row)

        # ── Trạng thái + Progress Bar ────────────────────────────────
        self.lbl_status = QLabel("Trạng Thái Không")
        root.addWidget(self.lbl_status)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        root.addWidget(self.progress_bar)

        # ── Console Logs ─────────────────────────────────────────────
        lbl_logs = QLabel("Logs")
        root.addWidget(lbl_logs)

        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setFont(QFont("Consolas", 9))
        self.txt_log.setMinimumHeight(120)
        root.addWidget(self.txt_log, stretch=1)

    # ---------------------------------------------------------------
    # Khởi tạo dữ liệu
    # ---------------------------------------------------------------
    def _populate_host_combo(self):
        """Nạp danh sách host từ config vào ComboBox"""
        self.cbo_page_config.clear()
        configs = self._all_configs

        # Lọc theo search text + type
        txt = self.txt_filter.text().strip().lower()
        type_filter = self.cbo_host_type.currentText()

        filtered = []
        for c in configs:
            if txt and txt not in c.page_code.lower():
                continue
            if type_filter == "Web: Việt Nam" and not getattr(c, 'is_vietnamese_host', False):
                continue
            filtered.append(c)

        for c in filtered:
            label = f"{c.page_code}"
            if getattr(c, 'is_vietnamese_host', False):
                label += " - Web: Việt Nam"
            self.cbo_page_config.addItem(label, userData=c)

        self.btn_host_count.setText(f"{len(self._all_configs)} Host")

    def _restore_settings(self):
        """Khôi phục trạng thái UX (checkbox) từ lần chạy trước"""
        self.chk_one_file_per.setChecked(
            self.settings.value(self.SETTINGS_KEY_ONE_PER_FILE, False, type=bool)
        )
        self.chk_add_ebook_info.setChecked(
            self.settings.value(self.SETTINGS_KEY_ADD_EBOOK_INFO, False, type=bool)
        )
        self.chk_download_range.setChecked(
            self.settings.value(self.SETTINGS_KEY_USE_RANGE, False, type=bool)
        )

    def _save_settings(self):
        """Lưu trạng thái UX"""
        self.settings.setValue(self.SETTINGS_KEY_ONE_PER_FILE, self.chk_one_file_per.isChecked())
        self.settings.setValue(self.SETTINGS_KEY_ADD_EBOOK_INFO, self.chk_add_ebook_info.isChecked())
        self.settings.setValue(self.SETTINGS_KEY_USE_RANGE, self.chk_download_range.isChecked())

    # ---------------------------------------------------------------
    # Event Handlers
    # ---------------------------------------------------------------
    def _on_url_changed(self, text: str):
        """Khi URL thay đổi → tự động chọn host phù hợp trong dropdown"""
        if not text:
            return
        matched = self.config_mgr.get_config_by_url(text)
        if matched:
            for i in range(self.cbo_page_config.count()):
                data = self.cbo_page_config.itemData(i)
                if data and data.page_code == matched.page_code:
                    self.cbo_page_config.setCurrentIndex(i)
                    break

    def _on_host_selected(self, idx: int):
        """Khi chọn host trong dropdown → cập nhật link hướng dẫn"""
        config = self.cbo_page_config.itemData(idx)
        if config:
            url = getattr(config, 'url_page_test', '') or f"https://{config.page_code}"
            guide = getattr(config, 'text_guide', '') or ""
            host_label = config.page_code
            self.lbl_guide.setText(
                f'🔴 <a href="{url}">Hướng dẫn tải truyện trên "{host_label}"</a>'
            )
            self.btn_help_tooltip = guide

    @pyqtSlot()
    def _on_browse_save(self):
        """Mở dialog chọn nơi lưu file"""
        ext_filter = "HTML Files (*.html);;Text Files (*.txt)"
        save_path, _ = QFileDialog.getSaveFileName(self, "Chọn nơi lưu file", "", ext_filter)
        if save_path:
            self.txt_save_path.setText(save_path)

    @pyqtSlot()
    def _on_start_download(self):
        url = self.txt_url.text().strip()
        if not url:
            QMessageBox.warning(self, "Thiếu URL", "Vui lòng nhập URL truyện!")
            return
        if not url.startswith("http://") and not url.startswith("https://"):
            QMessageBox.warning(self, "URL không hợp lệ", "URL phải bắt đầu bằng http:// hoặc https://")
            return

        save_path = self.txt_save_path.text().strip()
        if not save_path:
            # Hỏi nếu chưa chọn đường dẫn
            ext_filter = "HTML Files (*.html);;Text Files (*.txt)"
            save_path, _ = QFileDialog.getSaveFileName(self, "Chọn nơi lưu file", "", ext_filter)
            if not save_path:
                return
            self.txt_save_path.setText(save_path)

        file_format = "txt" if save_path.endswith(".txt") else "html"

        self._toggle_download_state(True)
        self.txt_log.clear()
        self.progress_bar.setValue(0)
        self.lbl_status.setText("Đang tải...")

        start_idx, end_idx = self._download_range

        self.worker = DownloadWorker(
            url=url,
            config_mgr=self.config_mgr,
            save_path=save_path,
            is_divide_file=self.chk_one_file_per.isChecked(),
            ebook_info=self._ebook_info_html,
            start_idx=start_idx,
            end_idx=end_idx,
            file_format=file_format,
        )
        self.worker.log_signal.connect(self.txt_log.append)
        self.worker.progress_signal.connect(self._on_progress)
        self.worker.finished_signal.connect(self._on_finished)
        self.worker.chapter_list_ready.connect(self._on_chapter_list_ready)
        self.worker.start()

    @pyqtSlot()
    def _on_cancel(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.lbl_status.setText("Đã hủy")
        self._toggle_download_state(False)

    @pyqtSlot()
    def _on_resume(self):
        """Tiếp tục tải (Resume) — đặt lại trạng thái và bắt đầu lại"""
        self._on_start_download()

    @pyqtSlot(int, str, str)
    def _on_progress(self, idx: int, status: str, error: str):
        self.lbl_status.setText(f"Chương {idx + 1}: {status}")
        if self._total_chapters > 0 and self.worker:
            start = self.worker.start_idx
            end = self.worker.end_idx if self.worker.end_idx != -1 else (self._total_chapters - 1)
            total = end - start + 1
            if total > 0:
                done = idx - start + 1
                pct = max(0, min(100, int(done / total * 100)))
                self.progress_bar.setValue(pct)

    @pyqtSlot(int)
    def _on_chapter_list_ready(self, total: int):
        """Được gọi khi lấy xong danh sách chương."""
        self._total_chapters = total
        self.txt_log.append(f"📋 Tổng số chương: {total}")
        # Hiển thị dialog Range nếu checkbox bật
        if self.chk_download_range.isChecked():
            dlg = DownloadRangeDialog(total, self)
            if dlg.exec():
                self._download_range = (dlg.start_index, dlg.end_index)
                if self.worker:
                    self.worker.start_idx = dlg.start_index
                    self.worker.end_idx = dlg.end_index

    @pyqtSlot(str)
    def _on_finished(self, msg: str):
        self._toggle_download_state(False)
        self.progress_bar.setValue(100)
        self.lbl_status.setText("Trạng Thái Không")
        self._save_settings()
        self.txt_log.append(f"\n🏁 {msg}")
        if "Lỗi" not in msg:
            QMessageBox.information(self, "Hoàn tất", f"Đã tải xong!\n{msg}")

    @pyqtSlot(int)
    def _on_range_checked(self, state: int):
        """Khi bật "Chọn phạm vi tải" → reset range về mặc định"""
        if state == 0:
            self._download_range = (0, -1)

    @pyqtSlot(int)
    def _on_ebook_info_checked(self, state: int):
        """Khi bật Chèn Thông Tin Ebook → mở dialog nhập thông tin"""
        if state == 2:  # Checked
            dlg = EbookInfoDialog(self)
            if dlg.exec():
                self._ebook_info_html = dlg.get_info_html()
            else:
                self.chk_add_ebook_info.setChecked(False)
                self._ebook_info_html = ""
        else:
            self._ebook_info_html = ""

    def _filter_host_list(self):
        """Lọc danh sách host theo text search"""
        self._populate_host_combo()

    def _toggle_download_state(self, is_downloading: bool):
        self.btn_download.setEnabled(not is_downloading)
        self.btn_cancel.setEnabled(is_downloading)
        self.btn_resume.setEnabled(not is_downloading)

    # ---------------------------------------------------------------
    # Menu Actions
    # ---------------------------------------------------------------
    def _on_open_config(self):
        path, _ = QFileDialog.getOpenFileName(self, "Mở file config", "", "JSON Files (*.json)")
        if path:
            try:
                self.config_mgr = PageConfigManager(path)
                self._all_configs = self.config_mgr.get_all_configs()
                self._populate_host_combo()
                self.txt_log.append(f"✅ Đã nạp config: {path}")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể nạp config:\n{e}")

    def _on_settings(self):
        try:
            dlg = SettingsDialog(self)
            dlg.exec()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể mở Cài Đặt:\n{e}")

    def _on_new_window(self):
        import subprocess
        subprocess.Popen([sys.executable, sys.argv[0]])

    def _on_open_browser(self):
        QMessageBox.information(self, "Mở trình duyệt", "Sẽ mở MKBrowser trong tương lai.")

    def _on_host_manager(self):
        try:
            dlg = ConfigManagerDialog(self.config_mgr, self)
            if dlg.exec():
                # Nạp lại dữ liệu vào list nếu user lưu thành công
                self._all_configs = self.config_mgr.get_all_configs()
                self._populate_host_combo()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể mở Quản Lý Host:\n{e}")

    def _on_manual_get(self):
        try:
            if not hasattr(self, 'manual_get_ui') or self.manual_get_ui is None:
                self.manual_get_ui = ManualGetUI(self.config_mgr, self)
            self.manual_get_ui.show()
            self.manual_get_ui.raise_()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể mở Manual GET:\n{e}")

    def _on_about_author(self):
        QMessageBox.about(self, "Tác Giả", "code by Mkbyme\nemail: mkbyme@gmail.com\nfacebook: fb.com/mkbyme")

    def _on_about_help(self):
        QMessageBox.information(self, "Trợ Giúp", "Cửa sổ hướng dẫn (Info.java)...")

    def _on_check_update(self):
        QMessageBox.information(self, "Cập nhật", "Đang kiểm tra cập nhật trên Github...")

    def _on_download_config(self):
        QMessageBox.information(self, "Tải Config", "Đang tải ghfuConfig.json mới nhất từ server...")

    def _on_login_to(self):
        QMessageBox.information(self, "Login", "Mở trình duyệt nhúng để đăng nhập (giữ cookies)...")

    def _on_quick_login(self):
        try:
            dlg = QuickLoginDialog(self.config_mgr, self)
            dlg.exec()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể mở Quick Login:\n{e}")

    def _on_resume_manager(self):
        try:
            dlg = ResumeDialog(self, self)
            dlg.exec()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể mở Quản Lý Resume:\n{e}")

    def _on_fix_html(self):
        try:
            dlg = HtmlFixerDialog(self)
            dlg.exec()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể mở Sửa HTML:\n{e}")

    # ---------------------------------------------------------------
    # Window Close
    # ---------------------------------------------------------------
    def closeEvent(self, event):
        self._save_settings()
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(2000)
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
