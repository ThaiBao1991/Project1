import tkinter as tk
from tkinter import filedialog
import fitz  # PyMuPDF

class PDFViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple PDF Viewer")
        self.root.geometry("800x600")  # Kích thước mặc định của cửa sổ

        # Frame cho nút và ô nhập trang
        self.top_frame = tk.Frame(root)
        self.top_frame.pack(pady=5)

        # Nút mở file PDF
        self.open_button = tk.Button(self.top_frame, text="Open PDF", command=self.open_pdf)
        self.open_button.pack(side=tk.LEFT, padx=5)

        # Ô nhập số trang
        tk.Label(self.top_frame, text="Go to page:").pack(side=tk.LEFT, padx=5)
        self.page_entry = tk.Entry(self.top_frame, width=5)
        self.page_entry.pack(side=tk.LEFT, padx=5)
        self.go_button = tk.Button(self.top_frame, text="Go", command=self.go_to_page)
        self.go_button.pack(side=tk.LEFT, padx=5)

        # Frame chứa canvas và các thanh cuộn
        self.frame = tk.Frame(root)
        self.frame.pack(fill=tk.BOTH, expand=True)

        # Canvas để hiển thị nội dung PDF
        self.canvas = tk.Canvas(self.frame, bg="white")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Thanh cuộn dọc
        self.v_scrollbar = tk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Thanh cuộn ngang
        self.h_scrollbar = tk.Scrollbar(root, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Cấu hình canvas với cả hai thanh cuộn
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)

        # Biến lưu trữ file PDF và thông tin trang
        self.pdf_document = None
        self.page_images = []  # Lưu trữ ảnh của từng trang
        self.page_positions = []  # Lưu vị trí y của từng trang trên canvas
        self.zoom_level = 1.0  # Giá trị zoom mặc định ban đầu
        self.base_zoom = 1.0   # Zoom cơ bản để fit với màn hình
        self.current_page = 0  # Trang hiện tại

        # Bind các phím và sự kiện chuột
        self.root.bind("<Up>", self.scroll_up)
        self.root.bind("<Down>", self.scroll_down)
        self.root.bind("<Left>", self.scroll_left)
        self.root.bind("<Right>", self.scroll_right)
        self.root.bind("<Prior>", self.prev_page)  # PageUp
        self.root.bind("<Next>", self.next_page)   # PageDown
        self.root.bind("+", self.zoom_in)          # Phím +
        self.root.bind("-", self.zoom_out)         # Phím -
        self.root.bind("<Return>", lambda event: self.go_to_page())  # Phím Enter để nhảy trang
        self.canvas.bind("<Configure>", self.resize_pdf)  # Thay đổi kích thước khi cửa sổ thay đổi
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)  # Cuộn chuột

    def open_pdf(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if file_path:
            self.pdf_document = fitz.open(file_path)
            self.adjust_zoom_to_fit()  # Tự động điều chỉnh zoom khi mở file
            self.load_all_pages()
            self.current_page = 0  # Đặt trang đầu tiên
            self.page_entry.delete(0, tk.END)  # Xóa nội dung cũ trong ô nhập
            self.page_entry.insert(0, "1")  # Hiển thị trang 1 mặc định

    def adjust_zoom_to_fit(self):
        if not self.pdf_document:
            return

        # Lấy kích thước của trang đầu tiên
        page = self.pdf_document[0]
        page_rect = page.rect  # Kích thước gốc của trang (width, height)
        page_width = page_rect.width

        # Lấy kích thước của canvas (cửa sổ hiển thị)
        canvas_width = self.canvas.winfo_width()
        if canvas_width <= 1:  # Nếu canvas chưa có kích thước
            canvas_width = 800

        # Tính tỷ lệ zoom để vừa với chiều rộng màn hình
        self.base_zoom = (canvas_width / page_width) * 0.9  # Giảm 10% để có lề
        self.zoom_level = self.base_zoom  # Đặt zoom ban đầu

    def load_all_pages(self):
        if not self.pdf_document:
            return

        self.canvas.delete("all")  # Xóa nội dung cũ
        self.page_images.clear()   # Xóa danh sách ảnh cũ
        self.page_positions.clear()  # Xóa vị trí trang cũ

        y_position = 0  # Vị trí y bắt đầu
        for page_num in range(len(self.pdf_document)):
            page = self.pdf_document[page_num]
            pix = page.get_pixmap(matrix=fitz.Matrix(self.zoom_level, self.zoom_level))
            img_data = pix.tobytes("ppm")  # Chuyển thành định dạng ảnh PPM

            # Tạo đối tượng PhotoImage từ dữ liệu ảnh
            photo = tk.PhotoImage(data=img_data)
            self.page_images.append(photo)  # Lưu lại ảnh

            # Thêm ảnh vào canvas
            self.canvas.create_image(0, y_position, image=photo, anchor=tk.NW)
            self.page_positions.append(y_position)  # Lưu vị trí y của trang

            # Cập nhật vị trí y cho trang tiếp theo
            y_position += pix.height + 10  # Thêm khoảng cách 10px giữa các trang

        # Cập nhật vùng cuộn của canvas
        self.canvas.config(scrollregion=(0, 0, pix.width, y_position))

        # Cập nhật tiêu đề ban đầu
        self.root.title(f"Simple PDF Viewer - Page 1/{len(self.pdf_document)} (Zoom: {self.zoom_level:.1f}x)")

    def resize_pdf(self, event):
        # Tự động điều chỉnh kích thước khi cửa sổ thay đổi
        if self.pdf_document:
            self.adjust_zoom_to_fit()  # Cập nhật lại zoom khi thay đổi kích thước cửa sổ
            self.zoom_level = self.base_zoom  # Reset zoom về mức fit
            self.load_all_pages()
            self.update_current_page()  # Cập nhật lại ô nhập sau khi resize

    def scroll_up(self, event):
        self.canvas.yview_scroll(-1, "units")
        self.update_current_page()

    def scroll_down(self, event):
        self.canvas.yview_scroll(1, "units")
        self.update_current_page()

    def scroll_left(self, event):
        self.canvas.xview_scroll(-1, "units")

    def scroll_right(self, event):
        self.canvas.xview_scroll(1, "units")

    def on_mousewheel(self, event):
        # Cuộn chuột lên/xuống
        self.canvas.yview_scroll(-1 * (event.delta // 120), "units")
        self.update_current_page()

    def prev_page(self, event):
        # Cuộn đến trang trước
        if self.pdf_document:
            current_y = self.canvas.canvasy(0)
            for i in range(len(self.page_positions) - 1, -1, -1):
                if self.page_positions[i] < current_y:
                    self.canvas.yview_moveto(self.page_positions[i] / self.canvas.bbox(tk.ALL)[3])
                    self.update_current_page()
                    break

    def next_page(self, event):
        # Cuộn đến trang tiếp theo
        if self.pdf_document:
            current_y = self.canvas.canvasy(0)
            for i in range(len(self.page_positions)):
                if self.page_positions[i] > current_y + 10:  # +10 để tránh nhầm khi gần mép
                    self.canvas.yview_moveto(self.page_positions[i] / self.canvas.bbox(tk.ALL)[3])
                    self.update_current_page()
                    break

    def zoom_in(self, event):
        # Tăng mức zoom (phóng to)
        self.zoom_level += 0.2
        if self.zoom_level > 5.0:  # Giới hạn zoom tối đa
            self.zoom_level = 5.0
        if self.pdf_document:
            self.load_all_pages()
            self.update_current_page()  # Cập nhật lại ô nhập sau khi zoom

    def zoom_out(self, event):
        # Giảm mức zoom (thu nhỏ)
        self.zoom_level -= 0.2
        if self.zoom_level < 0.2:  # Giới hạn zoom tối thiểu
            self.zoom_level = 0.2
        if self.pdf_document:
            self.load_all_pages()
            self.update_current_page()  # Cập nhật lại ô nhập sau khi zoom

    def update_current_page(self):
        # Cập nhật trang hiện tại dựa trên vị trí cuộn
        if self.pdf_document:
            current_y = self.canvas.canvasy(0)  # Vị trí y hiện tại trên canvas
            canvas_height = self.canvas.winfo_height()
            current_page = 0

            # Xác định trang đang ở giữa màn hình
            for i, pos in enumerate(self.page_positions):
                if pos <= current_y + canvas_height / 2 < pos + self.page_images[i].height():
                    current_page = i
                    break
                elif i == len(self.page_positions) - 1 and current_y + canvas_height / 2 >= pos:
                    current_page = i

            self.current_page = current_page
            self.root.title(f"Simple PDF Viewer - Page {self.current_page + 1}/{len(self.pdf_document)} (Zoom: {self.zoom_level:.1f}x)")
            # Cập nhật ô nhập trang
            self.page_entry.delete(0, tk.END)
            self.page_entry.insert(0, str(self.current_page + 1))

    def go_to_page(self):
        # Nhảy đến trang được nhập trong ô
        if not self.pdf_document:
            return

        try:
            page_num = int(self.page_entry.get()) - 1  # Chuyển về chỉ số 0-based
            if 0 <= page_num < len(self.pdf_document):
                # Cuộn đến vị trí của trang được nhập
                self.canvas.yview_moveto(self.page_positions[page_num] / self.canvas.bbox(tk.ALL)[3])
                self.update_current_page()  # Cập nhật tiêu đề và ô nhập
            else:
                tk.messagebox.showwarning("Warning", f"Page number must be between 1 and {len(self.pdf_document)}")
        except ValueError:
            tk.messagebox.showwarning("Warning", "Please enter a valid page number")

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFViewer(root)
    root.mainloop()