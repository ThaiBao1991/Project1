"""
dialogs.py — Các hộp thoại phụ của ứng dụng
Tương đương DownloadRange.java và các JDialog khác trong Java gốc.
"""

from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QVBoxLayout, QHBoxLayout,
    QLabel, QSpinBox, QFormLayout, QGroupBox, QTextBrowser,
    QSizePolicy
)
from PyQt6.QtCore import Qt


class DownloadRangeDialog(QDialog):
    """
    Hộp thoại chọn phạm vi tải xuống (Chương bắt đầu → Chương kết thúc).
    Tương đương DownloadRange.java.
    """

    def __init__(self, total_chapters: int, parent=None):
        super().__init__(parent)
        self.total = total_chapters
        self.setWindowTitle("Chọn Phạm Vi Tải")
        self.setFixedSize(320, 180)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        grp = QGroupBox(f"Phạm vi (Tổng: {self.total} chương)")
        form = QFormLayout(grp)

        self.spin_start = QSpinBox()
        self.spin_start.setMinimum(1)
        self.spin_start.setMaximum(self.total)
        self.spin_start.setValue(1)
        form.addRow("Từ chương:", self.spin_start)

        self.spin_end = QSpinBox()
        self.spin_end.setMinimum(1)
        self.spin_end.setMaximum(self.total)
        self.spin_end.setValue(self.total)
        form.addRow("Đến chương:", self.spin_end)

        layout.addWidget(grp)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    @property
    def start_index(self) -> int:
        """Trả về 0-based index của chương bắt đầu"""
        return self.spin_start.value() - 1

    @property
    def end_index(self) -> int:
        """Trả về 0-based index của chương kết thúc"""
        return self.spin_end.value() - 1


class EbookInfoDialog(QDialog):
    """
    Hộp thoại nhập thông tin ebook (Tên truyện, Tác giả, Ghi chú).
    Tương đương tính năng AddEbookInfo trong Java.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Thông Tin Ebook")
        self.setFixedSize(400, 280)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Nhập thông tin ebook (sẽ chèn vào đầu file):"))

        from PyQt6.QtWidgets import QLineEdit, QPlainTextEdit
        form = QFormLayout()

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Tên truyện...")
        form.addRow("Tên truyện:", self.title_edit)

        self.author_edit = QLineEdit()
        self.author_edit.setPlaceholderText("Tên tác giả...")
        form.addRow("Tác giả:", self.author_edit)

        self.note_edit = QPlainTextEdit()
        self.note_edit.setPlaceholderText("Ghi chú thêm...")
        self.note_edit.setFixedHeight(80)
        form.addRow("Ghi chú:", self.note_edit)

        layout.addLayout(form)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def get_info_html(self) -> str:
        """Tạo chuỗi HTML thông tin ebook để chèn vào đầu file"""
        title = self.title_edit.text().strip()
        author = self.author_edit.text().strip()
        note = self.note_edit.toPlainText().strip()
        parts = []
        if title:
            parts.append(f"<b>Tên truyện:</b> {title}")
        if author:
            parts.append(f"<b>Tác giả:</b> {author}")
        if note:
            parts.append(f"<b>Ghi chú:</b> {note}")
        if not parts:
            return ""
        return "<div class='ebook-info'>" + "<br/>".join(parts) + "</div>"
