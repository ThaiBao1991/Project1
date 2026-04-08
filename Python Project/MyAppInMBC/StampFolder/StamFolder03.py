import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from PIL import Image, ImageTk, ImageDraw
import fitz  # PyMuPDF
import subprocess
import sys
import shutil
from datetime import datetime
import cv2
import numpy as np
import io

class StampApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Công cụ đóng dấu PDF - Chất lượng cao")
        self.root.geometry("1200x800")
        
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Biến lưu thông tin
        self.folder_path = tk.StringVar()
        self.pdf_sample_path = tk.StringVar()
        self.stamp_image_path = tk.StringVar()
        self.scale_percent = tk.DoubleVar(value=100.0)
        self.match_threshold = tk.DoubleVar(value=80.0)
        self.file_format = tk.StringVar(value="pdf")
        
        # Biến trang
        self.current_page_num = 0
        self.total_pages = 0
        self.current_pdf_doc = None
        self.current_page = None
        self.page_images = []
        self.page_images_original = []
        
        # Vị trí đóng dấu
        self.stamp_bbox = None
        self.stamp_center = None
        self.exact_center = None
        
        # Template matching
        self.template_image = None
        self.template_image_original = None
        self.use_template_matching = tk.BooleanVar(value=True)
        
        # Tỷ lệ giữa ảnh hiển thị và ảnh gốc
        self.display_scale_x = 1.0
        self.display_scale_y = 1.0
        
        # Ảnh hiển thị
        self.display_image = None
        self.canvas_rect = None
        self.center_mark = None
        self.start_x = None
        self.start_y = None
        
        self.config_name = None
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.temp_cropped_image = None
        
        # Trạng thái chọn tâm
        self.picking_center = False

        self.create_widgets()
        self.refresh_category_list()
        self.log(f"Đường dẫn làm việc: {self.script_dir}")
        self.log("Chế độ đóng dấu: Nhúng ảnh gốc - KHÔNG resize - Chất lượng cao nhất")

    def create_widgets(self):
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)
        
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=1)
        
        notebook = ttk.Notebook(left_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        config_frame = ttk.Frame(notebook, padding="10")
        notebook.add(config_frame, text="Cấu hình")
        
        log_frame = ttk.Frame(notebook, padding="10")
        notebook.add(log_frame, text="Nhật ký")
        
        row = 0
        
        ttk.Label(config_frame, text="0. Thể loại đã lưu:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.category_combo = ttk.Combobox(config_frame, values=[], width=25)
        self.category_combo.grid(row=row, column=1, sticky=tk.W, pady=5)
        self.category_combo.bind('<<ComboboxSelected>>', lambda e: self.load_selected_config())
        ttk.Button(config_frame, text="Tải", command=self.load_selected_config, width=8).grid(row=row, column=2, padx=5)
        ttk.Button(config_frame, text="Xóa", command=self.delete_config, width=8).grid(row=row, column=3, padx=5)
        row += 1

        ttk.Label(config_frame, text="1. Thư mục PDF:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(config_frame, textvariable=self.folder_path, width=35).grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5)
        ttk.Button(config_frame, text="Chọn", command=self.select_folder, width=8).grid(row=row, column=3, padx=5)
        row += 1

        ttk.Label(config_frame, text="2. PDF mẫu:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(config_frame, textvariable=self.pdf_sample_path, width=35).grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5)
        ttk.Button(config_frame, text="Chọn", command=self.select_pdf_sample, width=8).grid(row=row, column=3, padx=5)
        row += 1

        ttk.Label(config_frame, text="3. Ảnh con dấu:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(config_frame, textvariable=self.stamp_image_path, width=35).grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5)
        ttk.Button(config_frame, text="Chọn", command=self.select_stamp_image, width=8).grid(row=row, column=3, padx=5)
        row += 1

        ttk.Label(config_frame, text="4. Khoanh vùng đóng dấu:").grid(row=row, column=0, sticky=tk.W, pady=5)
        
        page_control_frame = ttk.Frame(config_frame)
        page_control_frame.grid(row=row+1, column=0, columnspan=4, pady=5)
        
        ttk.Button(page_control_frame, text="◀ Trang đầu", command=self.first_page, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(page_control_frame, text="◀ Trước", command=self.prev_page, width=8).pack(side=tk.LEFT, padx=2)
        self.page_label = ttk.Label(page_control_frame, text="Trang 1/1", width=12)
        self.page_label.pack(side=tk.LEFT, padx=5)
        ttk.Button(page_control_frame, text="Sau ▶", command=self.next_page, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(page_control_frame, text="Trang cuối ▶", command=self.last_page, width=10).pack(side=tk.LEFT, padx=2)
        
        self.canvas = tk.Canvas(config_frame, width=500, height=350, bg="gray", cursor="cross")
        self.canvas.grid(row=row+2, column=0, columnspan=4, pady=5)
        
        self.bind_canvas_for_region_select()
        row += 3

        ttk.Label(config_frame, text="5. Vị trí đóng dấu:").grid(row=row, column=0, sticky=tk.W, pady=5)
        
        position_frame = ttk.Frame(config_frame)
        position_frame.grid(row=row, column=1, columnspan=3, sticky=tk.W)
        
        self.bbox_label = ttk.Label(position_frame, text="Chưa chọn vùng", foreground="red", width=25)
        self.bbox_label.pack(side=tk.LEFT, padx=5)
        row += 1
        
        ttk.Label(config_frame, text="Tâm con dấu (vị trí đóng):").grid(row=row, column=0, sticky=tk.W, pady=5)
        
        center_frame = ttk.Frame(config_frame)
        center_frame.grid(row=row, column=1, columnspan=3, sticky=tk.W)
        
        self.center_label = ttk.Label(center_frame, text="Chưa xác định", foreground="blue", width=35)
        self.center_label.pack(side=tk.LEFT, padx=5)
        ttk.Button(center_frame, text="Chọn tâm", command=self.activate_center_picker, width=10).pack(side=tk.LEFT, padx=5)
        row += 1

        ttk.Label(config_frame, text="6. Tỉ lệ ảnh con dấu (%):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.scale_slider = ttk.Scale(config_frame, from_=0.1, to=300, variable=self.scale_percent, orient=tk.HORIZONTAL, length=200)
        self.scale_slider.grid(row=row, column=1, sticky=tk.W)
        self.scale_entry = ttk.Entry(config_frame, textvariable=self.scale_percent, width=8)
        self.scale_entry.grid(row=row, column=2, sticky=tk.W, padx=5)
        self.scale_entry.bind('<Return>', lambda e: self.update_scale_from_entry())
        ttk.Button(config_frame, text="Xem trước dấu", command=self.preview_stamp_on_pdf, width=12).grid(row=row, column=3, padx=5)
        row += 1

        ttk.Label(config_frame, text="7. Tỷ lệ nhận diện (%):").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Scale(config_frame, from_=10, to=100, variable=self.match_threshold, orient=tk.HORIZONTAL, length=200).grid(row=row, column=1, sticky=tk.W)
        self.threshold_entry = ttk.Entry(config_frame, textvariable=self.match_threshold, width=8)
        self.threshold_entry.grid(row=row, column=2, sticky=tk.W, padx=5)
        
        self.match_check = ttk.Checkbutton(config_frame, text="Sử dụng nhận diện vị trí (Template Matching)", 
                                           variable=self.use_template_matching)
        self.match_check.grid(row=row, column=3, sticky=tk.W, padx=5)
        row += 1

        ttk.Label(config_frame, text="8. Định dạng file:").grid(row=row, column=0, sticky=tk.W, pady=5)
        format_combo = ttk.Combobox(config_frame, textvariable=self.file_format, values=["pdf"], state="readonly", width=10)
        format_combo.grid(row=row, column=1, sticky=tk.W)
        row += 2

        button_frame = ttk.Frame(config_frame)
        button_frame.grid(row=row, column=0, columnspan=4, pady=10)
        
        ttk.Button(button_frame, text="9. Test đóng dấu", command=self.test_stamp, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="10. Lưu thông tin", command=self.save_config, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="11. Start", command=self.start_stamp_all, width=15).pack(side=tk.LEFT, padx=5)
        
        log_text_frame = ttk.Frame(log_frame)
        log_text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(log_text_frame, height=20, width=50, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(log_text_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        preview_label = ttk.Label(right_frame, text="Xem trước kết quả đóng dấu", font=('Arial', 12, 'bold'))
        preview_label.pack(pady=10)
        
        self.preview_canvas = tk.Canvas(right_frame, width=550, height=700, bg="white", relief=tk.SUNKEN, bd=2)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.preview_info = ttk.Label(right_frame, text="Chưa có dữ liệu xem trước\n1. Khoanh vùng\n2. Chọn tâm\n3. Bấm 'Xem trước dấu'", 
                                      foreground="gray", justify=tk.CENTER)
        self.preview_info.pack(pady=5)

    def bind_canvas_for_region_select(self):
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

    def unbind_canvas_for_region_select(self):
        self.canvas.unbind("<ButtonPress-1>")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease-1>")

    def convert_to_rgba(self, img):
        """Chuyển đổi ảnh sang định dạng RGBA để tương thích với PyMuPDF"""
        try:
            # Nếu ảnh đang ở mode Palette (P)
            if img.mode in ('P', 'PA'):
                self.log(f"Chuyển đổi ảnh từ mode {img.mode} sang RGBA")
                return img.convert('RGBA')
            # Nếu ảnh không có kênh Alpha, thêm vào
            elif img.mode == 'RGB':
                return img.convert('RGBA')
            # Giữ nguyên nếu đã là RGBA
            elif img.mode == 'RGBA':
                return img
            # Các mode khác chuyển về RGB
            else:
                self.log(f"Chuyển đổi ảnh từ mode {img.mode} sang RGB")
                return img.convert('RGB')
        except Exception as e:
            self.log(f"Lỗi chuyển đổi ảnh: {e}")
            return img

    def activate_center_picker(self):
        self.picking_center = True
        self.center_label.config(text="Đang chọn tâm... Click vào vùng đã khoanh", foreground="orange")
        self.canvas.config(cursor="target")
        
        self.unbind_canvas_for_region_select()
        self.canvas.bind("<Button-1>", self.pick_center)
        self.log("Chế độ chọn tâm: Hãy click vào vị trí muốn đóng dấu trong vùng đã khoanh")

    def pick_center(self, event):
        if self.picking_center:
            if self.stamp_bbox:
                x, y = event.x, event.y
                if (self.stamp_bbox[0] <= x <= self.stamp_bbox[2] and 
                    self.stamp_bbox[1] <= y <= self.stamp_bbox[3]):
                    self.stamp_center = (x, y)
                    self.draw_center_mark()
                    self.center_label.config(text=f"Đã chọn tâm tại ({x}, {y})", foreground="green")
                    self.log(f"Đã chọn tâm con dấu tại: ({x}, {y})")
                    self.calculate_exact_position()
                else:
                    self.log("Vui lòng click vào bên trong vùng đã khoanh!")
            else:
                self.log("Hãy khoanh vùng trước khi chọn tâm!")
            
            self.picking_center = False
            self.canvas.config(cursor="cross")
            self.canvas.unbind("<Button-1>")
            self.bind_canvas_for_region_select()

    def select_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.folder_path.set(path)
            self.log(f"Đã chọn thư mục: {path}")

    def select_pdf_sample(self):
        path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if path:
            self.pdf_sample_path.set(path)
            self.log(f"Đã chọn PDF mẫu: {path}")
            self.load_pdf_preview(path)

    def select_stamp_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp")])
        if path:
            self.stamp_image_path.set(path)
            # Kiểm tra và chuyển đổi ảnh ngay khi chọn
            try:
                test_img = Image.open(path)
                if test_img.mode in ('P', 'PA'):
                    self.log(f"Cảnh báo: Ảnh {os.path.basename(path)} ở mode {test_img.mode}, sẽ tự động chuyển sang RGBA")
                test_img.close()
            except Exception as e:
                self.log(f"Lỗi đọc ảnh: {e}")
            self.log(f"Đã chọn ảnh con dấu: {path}")

    def load_pdf_preview(self, pdf_path):
        try:
            if self.current_pdf_doc:
                self.current_pdf_doc.close()
            
            self.current_pdf_doc = fitz.open(pdf_path)
            self.total_pages = len(self.current_pdf_doc)
            self.current_page_num = 0
            self.page_images = []
            self.page_images_original = []
            
            for page_num in range(self.total_pages):
                page = self.current_pdf_doc[page_num]
                mat = fitz.Matrix(2.0, 2.0)
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                self.page_images_original.append(img.copy())
                
                display_img = img.copy()
                display_img.thumbnail((500, 350))
                self.page_images.append(display_img)
            
            self.show_page(0)
            self.log(f"Đã tải PDF: {self.total_pages} trang")
        except Exception as e:
            self.log(f"Lỗi tải PDF: {e}")

    def show_page(self, page_num):
        if 0 <= page_num < self.total_pages:
            self.current_page_num = page_num
            self.current_page = self.current_pdf_doc[page_num]
            
            img = self.page_images[page_num]
            self.display_image = ImageTk.PhotoImage(img)
            
            original_img = self.page_images_original[page_num]
            self.display_scale_x = original_img.width / img.width
            self.display_scale_y = original_img.height / img.height
            
            self.canvas.delete("all")
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

    def first_page(self):
        self.show_page(0)
    
    def prev_page(self):
        if self.current_page_num > 0:
            self.show_page(self.current_page_num - 1)
    
    def next_page(self):
        if self.current_page_num < self.total_pages - 1:
            self.show_page(self.current_page_num + 1)
    
    def last_page(self):
        self.show_page(self.total_pages - 1)

    def on_mouse_down(self, event):
        if not self.picking_center:
            self.start_x = event.x
            self.start_y = event.y
            if self.canvas_rect:
                self.canvas.delete(self.canvas_rect)

    def on_mouse_move(self, event):
        if not self.picking_center and self.start_x and self.start_y:
            if self.canvas_rect:
                self.canvas.delete(self.canvas_rect)
            self.canvas_rect = self.canvas.create_rectangle(
                self.start_x, self.start_y, event.x, event.y,
                outline="red", width=2, dash=(4, 4)
            )

    def on_mouse_up(self, event):
        if not self.picking_center and self.start_x and self.start_y:
            x1, y1 = self.start_x, self.start_y
            x2, y2 = event.x, event.y
            if x1 > x2: x1, x2 = x2, x1
            if y1 > y2: y1, y2 = y2, y1
            self.stamp_bbox = (x1, y1, x2, y2)
            self.bbox_label.config(text=f"({x1}, {y1}) -> ({x2}, {y2})", foreground="green")
            self.log(f"Đã khoanh vùng trang {self.current_page_num+1}: {self.stamp_bbox}")
            
            if self.canvas_rect:
                self.canvas.delete(self.canvas_rect)
            self.canvas_rect = self.canvas.create_rectangle(
                x1, y1, x2, y2, outline="red", width=2
            )
            
            self.create_template_from_bbox()
            self.create_temp_cropped_image()
            
            self.stamp_center = None
            if self.center_mark:
                self.canvas.delete(self.center_mark)
            self.center_label.config(text="Chưa xác định", foreground="blue")
            
            self.start_x = None
            self.start_y = None

    def create_template_from_bbox(self):
        if not self.stamp_bbox or not self.display_image:
            return False
        
        try:
            original_img = self.page_images_original[self.current_page_num]
            
            x1 = int(self.stamp_bbox[0] * self.display_scale_x)
            y1 = int(self.stamp_bbox[1] * self.display_scale_y)
            x2 = int(self.stamp_bbox[2] * self.display_scale_x)
            y2 = int(self.stamp_bbox[3] * self.display_scale_y)
            
            x1 = max(0, min(x1, original_img.width))
            y1 = max(0, min(y1, original_img.height))
            x2 = max(0, min(x2, original_img.width))
            y2 = max(0, min(y2, original_img.height))
            
            if x1 >= x2 or y1 >= y2:
                return False
            
            self.template_image_original = original_img.crop((x1, y1, x2, y2))
            
            display_template = self.template_image_original.copy()
            display_template.thumbnail((100, 100))
            self.template_image = display_template
            
            self.log(f"Đã tạo ảnh mẫu kích thước: {self.template_image_original.size}")
            return True
        except Exception as e:
            self.log(f"Lỗi tạo ảnh mẫu: {e}")
            return False

    def create_temp_cropped_image(self):
        if not self.stamp_bbox or not self.display_image:
            return
        
        try:
            original_img = self.page_images_original[self.current_page_num]
            
            x1 = int(self.stamp_bbox[0] * self.display_scale_x)
            y1 = int(self.stamp_bbox[1] * self.display_scale_y)
            x2 = int(self.stamp_bbox[2] * self.display_scale_x)
            y2 = int(self.stamp_bbox[3] * self.display_scale_y)
            
            x1 = max(0, min(x1, original_img.width))
            y1 = max(0, min(y1, original_img.height))
            x2 = max(0, min(x2, original_img.width))
            y2 = max(0, min(y2, original_img.height))
            
            if x1 >= x2 or y1 >= y2:
                self.log("Vùng khoanh không hợp lệ!")
                return
            
            cropped_img = original_img.crop((x1, y1, x2, y2))
            
            draw = ImageDraw.Draw(cropped_img)
            draw.rectangle([(0, 0), (cropped_img.width-1, cropped_img.height-1)], outline="red", width=3)
            
            temp_dir = os.path.join(self.script_dir, "temp")
            os.makedirs(temp_dir, exist_ok=True)
            temp_img_path = os.path.join(temp_dir, "temp_cropped.png")
            cropped_img.save(temp_img_path)
            self.temp_cropped_image = temp_img_path
            
            self.display_temp_preview()
        except Exception as e:
            self.log(f"Lỗi tạo ảnh tạm: {e}")

    def display_temp_preview(self):
        if self.temp_cropped_image and os.path.exists(self.temp_cropped_image):
            try:
                img = Image.open(self.temp_cropped_image)
                
                canvas_width = self.preview_canvas.winfo_width()
                canvas_height = self.preview_canvas.winfo_height()
                
                if canvas_width <= 1:
                    canvas_width = 550
                    canvas_height = 700
                
                img_ratio = img.width / img.height
                canvas_ratio = canvas_width / canvas_height
                
                if img_ratio > canvas_ratio:
                    new_width = canvas_width - 40
                    new_height = int(new_width / img_ratio)
                else:
                    new_height = canvas_height - 40
                    new_width = int(new_height * img_ratio)
                
                img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                preview_img = ImageTk.PhotoImage(img_resized)
                
                self.preview_canvas.delete("all")
                self.preview_canvas.create_image(canvas_width//2, canvas_height//2, anchor=tk.CENTER, image=preview_img)
                self.preview_canvas.image = preview_img
                self.preview_info.config(text="Đã khoanh vùng - Chờ chọn tâm và xem trước dấu", foreground="blue")
            except Exception as e:
                self.log(f"Lỗi hiển thị preview: {e}")

    def draw_center_mark(self):
        if self.center_mark:
            self.canvas.delete(self.center_mark)
        if self.stamp_center:
            x, y = self.stamp_center
            size = 10
            self.center_mark = self.canvas.create_line(
                x - size, y, x + size, y,
                fill="blue", width=2
            )
            self.canvas.create_line(
                x, y - size, x, y + size,
                fill="blue", width=2
            )

    def calculate_exact_position(self):
        if not self.stamp_bbox or not self.stamp_center:
            return False
        
        if not self.current_page:
            return False
        
        canvas_width = self.display_image.width()
        canvas_height = self.display_image.height()
        pdf_rect = self.current_page.rect
        
        scale_x = pdf_rect.width / canvas_width
        scale_y = pdf_rect.height / canvas_height
        
        center_x_pdf = self.stamp_center[0] * scale_x
        center_y_pdf = self.stamp_center[1] * scale_y
        
        self.exact_center = (center_x_pdf, center_y_pdf)
        self.log(f"Đã tính vị trí chính xác trên PDF: tâm tại ({center_x_pdf:.2f}, {center_y_pdf:.2f})")
        return True

    def update_scale_from_entry(self):
        try:
            value = float(self.scale_entry.get())
            if 0.1 <= value <= 300:
                self.scale_percent.set(value)
                self.log(f"Đã cập nhật tỉ lệ: {value}%")
            else:
                self.log("Tỉ lệ phải trong khoảng 0.1% - 300%")
        except ValueError:
            self.log("Vui lòng nhập số hợp lệ")

    def preview_stamp_on_pdf(self):
        """Xem trước con dấu - HIỂN THỊ ẢNH PNG từ vùng khoanh và con dấu"""
        if not self.exact_center and not self.use_template_matching.get():
            self.log("Chưa có vị trí đóng dấu! Hãy khoanh vùng và chọn tâm trước.")
            return
        
        if not self.stamp_image_path.get():
            self.log("Chưa chọn ảnh con dấu!")
            return
        
        if not self.temp_cropped_image or not os.path.exists(self.temp_cropped_image):
            self.log("Chưa có ảnh vùng khoanh! Hãy khoanh vùng trước.")
            return
        
        try:
            # Đọc ảnh vùng khoanh
            base_img = Image.open(self.temp_cropped_image)
            
            # Đọc và xử lý ảnh con dấu
            stamp_img = Image.open(self.stamp_image_path.get())
            
            # Chuyển đổi ảnh con dấu sang RGBA nếu cần
            if stamp_img.mode in ('P', 'PA'):
                stamp_img = stamp_img.convert('RGBA')
            elif stamp_img.mode == 'RGB':
                stamp_img = stamp_img.convert('RGBA')
            
            # Tính kích thước hiển thị của con dấu (dựa trên tỉ lệ)
            scale = self.scale_percent.get() / 100.0
            new_width = int(stamp_img.width * scale)
            new_height = int(stamp_img.height * scale)
            
            if new_width > 0 and new_height > 0:
                # Resize ảnh con dấu để hiển thị preview
                stamp_img_resized = stamp_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            else:
                self.log("Kích thước ảnh con dấu quá nhỏ!")
                return
            
            # Tính vị trí đặt con dấu trong ảnh vùng khoanh
            if self.stamp_center:
                # Tọa độ tâm trong ảnh gốc
                center_in_original_x = self.stamp_center[0] * self.display_scale_x
                center_in_original_y = self.stamp_center[1] * self.display_scale_y
                
                # Tọa độ góc trên trái của vùng khoanh trong ảnh gốc
                x1_original = self.stamp_bbox[0] * self.display_scale_x
                y1_original = self.stamp_bbox[1] * self.display_scale_y
                
                # Tọa độ tâm trong ảnh đã cắt
                center_in_crop_x = center_in_original_x - x1_original
                center_in_crop_y = center_in_original_y - y1_original
                
                # Vị trí dán ảnh (góc trên trái)
                paste_x = int(center_in_crop_x - new_width/2)
                paste_y = int(center_in_crop_y - new_height/2)
                
                # Tạo bản sao để vẽ
                result_img = base_img.copy()
                
                # Dán ảnh con dấu lên ảnh kết quả
                if stamp_img_resized.mode == 'RGBA':
                    result_img.paste(stamp_img_resized, (paste_x, paste_y), stamp_img_resized)
                else:
                    result_img.paste(stamp_img_resized, (paste_x, paste_y))
                
                # Vẽ khung đỏ và tâm xanh lên ảnh kết quả
                draw = ImageDraw.Draw(result_img)
                # Khung đỏ
                draw.rectangle([(0, 0), (result_img.width-1, result_img.height-1)], outline="red", width=3)
                # Dấu + xanh tại tâm
                draw.line([(center_in_crop_x-10, center_in_crop_y), (center_in_crop_x+10, center_in_crop_y)], fill="blue", width=2)
                draw.line([(center_in_crop_x, center_in_crop_y-10), (center_in_crop_x, center_in_crop_y+10)], fill="blue", width=2)
                
                # Hiển thị lên canvas preview
                canvas_width = self.preview_canvas.winfo_width()
                canvas_height = self.preview_canvas.winfo_height()
                
                if canvas_width <= 1:
                    canvas_width = 550
                    canvas_height = 700
                
                # Resize ảnh kết quả để vừa canvas
                img_ratio = result_img.width / result_img.height
                canvas_ratio = canvas_width / canvas_height
                
                if img_ratio > canvas_ratio:
                    new_width_display = canvas_width - 40
                    new_height_display = int(new_width_display / img_ratio)
                else:
                    new_height_display = canvas_height - 40
                    new_width_display = int(new_height_display * img_ratio)
                
                result_img_resized = result_img.resize((new_width_display, new_height_display), Image.Resampling.LANCZOS)
                preview_img = ImageTk.PhotoImage(result_img_resized)
                
                self.preview_canvas.delete("all")
                self.preview_canvas.create_image(canvas_width//2, canvas_height//2, anchor=tk.CENTER, image=preview_img)
                self.preview_canvas.image = preview_img
                self.preview_info.config(text=f"Xem trước với tỉ lệ {self.scale_percent.get()}%", foreground="green")
                self.log(f"Đã tạo xem trước với tỉ lệ {self.scale_percent.get()}%")
            else:
                self.log("Chưa có tâm con dấu! Hãy chọn tâm trước khi xem trước.")
                
        except Exception as e:
            self.log(f"Lỗi xem trước: {e}")
            import traceback
            self.log(traceback.format_exc())

    def find_best_match_position(self, page_image):
        if not self.template_image_original or not self.use_template_matching.get():
            return None
        
        try:
            template = self.template_image_original
            
            if template.mode == 'RGBA':
                template_rgb = Image.new('RGB', template.size, (255, 255, 255))
                template_rgb.paste(template, mask=template.split()[3] if template.mode == 'RGBA' else None)
                template_gray = cv2.cvtColor(np.array(template_rgb), cv2.COLOR_RGB2GRAY)
            else:
                template_gray = cv2.cvtColor(np.array(template), cv2.COLOR_RGB2GRAY)
            
            if page_image.mode == 'RGBA':
                page_rgb = Image.new('RGB', page_image.size, (255, 255, 255))
                page_rgb.paste(page_image, mask=page_image.split()[3] if page_image.mode == 'RGBA' else None)
                page_gray = cv2.cvtColor(np.array(page_rgb), cv2.COLOR_RGB2GRAY)
            else:
                page_gray = cv2.cvtColor(np.array(page_image), cv2.COLOR_RGB2GRAY)
            
            result = cv2.matchTemplate(page_gray, template_gray, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            threshold = self.match_threshold.get() / 100.0
            
            if max_val >= threshold:
                h, w = template_gray.shape
                top_left = max_loc
                center_x = top_left[0] + w // 2
                center_y = top_left[1] + h // 2
                self.log(f"Tìm thấy vị trí với độ tương đồng: {max_val*100:.2f}%")
                return (center_x, center_y)
            else:
                self.log(f"Không tìm thấy vị trí phù hợp (độ tương đồng cao nhất: {max_val*100:.2f}%)")
                return None
        except Exception as e:
            self.log(f"Lỗi template matching: {e}")
            return None

    def add_stamp_to_pdf(self, input_pdf, output_pdf, stamp_path, scale_percent, position_center=None):
        """
        Chèn ảnh con dấu vào PDF - NHÚNG ẢNH GỐC, KHÔNG RESIZE TRƯỚC
        Để PDF viewer tự xử lý scale khi render - chất lượng cao nhất
        """
        try:
            temp_output = None
            if input_pdf == output_pdf:
                temp_output = os.path.join(self.script_dir, "temp_stamped.pdf")
                output_path = temp_output
            else:
                output_path = output_pdf
            
            doc = fitz.open(input_pdf)
            
            # Đọc ảnh gốc và CHUYỂN ĐỔI sang RGBA để tránh lỗi Palette
            img = Image.open(stamp_path)
            
            # XỬ LÝ LỖI PALETTE MODE - ĐÂY LÀ PHẦN QUAN TRỌNG NHẤT
            if img.mode in ('P', 'PA'):
                self.log(f"Phát hiện ảnh Palette mode ({img.mode}), chuyển sang RGBA...")
                img = img.convert('RGBA')
            elif img.mode == 'RGB':
                # Chuyển sang RGBA để hỗ trợ trong suốt nếu cần
                img = img.convert('RGBA')
            elif img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            original_width = img.width
            original_height = img.height
            
            # Tính kích thước hiển thị dựa trên tỉ lệ
            scale = scale_percent / 100.0
            display_width = original_width * scale
            display_height = original_height * scale
            
            # Lưu ảnh tạm (đã được chuyển sang RGBA)
            temp_img_path = os.path.join(self.script_dir, "temp_stamp.png")
            img.save(temp_img_path, "PNG", optimize=False)
            
            if self.use_template_matching.get() and self.template_image_original:
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    
                    mat = fitz.Matrix(2.0, 2.0)
                    pix = page.get_pixmap(matrix=mat)
                    img_data = pix.tobytes("png")
                    page_img = Image.open(io.BytesIO(img_data))
                    
                    match_pos = self.find_best_match_position(page_img)
                    
                    if match_pos:
                        scale_to_pdf = page.rect.width / page_img.width
                        center_x_pdf = match_pos[0] * scale_to_pdf
                        center_y_pdf = match_pos[1] * scale_to_pdf
                        
                        if self.stamp_center:
                            template_center_x = self.template_image_original.width / 2
                            template_center_y = self.template_image_original.height / 2
                            
                            selected_center_x = (self.stamp_center[0] * self.display_scale_x) - (self.stamp_bbox[0] * self.display_scale_x)
                            selected_center_y = (self.stamp_center[1] * self.display_scale_y) - (self.stamp_bbox[1] * self.display_scale_y)
                            
                            offset_x = (selected_center_x - template_center_x) * scale_to_pdf
                            offset_y = (selected_center_y - template_center_y) * scale_to_pdf
                            
                            center_x_pdf += offset_x
                            center_y_pdf += offset_y
                        
                        # Tạo rect với kích thước hiển thị - nhúng ảnh gốc
                        img_rect = fitz.Rect(
                            center_x_pdf - display_width/2,
                            center_y_pdf - display_height/2,
                            center_x_pdf + display_width/2,
                            center_y_pdf + display_height/2
                        )
                        # Nhúng ảnh gốc (đã chuyển sang RGBA)
                        page.insert_image(img_rect, filename=temp_img_path)
                        self.log(f"Trang {page_num+1}: Đã đóng dấu (ảnh {original_width}x{original_height}, hiển thị {scale_percent}%)")
                    else:
                        self.log(f"Trang {page_num+1}: Không tìm thấy vị trí phù hợp, bỏ qua")
            else:
                if not position_center:
                    self.log("Chưa có vị trí đóng dấu!")
                    return False
                
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    img_rect = fitz.Rect(
                        position_center[0] - display_width/2,
                        position_center[1] - display_height/2,
                        position_center[0] + display_width/2,
                        position_center[1] + display_height/2
                    )
                    page.insert_image(img_rect, filename=temp_img_path)
                    self.log(f"Trang {page_num+1}: Đã đóng dấu tại tọa độ cố định (ảnh {original_width}x{original_height}, hiển thị {scale_percent}%)")
            
            doc.save(output_path)
            doc.close()
            os.remove(temp_img_path)
            
            if temp_output and os.path.exists(temp_output):
                shutil.move(temp_output, input_pdf)
            
            return True
        except Exception as e:
            self.log(f"Lỗi đóng dấu: {e}")
            import traceback
            self.log(traceback.format_exc())
            return False

    def test_stamp(self):
        if not self.validate_inputs():
            return
        
        if not self.use_template_matching.get() and not self.exact_center:
            self.log("Chưa có vị trí đóng dấu! Hãy khoanh vùng và chọn tâm trước.")
            return
        
        if self.use_template_matching.get() and not self.template_image_original:
            self.log("Chưa có ảnh mẫu! Hãy khoanh vùng trước.")
            return
            
        output_path = filedialog.asksaveasfilename(
            defaultextension=".pdf", 
            filetypes=[("PDF files", "*.pdf")],
            initialfile="test_stamped.pdf"
        )
        if not output_path:
            return
        
        temp_doc = fitz.open(self.pdf_sample_path.get())
        total_test_pages = len(temp_doc)
        temp_doc.close()
        
        self.log(f"Bắt đầu test trên {total_test_pages} trang với ảnh gốc (không resize)...")
        
        if self.add_stamp_to_pdf(self.pdf_sample_path.get(), output_path,
                                 self.stamp_image_path.get(), self.scale_percent.get(), self.exact_center):
            self.log(f"Test thành công! Đã xử lý {total_test_pages} trang. File lưu tại: {output_path}")
            
            if sys.platform == "win32":
                os.startfile(output_path)
            elif sys.platform == "darwin":
                subprocess.run(["open", output_path])
            else:
                subprocess.run(["xdg-open", output_path])
        else:
            self.log("Test thất bại!")

    def start_stamp_all(self):
        if not self.validate_inputs():
            return
        
        if not self.use_template_matching.get() and not self.exact_center:
            self.log("Chưa có vị trí đóng dấu! Hãy khoanh vùng và chọn tâm trước.")
            return
        
        if self.use_template_matching.get() and not self.template_image_original:
            self.log("Chưa có ảnh mẫu! Hãy khoanh vùng trước.")
            return
            
        folder = self.folder_path.get()
        if not os.path.isdir(folder):
            self.log("Thư mục không hợp lệ!")
            return

        pdf_files = [f for f in os.listdir(folder) if f.lower().endswith(".pdf")]
        
        if not pdf_files:
            self.log("Không tìm thấy file PDF nào trong thư mục!")
            return

        if not messagebox.askyesno("Xác nhận", 
                                   f"Bạn có chắc muốn đóng dấu {len(pdf_files)} file PDF?\n\n"
                                   "Các file sẽ bị GHI ĐÈ. Bạn nên backup trước khi tiếp tục.\n\n"
                                   "Chế độ: Nhúng ảnh gốc - Chất lượng cao nhất"):
            self.log("Đã hủy thao tác đóng dấu hàng loạt.")
            return

        success_count = 0
        for pdf_file in pdf_files:
            input_path = os.path.join(folder, pdf_file)
            
            temp_doc = fitz.open(input_path)
            page_count = len(temp_doc)
            temp_doc.close()
            
            self.log(f"Đang xử lý: {pdf_file} ({page_count} trang) - nhúng ảnh gốc...")
            
            if self.add_stamp_to_pdf(input_path, input_path,
                                     self.stamp_image_path.get(), self.scale_percent.get(), self.exact_center):
                self.log(f"✓ Đã đóng dấu: {pdf_file}")
                success_count += 1
            else:
                self.log(f"✗ Lỗi khi đóng dấu: {pdf_file}")
        
        self.log(f"Hoàn tất! Đã đóng dấu thành công {success_count}/{len(pdf_files)} file.")
        messagebox.showinfo("Hoàn thành", f"Đã đóng dấu thành công {success_count}/{len(pdf_files)} file PDF\n\nChế độ: Ảnh gốc - Chất lượng cao")

    def validate_inputs(self):
        if not self.folder_path.get():
            self.log("Chưa chọn thư mục!")
            return False
        if not self.pdf_sample_path.get() or not os.path.exists(self.pdf_sample_path.get()):
            self.log("PDF mẫu không hợp lệ!")
            return False
        if not self.stamp_image_path.get() or not os.path.exists(self.stamp_image_path.get()):
            self.log("Ảnh con dấu không hợp lệ!")
            return False
        return True

    def save_config(self):
        if not self.stamp_bbox:
            self.log("Chưa có vùng khoanh! Hãy khoanh vùng trước khi lưu.")
            messagebox.showwarning("Chưa có dữ liệu", "Vui lòng khoanh vùng trước khi lưu cấu hình!")
            return
        
        script_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
        default_name = f"{script_name}_KhoanhVung"
        
        name = simpledialog.askstring("Lưu cấu hình", 
                                      f"Nhập tên cấu hình (mặc định: {default_name}):\n\n"
                                      f"Ảnh vùng khoanh sẽ được lưu tại:\n"
                                      f"{self.script_dir}/img/[TÊN]/KhoanhVung.png\n\n"
                                      f"Cấu hình sẽ được lưu tại:\n"
                                      f"{self.script_dir}/stamp_configs/[TÊN].json",
                                      initialvalue=default_name,
                                      parent=self.root)
        
        if not name:
            self.log("Đã hủy lưu cấu hình")
            return
        
        self.config_name = name
        
        img_dir = os.path.join(self.script_dir, "img", self.config_name)
        os.makedirs(img_dir, exist_ok=True)
        
        if self.display_image:
            original_img = self.page_images_original[self.current_page_num]
            
            x1 = int(self.stamp_bbox[0] * self.display_scale_x)
            y1 = int(self.stamp_bbox[1] * self.display_scale_y)
            x2 = int(self.stamp_bbox[2] * self.display_scale_x)
            y2 = int(self.stamp_bbox[3] * self.display_scale_y)
            
            x1 = max(0, min(x1, original_img.width))
            y1 = max(0, min(y1, original_img.height))
            x2 = max(0, min(x2, original_img.width))
            y2 = max(0, min(y2, original_img.height))
            
            cropped_img = original_img.crop((x1, y1, x2, y2))
            
            draw = ImageDraw.Draw(cropped_img)
            draw.rectangle([(0, 0), (cropped_img.width-1, cropped_img.height-1)], outline="red", width=3)
            if self.stamp_center:
                center_in_original_x = self.stamp_center[0] * self.display_scale_x
                center_in_original_y = self.stamp_center[1] * self.display_scale_y
                center_rel_x = center_in_original_x - x1
                center_rel_y = center_in_original_y - y1
                if 0 <= center_rel_x < cropped_img.width and 0 <= center_rel_y < cropped_img.height:
                    draw.line([(center_rel_x-10, center_rel_y), (center_rel_x+10, center_rel_y)], fill="blue", width=2)
                    draw.line([(center_rel_x, center_rel_y-10), (center_rel_x, center_rel_y+10)], fill="blue", width=2)
            
            img_path = os.path.join(img_dir, "KhoanhVung.png")
            cropped_img.save(img_path)
            self.log(f"Đã lưu ảnh vùng khoanh tại: {img_path}")
        
        exact_center_tuple = None
        if self.exact_center:
            exact_center_tuple = (self.exact_center[0], self.exact_center[1])
            
        config = {
            "folder_path": self.folder_path.get(),
            "pdf_sample_path": self.pdf_sample_path.get(),
            "stamp_image_path": self.stamp_image_path.get(),
            "stamp_bbox": self.stamp_bbox,
            "stamp_center": self.stamp_center,
            "exact_center": exact_center_tuple,
            "scale_percent": self.scale_percent.get(),
            "match_threshold": self.match_threshold.get(),
            "file_format": self.file_format.get(),
            "page_number": self.current_page_num,
            "use_template_matching": self.use_template_matching.get()
        }
        
        config_dir = os.path.join(self.script_dir, "stamp_configs")
        os.makedirs(config_dir, exist_ok=True)
        
        config_path = os.path.join(config_dir, f"{name}.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        
        self.log(f"✓ Đã lưu cấu hình: {name}")
        messagebox.showinfo("Lưu thành công", f"Đã lưu cấu hình '{name}' thành công!\n\nẢnh: {img_dir}/KhoanhVung.png")
        self.refresh_category_list()

    def load_config(self, name=None):
        if not name:
            return
            
        config_path = os.path.join(self.script_dir, "stamp_configs", f"{name}.json")
        
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            self.config_name = name
            self.folder_path.set(config.get("folder_path", ""))
            self.pdf_sample_path.set(config.get("pdf_sample_path", ""))
            self.stamp_image_path.set(config.get("stamp_image_path", ""))
            self.stamp_bbox = tuple(config["stamp_bbox"]) if config.get("stamp_bbox") else None
            self.stamp_center = tuple(config["stamp_center"]) if config.get("stamp_center") else None
            
            exact_center = config.get("exact_center")
            if exact_center:
                self.exact_center = (exact_center[0], exact_center[1])
            
            self.scale_percent.set(config.get("scale_percent", 100))
            self.match_threshold.set(config.get("match_threshold", 80))
            self.file_format.set(config.get("file_format", "pdf"))
            self.use_template_matching.set(config.get("use_template_matching", True))
            
            self.log(f"Đã tải cấu hình: {name}")
            
            if self.pdf_sample_path.get():
                self.load_pdf_preview(self.pdf_sample_path.get())
                page_num = config.get("page_number", 0)
                self.show_page(page_num)
                
                if self.stamp_bbox:
                    self.canvas_rect = self.canvas.create_rectangle(
                        self.stamp_bbox[0], self.stamp_bbox[1],
                        self.stamp_bbox[2], self.stamp_bbox[3],
                        outline="red", width=2
                    )
                    self.bbox_label.config(text=f"({self.stamp_bbox[0]}, {self.stamp_bbox[1]}) -> ({self.stamp_bbox[2]}, {self.stamp_bbox[3]})", foreground="green")
                    self.create_template_from_bbox()
                    self.create_temp_cropped_image()
                
                if self.stamp_center:
                    self.draw_center_mark()
                    self.center_label.config(text=f"Đã chọn tâm tại ({self.stamp_center[0]}, {self.stamp_center[1]})", foreground="green")
            
            if self.exact_center and self.stamp_image_path.get():
                self.preview_stamp_on_pdf()
            
            messagebox.showinfo("Tải thành công", f"Đã tải cấu hình '{name}' thành công!")

    def load_selected_config(self):
        selected = self.category_combo.get()
        if selected:
            self.load_config(selected)

    def delete_config(self):
        selected = self.category_combo.get()
        if not selected:
            self.log("Chưa chọn cấu hình để xóa!")
            return
            
        if messagebox.askyesno("Xóa cấu hình", f"Bạn có chắc muốn xóa cấu hình '{selected}'?"):
            config_path = os.path.join(self.script_dir, "stamp_configs", f"{selected}.json")
            img_path = os.path.join(self.script_dir, "img", selected)
            
            if os.path.exists(config_path):
                os.remove(config_path)
                self.log(f"Đã xóa file cấu hình: {selected}")
            
            if os.path.exists(img_path):
                shutil.rmtree(img_path)
                self.log(f"Đã xóa thư mục ảnh: img/{selected}")
            
            self.refresh_category_list()
            self.category_combo.set('')
            messagebox.showinfo("Xóa thành công", f"Đã xóa cấu hình '{selected}'")

    def refresh_category_list(self):
        config_dir = os.path.join(self.script_dir, "stamp_configs")
        
        if os.path.exists(config_dir):
            files = [f.replace(".json", "") for f in os.listdir(config_dir) if f.endswith(".json")]
            self.category_combo['values'] = files

    def cleanup_temp_file(self, filepath):
        """Xóa file tạm"""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except:
            pass

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

if __name__ == "__main__":
    root = tk.Tk()
    app = StampApp(root)
    root.mainloop()