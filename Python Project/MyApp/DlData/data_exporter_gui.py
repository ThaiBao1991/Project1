import tkinter as tk
from tkinter import filedialog, messagebox
import os
import excel_processor
import threading

class DataExporterGUI:
    def __init__(self, master):
        self.master = master
        self.top_level = None
        self.create_exporter_window()

    def create_exporter_window(self):
        """Tạo và hiển thị cửa sổ xuất dữ liệu."""
        if self.top_level is not None and self.top_level.winfo_exists():
            self.top_level.deiconify()
            self.top_level.lift()
            return

        self.top_level = tk.Toplevel(self.master)
        self.top_level.title("Xuất dữ liệu 4 Điểm")
        self.top_level.protocol("WM_DELETE_WINDOW", self.hide_window)

        # Frame chọn file bộ 4 điểm Excel
        excel_file_frame = tk.LabelFrame(self.top_level, text="Chọn file Excel bộ 4 điểm", padx=5, pady=5)
        excel_file_frame.pack(padx=10, pady=5, fill=tk.X)

        self.excel_file_entry = tk.Entry(excel_file_frame, width=50)
        self.excel_file_entry.pack(side=tk.LEFT, padx=5)

        browse_excel_btn = tk.Button(excel_file_frame, text="Duyệt...", command=self.browse_excel_file)
        browse_excel_btn.pack(side=tk.LEFT, padx=5)

        # Frame chọn thư mục lấy dữ liệu (Data DL4D)
        output_folder_frame = tk.LabelFrame(self.top_level, text="Chọn thư mục Data DL4D", padx=5, pady=5)
        output_folder_frame.pack(padx=10, pady=5, fill=tk.X)

        self.output_folder_entry = tk.Entry(output_folder_frame, width=50)
        self.output_folder_entry.pack(side=tk.LEFT, padx=5)

        browse_folder_btn = tk.Button(output_folder_frame, text="Duyệt...", command=self.browse_output_folder)
        browse_folder_btn.pack(side=tk.LEFT, padx=5)

        # --- Frame hiển thị tiến độ và dữ liệu cho "Xuất Data" ---
        export_progress_frame = tk.LabelFrame(self.top_level, text="Tiến độ Xuất Data", padx=5, pady=5)
        export_progress_frame.pack(padx=10, pady=5, fill=tk.X)

        tk.Label(export_progress_frame, text="Đang đọc dòng:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.export_current_row_label = tk.Label(export_progress_frame, text="N/A", fg="blue")
        self.export_current_row_label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)

        tk.Label(export_progress_frame, text="Dữ liệu cột B:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.export_column_b_data_label = tk.Label(export_progress_frame, text="N/A", fg="blue")
        self.export_column_b_data_label.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        tk.Label(export_progress_frame, text="Tổng ô khác rỗng:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.export_non_empty_count_label = tk.Label(export_progress_frame, text="N/A", fg="blue")
        self.export_non_empty_count_label.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        # ----------------------------------------------------

        # --- Frame hiển thị tiến độ cho "Lấy dữ liệu" ---
        fetch_progress_frame = tk.LabelFrame(self.top_level, text="Tiến độ Lấy dữ liệu (Files gốc)", padx=5, pady=5)
        fetch_progress_frame.pack(padx=10, pady=5, fill=tk.X)

        tk.Label(fetch_progress_frame, text="Trạng thái:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.fetch_status_label = tk.Label(fetch_progress_frame, text="Chờ...", fg="green")
        self.fetch_status_label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)

        tk.Label(fetch_progress_frame, text="Đã xử lý:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.fetch_count_label = tk.Label(fetch_progress_frame, text="0/0", fg="blue")
        self.fetch_count_label.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        # ----------------------------------------------------

        # --- Frame hiển thị tiến độ cho "Nhập data đã xuất" ---
        import_progress_frame = tk.LabelFrame(self.top_level, text="Tiến độ Nhập data đã xuất (Files mới)", padx=5, pady=5)
        import_progress_frame.pack(padx=10, pady=5, fill=tk.X)

        tk.Label(import_progress_frame, text="Trạng thái:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.import_status_label = tk.Label(import_progress_frame, text="Chờ...", fg="purple")
        self.import_status_label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)

        tk.Label(import_progress_frame, text="Files mới:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.import_new_files_count_label = tk.Label(import_progress_frame, text="0", fg="purple")
        self.import_new_files_count_label.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)

        tk.Label(import_progress_frame, text="Đã kiểm tra:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.import_processed_count_label = tk.Label(import_progress_frame, text="0/0", fg="blue")
        self.import_processed_count_label.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        # ----------------------------------------------------

        # Frame các nút chức năng
        button_frame = tk.Frame(self.top_level, padx=5, pady=5)
        button_frame.pack(padx=10, pady=5, fill=tk.X)

        export_data_btn = tk.Button(button_frame, text="Xuất Data", command=self.handle_export_data)
        export_data_btn.pack(side=tk.LEFT, padx=5)

        get_data_btn = tk.Button(button_frame, text="Lấy dữ liệu", command=self.handle_fetch_data) 
        get_data_btn.pack(side=tk.LEFT, padx=5)

        # Kích hoạt nút "Nhập data đã xuất"
        import_exported_data_btn = tk.Button(button_frame, text="Nhập data đã xuất", command=self.handle_import_data)
        import_exported_data_btn.pack(side=tk.LEFT, padx=5)

        self.top_level.withdraw()

    def hide_window(self):
        """Ẩn cửa sổ thay vì đóng hoàn toàn."""
        if self.top_level:
            self.top_level.withdraw()

    def browse_excel_file(self):
        file_path = filedialog.askopenfilename(
            title="Chọn file Excel bộ 4 điểm",
            filetypes=(("Excel Files", "*.xlsx;*.xlsb;*.xlsm;*.xls"), ("All Files", "*.*"))
        )
        if file_path:
            self.excel_file_entry.delete(0, tk.END)
            self.excel_file_entry.insert(0, file_path)

    def browse_output_folder(self):
        folder_path = filedialog.askdirectory(
            title="Chọn thư mục Data DL4D"
        )
        if folder_path:
            self.output_folder_entry.delete(0, tk.END)
            self.output_folder_entry.insert(0, folder_path)
            
    def update_export_progress_labels(self, processed_rows_count, current_row, non_empty_count, total_rows_to_process=None):
        """Cập nhật các nhãn hiển thị tiến độ Xuất Data."""
        progress_text = f"{processed_rows_count}/{total_rows_to_process}" if total_rows_to_process is not None else str(processed_rows_count)
        self.export_current_row_label.config(text=progress_text)
        self.export_column_b_data_label.config(text=str(current_row)[:50] + "..." if len(str(current_row)) > 50 else str(current_row))
        self.export_non_empty_count_label.config(text=str(non_empty_count))
        self.master.update_idletasks()  # Cập nhật giao diện ngay lập tức

    def handle_export_data(self):
        excel_path = self.excel_file_entry.get()
        output_folder = self.output_folder_entry.get()

        if not excel_path:
            messagebox.showerror("Lỗi", "Vui lòng chọn file Excel bộ 4 điểm.")
            return

        if not output_folder:
            messagebox.showerror("Lỗi", "Vui lòng chọn thư mục Data DL4D.")
            return
        
        self.update_export_progress_labels("Bắt đầu...", "", "")
        
        threading.Thread(target=self._run_export_data_task, args=(excel_path, output_folder)).start()

    def _run_export_data_task(self, excel_path, output_folder):
        success = excel_processor.export_4_point_data(excel_path, output_folder, self.update_export_progress_labels)
        if success:
            self.update_export_progress_labels("Hoàn tất!", "", "")
        else:
            self.update_export_progress_labels("Thất bại!", "", "")


    def update_fetch_progress_labels(self, status_text, processed_count, total_items):
        """Cập nhật các nhãn hiển thị tiến độ Lấy dữ liệu."""
        self.fetch_status_label.config(text=status_text)
        self.fetch_count_label.config(text=f"{processed_count}/{total_items}")
        self.master.update_idletasks()

    def handle_fetch_data(self):
        excel_path = self.excel_file_entry.get()
        output_folder = self.output_folder_entry.get()

        if not excel_path:
            messagebox.showerror("Lỗi", "Vui lòng chọn file Excel bộ 4 điểm.")
            return

        if not output_folder:
            messagebox.showerror("Lỗi", "Vui lòng chọn thư mục Data DL4D.")
            return

        self.update_fetch_progress_labels("Bắt đầu...", 0, 0)
        
        threading.Thread(target=self._run_fetch_data_task, args=(excel_path, output_folder)).start()

    def _run_fetch_data_task(self, excel_path, output_folder):
        success = excel_processor.fetch_hyperlink_data(excel_path, output_folder, self.update_fetch_progress_labels)
        if success:
            self.update_fetch_progress_labels("Hoàn tất!", processed_count=self.fetch_count_label.winfo_text().split('/')[0], total_items=self.fetch_count_label.winfo_text().split('/')[1])
        else:
            self.update_fetch_progress_labels("Thất bại!", processed_count=0, total_items=0)

    # --- Hàm mới cho tiến độ "Nhập data đã xuất" ---
    def update_import_progress_labels(self, status_text, new_files_count, processed_count, total_items):
        """Cập nhật các nhãn hiển thị tiến độ Nhập data đã xuất."""
        self.import_status_label.config(text=status_text)
        self.import_new_files_count_label.config(text=str(new_files_count))
        self.import_processed_count_label.config(text=f"{processed_count}/{total_items}")
        self.master.update_idletasks()

    def handle_import_data(self):
        excel_path = self.excel_file_entry.get()
        output_folder = self.output_folder_entry.get()

        if not excel_path:
            messagebox.showerror("Lỗi", "Vui lòng chọn file Excel bộ 4 điểm.")
            return

        if not output_folder:
            messagebox.showerror("Lỗi", "Vui lòng chọn thư mục Data DL4D.")
            return
        
        self.update_import_progress_labels("Bắt đầu kiểm tra...", 0, 0, 0) # Reset labels
        
        threading.Thread(target=self._run_import_data_task, args=(excel_path, output_folder)).start()

    def _run_import_data_task(self, excel_path, output_folder):
        success = excel_processor.import_exported_data(excel_path, output_folder, self.update_import_progress_labels)
        if success:
            # Lấy số lượng file mới đã được cập nhật từ label
            current_new_files = self.import_new_files_count_label.cget("text")
            # Cập nhật trạng thái cuối cùng
            self.update_import_progress_labels(
                f"Hoàn tất! ({current_new_files} files mới)",
                current_new_files,
                self.import_processed_count_label.cget("text").split('/')[0],
                self.import_processed_count_label.cget("text").split('/')[1]
            )
        else:
            self.update_import_progress_labels("Thất bại!", 0, 0, 0)