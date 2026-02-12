import tkinter as tk
from tkinter import ttk
import pyautogui
from PIL import ImageGrab
import requests
import pyperclip
import io
import base64
from tkinter import messagebox

class OCRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OCR Tool - Kéo chọn vùng để quét")
        self.root.geometry("800x600")
        
        # Biến lưu vùng chọn
        self.start_x = None
        self.start_y = None
        self.current_x = None
        self.current_y = None
        self.rect = None
        
        # Tạo giao diện
        self.create_widgets()
        
        # Biến để theo dõi trạng thái kéo chọn
        self.selecting = False
        
    def create_widgets(self):
        # Frame chứa nút và kết quả
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Nút bắt đầu quét
        self.scan_btn = ttk.Button(main_frame, text="Quét vùng màn hình", command=self.start_selection)
        self.scan_btn.pack(pady=10)
        
        # Ô hiển thị kết quả
        self.result_text = tk.Text(main_frame, wrap=tk.WORD, height=20, font=('Arial', 12))
        self.result_text.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Nút copy kết quả
        copy_btn = ttk.Button(main_frame, text="Copy vào Clipboard", command=self.copy_to_clipboard)
        copy_btn.pack(pady=5)
        
        # Nút xóa kết quả
        clear_btn = ttk.Button(main_frame, text="Xóa kết quả", command=self.clear_result)
        clear_btn.pack(pady=5)
        
        # Label trạng thái
        self.status_label = ttk.Label(main_frame, text="Sẵn sàng", foreground="green")
        self.status_label.pack()
    
    def start_selection(self):
        self.status_label.config(text="Đang chờ chọn vùng...", foreground="blue")
        self.root.withdraw()  # Ẩn cửa sổ chính
        
        # Tạo cửa sổ trong suốt toàn màn hình
        self.selection_window = tk.Toplevel()
        self.selection_window.attributes('-fullscreen', True)
        self.selection_window.attributes('-alpha', 0.3)
        self.selection_window.attributes('-topmost', True)
        self.selection_window.configure(background='black')
        
        # Canvas để vẽ hình chữ nhật chọn vùng
        self.canvas = tk.Canvas(self.selection_window, cursor="cross", bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bắt sự kiện chuột
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.selection_window.bind("<Escape>", self.cancel_selection)
        
        self.selecting = True
    
    def on_press(self, event):
        # Bắt đầu chọn vùng
        self.start_x = event.x
        self.start_y = event.y
        
        # Tạo hình chữ nhật
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline='red', width=2, fill='white'
        )
    
    def on_drag(self, event):
        # Cập nhật hình chữ nhật khi kéo chuột
        self.current_x, self.current_y = event.x, event.y
        self.canvas.coords(
            self.rect, self.start_x, self.start_y, self.current_x, self.current_y
        )
    
    def on_release(self, event):
        # Kết thúc chọn vùng
        self.current_x, self.current_y = event.x, event.y
        
        # Đảm bảo tọa độ hợp lệ
        x1, y1 = min(self.start_x, self.current_x), min(self.start_y, self.current_y)
        x2, y2 = max(self.start_x, self.current_x), max(self.start_y, self.current_y)
        
        # Đóng cửa sổ chọn vùng
        self.selection_window.destroy()
        self.root.deiconify()  # Hiện lại cửa sổ chính
        
        # Chụp ảnh vùng đã chọn
        self.capture_and_ocr(x1, y1, x2, y2)
    
    def cancel_selection(self, event=None):
        # Hủy chọn vùng
        if hasattr(self, 'selection_window'):
            self.selection_window.destroy()
        self.root.deiconify()
        self.status_label.config(text="Đã hủy chọn vùng", foreground="red")
        self.selecting = False
    
    def capture_and_ocr(self, x1, y1, x2, y2):
        self.status_label.config(text="Đang xử lý ảnh...", foreground="blue")
        self.root.update()
        
        try:
            # Chụp ảnh vùng đã chọn
            screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            
            # Chuyển ảnh sang base64 để gửi API
            buffered = io.BytesIO()
            screenshot.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            # Gọi API OCR.space
            api_key = 'helloworld'  # API key miễn phí
            payload = {
                'base64Image': f'data:image/png;base64,{img_base64}',
                'language': 'auto',
                'isOverlayRequired': False,
                'OCREngine': 2
            }
            
            response = requests.post(
                'https://api.ocr.space/parse/image',
                data=payload,
                headers={'apikey': api_key}
            )
            
            result = response.json()
            
            if result['IsErroredOnProcessing']:
                raise Exception(result['ErrorMessage'])
            
            # Lấy kết quả OCR
            parsed_text = result['ParsedResults'][0]['ParsedText']
            
            # Hiển thị kết quả
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, parsed_text)
            
            # Tự động copy vào clipboard
            pyperclip.copy(parsed_text)
            
            self.status_label.config(text="Hoàn thành! Đã copy vào clipboard", foreground="green")
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {str(e)}")
            self.status_label.config(text="Lỗi khi xử lý", foreground="red")
    
    def copy_to_clipboard(self):
        text = self.result_text.get(1.0, tk.END).strip()
        if text:
            pyperclip.copy(text)
            self.status_label.config(text="Đã copy vào clipboard", foreground="green")
        else:
            self.status_label.config(text="Không có nội dung để copy", foreground="red")
    
    def clear_result(self):
        self.result_text.delete(1.0, tk.END)
        self.status_label.config(text="Đã xóa kết quả", foreground="blue")

if __name__ == "__main__":
    root = tk.Tk()
    app = OCRApp(root)
    root.mainloop()