"""
main_gui.py — Giao diện Tkinter cho StampByAntigravity
=======================================================
=======================================================================
AI ASSISTANT — ĐỌC TRƯỚC KHI CHỈNH SỬA BẤT KỲ ĐIỀU GÌ:
  1. Đọc ProjectLog.md trong cùng thư mục này
  2. self.stamp_bbox      = canvas pixels (chỉ dùng để vẽ trên canvas)
     self.stamp_bbox_pdf  = PDF points    (truyền cho engine)
     self.exact_center    = PDF points    (truyền cho engine)
  3. all_configs = {"[Ảnh] Tên": "/full/path.json"} — init trong __init__
  4. Config lưu vào stamp_configs/Image/ hoặc stamp_configs/Text/
  5. test_stamp() và start_stamp_all() dùng all_configs dict (không parse prefix)
=======================================================================
"""
import sys
import os
import json
import shutil
import io
import traceback
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from PIL import Image, ImageTk, ImageDraw
import fitz
import cv2
import numpy as np

import config_generator

class StampApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Công cụ đóng dấu PDF - Nâng Cao")
        self.root.geometry("1400x900")
        self.root.state('zoomed') # Maximize window
        
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # --- Shared Variables ---
        self.folder_path = tk.StringVar()
        self.pdf_sample_path = tk.StringVar()
        self.stamp_image_path = tk.StringVar()
        self.scale_percent = tk.DoubleVar(value=100.0)
        self.file_format = tk.StringVar(value="pdf")
        self.config_name = None
        
        # --- Image Match Variables ---
        self.use_template_matching = tk.BooleanVar(value=True)
        self.match_threshold = tk.DoubleVar(value=80.0)
        self.stamp_bbox = None
        self.stamp_center = None
        self.exact_center = None
        
        # --- Text Anchor Variables ---
        self.use_text_anchor = tk.BooleanVar(value=False)
        self.anchor_text = tk.StringVar()
        self.text_match_mode = tk.StringVar(value="first")
        self.text_match_count = tk.IntVar(value=1)
        self.text_offset_x = tk.DoubleVar(value=0.0)
        self.text_offset_y = tk.DoubleVar(value=0.0)
        
        # --- PDF State ---
        self.current_page_num = 0
        self.total_pages = 0
        self.current_pdf_doc = None
        self.current_page = None
        self.page_images = []
        self.page_images_original = []
        self.display_image = None
        self.display_scale_x = 1.0
        self.display_scale_y = 1.0
        self.temp_cropped_image = None
        self.template_image_original = None
        
        # --- Drawing & Scale State ---
        self.canvas_rect = None
        self.center_mark = None
        self.scale_preview_rect = None
        self.start_x = None
        self.start_y = None
        self.picking_center = False
        
        # --- Stamp Positioning State ---
        self.stamp_bbox = None        # canvas coords (pixels)
        self.stamp_bbox_pdf = None    # PDF points (for engine)
        self.stamp_center = None      # canvas coords
        self.exact_center = None      # PDF points
        
        # --- Config Registry ---
        self.all_configs = {}         # {"[Ảnh] Name": "/path/to/file.json"}
        
        # --- Advanced Options ---
        self.use_annotation = tk.BooleanVar(value=False)
        self.remove_mode = tk.BooleanVar(value=False)
        
        self.setup_ui()
        self.refresh_category_list()
        self.log("Khởi động thành công. Hỗ trợ nhận diện ảnh đa tỉ lệ và tìm kiếm văn bản.")

    def setup_ui(self):
        # Layout tổng thể: Trái (Cấu hình) - Phải (Preview PDF Siêu To)
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        left_frame = ttk.Frame(main_paned, width=450)
        main_paned.add(left_frame, weight=0)
        
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=1)
        
        # ----- CỘT TRÁI: TAB CẤU HÌNH & NHẬT KÝ -----
        self.notebook = ttk.Notebook(left_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Cấu hình Chung & Image
        self.tab_image = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tab_image, text="Đóng Dấu Hình Ảnh")
        
        # Tab 2: Text Anchor
        self.tab_text = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tab_text, text="Đóng Dấu Theo Chữ")
        
        # Tab 3: Log
        self.tab_log = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tab_log, text="Nhật Ký")
        
        # Sự kiện đổi tab
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        self.build_image_tab()
        self.build_text_tab()
        self.build_log_tab()
        
        # ----- CỘT PHẢI: PREVIEW PDF LỚN -----
        preview_top = ttk.Frame(right_frame)
        preview_top.pack(fill=tk.X, pady=5)
        
        ttk.Button(preview_top, text="◀ Trang đầu", command=self.first_page, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(preview_top, text="◀ Trước", command=self.prev_page, width=10).pack(side=tk.LEFT, padx=5)
        self.page_label = ttk.Label(preview_top, text="Trang 1/1", font=('Arial', 11, 'bold'))
        self.page_label.pack(side=tk.LEFT, padx=15)
        ttk.Button(preview_top, text="Sau ▶", command=self.next_page, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(preview_top, text="Trang cuối ▶", command=self.last_page, width=12).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(preview_top, text="Lưu ý: Click ĐÚP vào bất kỳ đâu trên ảnh này để chọn TÂM con dấu", foreground="blue", font=('Arial', 10, 'italic')).pack(side=tk.RIGHT, padx=10)

        # Canvas cho Preview
        self.canvas_frame = ttk.Frame(right_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Tạo canvas với scrollbar
        self.h_scroll = ttk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL)
        self.v_scroll = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg="gray", cursor="cross",
                                xscrollcommand=self.h_scroll.set,
                                yscrollcommand=self.v_scroll.set)
        
        self.h_scroll.config(command=self.canvas.xview)
        self.v_scroll.config(command=self.canvas.yview)
        
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Bind các sự kiện kéo chuột (Khoanh vùng) và click đúp (Chọn tâm)
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind("<Double-Button-1>", self.on_double_click_center)
        
    def build_image_tab(self):
        f = self.tab_image
        row = 0
        
        # Shared top section
        self.build_shared_config(f, row, "image")
        row += 5
        
        ttk.Separator(f, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=4, sticky='ew', pady=10)
        row += 1
        
        ttk.Label(f, text="--- Chế độ Nhận Diện Ảnh (Template Matching) ---", font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=4, sticky=tk.W, pady=5)
        row += 1
        
        self.match_check = ttk.Checkbutton(f, text="Sử dụng nhận diện vị trí ảnh (Multi-scale)", variable=self.use_template_matching)
        self.match_check.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        ttk.Label(f, text="Độ tương đồng (%):").grid(row=row, column=2, sticky=tk.E, pady=5)
        ttk.Entry(f, textvariable=self.match_threshold, width=8).grid(row=row, column=3, sticky=tk.W, padx=5)
        row += 1
        
        ttk.Label(f, text="Khoanh vùng:", foreground="gray").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.bbox_label = ttk.Label(f, text="Chưa chọn vùng", foreground="red")
        self.bbox_label.grid(row=row, column=1, columnspan=3, sticky=tk.W, pady=5)
        row += 1
        
        ttk.Label(f, text="Tâm con dấu:", foreground="gray").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.center_label = ttk.Label(f, text="Chưa xác định", foreground="blue")
        self.center_label.grid(row=row, column=1, columnspan=3, sticky=tk.W, pady=5)
        row += 1
        
        # Action Buttons
        self.build_action_buttons(f, row)
        
    def build_text_tab(self):
        f = self.tab_text
        row = 0
        
        # Shared top section
        self.build_shared_config(f, row, "text")
        row += 5
        
        ttk.Separator(f, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=4, sticky='ew', pady=10)
        row += 1
        
        ttk.Label(f, text="--- Chế độ Tìm Kiếm Chữ (Text Anchor) ---", font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=4, sticky=tk.W, pady=5)
        row += 1
        
        ttk.Label(f, text="Chữ cần tìm:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(f, textvariable=self.anchor_text, width=30).grid(row=row, column=1, columnspan=3, sticky=tk.W, pady=5)
        row += 1
        
        ttk.Label(f, text="Chế độ đóng dấu:").grid(row=row, column=0, sticky=tk.W, pady=5)
        mode_combo = ttk.Combobox(f, textvariable=self.text_match_mode, values=["first", "all", "custom"], state="readonly", width=10)
        mode_combo.grid(row=row, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(f, text="Số lượng (nếu custom):").grid(row=row, column=2, sticky=tk.E, pady=5)
        ttk.Entry(f, textvariable=self.text_match_count, width=5).grid(row=row, column=3, sticky=tk.W, padx=5)
        row += 1
        
        ttk.Label(f, text="Lệch X (pixel PDF):").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(f, textvariable=self.text_offset_x, width=10).grid(row=row, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(f, text="Lệch Y:").grid(row=row, column=2, sticky=tk.E, pady=5)
        ttk.Entry(f, textvariable=self.text_offset_y, width=10).grid(row=row, column=3, sticky=tk.W, padx=5)
        row += 1
        
        # Action Buttons
        self.build_action_buttons(f, row)
        
    def build_shared_config(self, parent, start_row, tab_type):
        r = start_row
        ttk.Label(parent, text="Cấu hình:").grid(row=r, column=0, sticky=tk.W, pady=5)
        
        combo = ttk.Combobox(parent, values=[], width=20, state="readonly")
        if tab_type == "image":
            self.combo_image = combo
        else:
            self.combo_text = combo
            
        combo.grid(row=r, column=1, sticky=tk.W, pady=5)
        combo.bind('<<ComboboxSelected>>', lambda e, t=tab_type: self.load_selected_config(t))
        ttk.Button(parent, text="Tải", command=lambda t=tab_type: self.load_selected_config(t), width=6).grid(row=r, column=2, padx=2)
        ttk.Button(parent, text="Xóa", command=lambda t=tab_type: self.delete_config(t), width=6).grid(row=r, column=3, padx=2)
        r += 1
        
        ttk.Label(parent, text="Thư mục:").grid(row=r, column=0, sticky=tk.W, pady=5)
        ttk.Entry(parent, textvariable=self.folder_path, width=30).grid(row=r, column=1, columnspan=2, sticky=tk.W, pady=5)
        ttk.Button(parent, text="Chọn", command=self.select_folder, width=6).grid(row=r, column=3, padx=2)
        r += 1
        
        ttk.Label(parent, text="PDF mẫu:").grid(row=r, column=0, sticky=tk.W, pady=5)
        ttk.Entry(parent, textvariable=self.pdf_sample_path, width=30).grid(row=r, column=1, columnspan=2, sticky=tk.W, pady=5)
        ttk.Button(parent, text="Chọn", command=self.select_pdf_sample, width=6).grid(row=r, column=3, padx=2)
        r += 1
        
        ttk.Label(parent, text="Ảnh dấu:").grid(row=r, column=0, sticky=tk.W, pady=5)
        ttk.Entry(parent, textvariable=self.stamp_image_path, width=30).grid(row=r, column=1, columnspan=2, sticky=tk.W, pady=5)
        ttk.Button(parent, text="Chọn", command=self.select_stamp_image, width=6).grid(row=r, column=3, padx=2)
        r += 1
        
        ttk.Label(parent, text="Tỉ lệ ảnh (%):").grid(row=r, column=0, sticky=tk.W, pady=5)
        self.scale_slider = ttk.Scale(parent, from_=10, to=300, variable=self.scale_percent, orient=tk.HORIZONTAL, length=120)
        self.scale_slider.grid(row=r, column=1, sticky=tk.W)
        self.scale_slider.configure(command=self.on_scale_change)
        
        self.scale_entry = ttk.Entry(parent, textvariable=self.scale_percent, width=8)
        self.scale_entry.grid(row=r, column=2, sticky=tk.W, padx=5)
        self.scale_entry.bind('<Return>', lambda e: self.update_scale_from_entry())
        
        ttk.Label(parent, text="Loại đóng dấu:").grid(row=r+1, column=0, sticky=tk.W, pady=5)
        ttk.Checkbutton(parent, text="Đóng dấu Nổi (Có thể xoá)", variable=self.use_annotation).grid(row=r+1, column=1, columnspan=2, sticky=tk.W)

    def build_action_buttons(self, parent, start_row):
        btn_frame = ttk.Frame(parent)
        btn_frame.grid(row=start_row, column=0, columnspan=4, pady=20)
        
        ttk.Checkbutton(btn_frame, text="Chế độ Gỡ Dấu", variable=self.remove_mode).pack(side=tk.LEFT, padx=15)
        ttk.Button(btn_frame, text="Lưu Cấu Hình", command=self.save_config, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Test Dấu", command=self.test_stamp, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="START", command=self.start_stamp_all, width=12).pack(side=tk.LEFT, padx=5)

    def build_log_tab(self):
        self.log_text = tk.Text(self.tab_log, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(self.tab_log, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def on_tab_changed(self, event):
        tab_id = self.notebook.index("current")
        if tab_id == 0:
            self.use_text_anchor.set(False)
            self.log("Chuyển sang chế độ Hình Ảnh")
        elif tab_id == 1:
            self.use_text_anchor.set(True)
            self.log("Chuyển sang chế độ Văn Bản")
            
    # --- File Selection ---
    def select_folder(self):
        path = filedialog.askdirectory()
        if path: self.folder_path.set(path)
            
    def select_pdf_sample(self):
        path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if path:
            self.pdf_sample_path.set(path)
            self.load_pdf_preview(path)
            
    def select_stamp_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg")])
        if path: self.stamp_image_path.set(path)
        
    # --- PDF Preview ---
    def load_pdf_preview(self, path):
        try:
            if self.current_pdf_doc:
                self.current_pdf_doc.close()
                
            self.current_pdf_doc = fitz.open(path)
            self.total_pages = len(self.current_pdf_doc)
            self.page_images = []
            self.page_images_original = []
            
            for page_num in range(self.total_pages):
                page = self.current_pdf_doc[page_num]
                mat = fitz.Matrix(2.0, 2.0)
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                self.page_images_original.append(img.copy())
                
                # Resize for display
                display_img = img.copy()
                display_img.thumbnail((1200, 1600))
                self.page_images.append(display_img)
                
            self.show_page(0)
            self.log(f"Đã tải PDF: {self.total_pages} trang")
        except Exception as e:
            self.log(f"Lỗi tải PDF: {e}")

    def show_page(self, page_num):
        # Guard: nếu tài liệu PDF chưa được mở hoặc đã bị đóng thì bỏ qua
        if self.current_pdf_doc is None:
            return
        try:
            if self.current_pdf_doc.is_closed:
                return
        except Exception:
            return
        if 0 <= page_num < self.total_pages:
            self.current_page_num = page_num
            self.current_page = self.current_pdf_doc[page_num]
            
            img = self.page_images[page_num]
            self.display_image = ImageTk.PhotoImage(img)
            
            original_img = self.page_images_original[page_num]
            self.display_scale_x = original_img.width / img.width
            self.display_scale_y = original_img.height / img.height
            
            self.canvas.delete("all")
            self.canvas.config(scrollregion=(0, 0, img.width, img.height))
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.display_image)
            self.canvas.img = self.display_image
            self.page_label.config(text=f"Trang {page_num+1}/{self.total_pages}")
            
            if self.stamp_bbox:
                self.canvas_rect = self.canvas.create_rectangle(
                    self.stamp_bbox[0], self.stamp_bbox[1],
                    self.stamp_bbox[2], self.stamp_bbox[3],
                    outline="red", width=2
                )
            if self.stamp_center:
                self.draw_center_mark()

    def first_page(self): self.show_page(0)
    def prev_page(self): self.show_page(self.current_page_num - 1)
    def next_page(self): self.show_page(self.current_page_num + 1)
    def last_page(self): self.show_page(self.total_pages - 1)

    # --- Canvas Interaction ---
    def on_mouse_down(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.start_x = x
        self.start_y = y
        if self.canvas_rect:
            self.canvas.delete(self.canvas_rect)

    def on_mouse_move(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        if self.start_x and self.start_y:
            if self.canvas_rect:
                self.canvas.delete(self.canvas_rect)
            self.canvas_rect = self.canvas.create_rectangle(
                self.start_x, self.start_y, x, y,
                outline="red", width=2, dash=(4, 4)
            )

    def on_mouse_up(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        if self.start_x and self.start_y:
            x1, y1 = self.start_x, self.start_y
            x2, y2 = x, y
            if x1 > x2: x1, x2 = x2, x1
            if y1 > y2: y1, y2 = y2, y1
            
            # Avoid microscopic boxes from accidental clicks
            if (x2 - x1) > 10 and (y2 - y1) > 10:
                self.stamp_bbox = (x1, y1, x2, y2)
                self.bbox_label.config(text=f"Đã chọn: ({int(x1)}, {int(y1)})", foreground="green")
                self.log(f"Đã khoanh vùng trang {self.current_page_num+1}")
                
                if self.canvas_rect:
                    self.canvas.delete(self.canvas_rect)
                self.canvas_rect = self.canvas.create_rectangle(x1, y1, x2, y2, outline="red", width=2)
                self.create_template_from_bbox()
                self.calculate_exact_position()
                
            self.start_x = None
            self.start_y = None

    def on_double_click_center(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.stamp_center = (x, y)
        self.center_label.config(text=f"({int(x)}, {int(y)})", foreground="green")
        self.log(f"Đã chọn TÂM con dấu tại: {int(x)}, {int(y)}")
        self.draw_center_mark()
        self.calculate_exact_position()
        self.draw_scale_preview()

    def update_scale_from_entry(self):
        try:
            txt = self.scale_entry.get().replace("%", "").strip()
            val = float(txt)
            self.scale_percent.set(val)
            self.draw_scale_preview()
        except: pass
        
    def on_scale_change(self, event=None):
        self.scale_entry.delete(0, tk.END)
        self.scale_entry.insert(0, f"{self.scale_percent.get():.1f}")
        self.draw_scale_preview()
        
    def draw_scale_preview(self):
        if self.scale_preview_rect:
            self.canvas.delete(self.scale_preview_rect)
            
        if not self.stamp_center or not self.stamp_image_path.get() or not os.path.exists(self.stamp_image_path.get()):
            return
            
        try:
            # Lấy kích thước ảnh con dấu thật
            img = Image.open(self.stamp_image_path.get())
            w, h = img.width, img.height
            
            # Tính tỉ lệ và kích thước hiển thị trên canvas
            scale = self.scale_percent.get() / 100.0
            
            # Kích thước thật trên PDF = w * scale (PDF points)
            # Kích thước hiển thị trên Canvas = kích thước PDF * 2.0 / scale_x của Canvas
            # Vì lúc render PDF->Ảnh ta dùng fitz.Matrix(2.0, 2.0)
            disp_w = (w * scale) * 2.0 / self.display_scale_x
            disp_h = (h * scale) * 2.0 / self.display_scale_y
            
            cx, cy = self.stamp_center
            self.scale_preview_rect = self.canvas.create_rectangle(
                cx - disp_w/2, cy - disp_h/2,
                cx + disp_w/2, cy + disp_h/2,
                outline="blue", dash=(4,4), width=2
            )
        except:
            pass

    def draw_center_mark(self):
        if self.center_mark:
            self.canvas.delete(self.center_mark)
        if self.stamp_center:
            x, y = self.stamp_center
            size = 15
            self.center_mark = self.canvas.create_line(x - size, y, x + size, y, fill="blue", width=3)
            self.canvas.create_line(x, y - size, x, y + size, fill="blue", width=3)

    def calculate_exact_position(self):
        if not self.current_page: return False
        
        pdf_w = self.current_page.rect.width
        pdf_h = self.current_page.rect.height
        canvas_width = self.display_image.width()
        canvas_height = self.display_image.height()
        
        scale_x = pdf_w / canvas_width
        scale_y = pdf_h / canvas_height
        
        if self.stamp_center:
            center_x_pdf = self.stamp_center[0] * scale_x
            center_y_pdf = self.stamp_center[1] * scale_y
            self.exact_center = (center_x_pdf, center_y_pdf)
        else:
            self.exact_center = None

        
        if self.stamp_bbox:
            self.stamp_bbox_pdf = [
                self.stamp_bbox[0] * scale_x,
                self.stamp_bbox[1] * scale_y,
                self.stamp_bbox[2] * scale_x,
                self.stamp_bbox[3] * scale_y
            ]
        else:
            self.stamp_bbox_pdf = None
        self.log(f"Tọa độ thực tế PDF: ({center_x_pdf:.2f}, {center_y_pdf:.2f})")
        return True

    def create_template_from_bbox(self):
        if not self.stamp_bbox or not self.display_image: return False
        try:
            original_img = self.page_images_original[self.current_page_num]
            x1 = max(0, min(int(self.stamp_bbox[0] * self.display_scale_x), original_img.width))
            y1 = max(0, min(int(self.stamp_bbox[1] * self.display_scale_y), original_img.height))
            x2 = max(0, min(int(self.stamp_bbox[2] * self.display_scale_x), original_img.width))
            y2 = max(0, min(int(self.stamp_bbox[3] * self.display_scale_y), original_img.height))
            
            if x1 >= x2 or y1 >= y2: return False
            self.template_image_original = original_img.crop((x1, y1, x2, y2))
            return True
        except Exception as e:
            self.log(f"Lỗi tạo ảnh mẫu: {e}")
            return False

    # --- Config Management ---
    def save_config(self):
        # Validation based on Mode
        if self.use_text_anchor.get():
            if not self.anchor_text.get():
                messagebox.showwarning("Thiếu dữ liệu", "Vui lòng nhập 'Chữ cần tìm'!")
                return
        else:
            if not self.stamp_bbox and self.use_template_matching.get():
                messagebox.showwarning("Thiếu dữ liệu", "Vui lòng khoanh vùng hình ảnh làm mẫu nhận diện!")
                return
        
        initial_name = self.config_name if self.config_name else ""
        name = simpledialog.askstring("Lưu", "Nhập tên cấu hình (không dấu):", initialvalue=initial_name, parent=self.root)
        if not name: return
        self.config_name = name
        
        use_text = self.use_text_anchor.get()
        sub_dir = "Text" if use_text else "Image"
        config_dir = os.path.join(self.script_dir, "stamp_configs", sub_dir)
        os.makedirs(config_dir, exist_ok=True)
        
        config_path = os.path.join(config_dir, f"{name}.json")
        
        exact_center_tuple = (self.exact_center[0], self.exact_center[1]) if self.exact_center else None
            
        template_image_path = ""
        if not self.use_text_anchor.get() and self.use_template_matching.get() and self.template_image_original:
            template_path = os.path.join(config_dir, f"{name}_template.png")
            try:
                self.template_image_original.save(template_path, "PNG")
                template_image_path = template_path
                self.log(f"Đã lưu ảnh khoanh vùng mẫu: {template_path}")
            except Exception as e:
                self.log(f"Lỗi khi lưu ảnh khoanh vùng mẫu: {e}")

        config = {
            "folder_path": self.folder_path.get(),
            "pdf_sample_path": self.pdf_sample_path.get(),
            "stamp_image_path": self.stamp_image_path.get(),
            "template_image_path": template_image_path,
            "scale_percent": self.scale_percent.get(),
            
            "use_template_matching": self.use_template_matching.get(),
            "match_threshold": self.match_threshold.get(),
            "page_number": self.current_page_num,
            "stamp_bbox": self.stamp_bbox,
            "stamp_bbox_pdf": self.stamp_bbox_pdf,
            "stamp_center": self.stamp_center,
            "exact_center": exact_center_tuple,
            
            "use_text_anchor": self.use_text_anchor.get(),
            "anchor_text": self.anchor_text.get(),
            "text_match_mode": self.text_match_mode.get(),
            "text_match_count": self.text_match_count.get(),
            "text_offset_x": self.text_offset_x.get(),
            "text_offset_y": self.text_offset_y.get(),
            
            "use_annotation": self.use_annotation.get(),
            "file_format": self.file_format.get()
        }
        
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
            
        try:
            py_path = config_generator.generate_py_config(name, config_path)
            self.log(f"Đã xuất cấu hình ra file Python: {py_path}")
            messagebox.showinfo("Lưu thành công", f"Cấu hình '{name}.py' đã sẵn sàng cho Access VBA!", parent=self.root)
        except Exception as e:
            self.log(f"Lỗi khi sinh file .py: {e}")
            
        self.refresh_category_list()
        # Auto-select the newly saved config
        prefix = "[Chữ] " if use_text else "[Ảnh] "
        combo = self.combo_text if use_text else self.combo_image
        combo.set(f"{prefix}{name}")

    def load_config(self, name=None, full_path=None):
        if not full_path and name:
            for sub in ["Text", "Image"]:
                p = os.path.join(self.script_dir, "stamp_configs", sub, f"{name}.json")
                if os.path.exists(p):
                    full_path = p
                    break
                    
        # Nếu full_path là .py, GUI không đọc trực tiếp file .py được (chỉ engine mới thực thi file .py),
        # Do đó ta tự động chuyển hướng tìm file .json tương ứng đã lưu ở trong thư mục Text/Image
        if full_path and full_path.endswith(".py"):
            json_name = os.path.splitext(os.path.basename(full_path))[0]
            # Ưu tiên tìm trong Image trước, sau đó Text
            p_img = os.path.join(self.script_dir, "stamp_configs", "Image", f"{json_name}.json")
            p_txt = os.path.join(self.script_dir, "stamp_configs", "Text", f"{json_name}.json")
            if os.path.exists(p_img): full_path = p_img
            elif os.path.exists(p_txt): full_path = p_txt
            else:
                self.log(f"Lỗi: GUI chỉ có thể hiển thị file .json. Không tìm thấy {json_name}.json")
                return
        
        if not full_path or not os.path.exists(full_path): return
        
        self.config_name = os.path.splitext(os.path.basename(full_path))[0]
        
        with open(full_path, "r", encoding="utf-8") as f:
            c = json.load(f)
            
        self.folder_path.set(c.get("folder_path", ""))
        self.pdf_sample_path.set(c.get("pdf_sample_path", ""))
        self.stamp_image_path.set(c.get("stamp_image_path", ""))
        self.scale_percent.set(c.get("scale_percent", 100))
        
        template_img_path = c.get("template_image_path", "")
        if template_img_path and os.path.exists(template_img_path):
            try:
                self.template_image_original = Image.open(template_img_path)
            except Exception as e:
                self.log(f"Lỗi tải ảnh mẫu (template): {e}")
                self.template_image_original = None
        else:
            self.template_image_original = None
            
        self.use_template_matching.set(c.get("use_template_matching", True))
        self.match_threshold.set(c.get("match_threshold", 80))
        self.stamp_bbox = tuple(c["stamp_bbox"]) if c.get("stamp_bbox") else None
        self.stamp_bbox_pdf = c.get("stamp_bbox_pdf")
        self.stamp_center = tuple(c["stamp_center"]) if c.get("stamp_center") else None
        if c.get("exact_center"):
            self.exact_center = tuple(c.get("exact_center"))
        else: self.exact_center = None
        
        self.use_text_anchor.set(c.get("use_text_anchor", False))
        self.anchor_text.set(c.get("anchor_text", ""))
        self.text_match_mode.set(c.get("text_match_mode", "first"))
        self.text_match_count.set(c.get("text_match_count", 1))
        self.text_offset_x.set(c.get("text_offset_x", 0.0))
        self.text_offset_y.set(c.get("text_offset_y", 0.0))
        
        self.use_annotation.set(c.get("use_annotation", False))
        
        if self.use_text_anchor.get():
            self.notebook.select(1)
        else:
            self.notebook.select(0)
            
        self.log(f"Đã tải cấu hình: {os.path.basename(full_path) if full_path else name}")
        pdf_path = self.pdf_sample_path.get()
        if pdf_path:
            if os.path.exists(pdf_path):
                self.load_pdf_preview(pdf_path)
                self.show_page(c.get("page_number", 0))
            else:
                self.log(f"⚠ PDF mẫu trong config không tồn tại: {pdf_path}")
                self.log("➡ Hãy chọn lại file PDF bằng nút 'Chọn'.")

    def refresh_category_list(self):
        base_dir = os.path.join(self.script_dir, "stamp_configs")
        files = {}
        for sub in ["Text", "Image", ""]:
            d = os.path.join(base_dir, sub) if sub else base_dir
            if os.path.exists(d):
                for f in os.listdir(d):
                    # Bỏ qua các file ẩn/temp bắt đầu bằng _
                    if f.startswith("_"): continue
                    
                    if f.endswith(".json"):
                        name = os.path.splitext(f)[0]
                        # Nếu file nằm ở thư mục gốc, dự đoán loại dựa vào có thư mục con không
                        if not sub:
                            if os.path.exists(os.path.join(base_dir, "Text", f)):
                                continue
                            if os.path.exists(os.path.join(base_dir, "Image", f)):
                                continue
                            prefix = "[Ảnh] "
                        else:
                            prefix = "[Chữ] " if sub == "Text" else "[Ảnh] "
                            
                        files[f"{prefix}{name}"] = os.path.join(d, f)
        
        self.all_configs = files
        sorted_keys = sorted(list(files.keys()))
        if hasattr(self, 'combo_image'): self.combo_image['values'] = sorted_keys
        if hasattr(self, 'combo_text'): self.combo_text['values'] = sorted_keys

    def load_selected_config(self, tab_type=None):
        combo = self.combo_image if tab_type == "image" else self.combo_text
        val = combo.get()
        if val in self.all_configs:
            self.load_config(full_path=self.all_configs[val])

    def delete_config(self, tab_type=None):
        combo = self.combo_image if tab_type == "image" else self.combo_text
        val = combo.get()
        if not val or val not in self.all_configs: return
        
        clean_name = val.split("] ", 1)[1]
        if messagebox.askyesno("Xác nhận", f"Xóa cấu hình '{val}'?", parent=self.root):
            p1 = self.all_configs[val]
            
            if os.path.exists(p1): os.remove(p1)
            
            # File .py sinh ra luon nam o thu muc stamp_configs (root)
            p_py = os.path.join(self.script_dir, "stamp_configs", f"{clean_name}.py")
            if os.path.exists(p_py): os.remove(p_py)
            
            # Xoa template image neu co
            p_img = p1.replace(".json", "_template.png")
            if os.path.exists(p_img): os.remove(p_img)
            
            if self.config_name == clean_name:
                self.config_name = None
                
            self.refresh_category_list()
            self.combo_image.set('')
            self.combo_text.set('')
            self.log(f"Đã xóa cấu hình: {val} và file .py đi kèm")

    # --- Engine Actions ---
    def validate_inputs(self):
        pdf_path = self.pdf_sample_path.get()
        if not pdf_path:
            self.log("Lỗi: Cần chọn PDF mẫu!")
            return False
        if not os.path.exists(pdf_path):
            self.log(f"Lỗi: File PDF mẫu không tồn tại: {pdf_path}")
            self.log("Gợi ý: Hãy chọn lại file PDF bằng nút Chọn.'")
            return False
        # Chỉ bắt buộc ảnh đóng dấu ở tab Ảnh, không cần ở tab Chữ
        if not self.use_text_anchor.get() and not self.stamp_image_path.get():
            self.log("Lỗi: Cần chọn Ảnh đóng dấu!")
            return False
        if not self.use_text_anchor.get() and self.stamp_image_path.get() and not os.path.exists(self.stamp_image_path.get()):
            self.log(f"Lỗi: File ảnh dấu không tồn tại: {self.stamp_image_path.get()}")
            self.log("Gợi ý: Hãy chọn lại ảnh dấu bằng nút Chọn.'")
            return False
        return True

    def get_current_ui_config(self):
        exact_center_tuple = (self.exact_center[0], self.exact_center[1]) if self.exact_center else None
        
        # Determine temporary template path if any
        template_image_path = ""
        if self.template_image_original:
            try:
                temp_dir = os.path.join(self.script_dir, "temp")
                os.makedirs(temp_dir, exist_ok=True)
                temp_path = os.path.join(temp_dir, "temp_gui_template.png")
                self.template_image_original.save(temp_path, "PNG")
                template_image_path = temp_path
            except:
                pass

        return {
            "folder_path":           self.folder_path.get(),
            "pdf_sample_path":       self.pdf_sample_path.get(),
            "stamp_image_path":      self.stamp_image_path.get(),
            "template_image_path":   template_image_path,
            "scale_percent":         self.scale_percent.get(),
            
            "use_template_matching": self.use_template_matching.get(),
            "match_threshold":       self.match_threshold.get(),
            "page_number":           self.current_page_num,
            "apply_to_all_pages":    True,
            # Dùng stamp_bbox_pdf (đơn vị PDF points) để engine hoạt động đúng
            "stamp_bbox":            self.stamp_bbox_pdf,
            "stamp_center":          self.stamp_center,
            "exact_center":          exact_center_tuple,
            
            "use_text_anchor":       self.use_text_anchor.get(),
            "anchor_text":           self.anchor_text.get(),
            "text_match_mode":       self.text_match_mode.get(),
            "text_match_count":      self.text_match_count.get(),
            "text_offset_x":         self.text_offset_x.get(),
            "text_offset_y":         self.text_offset_y.get(),
            
            "use_annotation":        self.use_annotation.get(),
            "file_format":           self.file_format.get()
        }

    def test_stamp(self):
        if not self.validate_inputs(): return
        output_path = filedialog.asksaveasfilename(
            defaultextension=".pdf", initialfile="TEST_STAMP.pdf", parent=self.root)
        if not output_path: return
        
        try:
            import StampByAntigravity
            use_text = self.use_text_anchor.get()
            cfg = self.get_current_ui_config()
            self.log("Đang Test bằng thiết lập hiện tại trên màn hình...")

            if self.remove_mode.get():
                success = StampByAntigravity.remove_stamp_pdf(
                    self.pdf_sample_path.get(), cfg, custom_output=output_path)
            else:
                success = StampByAntigravity.stamp_pdf(
                    self.pdf_sample_path.get(), cfg, custom_output=output_path)
                    
            if success:
                action_name = "Gỡ dấu" if self.remove_mode.get() else "Đóng dấu"
                self.log(f"Test {action_name.lower()} thành công! File: {output_path}")
                if sys.platform == "win32": os.startfile(output_path)
            else:
                self.log("Test không thành công (không tìm thấy vị trí / đối tượng).")
        except Exception as e:
            self.log(f"LỖI Test: {e}")
            self.log(traceback.format_exc())

    def start_stamp_all(self):
        if not self.validate_inputs(): return
        folder = self.folder_path.get()
        if not os.path.isdir(folder):
            self.log("Lỗi: Chọn thư mục PDF hợp lệ để quét.")
            return
            
        try:
            import StampByAntigravity
            use_text = self.use_text_anchor.get()
            combo = self.combo_text if use_text else self.combo_image
            cfg_key = combo.get()
            if cfg_key and cfg_key in self.all_configs:
                with open(self.all_configs[cfg_key], "r", encoding="utf-8") as f:
                    cfg = json.load(f)
            else:
                cfg = self.get_current_ui_config()
                self.log("Cảnh báo: Chạy hàng loạt bằng thiết lập tạm (chưa lưu).")
            
            pdf_files = [f for f in os.listdir(folder) if f.lower().endswith(".pdf")]
            if not pdf_files:
                self.log("Không có file PDF nào trong thư mục!")
                return
                
            action_name = "GỠ DẤU khỏi" if self.remove_mode.get() else "ĐÓNG DẤU lên"
            if not messagebox.askyesno(
                "Xác nhận",
                f"Thực hiện {action_name} {len(pdf_files)} file PDF trong thư mục?\n{folder}",
                parent=self.root):
                return
                
            success_count = 0
            for fname in pdf_files:
                p = os.path.join(folder, fname)
                try:
                    if self.remove_mode.get():
                        ok = StampByAntigravity.remove_stamp_pdf(p, cfg)
                    else:
                        ok = StampByAntigravity.stamp_pdf(p, cfg)
                    if ok:
                        success_count += 1
                        self.log(f"✓ Đóng dấu: {fname}")
                    else:
                        self.log(f"✗ Bỏ qua (không tìm thấy vị trí): {fname}")
                except Exception as ex:
                    self.log(f"✗ Lỗi khi xử lý {fname}: {ex}")
                    
            messagebox.showinfo(
                "Hoàn tất",
                f"Đã đóng dấu {success_count}/{len(pdf_files)} file.",
                parent=self.root)
        except Exception as e:
            self.log(f"LỖI trong Start: {e}")
            self.log(traceback.format_exc())

if __name__ == "__main__":
    root = tk.Tk()
    app = StampApp(root)
    root.mainloop()