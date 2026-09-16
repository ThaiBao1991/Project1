import os
import re
import json
import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QTextEdit, QPushButton, QFileDialog, QMessageBox, 
    QLineEdit, QProgressBar, QCheckBox, QSpinBox, 
    QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget,
    QWidget, QGroupBox, QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from core.ai_translator import (
    GeminiTranslator, GlossaryManager, TranslateProgress,
    extract_chapter_from_html, save_translated_chapter,
    load_askcpl_keys, DEFAULT_MODELS
)
from gui.workers import MergeWorker, PrcWorker

logger = logging.getLogger("translate_dialog")


class TranslateWorker(QThread):
    """Worker chạy tiến trình dịch truyện nền, tránh block giao diện PyQt6."""
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int, int, str)  # current, total, status_text
    glossary_updated_signal = pyqtSignal(int)    # total_terms
    finished_signal = pyqtSignal(bool, str)      # success, message

    def __init__(self, source_dir: str, target_dir: str, 
                 api_keys: list, start_idx: int, end_idx: int,
                 skip_existing: bool, pace_seconds: float = 3.5):
        super().__init__()
        self.source_dir = source_dir
        self.target_dir = target_dir
        self.api_keys = api_keys
        self.start_idx = start_idx
        self.end_idx = end_idx
        self.skip_existing = skip_existing
        self.pace_seconds = pace_seconds
        self._is_stopped = False
        self.translator = None

    def stop(self):
        self._is_stopped = True
        if self.translator:
            self.translator.stop()

    def run(self):
        try:
            if not os.path.exists(self.source_dir):
                self.finished_signal.emit(False, f"Thư mục nguồn không tồn tại: {self.source_dir}")
                return

            os.makedirs(self.target_dir, exist_ok=True)

            # 1. Tìm tất cả file HTML trong thư mục nguồn
            all_files = sorted([
                f for f in os.listdir(self.source_dir)
                if f.lower().endswith((".html", ".htm")) and not f.startswith("_")
            ])

            if not all_files:
                self.finished_signal.emit(False, "Không tìm thấy file chương HTML nào trong thư mục nguồn.")
                return

            # Cắt theo khoảng range
            total_available = len(all_files)
            actual_start = max(0, self.start_idx - 1)
            actual_end = min(total_available, self.end_idx) if self.end_idx > 0 else total_available
            target_files = all_files[actual_start:actual_end]

            if not target_files:
                self.finished_signal.emit(False, "Không có file nào trong khoảng chương đã chọn.")
                return

            self.log_signal.emit(f"🚀 Bắt đầu tiến trình dịch {len(target_files)} chương (từ #{actual_start + 1} đến #{actual_end})...")

            # 2. Khởi tạo Glossary & Progress manager
            glossary_path = os.path.join(self.target_dir, "_glossary.json")
            progress_path = os.path.join(self.target_dir, "_translate_progress.json")
            
            glossary = GlossaryManager(glossary_path)
            progress = TranslateProgress(progress_path)

            total_terms = sum(len(v) for v in glossary.data.values())
            self.glossary_updated_signal.emit(total_terms)
            self.log_signal.emit(f"📖 Đã tải từ điển thuật ngữ: {total_terms} từ (nhân vật, pháp bảo, môn phái, địa danh).")

            # 3. Khởi tạo Translator
            self.translator = GeminiTranslator(
                api_keys=self.api_keys,
                pace_seconds=self.pace_seconds,
                log_callback=self.log_signal.emit
            )

            completed_count = 0
            total_task = len(target_files)

            for i, fname in enumerate(target_files):
                if self._is_stopped:
                    self.log_signal.emit("⏸ Đã dừng tiến trình dịch theo yêu cầu.")
                    self.finished_signal.emit(False, "Đã tạm dừng tiến trình dịch.")
                    return

                src_file_path = os.path.join(self.source_dir, fname)
                dst_file_path = os.path.join(self.target_dir, fname)

                # Kiểm tra resume
                if self.skip_existing and (progress.is_completed(fname) or os.path.exists(dst_file_path)):
                    self.log_signal.emit(f"⏩ [Bỏ qua] {fname} (đã dịch trước đó).")
                    completed_count += 1
                    self.progress_signal.emit(completed_count, total_task, f"Đã qua: {fname}")
                    continue

                self.log_signal.emit(f"\n⏳ [{i + 1}/{total_task}] Đang đọc & dịch: {fname}...")
                self.progress_signal.emit(completed_count, total_task, f"Đang dịch: {fname}")

                # Trích xuất nội dung chương tiếng Trung
                title_zh, content_zh = extract_chapter_from_html(src_file_path)
                if not content_zh.strip():
                    self.log_signal.emit(f"⚠️ File {fname} không có nội dung văn bản. Bỏ qua.")
                    continue

                # Lấy ngữ cảnh tóm tắt trước đó
                prev_summary = progress.data.get("last_summary", "")

                try:
                    # Gọi Gemini dịch
                    res = self.translator.translate_chapter(
                        title_zh=title_zh,
                        content_zh=content_zh,
                        glossary=glossary,
                        previous_summary=prev_summary
                    )

                    title_vi = res.get("title_vi", title_zh)
                    content_vi = res.get("content_vi", "")
                    new_terms = res.get("new_terms", {})
                    summary = res.get("summary", "")

                    # Cập nhật từ điển nếu phát hiện thuật ngữ mới
                    if new_terms:
                        glossary.add_terms(new_terms)
                        total_terms = sum(len(v) for v in glossary.data.values())
                        self.glossary_updated_signal.emit(total_terms)
                        
                        # In thông tin thuật ngữ mới
                        added_strs = []
                        for cat, kvs in new_terms.items():
                            if isinstance(kvs, dict):
                                for zh, vi in kvs.items():
                                    added_strs.append(f"{zh}→{vi}")
                        if added_strs:
                            self.log_signal.emit(f"  ✨ Thuật ngữ mới ghi nhận: {', '.join(added_strs[:6])}")

                    # Lưu file dịch ra HTML
                    save_translated_chapter(dst_file_path, title_vi, content_vi)

                    # Đánh dấu hoàn thành & lưu rolling summary
                    progress.mark_completed(fname, summary)

                    completed_count += 1
                    self.progress_signal.emit(completed_count, total_task, f"Xong: {title_vi}")
                    self.log_signal.emit(f"  ✅ Dịch thành công: {title_vi} ({len(content_vi)} ký tự)")
                    if summary:
                        self.log_signal.emit(f"  📝 Tóm tắt ngữ cảnh: {summary[:100]}...")

                except Exception as ex:
                    self.log_signal.emit(f"  ❌ Lỗi khi dịch {fname}: {ex}")
                    logger.error(f"Lỗi dịch {fname}: {ex}")
                    # Chờ một chút trước khi tiếp tục
                    self.sleep(2)

            self.progress_signal.emit(total_task, total_task, "Hoàn tất dịch!")
            self.log_signal.emit(f"\n🎉 HOÀN THÀNH DỊCH {completed_count}/{total_task} chương!")
            self.finished_signal.emit(True, f"Đã hoàn thành dịch {completed_count}/{total_task} chương.")

        except Exception as e:
            self.log_signal.emit(f"❌ Lỗi ngoại lệ trong luồng dịch: {e}")
            self.finished_signal.emit(False, f"Lỗi: {e}")


class GlossaryDialog(QDialog):
    """Giao diện xem và chỉnh sửa Từ điển Thuật ngữ (Nhân vật, Môn phái, Vũ khí, Địa danh)."""
    def __init__(self, glossary: GlossaryManager, parent=None):
        super().__init__(parent)
        self.glossary = glossary
        self.setWindowTitle("📖 Quản Lý Từ Điển Thuật Ngữ (Glossary)")
        self.resize(750, 500)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        lbl_desc = QLabel(
            "Từ điển giúp AI cố định cách dịch tên nhân vật, môn phái, vũ khí, địa danh xuyên suốt toàn bộ tác phẩm.\n"
            "AI sẽ tự động bổ sung từ mới trong quá trình dịch, bạn cũng có thể tự do thêm/sửa/xóa từ tại đây:"
        )
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("color: #444; font-size: 13px; margin-bottom: 6px;")
        layout.addWidget(lbl_desc)

        self.tabs = QTabWidget()
        self.tables = {}

        categories = [
            ("characters", "👤 Nhân vật"),
            ("weapons", "⚔️ Vũ khí / Bảo vật"),
            ("sects", "🏯 Tông môn / Thế lực"),
            ("locations", "🗺️ Địa danh"),
            ("others", "📌 Khác")
        ]

        for cat_key, cat_title in categories:
            tab_widget = QWidget()
            tab_layout = QVBoxLayout(tab_widget)

            table = QTableWidget()
            table.setColumnCount(2)
            table.setHorizontalHeaderLabels(["Tiếng Trung (Gốc)", "Tiếng Việt (Hán-Việt)"])
            table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

            # Load data
            items = self.glossary.data.get(cat_key, {})
            table.setRowCount(len(items))
            for row_idx, (zh, vi) in enumerate(items.items()):
                table.setItem(row_idx, 0, QTableWidgetItem(zh))
                table.setItem(row_idx, 1, QTableWidgetItem(vi))

            tab_layout.addWidget(table)

            # Button add/delete row
            btn_row = QHBoxLayout()
            btn_add = QPushButton("➕ Thêm dòng")
            btn_del = QPushButton("➖ Xóa dòng chọn")
            btn_add.clicked.connect(lambda _, t=table: self._add_row(t))
            btn_del.clicked.connect(lambda _, t=table: self._del_row(t))

            btn_row.addWidget(btn_add)
            btn_row.addWidget(btn_del)
            btn_row.addStretch()
            tab_layout.addLayout(btn_row)

            self.tables[cat_key] = table
            self.tabs.addTab(tab_widget, cat_title)

        layout.addWidget(self.tabs)

        # Bottom buttons
        bottom_row = QHBoxLayout()
        btn_save = QPushButton("💾 Lưu Thay Đổi")
        btn_save.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; padding: 6px 16px;")
        btn_save.clicked.connect(self._on_save)

        btn_close = QPushButton("Đóng")
        btn_close.clicked.connect(self.reject)

        bottom_row.addStretch()
        bottom_row.addWidget(btn_save)
        bottom_row.addWidget(btn_close)
        layout.addLayout(bottom_row)

    def _add_row(self, table: QTableWidget):
        row = table.rowCount()
        table.insertRow(row)
        table.setItem(row, 0, QTableWidgetItem(""))
        table.setItem(row, 1, QTableWidgetItem(""))

    def _del_row(self, table: QTableWidget):
        row = table.currentRow()
        if row >= 0:
            table.removeRow(row)

    def _on_save(self):
        for cat_key, table in self.tables.items():
            new_dict = {}
            for r in range(table.rowCount()):
                zh_item = table.item(r, 0)
                vi_item = table.item(r, 1)
                zh = zh_item.text().strip() if zh_item else ""
                vi = vi_item.text().strip() if vi_item else ""
                if zh and vi:
                    new_dict[zh] = vi
            self.glossary.data[cat_key] = new_dict
        self.glossary.save()
        QMessageBox.information(self, "Thành công", "Đã lưu từ điển thuật ngữ thành công!")
        self.accept()


class TranslateDialog(QDialog):
    """Dialog Tiện ích Dịch Truyện AI (Trung → Việt) tích hợp vào GetHtmlFromUrl."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🌐 Tiện Ích AI Dịch Truyện (Google Gemini)")
        self.resize(880, 680)
        self.setMinimumSize(780, 580)
        self.worker: TranslateWorker | None = None
        self.merge_worker: MergeWorker | None = None
        self.prc_worker: PrcWorker | None = None

        self._build_ui()
        self._auto_load_keys()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # ── 1. Group: Thư mục nguồn & đích ──────────────────────────────
        grp_folders = QGroupBox("1. Thư mục truyện")
        f_layout = QVBoxLayout(grp_folders)

        # Hàng chọn thư mục nguồn
        row_src = QHBoxLayout()
        lbl_src = QLabel("Thư mục tiếng Trung:")
        lbl_src.setFixedWidth(140)
        self.txt_source = QLineEdit()
        self.txt_source.setPlaceholderText("Chọn thư mục chứa các file .html tiếng Trung đã tải về...")
        self.txt_source.textChanged.connect(self._on_source_changed)
        btn_browse_src = QPushButton("📁 Chọn Thư Mục...")
        btn_browse_src.clicked.connect(self._on_browse_source)
        btn_split_src = QPushButton("✂️ Tách File Gộp...")
        btn_split_src.setToolTip("Tách file HTML/TXT gộp lớn thành từng chương riêng lẻ trước khi dịch")
        btn_split_src.clicked.connect(self._on_split_source_file)
        row_src.addWidget(lbl_src)
        row_src.addWidget(self.txt_source)
        row_src.addWidget(btn_browse_src)
        row_src.addWidget(btn_split_src)
        f_layout.addLayout(row_src)

        # Hàng thư mục dịch
        row_dst = QHBoxLayout()
        lbl_dst = QLabel("Thư mục lưu bản dịch:")
        lbl_dst.setFixedWidth(140)
        self.txt_target = QLineEdit()
        self.txt_target.setPlaceholderText("Tự động tạo thư mục 'dich' bên trong thư mục nguồn...")
        btn_browse_dst = QPushButton("📂 Thay Đổi...")
        btn_browse_dst.clicked.connect(self._on_browse_target)
        row_dst.addWidget(lbl_dst)
        row_dst.addWidget(self.txt_target)
        row_dst.addWidget(btn_browse_dst)
        f_layout.addLayout(row_dst)

        # Trạng thái scan thư mục
        self.lbl_folder_stats = QLabel("Chưa chọn thư mục nguồn.")
        self.lbl_folder_stats.setStyleSheet("color: #1976d2; font-weight: 500;")
        f_layout.addWidget(self.lbl_folder_stats)

        layout.addWidget(grp_folders)

        # ── 2. Group: Cấu hình AI & API Keys ───────────────────────────
        grp_ai = QGroupBox("2. Cấu hình Gemini AI & Thuật ngữ")
        ai_layout = QVBoxLayout(grp_ai)

        row_key = QHBoxLayout()
        lbl_key = QLabel("Gemini API Key(s):")
        lbl_key.setFixedWidth(140)
        self.txt_api_keys = QLineEdit()
        self.txt_api_keys.setPlaceholderText("Dán API Key (phân cách bằng dấu phẩy nếu có nhiều key)...")
        btn_load_askcpl = QPushButton("🔑 Nạp từ AskCpl")
        btn_load_askcpl.setToolTip("Tự động đọc danh sách API Key đã lưu trong AskCpl")
        btn_load_askcpl.clicked.connect(self._on_load_from_askcpl)
        row_key.addWidget(lbl_key)
        row_key.addWidget(self.txt_api_keys)
        row_key.addWidget(btn_load_askcpl)
        ai_layout.addLayout(row_key)

        row_params = QHBoxLayout()
        self.lbl_key_status = QLabel("Chưa nạp key.")
        self.lbl_key_status.setStyleSheet("color: #388e3c;")
        row_params.addWidget(self.lbl_key_status)

        row_params.addStretch()

        # Khoảng nghỉ (pacing)
        lbl_pace = QLabel("Nghỉ giữa 2 chương (s):")
        self.spn_pace = QSpinBox()
        self.spn_pace.setRange(2, 30)
        self.spn_pace.setValue(4)
        self.spn_pace.setToolTip("Khoảng nghỉ an toàn để tránh bị Google giới hạn tần suất 429")
        row_params.addWidget(lbl_pace)
        row_params.addWidget(self.spn_pace)

        # Nút xem từ điển
        self.btn_glossary = QPushButton("📖 Từ Điển Thuật Ngữ (0 từ)")
        self.btn_glossary.setStyleSheet("font-weight: bold; color: #0d47a1;")
        self.btn_glossary.clicked.connect(self._on_open_glossary)
        row_params.addWidget(self.btn_glossary)

        ai_layout.addLayout(row_params)
        layout.addWidget(grp_ai)

        # ── 3. Group: Phạm vi & Điều khiển ─────────────────────────────
        grp_ctrl = QGroupBox("3. Phạm vi dịch & Điều khiển")
        ctrl_layout = QVBoxLayout(grp_ctrl)

        row_range = QHBoxLayout()
        lbl_from = QLabel("Từ chương:")
        self.spn_from = QSpinBox()
        self.spn_from.setRange(1, 99999)
        self.spn_from.setValue(1)

        lbl_to = QLabel("Đến chương:")
        self.spn_to = QSpinBox()
        self.spn_to.setRange(0, 99999)
        self.spn_to.setValue(0)
        self.spn_to.setSpecialValueText("Hết (All)")

        self.chk_resume = QCheckBox("Bỏ qua các chương đã dịch (Resume thông minh)")
        self.chk_resume.setChecked(True)

        row_range.addWidget(lbl_from)
        row_range.addWidget(self.spn_from)
        row_range.addWidget(lbl_to)
        row_range.addWidget(self.spn_to)
        row_range.addSpacing(20)
        row_range.addWidget(self.chk_resume)
        row_range.addStretch()

        ctrl_layout.addLayout(row_range)

        # Hàng nút điều khiển
        row_actions = QHBoxLayout()
        self.btn_start = QPushButton("🚀 Bắt Đầu Dịch")
        self.btn_start.setStyleSheet("background-color: #1976d2; color: white; font-weight: bold; padding: 8px 20px; font-size: 14px;")
        self.btn_start.clicked.connect(self._on_start_translate)

        self.btn_stop = QPushButton("⏸ Tạm Dừng")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._on_stop_translate)

        self.btn_merge = QPushButton("📚 Gộp Truyện Dịch")
        self.btn_merge.setToolTip("Gộp tất cả các chương trong thư mục 'dich' thành 1 file HTML duy nhất có mục lục")
        self.btn_merge.clicked.connect(self._on_merge_translated)

        self.btn_prc = QPushButton("📱 Tạo PRC (Mobi)")
        self.btn_prc.setToolTip("Biên dịch file HTML dịch thành định dạng PRC/Mobi cho máy đọc sách Kindle")
        self.btn_prc.clicked.connect(self._on_create_prc)

        self.btn_open_folder = QPushButton("📂 Mở Thư Mục Dịch")
        self.btn_open_folder.clicked.connect(self._on_open_target_folder)

        row_actions.addWidget(self.btn_start)
        row_actions.addWidget(self.btn_stop)
        row_actions.addStretch()
        row_actions.addWidget(self.btn_merge)
        row_actions.addWidget(self.btn_prc)
        row_actions.addWidget(self.btn_open_folder)

        ctrl_layout.addLayout(row_actions)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        ctrl_layout.addWidget(self.progress_bar)

        layout.addWidget(grp_ctrl)

        # ── 4. Console Log ─────────────────────────────────────────────
        layout.addWidget(QLabel("Nhật ký hoạt động:"))
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setStyleSheet("background-color: #1e1e1e; color: #dcdcdc; font-family: Consolas, monospace; font-size: 12px;")
        layout.addWidget(self.txt_log, stretch=1)

    # -------------------------------------------------------------------
    # Logic Helpers & Event Handlers
    # -------------------------------------------------------------------
    def _auto_load_keys(self):
        """Tự động nạp keys từ AskCpl settings khi mở dialog."""
        keys = load_askcpl_keys()
        if keys:
            self.txt_api_keys.setText(", ".join(keys))
            self.lbl_key_status.setText(f"✅ Đã tự động nạp {len(keys)} Gemini API keys từ AskCpl.")
        else:
            self.lbl_key_status.setText("Chưa tìm thấy keys từ AskCpl. Vui lòng dán key thủ công.")

    def _on_load_from_askcpl(self):
        keys = load_askcpl_keys()
        if keys:
            self.txt_api_keys.setText(", ".join(keys))
            self.lbl_key_status.setText(f"✅ Đã nạp {len(keys)} Gemini API keys từ AskCpl.")
            QMessageBox.information(self, "Thông báo", f"Đã nạp thành công {len(keys)} API Key từ AskCpl!")
        else:
            QMessageBox.warning(self, "Không tìm thấy", "Không tìm thấy API Key nào trong AskCpl settings.json.")

    def _on_browse_source(self):
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục chứa các file chương tiếng Trung")
        if folder:
            self.txt_source.setText(folder)

    def _on_split_source_file(self):
        """Mở dialog tách file gộp và tự động điền thư mục xuất vào ô nguồn."""
        from gui.chapter_splitter_dialog import ChapterSplitterDialog
        dlg = ChapterSplitterDialog(parent=self)
        if dlg.exec():
            if dlg.result_output_dir and os.path.exists(dlg.result_output_dir):
                self.txt_source.setText(dlg.result_output_dir)
                self._log(f"✂️ Đã chọn thư mục vừa tách chương: {dlg.result_output_dir}")

    def _on_source_changed(self, text: str):
        src_path = text.strip()
        if not src_path or not os.path.exists(src_path):
            self.lbl_folder_stats.setText("Thư mục không tồn tại.")
            return

        # Auto set target to /dich
        target_path = os.path.join(src_path, "dich")
        self.txt_target.setText(target_path)

        # Scan files
        html_files = [
            f for f in os.listdir(src_path)
            if f.lower().endswith((".html", ".htm")) and not f.startswith("_")
        ]
        count = len(html_files)
        self.spn_to.setMaximum(max(1, count))

        # Check existing translations
        translated_count = 0
        if os.path.exists(target_path):
            translated_count = len([
                f for f in os.listdir(target_path)
                if f.lower().endswith((".html", ".htm")) and not f.startswith("_")
            ])

        self.lbl_folder_stats.setText(
            f"📂 Tìm thấy {count} chương tiếng Trung trong thư mục. "
            f"(Thư mục dịch hiện có: {translated_count} chương)."
        )

        # Update glossary button label
        self._update_glossary_button_count()

    def _on_browse_target(self):
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu bản dịch")
        if folder:
            self.txt_target.setText(folder)
            self._update_glossary_button_count()

    def _update_glossary_button_count(self):
        target_dir = self.txt_target.text().strip()
        if target_dir:
            glossary_path = os.path.join(target_dir, "_glossary.json")
            if os.path.exists(glossary_path):
                g = GlossaryManager(glossary_path)
                total = sum(len(v) for v in g.data.values())
                self.btn_glossary.setText(f"📖 Từ Điển Thuật Ngữ ({total} từ)")
                return
        self.btn_glossary.setText("📖 Từ Điển Thuật Ngữ (0 từ)")

    def _on_open_glossary(self):
        target_dir = self.txt_target.text().strip()
        if not target_dir:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn thư mục lưu trước khi xem từ điển.")
            return
        glossary_path = os.path.join(target_dir, "_glossary.json")
        g = GlossaryManager(glossary_path)
        dlg = GlossaryDialog(g, self)
        dlg.exec()
        self._update_glossary_button_count()

    def _on_start_translate(self):
        src_dir = self.txt_source.text().strip()
        dst_dir = self.txt_target.text().strip()

        if not src_dir or not os.path.exists(src_dir):
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn thư mục chứa các file chương tiếng Trung hợp lệ.")
            return

        raw_keys = self.txt_api_keys.text().strip()
        api_keys = [k.strip() for k in re.split(r"[,;\n\r]+", raw_keys) if k.strip()]
        if not api_keys:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng nhập ít nhất 1 Google Gemini API Key hoặc nhấn 'Nạp từ AskCpl'.")
            return

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.progress_bar.setValue(0)

        start_idx = self.spn_from.value()
        end_idx = self.spn_to.value()
        skip_existing = self.chk_resume.isChecked()
        pace_sec = float(self.spn_pace.value())

        self.worker = TranslateWorker(
            source_dir=src_dir,
            target_dir=dst_dir,
            api_keys=api_keys,
            start_idx=start_idx,
            end_idx=end_idx,
            skip_existing=skip_existing,
            pace_seconds=pace_sec
        )

        self.worker.log_signal.connect(self._log)
        self.worker.progress_signal.connect(self._on_progress)
        self.worker.glossary_updated_signal.connect(lambda n: self.btn_glossary.setText(f"📖 Từ Điển Thuật Ngữ ({n} từ)"))
        self.worker.finished_signal.connect(self._on_translate_finished)
        self.worker.start()

    def _on_stop_translate(self):
        if self.worker and self.worker.isRunning():
            self._log("⏳ Đang gửi yêu cầu dừng...")
            self.worker.stop()
            self.btn_stop.setEnabled(False)

    def _on_progress(self, current: int, total: int, status_text: str):
        if total > 0:
            pct = int((current / total) * 100)
            self.progress_bar.setValue(pct)
            self.progress_bar.setFormat(f"{current}/{total} ({pct}%) - {status_text}")

    def _on_translate_finished(self, success: bool, msg: str):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self._log(f"\n[TIẾN TRÌNH KẾT THÚC] {msg}")
        self._update_glossary_button_count()
        if success:
            QMessageBox.information(
                self, "Hoàn tất dịch", 
                f"{msg}\n\nBạn có thể bấm '📚 Gộp Truyện Dịch' để tạo file tổng hợp hoàn chỉnh!"
            )
        else:
            QMessageBox.warning(self, "Dừng / Lỗi dịch", msg)

    def _log(self, text: str):
        self.txt_log.append(text)

    def _on_merge_translated(self):
        """Gộp các file chương đã dịch thành 1 file HTML tổng có mục lục."""
        dst_dir = self.txt_target.text().strip()
        if not dst_dir or not os.path.exists(dst_dir):
            QMessageBox.warning(self, "Cảnh báo", "Thư mục dịch chưa tồn tại hoặc chưa có file nào.")
            return

        story_name = os.path.basename(os.path.dirname(dst_dir.rstrip("\\/")))
        default_out = os.path.join(os.path.dirname(dst_dir), f"{story_name}_Dich.html")

        out_path, _ = QFileDialog.getSaveFileName(
            self, "Lưu file truyện dịch gộp", default_out, "HTML Files (*.html)"
        )
        if not out_path:
            return

        self._log(f"\n📚 Bắt đầu gộp các chương dịch từ: {dst_dir} → {out_path}...")
        self.merge_worker = MergeWorker(
            folder_path=dst_dir,
            output_path=out_path,
            story_title=f"{story_name} (Bản Dịch AI)",
            ebook_info=f"Dịch tự động bởi AI Gemini. Tổng hợp từ thư mục {dst_dir}"
        )
        self.merge_worker.log_signal.connect(self._log)
        self.merge_worker.finished_signal.connect(lambda msg: QMessageBox.information(self, "Gộp file hoàn tất", msg))
        self.merge_worker.start()

    def _on_create_prc(self):
        """Tạo file PRC từ file HTML đã gộp."""
        dst_dir = self.txt_target.text().strip()
        initial_dir = os.path.dirname(dst_dir) if dst_dir else ""
        html_path, _ = QFileDialog.getOpenFileName(
            self, "Chọn file HTML truyện dịch đã gộp", initial_dir, "HTML Files (*.html)"
        )
        if not html_path:
            return

        base_dir = os.path.dirname(os.path.abspath(__file__))
        self._log(f"\n📱 Bắt đầu chuyển đổi sang PRC cho file: {html_path}...")

        self.prc_worker = PrcWorker(html_path=html_path, base_dir=base_dir)
        self.prc_worker.log_signal.connect(self._log)
        self.prc_worker.finished_signal.connect(
            lambda ok, msg: QMessageBox.information(self, "Tạo PRC", msg) if ok else QMessageBox.warning(self, "Lỗi tạo PRC", msg)
        )
        self.prc_worker.start()

    def _on_open_target_folder(self):
        dst_dir = self.txt_target.text().strip()
        if dst_dir and os.path.exists(dst_dir):
            os.startfile(dst_dir)
        else:
            QMessageBox.warning(self, "Cảnh báo", "Thư mục đích chưa tồn tại.")
