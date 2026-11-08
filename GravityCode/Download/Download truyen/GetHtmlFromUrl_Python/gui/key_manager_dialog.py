import os

import time

from typing import List

from PyQt6.QtWidgets import (

    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QComboBox, QApplication, QLabel, 

    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,

    QMessageBox, QInputDialog, QLineEdit, QGroupBox, QMenu

)

from PyQt6.QtCore import Qt, QThread, pyqtSignal

from PyQt6.QtGui import QColor, QBrush, QFont, QAction



from core.key_manager import (

    load_local_keys, save_local_keys, encode_token, decode_token,

    mask_key, sync_from_askcpl, sync_to_askcpl, validate_key,

    sync_merge_two_way, overwrite_from_askcpl, overwrite_to_askcpl,

    remove_keys_from_askcpl, format_reset_time_display, ASKCPL_SETTINGS_PATH

)





class KeyValidationWorker(QThread):
    """Worker kiểm tra danh sách API keys trên nền."""
    item_validated_signal = pyqtSignal(int, bool, str, str, int)  # row, is_valid, status_kind, msg, latency_ms
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
            ok, status_kind, msg, ms = validate_key(raw_key, timeout=7.0)
            if ok:
                valid_count += 1
            self.item_validated_signal.emit(row_idx, ok, status_kind, msg, ms)
            time.sleep(0.4)
        self.finished_signal.emit(f"Đã kiểm tra xong! {valid_count}/{len(self.key_rows)} key hoạt động bình thường.")





class ApiKeyEditDialog(QDialog):
    """Hộp thoại Thêm hoặc Sửa API Key đầy đủ tính năng chuẩn phong cách AskCpl."""
    def __init__(self, email: str = "", raw_key: str = "", note: str = "",
                 status: str = "active", reset_time: int = 0, project_id: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔑 Thông Tin Gemini API Key")
        self.resize(520, 360)
        self.reset_time_val = reset_time or 0
        self._build_ui(email, raw_key, note, status, project_id)

    def _build_ui(self, email: str, raw_key: str, note: str, status: str, project_id: str):
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.txt_email = QLineEdit(email)
        self.txt_email.setPlaceholderText("vi-du: user123@gmail.com")
        form_layout.addRow("Google Account (Email):", self.txt_email)

        key_box = QHBoxLayout()
        self.txt_key = QLineEdit(raw_key)
        self.txt_key.setPlaceholderText("Dán API Key (AIzaSy...)")
        self.txt_key.setEchoMode(QLineEdit.EchoMode.Password)
        btn_toggle_eye = QPushButton("👁️")
        btn_toggle_eye.setFixedWidth(36)
        btn_toggle_eye.setToolTip("Hiện / Ẩn API Key")
        def _toggle_echo():
            if self.txt_key.echoMode() == QLineEdit.EchoMode.Password:
                self.txt_key.setEchoMode(QLineEdit.EchoMode.Normal)
            else:
                self.txt_key.setEchoMode(QLineEdit.EchoMode.Password)
        btn_toggle_eye.clicked.connect(_toggle_echo)
        key_box.addWidget(self.txt_key)
        key_box.addWidget(btn_toggle_eye)
        form_layout.addRow("Gemini API Key (*):", key_box)

        self.combo_status = QComboBox()
        self.combo_status.addItem("✅ Active (Đang hoạt động)", "active")
        self.combo_status.addItem("⚠️ Exhausted (Hết Quota 24h)", "exhausted")
        self.combo_status.addItem("❌ Invalid (Khóa vĩnh viễn / Lỗi)", "invalid")
        self.combo_status.addItem("⏸ Disabled (Tạm tắt)", "disabled")
        idx_status = 0
        for i in range(self.combo_status.count()):
            if self.combo_status.itemData(i) == status:
                idx_status = i
                break
        self.combo_status.setCurrentIndex(idx_status)
        self.combo_status.currentIndexChanged.connect(self._on_status_changed)
        form_layout.addRow("Trạng thái:", self.combo_status)

        # Hàng hiển thị Khôi phục sau (Reset Time)
        reset_row = QHBoxLayout()
        self.lbl_reset_display = QLabel(self._format_rt_str())
        self.lbl_reset_display.setStyleSheet("font-weight: bold; color: #e65100;")
        btn_set_24h = QPushButton("⏰ Khóa 24h")
        btn_set_24h.setToolTip("Đặt thời gian phục hồi sau 24h kể từ bây giờ")
        btn_set_24h.clicked.connect(self._on_set_24h)
        btn_clear_rt = QPushButton("🔄 Reset ngay")
        btn_clear_rt.setToolTip("Xóa thời gian khóa, đưa về trạng thái Active ngay")
        btn_clear_rt.clicked.connect(self._on_clear_rt)
        reset_row.addWidget(self.lbl_reset_display)
        reset_row.addStretch()
        reset_row.addWidget(btn_set_24h)
        reset_row.addWidget(btn_clear_rt)
        form_layout.addRow("Khôi phục sau:", reset_row)

        self.txt_project_id = QLineEdit(project_id)
        self.txt_project_id.setPlaceholderText("ID dự án Google Cloud (nếu có)")
        form_layout.addRow("Project ID:", self.txt_project_id)

        self.txt_note = QLineEdit(note)
        self.txt_note.setPlaceholderText("Ghi chú bổ sung (tùy chọn)")
        form_layout.addRow("Ghi chú:", self.txt_note)

        layout.addLayout(form_layout)

        # Kiểm tra nhanh
        test_row = QHBoxLayout()
        self.btn_test_fast = QPushButton("🔍 Kiểm Tra Key")
        self.btn_test_fast.setStyleSheet("background-color: #f39c12; color: white; font-weight: bold; padding: 5px 12px;")
        self.lbl_test_result = QLabel("")
        self.btn_test_fast.clicked.connect(self._on_test_fast)
        test_row.addWidget(self.btn_test_fast)
        test_row.addWidget(self.lbl_test_result)
        test_row.addStretch()
        layout.addLayout(test_row)

        # Nút bấm dưới cùng
        row_btns = QHBoxLayout()
        row_btns.addStretch()
        btn_ok = QPushButton("💾 Lưu")
        btn_ok.setStyleSheet("background-color: #1976d2; color: white; font-weight: bold; padding: 6px 18px;")
        btn_ok.clicked.connect(self._on_save)
        btn_cancel = QPushButton("Hủy")
        btn_cancel.clicked.connect(self.reject)
        row_btns.addWidget(btn_ok)
        row_btns.addWidget(btn_cancel)
        layout.addLayout(row_btns)

    def _format_rt_str(self) -> str:
        rt = self.reset_time_val or 0
        now = int(time.time())
        if rt > now:
            dt_str = time.strftime('%Y-%m-%d %H:%M', time.localtime(rt))
            diff = rt - now
            h = diff // 3600
            m = (diff % 3600) // 60
            return f"{dt_str} (Còn {h}h {m}m)"
        elif rt > 0:
            return "Đã đến hạn phục hồi"
        return "— (Không bị khóa)"

    def _on_status_changed(self):
        st = self.combo_status.currentData()
        if st == "exhausted" and (not self.reset_time_val or self.reset_time_val <= int(time.time())):
            self.reset_time_val = int(time.time()) + 86400
        elif st == "active":
            self.reset_time_val = 0
        self.lbl_reset_display.setText(self._format_rt_str())

    def _on_set_24h(self):
        self.reset_time_val = int(time.time()) + 86400
        # Tự đổi combo sang Exhausted
        for i in range(self.combo_status.count()):
            if self.combo_status.itemData(i) == "exhausted":
                self.combo_status.setCurrentIndex(i)
                break
        self.lbl_reset_display.setText(self._format_rt_str())

    def _on_clear_rt(self):
        self.reset_time_val = 0
        for i in range(self.combo_status.count()):
            if self.combo_status.itemData(i) == "active":
                self.combo_status.setCurrentIndex(i)
                break
        self.lbl_reset_display.setText(self._format_rt_str())

    def _on_test_fast(self):
        k = self.txt_key.text().strip()
        if not k:
            self.lbl_test_result.setText("⚠️ Chưa nhập key!")
            return
        self.lbl_test_result.setText("⏳ Đang kiểm tra...")
        QApplication.processEvents()
        ok, status_kind, msg, ms = validate_key(k, timeout=7.0)
        if ok:
            self.lbl_test_result.setText(f"✅ {msg}")
            self.lbl_test_result.setStyleSheet("color: #2e7d32; font-weight: bold;")
            self._on_clear_rt()
        elif status_kind == "exhausted":
            self.lbl_test_result.setText(f"⚠️ {msg}")
            self.lbl_test_result.setStyleSheet("color: #e65100; font-weight: bold;")
            self._on_set_24h()
        else:
            self.lbl_test_result.setText(f"❌ {msg}")
            self.lbl_test_result.setStyleSheet("color: #c62828; font-weight: bold;")

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
            "status": self.combo_status.currentData(),
            "reset_time": self.reset_time_val,
            "project_id": self.txt_project_id.text().strip(),
            "note": self.txt_note.text().strip()
        }





class ApiKeyManagerDialog(QDialog):

    """Giao diện chính Quản Lý API Keys của GetHtmlFromUrl."""

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setWindowTitle("🔑 Quản Lý Gemini API Keys (Độc Lập & Đồng Bộ AskCpl)")

        self.resize(860, 540)

        self.keys_data = load_local_keys()

        self.validation_worker = None

        self._build_ui()

        self._refresh_table()



    def keyPressEvent(self, event):

        """Bắt sự kiện phím Delete trên bàn phím để xóa nhanh các dòng đã chọn."""

        if event.key() == Qt.Key.Key_Delete:

            self._on_delete_key()

            event.accept()

        else:

            super().keyPressEvent(event)



    def _build_ui(self):

        layout = QVBoxLayout(self)



        # Thanh hướng dẫn

        lbl_info = QLabel(

            "Quản lý danh sách Google Gemini API Keys (lưu tại config/gemini_keys.json).\n"

            "• Hỗ trợ chọn nhiều dòng (giữ Shift/Ctrl/kéo chuột) để Xóa hàng loạt bằng nút hoặc phím Delete.\n"

            "• Đồng bộ 2 chiều với AskCpl để 2 ứng dụng luôn sở hữu chung 100% danh sách key."

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



        btn_del = QPushButton("🗑️ Xóa (Delete)")

        btn_del.setStyleSheet("color: #c62828; font-weight: bold;")

        btn_del.setToolTip("Xóa một hoặc nhiều key đã chọn (Phím tắt: Delete)")

        btn_del.clicked.connect(self._on_delete_key)

        tb_layout.addWidget(btn_del)



        btn_toggle = QPushButton("☑/☒ Bật / Tắt")

        btn_toggle.setToolTip("Bật hoặc tắt trạng thái các key đã chọn")

        btn_toggle.clicked.connect(self._on_toggle_status)

        tb_layout.addWidget(btn_toggle)



        tb_layout.addSpacing(15)



        btn_test_sel = QPushButton("🔍 Kiểm Tra Đã Chọn")

        btn_test_sel.clicked.connect(self._on_test_selected)

        tb_layout.addWidget(btn_test_sel)



        btn_test_all = QPushButton("⚡ Kiểm Tra Tất Cả")

        btn_test_all.setStyleSheet("color: #6a1b9a; font-weight: 500;")

        btn_test_all.clicked.connect(self._on_test_all)

        tb_layout.addWidget(btn_test_all)



        btn_clean_invalid = QPushButton("🧹 Xóa Key Lỗi")

        btn_clean_invalid.setStyleSheet("color: #d32f2f;")

        btn_clean_invalid.setToolTip("Tự động xóa tất cả các key có kết quả kiểm tra thất bại (đỏ ❌)")

        btn_clean_invalid.clicked.connect(self._on_clean_invalid_keys)

        tb_layout.addWidget(btn_clean_invalid)



        tb_layout.addStretch()

        layout.addLayout(tb_layout)



        # ── Bảng hiển thị Keys ──────────────────────────────────

        self.table = QTableWidget(0, 6)

        self.table.setHorizontalHeaderLabels([

            "#", "Account (Email)", "API Key", "Trạng thái", "Khôi phục sau", "Ghi chú & Kiểm tra"

        ])

        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)

        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)

        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)

        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)

        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)

        self.table.setColumnWidth(1, 160)

        self.table.setColumnWidth(2, 180)

        self.table.setColumnWidth(4, 150)

        # Hỗ trợ chọn nhiều dòng (ExtendedSelection)

        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)

        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.table.doubleClicked.connect(self._on_edit_key)

        layout.addWidget(self.table)



        # ── Thanh đồng bộ & Lưu ─────────────────────────────────

        bottom_layout = QHBoxLayout()



        btn_sync_twoway = QPushButton("🔄 Đồng Bộ 2 Chiều (AskCpl)")

        btn_sync_twoway.setStyleSheet("background-color: #0288d1; color: white; font-weight: bold; padding: 6px 12px;")

        btn_sync_twoway.setToolTip("Hợp nhất tất cả keys của cả 2 bên: Cả GetHtmlFromUrl và AskCpl đều sẽ có cùng danh sách đầy đủ nhất 100%")

        btn_sync_twoway.clicked.connect(self._on_sync_merge_twoway)

        bottom_layout.addWidget(btn_sync_twoway)



        btn_sync_menu = QPushButton("⚙️ Tùy Chọn AskCpl ▾")

        btn_sync_menu.setToolTip("Các tùy chọn đồng bộ chuyên sâu: Nhập, Xuất, Ghi đè")

        menu_sync = QMenu(self)

        

        act_import = QAction("📥 Nhập Thêm từ AskCpl (Không ghi đè)", self)

        act_import.triggered.connect(self._on_sync_from_askcpl)

        menu_sync.addAction(act_import)



        act_export = QAction("📤 Xuất Thêm sang AskCpl (Không ghi đè)", self)

        act_export.triggered.connect(self._on_sync_to_askcpl)

        menu_sync.addAction(act_export)



        menu_sync.addSeparator()



        act_overwrite_from = QAction("📥 Ghi Đè 100% từ AskCpl sang Đây", self)

        act_overwrite_from.triggered.connect(self._on_overwrite_from_askcpl)

        menu_sync.addAction(act_overwrite_from)



        act_overwrite_to = QAction("📤 Ghi Đè 100% từ Đây sang AskCpl", self)

        act_overwrite_to.triggered.connect(self._on_overwrite_to_askcpl)

        menu_sync.addAction(act_overwrite_to)



        btn_sync_menu.setMenu(menu_sync)

        bottom_layout.addWidget(btn_sync_menu)



        bottom_layout.addStretch()



        self.lbl_summary = QLabel("")

        self.lbl_summary.setStyleSheet("font-weight: 500; color: #1565c0;")

        bottom_layout.addWidget(self.lbl_summary)



        btn_save = QPushButton("💾 Lưu & Áp Dụng")

        btn_save.setStyleSheet("background-color: #1976d2; color: white; font-weight: bold; padding: 6px 20px; font-size: 13px;")

        btn_save.clicked.connect(self._on_save_all)

        bottom_layout.addWidget(btn_save)



        btn_close = QPushButton("Đóng")

        btn_close.clicked.connect(self.accept)

        bottom_layout.addWidget(btn_close)



        layout.addLayout(bottom_layout)



    def _notify_pool_update(self):

        """Thông báo cho AccountPool đang chạy (in-memory) cập nhật tức thì danh sách key sau khi thêm/sửa/xóa."""

        try:

            from core.ai_translator import get_shared_account_pool, load_configured_key_objects, enrich_key_objects

            pool = get_shared_account_pool()

            raw_objs = load_configured_key_objects()

            pool.sync(enrich_key_objects(raw_objs))

        except Exception as e:

            pass



    def _refresh_table(self):
        self.table.setRowCount(len(self.keys_data))
        active_count = 0

        # Tìm các project_id bị trùng trên cùng email (giống AskCpl)
        project_counts = {}
        for k in self.keys_data:
            pid = (k.get("project_id") or "").strip()
            email = (k.get("email") or "").strip().lower()
            if pid and email:
                key_pair = (email, pid)
                project_counts[key_pair] = project_counts.get(key_pair, 0) + 1
        dup_projects = {pair for pair, cnt in project_counts.items() if cnt > 1}

        now_ts = int(time.time())

        for i, item in enumerate(self.keys_data):
            raw_key = decode_token(item.get("key", ""))
            status = item.get("status", "active")
            rt = item.get("reset_time") or 0
            pid = (item.get("project_id") or "").strip()
            email = (item.get("email") or "").strip().lower()

            # Tự động chuyển active nếu đã qua reset_time
            if status == "exhausted" and rt > 0 and now_ts > rt:
                item["status"] = "active"
                item["reset_time"] = 0
                item["next_check_time"] = 0
                item["error_msg"] = ""
                status = "active"
                rt = 0

            if status == "active":
                active_count += 1

            it_idx = QTableWidgetItem(str(i + 1))
            it_idx.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            it_email = QTableWidgetItem(item.get("email", ""))
            it_key = QTableWidgetItem(mask_key(raw_key))
            it_key.setFont(QFont("Consolas", 10))

            disp_status = "✅ Bật"
            if status == "exhausted":
                disp_status = "⚠️ Quota"
            elif status == "invalid":
                disp_status = "❌ Khóa"
            elif status == "disabled":
                disp_status = "☒ Tắt"

            it_status = QTableWidgetItem(disp_status)
            it_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            reset_str = format_reset_time_display(item)
            it_reset = QTableWidgetItem(reset_str)
            it_reset.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            note_str = item.get("note", "")
            if item.get("error_msg"):
                note_str = f"{note_str} | {item.get('error_msg')}".strip(" |")
            it_note = QTableWidgetItem(note_str)

            # Màu sắc và làm nổi bật theo trạng thái (visual highlighting)
            bg_color = None
            if status == "exhausted":
                bg_color = QColor("#fff9c4")  # Vàng nhạt nổi bật
                it_status.setForeground(QBrush(QColor("#e65100")))
                it_reset.setForeground(QBrush(QColor("#bf360c")))
                it_reset.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            elif status == "invalid":
                bg_color = QColor("#ffebee")  # Đỏ nhạt
                it_status.setForeground(QBrush(QColor("#c62828")))
                it_reset.setForeground(QBrush(QColor("#b71c1c")))
            elif status == "disabled":
                it_status.setForeground(QBrush(QColor("#757575")))
                it_reset.setForeground(QBrush(QColor("#757575")))
            else:
                it_status.setForeground(QBrush(QColor("#2e7d32")))
                if rt > now_ts:
                    it_reset.setForeground(QBrush(QColor("#e67e22")))
                else:
                    it_reset.setForeground(QBrush(QColor("#757575")))

            # Cảnh báo trùng project
            is_dup = (email, pid) in dup_projects
            if is_dup:
                it_email.setBackground(QBrush(QColor("#ffcdd2")))
                it_email.setToolTip(f"Cảnh báo: Project ID '{pid}' bị trùng trên cùng email '{email}'!")

            if bg_color:
                it_idx.setBackground(QBrush(bg_color))
                if not is_dup:
                    it_email.setBackground(QBrush(bg_color))
                it_key.setBackground(QBrush(bg_color))
                it_status.setBackground(QBrush(bg_color))
                it_reset.setBackground(QBrush(bg_color))
                it_note.setBackground(QBrush(bg_color))

            self.table.setItem(i, 0, it_idx)
            self.table.setItem(i, 1, it_email)
            self.table.setItem(i, 2, it_key)
            self.table.setItem(i, 3, it_status)
            self.table.setItem(i, 4, it_reset)
            self.table.setItem(i, 5, it_note)

        self.lbl_summary.setText(f"Tổng cộng: {len(self.keys_data)} keys ({active_count} đang bật)")



    def _get_selected_rows(self) -> List[int]:

        """Lấy danh sách các chỉ số dòng được chọn, sắp xếp giảm dần (để pop không bị lệch)."""

        selection_model = self.table.selectionModel()

        if not selection_model:

            return []

        rows = sorted(list({idx.row() for idx in selection_model.selectedRows()}), reverse=True)

        if not rows:

            rows = sorted(list({idx.row() for idx in self.table.selectedIndexes()}), reverse=True)

        return rows



    def _get_selected_row(self) -> int:

        rows = self._get_selected_rows()

        return rows[0] if rows else -1



    def _on_add_key(self):
        dlg = ApiKeyEditDialog(parent=self)
        if dlg.exec():
            data = dlg.get_data()
            raw = data["key"]
            item = {
                "id": f"key_{int(time.time()*1000)}",
                "key": encode_token(raw),
                "email": data["email"],
                "status": data["status"],
                "reset_time": data["reset_time"],
                "project_id": data["project_id"],
                "note": data["note"]
            }
            self.keys_data.append(item)
            self._refresh_table()
            save_local_keys(self.keys_data)
            self._notify_pool_update()

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
            status=item.get("status", "active"),
            reset_time=item.get("reset_time", 0),
            project_id=item.get("project_id", ""),
            parent=self
        )
        if dlg.exec():
            data = dlg.get_data()
            item["email"] = data["email"]
            item["key"] = encode_token(data["key"])
            item["note"] = data["note"]
            item["status"] = data["status"]
            item["reset_time"] = data["reset_time"]
            item["project_id"] = data["project_id"]
            self._refresh_table()
            save_local_keys(self.keys_data)
            self._notify_pool_update()

    def _on_delete_key(self):

        """Xóa 1 hoặc nhiều API key được chọn bằng nút hoặc phím Delete."""

        rows = self._get_selected_rows()

        if not rows:

            QMessageBox.warning(self, "Chọn dòng", "Vui lòng chọn ít nhất một dòng để xóa! (Giữ Shift hoặc Ctrl để chọn nhiều).")

            return

        count = len(rows)

        if count == 1:

            row = rows[0]

            item = self.keys_data[row]

            email = item.get("email", "Không tên")

            msg = f"Bạn có chắc muốn xóa API key của tài khoản '{email}'?"

        else:

            msg = f"Bạn có chắc muốn xóa {count} API keys đã chọn?"



        reply = QMessageBox.question(

            self, "Xác nhận xóa",

            msg,

            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No

        )

        if reply == QMessageBox.StandardButton.Yes:

            deleted_raw = []

            for r in rows:

                raw = decode_token(self.keys_data[r].get("key", ""))

                if raw:

                    deleted_raw.append(raw)

                self.keys_data.pop(r)



            self._refresh_table()

            save_local_keys(self.keys_data)

            self._notify_pool_update()



            if os.path.exists(ASKCPL_SETTINGS_PATH) and deleted_raw:

                ask_reply = QMessageBox.question(

                    self, "Đồng bộ xóa với AskCpl",

                    f"Đã xóa {count} keys khỏi cấu hình GetHtmlFromUrl.\n\n"

                    f"Bạn có muốn xóa đồng thời các key này trong AskCpl để giữ 2 bên luôn đồng nhất không?",

                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No

                )

                if ask_reply == QMessageBox.StandardButton.Yes:

                    removed = remove_keys_from_askcpl(deleted_raw)

                    QMessageBox.information(self, "Thông báo", f"Đã xóa thành công {removed} key tương ứng trong AskCpl!")



    def _on_toggle_status(self):

        """Bật/tắt trạng thái cho 1 hoặc nhiều key được chọn."""

        rows = self._get_selected_rows()

        if not rows:

            return

        any_active = any(self.keys_data[r].get("status", "active") == "active" for r in rows)

        new_status = "disabled" if any_active else "active"

        for r in rows:

            self.keys_data[r]["status"] = new_status

        self._refresh_table()

        save_local_keys(self.keys_data)



    def _on_clean_invalid_keys(self):

        """Quét và xóa toàn bộ các key bị đánh dấu đỏ ❌ sau khi kiểm tra."""

        invalid_rows = []

        for r in range(self.table.rowCount()):

            it = self.table.item(r, 5)

            if (it and "❌" in it.text()) or self.keys_data[r].get("status") == "invalid":

                invalid_rows.append(r)



        if not invalid_rows:

            QMessageBox.information(

                self, "Thông báo",

                "Không tìm thấy key lỗi nào (❌).\n"

                "Hãy bấm '⚡ Kiểm Tra Tất Cả' để quét tình trạng key trước khi dọn rác."

            )

            return



        # Sắp xếp giảm dần để xóa an toàn

        invalid_rows.sort(reverse=True)

        count = len(invalid_rows)

        reply = QMessageBox.question(

            self, "Xác nhận dọn key lỗi",

            f"Tìm thấy {count} API key bị lỗi (đỏ ❌).\n\n"

            f"Bạn có muốn xóa toàn bộ {count} key lỗi này khỏi danh sách không?",

            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No

        )

        if reply == QMessageBox.StandardButton.Yes:

            deleted_raw = []

            for r in invalid_rows:

                raw = decode_token(self.keys_data[r].get("key", ""))

                if raw:

                    deleted_raw.append(raw)

                self.keys_data.pop(r)



            self._refresh_table()

            save_local_keys(self.keys_data)

            self._notify_pool_update()



            if os.path.exists(ASKCPL_SETTINGS_PATH) and deleted_raw:

                ask_reply = QMessageBox.question(

                    self, "Dọn dẹp cả bên AskCpl",

                    f"Đã xóa {count} key lỗi khỏi GetHtmlFromUrl.\n\n"

                    f"Bạn có muốn xóa luôn các key hỏng này trong AskCpl không?",

                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No

                )

                if ask_reply == QMessageBox.StandardButton.Yes:

                    removed = remove_keys_from_askcpl(deleted_raw)

                    QMessageBox.information(self, "Thông báo", f"Đã xóa {removed} key lỗi khỏi AskCpl!")



    def _format_test_result_item(self, ok: bool, msg: str) -> QTableWidgetItem:

        clean_msg = msg.lstrip("✅❌⚠ ").strip()

        if ok:

            icon = "✅"

            color = "#2e7d32"  # Xanh lá: Hoạt động tốt

        elif "⚠" in msg or "503" in msg or "429" in msg or "timeout" in msg.lower() or "quá tải" in msg.lower() or "bận" in msg.lower():

            icon = "⚠"

            color = "#ef6c00"  # Cam: Cảnh báo tạm thời (Key vẫn sống, server bận hoặc mạng lag)

        else:

            icon = "❌"

            color = "#c62828"  # Đỏ: Key chết thực sự (401 / 400 Invalid / 403 Revoked)



        it = QTableWidgetItem(f"{icon} {clean_msg}")

        it.setForeground(QBrush(QColor(color)))

        return it



    def _start_validation(self, key_rows, done_title="Hoàn tất kiểm tra"):
        """P3: chạy KeyValidationWorker DÙNG CHUNG cho 'Kiểm tra đã chọn' + 'Kiểm tra tất cả'.

        Cập nhật từng dòng realtime qua signal trên GUI thread, KHÔNG block UI.
        Bản cũ của 'Kiểm tra đã chọn' validate ĐỒNG BỘ trong GUI thread (mỗi key
        timeout 7s + processEvents vá tạm) ⇒ chọn 20 key là cửa sổ treo hàng chục giây.
        """
        self.validation_worker = KeyValidationWorker(key_rows)

        def _on_item(row, ok, status_kind, msg, ms):
            if row < len(self.keys_data):
                now_ts = int(time.time())
                self.keys_data[row]["last_check_time"] = now_ts
                if status_kind == "active":
                    self.keys_data[row]["status"] = "active"
                    self.keys_data[row]["reset_time"] = 0
                    self.keys_data[row]["next_check_time"] = 0
                    self.keys_data[row]["error_msg"] = ""
                elif status_kind == "exhausted":
                    self.keys_data[row]["status"] = "exhausted"
                    self.keys_data[row]["reset_time"] = now_ts + 86400
                    self.keys_data[row]["next_check_time"] = now_ts + 10800
                    self.keys_data[row]["error_msg"] = msg
                elif status_kind == "invalid":
                    self.keys_data[row]["status"] = "invalid"
                    self.keys_data[row]["error_msg"] = msg

                self.table.setItem(row, 5, self._format_test_result_item(ok, msg))
                reset_str = format_reset_time_display(self.keys_data[row])
                it_reset = QTableWidgetItem(reset_str)
                it_reset.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 4, it_reset)

                disp_st = "✅ Bật" if self.keys_data[row].get("status") == "active" else ("⚠️ Quota" if self.keys_data[row].get("status") == "exhausted" else "❌ Khóa")
                it_status = QTableWidgetItem(disp_st)
                it_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 3, it_status)

        def _on_all_finished(txt):
            save_local_keys(self.keys_data)
            self._notify_pool_update()
            self._refresh_table()
            QMessageBox.information(self, done_title, txt)

        self.validation_worker.item_validated_signal.connect(_on_item)
        self.validation_worker.finished_signal.connect(_on_all_finished)
        self.validation_worker.start()

    def _on_test_selected(self):
        """P3: kiểm tra dòng đã chọn trên NỀN — dùng chung worker với _on_test_all."""
        rows = self._get_selected_rows()
        if not rows:
            QMessageBox.warning(self, "Chọn dòng", "Vui lòng chọn ít nhất một key để kiểm tra!")
            return
        key_rows = []
        for row in rows:
            key_rows.append((row, decode_token(self.keys_data[row].get("key", ""))))
            self.table.setItem(row, 5, QTableWidgetItem("⏳ Đang chờ..."))
        self._start_validation(key_rows, done_title="Hoàn tất kiểm tra (đã chọn)")

    def _on_test_all(self):
        if not self.keys_data:
            return
        key_rows = []
        for i, item in enumerate(self.keys_data):
            raw = decode_token(item.get("key", ""))
            key_rows.append((i, raw))
            self.table.setItem(i, 5, QTableWidgetItem("⏳ Đang chờ..."))
        # P3: gộp logic vào _start_validation — dùng chung với 'Kiểm tra đã chọn'
        self._start_validation(key_rows, done_title="Hoàn tất kiểm tra")



    def _on_sync_merge_twoway(self):

        """Hợp nhất 2 chiều để cả 2 ứng dụng đều có danh sách key giống hệt nhau 100%."""

        added_local, added_ask, total = sync_merge_two_way()

        self.keys_data = load_local_keys()

        self._refresh_table()

        QMessageBox.information(

            self, "Đồng Bộ 2 Chiều Thành Công",

            f"✅ Đã hợp nhất 100% API Keys giữa GetHtmlFromUrl và AskCpl!\n\n"

            f"• Thêm mới vào GetHtmlFromUrl: {added_local} keys\n"

            f"• Thêm mới vào AskCpl: {added_ask} keys\n"

            f"• Tổng số key hiện có ở cả 2 bên: {total} keys."

        )



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



    def _on_overwrite_from_askcpl(self):

        reply = QMessageBox.warning(

            self, "Xác nhận ghi đè",

            "Hành động này sẽ XÓA TOÀN BỘ danh sách key hiện tại của GetHtmlFromUrl "

            "và thay thế 100% bằng danh sách từ AskCpl.\n\nBạn có chắc chắn muốn tiếp tục?",

            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No

        )

        if reply == QMessageBox.StandardButton.Yes:

            count, total = overwrite_from_askcpl()

            self.keys_data = load_local_keys()

            self._refresh_table()

            QMessageBox.information(self, "Thông báo", f"Đã ghi đè thành công {count} keys từ AskCpl!")



    def _on_overwrite_to_askcpl(self):

        reply = QMessageBox.warning(

            self, "Xác nhận ghi đè",

            "Hành động này sẽ GHI ĐÈ 100% danh sách key trong AskCpl bằng danh sách hiện có ở đây.\n\n"

            "Bạn có chắc chắn muốn tiếp tục?",

            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No

        )

        if reply == QMessageBox.StandardButton.Yes:

            count, total = overwrite_to_askcpl()

            QMessageBox.information(self, "Thông báo", f"Đã ghi đè thành công {count} keys sang AskCpl!")



    def _on_save_all(self):

        save_local_keys(self.keys_data)

        self._notify_pool_update()

        self.accept()

