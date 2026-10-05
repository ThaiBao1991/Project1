import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QTextEdit, QGroupBox, QWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QBrush, QFont

from core.model_manager import (
    load_model_priority, save_model_priority, infer_tier,
    TIER_META, DEFAULT_MODEL_FALLBACKS, auto_discover_and_benchmark
)


class ModelDiscoverWorker(QThread):
    """Worker chạy Auto Discover & Benchmark ngầm không đơ giao diện PyQt6."""
    log_signal = pyqtSignal(str)
    done_signal = pyqtSignal(list)

    def __init__(self, api_key: str, existing_models: list):
        super().__init__()
        self.api_key = api_key
        self.existing_models = existing_models
        self.stop_flag = [False]

    def stop(self):
        self.stop_flag[0] = True

    def run(self):
        updated = auto_discover_and_benchmark(
            api_key=self.api_key,
            existing_models=self.existing_models,
            stop_flag=self.stop_flag,
            log_callback=self.log_signal.emit
        )
        self.done_signal.emit(updated)


class ModelPriorityDialog(QDialog):
    """Giao diện Quản Lý Thứ Tự Ưu Tiên & Tự Động Khám Phá Model AI (Chuẩn AskCpl)."""
    def __init__(self, api_key: str = "", parent=None):
        super().__init__(parent)
        self.api_key = api_key
        self.setWindowTitle("⚙️ Cài Đặt Thứ Tự Ưu Tiên & Khám Phá Model AI (Chuẩn AskCpl)")
        self.resize(850, 600)
        self.models_data = load_model_priority()
        self.worker = None
        self._build_ui()
        self._refresh_table()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Header giải thích
        lbl_info = QLabel(
            "Quản lý danh sách model Gemini và thứ tự fallback khi dịch truyện.\n"
            "Model đứng đầu danh sách sẽ được ưu tiên sử dụng trước. Khi gặp giới hạn 429 hoặc lỗi, hệ thống tự động fallback xuống các model tiếp theo."
        )
        lbl_info.setStyleSheet("color: #424242; font-size: 12px; margin-bottom: 4px;")
        lbl_info.setWordWrap(True)
        layout.addWidget(lbl_info)

        # ── Toolbar thao tác thủ công ───────────────────────────
        tb_layout = QHBoxLayout()
        btn_up = QPushButton("↑ Lên")
        btn_up.clicked.connect(self._on_move_up)
        tb_layout.addWidget(btn_up)

        btn_down = QPushButton("↓ Xuống")
        btn_down.clicked.connect(self._on_move_down)
        tb_layout.addWidget(btn_down)

        btn_toggle = QPushButton("☑/☒ Bật / Tắt")
        btn_toggle.clicked.connect(self._on_toggle_enabled)
        tb_layout.addWidget(btn_toggle)

        btn_sort = QPushButton("🔀 Xếp Theo Điểm")
        btn_sort.setToolTip("Xếp hạng dựa trên Hạng Tier (S > A > B > C) và tốc độ phản hồi thực tế")
        btn_sort.clicked.connect(self._on_auto_sort)
        tb_layout.addWidget(btn_sort)

        btn_reset = QPushButton("↩ Mặc Định")
        btn_reset.clicked.connect(self._on_reset_default)
        tb_layout.addWidget(btn_reset)

        tb_layout.addStretch()

        # Nút Discover
        self.btn_discover = QPushButton("🔍 Auto Discover & Đánh Giá")
        self.btn_discover.setStyleSheet("background-color: #00897b; color: white; font-weight: bold; padding: 6px 14px;")
        self.btn_discover.setToolTip("Gọi Google API để tìm toàn bộ model mới nhất, đo tốc độ thực tế và tự động xếp hạng")
        self.btn_discover.clicked.connect(self._on_start_discover)
        tb_layout.addWidget(self.btn_discover)

        self.btn_stop = QPushButton("⏹ Dừng")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._on_stop_discover)
        tb_layout.addWidget(self.btn_stop)

        layout.addLayout(tb_layout)

        # ── Bảng hiển thị Model ────────────────────────────────
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "#", "Tier", "Tên Model", "Độ Trễ", "Trạng Thái", "Ghi Chú"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(2, 230)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table, stretch=2)

        # ── Log panel ──────────────────────────────────────────
        layout.addWidget(QLabel("📋 Nhật ký khám phá & đánh giá:"))
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setStyleSheet("background-color: #1e1e1e; color: #00e676; font-family: Consolas, monospace; font-size: 11px;")
        layout.addWidget(self.txt_log, stretch=1)

        # ── Thanh dưới cùng: Lưu & Đóng ────────────────────────
        bottom_layout = QHBoxLayout()
        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("font-weight: 500; color: #1565c0;")
        bottom_layout.addWidget(self.lbl_status)
        bottom_layout.addStretch()

        btn_save = QPushButton("💾 Lưu Cấu Hình")
        btn_save.setStyleSheet("background-color: #1976d2; color: white; font-weight: bold; padding: 6px 20px; font-size: 13px;")
        btn_save.clicked.connect(self._on_save_all)
        bottom_layout.addWidget(btn_save)

        btn_close = QPushButton("Đóng")
        btn_close.clicked.connect(self.close)
        bottom_layout.addWidget(btn_close)

        layout.addLayout(bottom_layout)

    def _refresh_table(self):
        self.table.setRowCount(len(self.models_data))
        enabled_count = 0
        for i, m in enumerate(self.models_data):
            enabled = m.get("enabled", True)
            if enabled:
                enabled_count += 1
            tier = m.get("tier", infer_tier(m["name"]))
            tier_info = TIER_META.get(tier, TIER_META["C"])
            ms = m.get("latency_ms", 0)

            # 1. Thứ tự
            it_idx = QTableWidgetItem(str(i + 1))
            it_idx.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # 2. Tier
            it_tier = QTableWidgetItem(tier_info["badge"])
            it_tier.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it_tier.setForeground(QBrush(QColor(tier_info["color"])))
            it_tier.setFont(QFont("Consolas", 10, QFont.Weight.Bold))

            # 3. Model Name
            it_name = QTableWidgetItem(m["name"])
            it_name.setFont(QFont("Consolas", 10))

            # 4. Latency
            lat_str = f"{ms}ms" if ms > 0 else "—"
            it_lat = QTableWidgetItem(lat_str)
            it_lat.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # 5. Status
            it_st = QTableWidgetItem("✅ Bật" if enabled else "☒ Tắt")
            it_st.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it_st.setForeground(QBrush(QColor("#2e7d32") if enabled else QColor("#757575")))

            # 6. Note
            it_note = QTableWidgetItem(m.get("note", ""))

            if not enabled:
                it_name.setForeground(QBrush(QColor("#757575")))

            self.table.setItem(i, 0, it_idx)
            self.table.setItem(i, 1, it_tier)
            self.table.setItem(i, 2, it_name)
            self.table.setItem(i, 3, it_lat)
            self.table.setItem(i, 4, it_st)
            self.table.setItem(i, 5, it_note)

        self.lbl_status.setText(f"Tổng số: {len(self.models_data)} models ({enabled_count} đang kích hoạt).")

    def _get_selected_row(self) -> int:
        selected = self.table.selectedIndexes()
        if not selected:
            return -1
        return selected[0].row()

    def _on_move_up(self):
        row = self._get_selected_row()
        if row <= 0:
            return
        self.models_data[row - 1], self.models_data[row] = self.models_data[row], self.models_data[row - 1]
        self._refresh_table()
        self.table.selectRow(row - 1)
        save_model_priority(self.models_data)

    def _on_move_down(self):
        row = self._get_selected_row()
        if row < 0 or row >= len(self.models_data) - 1:
            return
        self.models_data[row], self.models_data[row + 1] = self.models_data[row + 1], self.models_data[row]
        self._refresh_table()
        self.table.selectRow(row + 1)
        save_model_priority(self.models_data)

    def _on_toggle_enabled(self):
        row = self._get_selected_row()
        if row < 0 or row >= len(self.models_data):
            return
        self.models_data[row]["enabled"] = not self.models_data[row].get("enabled", True)
        self._refresh_table()
        self.table.selectRow(row)
        save_model_priority(self.models_data)

    def _on_auto_sort(self):
        def _score(m):
            ms = m.get("latency_ms", 0)
            tier_bonus = TIER_META.get(m.get("tier", "C"), TIER_META["C"])["score_bonus"]
            speed = (1000 / ms) if ms > 0 else 0
            return tier_bonus + speed

        self.models_data.sort(key=_score, reverse=True)
        self._refresh_table()
        save_model_priority(self.models_data)
        self._log("🔀 Đã sắp xếp lại danh sách theo Điểm Mạnh (Hạng Tier + Tốc độ phản hồi)!")

    def _on_reset_default(self):
        reply = QMessageBox.question(
            self, "Khôi phục mặc định",
            "Bạn có chắc muốn đặt lại danh sách model về cấu hình mặc định ban đầu?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.models_data = [dict(m) for m in DEFAULT_MODEL_FALLBACKS]
            self._refresh_table()
            save_model_priority(self.models_data)
            self._log("↩ Đã khôi phục danh sách model mặc định.")

    def _on_start_discover(self):
        if not self.api_key:
            QMessageBox.warning(self, "Chưa có key", "Vui lòng cung cấp ít nhất 1 API key hợp lệ để quét model.")
            return

        self.btn_discover.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.txt_log.clear()
        self._log("🚀 Bắt đầu tiến trình Auto Discover & Đánh giá model trên Google API...")

        self.worker = ModelDiscoverWorker(self.api_key, self.models_data)
        self.worker.log_signal.connect(self._log)
        def _on_done(updated_list):
            self.models_data = updated_list
            self._refresh_table()
            self.btn_discover.setEnabled(True)
            self.btn_stop.setEnabled(False)
            QMessageBox.information(
                self, "Hoàn tất khám phá",
                f"Đã hoàn thành khám phá & đánh giá {len(self.models_data)} model!\n"
                f"Các model tối ưu nhất đã được đưa lên đầu danh sách."
            )
        self.worker.done_signal.connect(_on_done)
        self.worker.start()

    def _on_stop_discover(self):
        if self.worker and self.worker.isRunning():
            self._log("⏳ Đang gửi tín hiệu dừng...")
            self.worker.stop()
            self.btn_stop.setEnabled(False)

    def _log(self, text: str):
        self.txt_log.append(text)

    def _on_save_all(self):
        save_model_priority(self.models_data)
        self.accept()
