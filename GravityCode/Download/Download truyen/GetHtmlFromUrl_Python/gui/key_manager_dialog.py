import os
import time
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QInputDialog, QLineEdit, QGroupBox, QMenu
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QBrush, QFont

from core.key_manager import (
    load_local_keys, save_local_keys, encode_token, decode_token,
    mask_key, sync_from_askcpl, sync_to_askcpl, validate_key
)


class KeyValidationWorker(QThread):
    """Worker kiểm tra danh sách API keys trên nền."""
    item_validated_signal = pyqtSignal(int, bool, str, int)  # row, is_valid, msg, latency_ms
    finished_signal = pyqtSignal(str)

    def __init__(self, key_rows: list):
        super().__init__()
        self.key_rows = key_rows  # list of (row_idx, raw_key)
        self._is_stopped = False

    def stop(self):
        self._is_stopped = True

    def run(self):
        valid_count = 0
        for row_idx, raw_key in self.key_rows:
            if self._is_stopped:
                break
            ok, msg, ms = validate_key(raw_key, timeout=8.0)
            if ok:
                valid_count += 1
            self.item_validated_signal.emit(row_idx, ok, msg, ms)
            time.sleep(0.3)
        self.finished_signal.emit(f"Đã kiểm tra xong! {valid_count}/{len(self.key_rows)} key hoạt động bình thường.")


class ApiKeyEditDialog(QDialog):
    """Hộp thoại Thêm hoặc Sửa API Key."""
    def __init__(self, email: str = "", raw_key: str = "", note: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔑 Thông Tin Gemini API Key")
        self.resize(480, 200)
        self._build_ui(email, raw_key, note)

    def _build_ui(self, email: str, raw_key: str, note: str):
        layout = QVBoxLayout(self)

        row_email = QHBoxLayout()
        lbl_email = QLabel("Google Account (Email):")
        lbl_email.setFixedWidth(160)
        self.txt_email = QLineEdit(email)
        self.txt_email.setPlaceholderText("vi-du: user123@gmail.com")
        row_email.addWidget(lbl_email)
        row_email.addWidget(self.txt_email)
        layout.addLayout(row_email)

        row_key = QHBoxLayout()
        lbl_key = QLabel("Gemini API Key (*):")
        lbl_key.setFixedWidth(160)
        self.txt_key = QLineEdit(raw_key)
        self.txt_key.setPlaceholderText("Dán API Key (AIzaSy...)")
        self.txt_key.setEchoMode(QLineEdit.EchoMode.PasswordEchoOnEdit)
        row_key.addWidget(lbl_key)
        row_key.addWidget(self.txt_key)
        layout.addLayout(row_key)

        row_note = QHBoxLayout()
        lbl_note = QLabel("Ghi chú:")
        lbl_note.setFixedWidth(160)
        self.txt_note = QLineEdit(note)
        self.txt_note.setPlaceholderText("Ghi chú bổ sung (tùy chọn)")
        row_note.addWidget(lbl_note)
        row_note.addWidget(self.txt_note)
        layout.addLayout(row_note)

        # Nút bấm
        row_btns = QHBoxLayout()
        row_btns.addStretch()
        btn_ok = QPushButton("💾 Lưu")
        btn_ok.setStyleSheet("background-color: #1976d2; color: white; font-weight: bold; padding: 6px 16px;")
        btn_ok.clicked.connect(self._on_save)

        btn_cancel = QPushButton("Hủy")
        btn_cancel.clicked.connect(self.reject)

        row_btns.addWidget(btn_ok)
        row_btns.addWidget(btn_cancel)
        layout.addLayout(row_btns)

    def _on_save(self):
        k = self.txt_key.text().strip()
        if not k:
            QMessageBox.warning(self, "Thiếu dữ liệu", "Vui lòng nhập API Key!")
            return
        self.accept()

    def get_data(self):
        return {
            "email": self.txt_email.text().strip(),
            "key": self.txt_key.text().strip(),
            "note": self.txt_note.text().strip()
        }


class ApiKeyManagerDialog(QDialog):
    """Giao diện chính Quản Lý API Keys của GetHtmlFromUrl."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔑 Quản Lý Gemini API Keys (Độc Lập)")
        self.resize(800, 520)
        self.keys_data = load_local_keys()
        self.validation_worker = None
        self._build_ui()
        self._refresh_table()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Thanh hướng dẫn
        lbl_info = QLabel(
            "Quản lý danh sách Google Gemini API Keys được lưu trữ độc lập trong dự án (config/gemini_keys.json).\n"
            "Bạn có thể nạp, chỉnh sửa, kiểm tra trạng thái sống của key hoặc đồng bộ 2 chiều với AskCpl."
        )
        lbl_info.setStyleSheet("color: #424242; font-size: 12px; margin-bottom: 4px;")
        lbl_info.setWordWrap(True)
        layout.addWidget(lbl_info)

        # ── Toolbar nút điều khiển ──────────────────────────────
        tb_layout = QHBoxLayout()
        btn_add = QPushButton("➕ Thêm Key Mới")
        btn_add.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; padding: 6px 12px;")
        btn_add.clicked.connect(self._on_add_key)
        tb_layout.addWidget(btn_add)

        btn_edit = QPushButton("✏️ Sửa")
        btn_edit.clicked.connect(self._on_edit_key)
        tb_layout.addWidget(btn_edit)

        btn_del = QPushButton("🗑️ Xóa")
        btn_del.setStyleSheet("color: #c62828;")
        btn_del.clicked.connect(self._on_delete_key)
        tb_layout.addWidget(btn_del)

        btn_toggle = QPushButton("☑/☒ Bật / Tắt")
        btn_toggle.clicked.connect(self._on_toggle_status)
        tb_layout.addWidget(btn_toggle)

        tb_layout.addSpacing(15)

        btn_test_sel = QPushButton("🔍 Kiểm Tra Key Đã Chọn")
        btn_test_sel.clicked.connect(self._on_test_selected)
        tb_layout.addWidget(btn_test_sel)

        btn_test_all = QPushButton("⚡ Kiểm Tra Tất Cả")
        btn_test_all.setStyleSheet("color: #6a1b9a; font-weight: 500;")
        btn_test_all.clicked.connect(self._on_test_all)
        tb_layout.addWidget(btn_test_all)

        tb_layout.addStretch()
        layout.addLayout(tb_layout)

        # ── Bảng hiển thị Keys ──────────────────────────────────
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            "#", "Account (Email)", "API Key", "Trạng thái", "Ghi chú & Kiểm tra"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(1, 180)
        self.table.setColumnWidth(2, 220)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self._on_edit_key)
        layout.addWidget(self.table)

        # ── Thanh đồng bộ & Lưu ─────────────────────────────────
        bottom_layout = QHBoxLayout()

        btn_sync_from = QPushButton("📥 Nhập Từ AskCpl")
        btn_sync_from.setToolTip("Đọc tất cả keys từ AskCpl settings.json và gộp vào danh sách riêng của dự án này")
        btn_sync_from.clicked.connect(self._on_sync_from_askcpl)
        bottom_layout.addWidget(btn_sync_from)

        btn_sync_to = QPushButton("📤 Xuất Sang AskCpl")
        btn_sync_to.setToolTip("Gửi các keys đang có sang AskCpl settings.json để dùng chung")
        btn_sync_to.clicked.connect(self._on_sync_to_askcpl)
        bottom_layout.addWidget(btn_sync_to)

        bottom_layout.addStretch()

        self.lbl_summary = QLabel("")
        self.lbl_summary.setStyleSheet("font-weight: 500; color: #1565c0;")
        bottom_layout.addWidget(self.lbl_summary)

        btn_save = QPushButton("💾 Lưu & Áp Dụng")
        btn_save.setStyleSheet("background-color: #1976d2; color: white; font-weight: bold; padding: 6px 20px; font-size: 13px;")
        btn_save.clicked.connect(self._on_save_all)
        bottom_layout.addWidget(btn_save)

        btn_close = QPushButton("Đóng")
        btn_close.clicked.connect(self.close)
        bottom_layout.addWidget(btn_close)

        layout.addLayout(bottom_layout)

    def _refresh_table(self):
        self.table.setRowCount(len(self.keys_data))
        active_count = 0
        for i, item in enumerate(self.keys_data):
            raw_key = decode_token(item.get("key", ""))
            status = item.get("status", "active")
            if status == "active":
                active_count += 1

            it_idx = QTableWidgetItem(str(i + 1))
            it_idx.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            it_email = QTableWidgetItem(item.get("email", ""))
            it_key = QTableWidgetItem(mask_key(raw_key))
            it_key.setFont(QFont("Consolas", 10))

            it_status = QTableWidgetItem("✅ Bật" if status == "active" else "☒ Tắt")
            it_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if status == "active":
                it_status.setForeground(QBrush(QColor("#2e7d32")))
            else:
                it_status.setForeground(QBrush(QColor("#757575")))

            it_note = QTableWidgetItem(item.get("note", ""))

            self.table.setItem(i, 0, it_idx)
            self.table.setItem(i, 1, it_email)
            self.table.setItem(i, 2, it_key)
            self.table.setItem(i, 3, it_status)
            self.table.setItem(i, 4, it_note)

        self.lbl_summary.setText(f"Tổng cộng: {len(self.keys_data)} keys ({active_count} đang bật)")

    def _get_selected_row(self) -> int:
        selected = self.table.selectedIndexes()
        if not selected:
            return -1
        return selected[0].row()

    def _on_add_key(self):
        dlg = ApiKeyEditDialog(parent=self)
        if dlg.exec():
            data = dlg.get_data()
            raw = data["key"]
            item = {
                "id": f"key_{int(time.time()*1000)}",
                "key": encode_token(raw),
                "email": data["email"],
                "status": "active",
                "note": data["note"]
            }
            self.keys_data.append(item)
            self._refresh_table()
            save_local_keys(self.keys_data)

    def _on_edit_key(self):
        row = self._get_selected_row()
        if row < 0 or row >= len(self.keys_data):
            QMessageBox.warning(self, "Chọn dòng", "Vui lòng chọn một dòng để sửa!")
            return
        item = self.keys_data[row]
        raw = decode_token(item.get("key", ""))
        dlg = ApiKeyEditDialog(
            email=item.get("email", ""),
            raw_key=raw,
            note=item.get("note", ""),
            parent=self
        )
        if dlg.exec():
            data = dlg.get_data()
            item["email"] = data["email"]
            item["key"] = encode_token(data["key"])
            item["note"] = data["note"]
            self._refresh_table()
            save_local_keys(self.keys_data)

    def _on_delete_key(self):
        row = self._get_selected_row()
        if row < 0 or row >= len(self.keys_data):
            QMessageBox.warning(self, "Chọn dòng", "Vui lòng chọn một dòng để xóa!")
            return
        item = self.keys_data[row]
        email = item.get("email", "Không tên")
        reply = QMessageBox.question(
            self, "Xác nhận xóa",
            f"Bạn có chắc muốn xóa API key của tài khoản '{email}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.keys_data.pop(row)
            self._refresh_table()
            save_local_keys(self.keys_data)

    def _on_toggle_status(self):
        row = self._get_selected_row()
        if row < 0 or row >= len(self.keys_data):
            return
        item = self.keys_data[row]
        cur = item.get("status", "active")
        item["status"] = "disabled" if cur == "active" else "active"
        self._refresh_table()
        save_local_keys(self.keys_data)

    def _on_test_selected(self):
        row = self._get_selected_row()
        if row < 0 or row >= len(self.keys_data):
            QMessageBox.warning(self, "Chọn dòng", "Vui lòng chọn một key để kiểm tra!")
            return
        raw = decode_token(self.keys_data[row].get("key", ""))
        self.table.setItem(row, 4, QTableWidgetItem("⏳ Đang kiểm tra..."))
        ok, msg, ms = validate_key(raw)
        it = QTableWidgetItem(f"{'✅' if ok else '❌'} {msg}")
        if ok:
            it.setForeground(QBrush(QColor("#2e7d32")))
        else:
            it.setForeground(QBrush(QColor("#c62828")))
        self.table.setItem(row, 4, it)

    def _on_test_all(self):
        if not self.keys_data:
            return
        key_rows = []
        for i, item in enumerate(self.keys_data):
            raw = decode_token(item.get("key", ""))
            key_rows.append((i, raw))
            self.table.setItem(i, 4, QTableWidgetItem("⏳ Đang chờ..."))

        self.validation_worker = KeyValidationWorker(key_rows)
        def _on_item(row, ok, msg, ms):
            it = QTableWidgetItem(f"{'✅' if ok else '❌'} {msg}")
            it.setForeground(QBrush(QColor("#2e7d32") if ok else QColor("#c62828")))
            self.table.setItem(row, 4, it)

        self.validation_worker.item_validated_signal.connect(_on_item)
        self.validation_worker.finished_signal.connect(lambda txt: QMessageBox.information(self, "Hoàn tất kiểm tra", txt))
        self.validation_worker.start()

    def _on_sync_from_askcpl(self):
        added, total = sync_from_askcpl()
        self.keys_data = load_local_keys()
        self._refresh_table()
        QMessageBox.information(
            self, "Đồng bộ từ AskCpl",
            f"Đã nhập thành công {added} API Key mới từ AskCpl!\nTổng số keys hiện tại: {total}"
        )

    def _on_sync_to_askcpl(self):
        added, total = sync_to_askcpl()
        QMessageBox.information(
            self, "Xuất sang AskCpl",
            f"Đã xuất thành công {added} API Key sang AskCpl settings.json!\nTổng số keys trong AskCpl: {total}"
        )

    def _on_save_all(self):
        save_local_keys(self.keys_data)
        self.accept()
