import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QFileDialog, QMessageBox, 
    QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from core.chapter_splitter import ChapterSplitter


class SplitterWorker(QThread):
    progress_signal = pyqtSignal(int, int, str)
    finished_signal = pyqtSignal(bool, int, str)

    def __init__(self, input_file: str, output_dir: str):
        super().__init__()
        self.input_file = input_file
        self.output_dir = output_dir

    def run(self):
        try:
            splitter = ChapterSplitter(self.input_file, self.output_dir)
            total, out_dir = splitter.split_and_save(
                progress_callback=lambda c, t, title: self.progress_signal.emit(c, t, title)
            )
            self.finished_signal.emit(True, total, out_dir)
        except Exception as e:
            self.finished_signal.emit(False, 0, str(e))


class ChapterSplitterDialog(QDialog):
    """Dialog giao diện Tách Truyện Gộp Thành Từng Chương."""

    def __init__(self, default_file: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("✂️ Tiện Ích Tách Truyện Gộp Thành Từng Chương")
        self.resize(750, 520)
        self.worker = None
        self.result_output_dir = ""

        self._build_ui()
        if default_file:
            self.txt_file.setText(default_file)
            self._auto_set_output(default_file)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # ── Group 1: Chọn File & Thư mục xuất ────────────────────────────
        grp_paths = QGroupBox("1. File nguồn & Thư mục xuất")
        p_layout = QVBoxLayout(grp_paths)

        # Chọn file gộp
        row_f = QHBoxLayout()
        lbl_f = QLabel("File truyện gộp:")
        lbl_f.setFixedWidth(120)
        self.txt_file = QLineEdit()
        self.txt_file.setPlaceholderText("Chọn file HTML hoặc TXT cần tách chương...")
        self.txt_file.textChanged.connect(self._auto_set_output)
        btn_browse_f = QPushButton("📄 Chọn File...")
        btn_browse_f.clicked.connect(self._on_browse_file)
        row_f.addWidget(lbl_f)
        row_f.addWidget(self.txt_file)
        row_f.addWidget(btn_browse_f)
        p_layout.addLayout(row_f)

        # Thư mục xuất
        row_o = QHBoxLayout()
        lbl_o = QLabel("Thư mục lưu:")
        lbl_o.setFixedWidth(120)
        self.txt_output = QLineEdit()
        self.txt_output.setPlaceholderText("Tự động tạo thư mục tên_file_tach...")
        btn_browse_o = QPushButton("📁 Thay Đổi...")
        btn_browse_o.clicked.connect(self._on_browse_output)
        row_o.addWidget(lbl_o)
        row_o.addWidget(self.txt_output)
        row_o.addWidget(btn_browse_o)
        p_layout.addLayout(row_o)

        layout.addWidget(grp_paths)

        # ── Group 2: Preview & Điều khiển ──────────────────────────────
        grp_preview = QGroupBox("2. Quét trước danh sách chương (Preview)")
        prev_layout = QVBoxLayout(grp_preview)

        row_scan = QHBoxLayout()
        self.btn_scan = QPushButton("🔍 Quét Thử Danh Sách Chương")
        self.btn_scan.clicked.connect(self._on_scan_preview)
        self.lbl_scan_info = QLabel("Chưa quét file.")
        self.lbl_scan_info.setStyleSheet("color: #1976d2; font-weight: 500;")
        row_scan.addWidget(self.btn_scan)
        row_scan.addWidget(self.lbl_scan_info)
        row_scan.addStretch()
        prev_layout.addLayout(row_scan)

        # Bảng danh sách chương xem trước
        self.tbl_preview = QTableWidget()
        self.tbl_preview.setColumnCount(2)
        self.tbl_preview.setHorizontalHeaderLabels(["STT", "Tiêu đề chương"])
        self.tbl_preview.setColumnWidth(0, 70)
        self.tbl_preview.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        prev_layout.addWidget(self.tbl_preview)

        layout.addWidget(grp_preview, stretch=1)

        # ── Group 3: Tiến độ & Nút thực thi ────────────────────────────
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        row_actions = QHBoxLayout()
        self.btn_split = QPushButton("✂️ Bắt Đầu Tách Chương")
        self.btn_split.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; padding: 8px 24px; font-size: 14px;")
        self.btn_split.clicked.connect(self._on_start_split)

        self.btn_open = QPushButton("📂 Mở Thư Mục Đã Tách")
        self.btn_open.setEnabled(False)
        self.btn_open.clicked.connect(self._on_open_folder)

        btn_close = QPushButton("Đóng")
        btn_close.clicked.connect(self.accept if self.result_output_dir else self.reject)

        row_actions.addWidget(self.btn_split)
        row_actions.addWidget(self.btn_open)
        row_actions.addStretch()
        row_actions.addWidget(btn_close)
        layout.addLayout(row_actions)

    def _auto_set_output(self, file_path: str):
        path = file_path.strip()
        if path and os.path.exists(path):
            stem = os.path.splitext(os.path.basename(path))[0]
            parent = os.path.dirname(path)
            out = os.path.join(parent, f"{stem}_tach")
            self.txt_output.setText(out)

    def _on_browse_file(self):
        f, _ = QFileDialog.getOpenFileName(
            self, "Chọn file HTML hoặc TXT cần tách", "",
            "HTML & TXT Files (*.html *.htm *.txt);;All Files (*.*)"
        )
        if f:
            self.txt_file.setText(f)
            self._on_scan_preview()

    def _on_browse_output(self):
        d = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu các chương sau khi tách")
        if d:
            self.txt_output.setText(d)

    def _on_scan_preview(self):
        fpath = self.txt_file.text().strip()
        if not fpath or not os.path.exists(fpath):
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn file nguồn hợp lệ.")
            return

        self.lbl_scan_info.setText("⏳ Đang quét tiêu đề chương...")
        self.btn_scan.setEnabled(False)

        splitter = ChapterSplitter(fpath)
        chapters = splitter.scan_chapters()
        self.btn_scan.setEnabled(True)

        if not chapters:
            self.lbl_scan_info.setText("❌ Không nhận diện được tiêu đề chương nào.")
            self.tbl_preview.setRowCount(0)
            return

        self.lbl_scan_info.setText(f"✅ Tìm thấy {len(chapters)} chương!")
        self.tbl_preview.setRowCount(min(len(chapters), 500))

        for row_idx, ch in enumerate(chapters[:500]):
            self.tbl_preview.setItem(row_idx, 0, QTableWidgetItem(str(ch["index"])))
            self.tbl_preview.setItem(row_idx, 1, QTableWidgetItem(ch["title"]))

    def _on_start_split(self):
        fpath = self.txt_file.text().strip()
        out_dir = self.txt_output.text().strip()

        if not fpath or not os.path.exists(fpath):
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn file nguồn hợp lệ.")
            return

        if not out_dir:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chỉ định thư mục lưu.")
            return

        self.btn_split.setEnabled(False)
        self.progress_bar.setValue(0)

        self.worker = SplitterWorker(fpath, out_dir)
        self.worker.progress_signal.connect(self._on_progress)
        self.worker.finished_signal.connect(self._on_finished)
        self.worker.start()

    def _on_progress(self, current: int, total: int, title: str):
        if total > 0:
            pct = int((current / total) * 100)
            self.progress_bar.setValue(pct)
            self.progress_bar.setFormat(f"{current}/{total} ({pct}%) - {title[:30]}")

    def _on_finished(self, success: bool, total: int, out_dir: str):
        self.btn_split.setEnabled(True)
        if success:
            self.result_output_dir = out_dir
            self.btn_open.setEnabled(True)
            self.progress_bar.setValue(100)
            self.progress_bar.setFormat(f"Hoàn thành {total} chương!")
            QMessageBox.information(
                self, "Tách chương thành công",
                f"🎉 Đã tách thành công {total} chương vào thư mục:\n{out_dir}\n\n"
                f"Bây giờ bạn có thể dùng thư mục này để đưa vào Tiện ích AI Dịch Truyện!"
            )
        else:
            QMessageBox.critical(self, "Lỗi tách chương", f"Đã xảy ra lỗi:\n{out_dir}")

    def _on_open_folder(self):
        out_dir = self.txt_output.text().strip()
        if out_dir and os.path.exists(out_dir):
            os.startfile(out_dir)
