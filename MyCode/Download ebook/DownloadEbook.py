import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from bs4 import BeautifulSoup
from PIL import Image
import os
import time
import requests
import shutil
import threading
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

CONFIG_FILE = "ebook_config.json"

class EBookDownloaderApp:
    def __init__(self, master):
        self.master = master
        master.title("Ebook Downloader")
        master.geometry("700x600")
        master.resizable(True, True)

        self.driver = None
        self.clicked_next_button_element = None
        self.stop_flag = False  # Cờ để dừng tải ảnh khi cần

        self.url_var = tk.StringVar()
        self.output_folder_var = tk.StringVar()
        self.pdf_name_var = tk.StringVar(value="ebook_combined.pdf")

        self.load_config()
        self.create_widgets()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.url_var.set(data.get("url", ""))
                    self.output_folder_var.set(data.get("output_folder", ""))
                    self.pdf_name_var.set(data.get("pdf_name", "ebook_combined.pdf"))
            except:
                pass

    def save_config(self):
        data = {
            "url": self.url_var.get(),
            "output_folder": self.output_folder_var.get(),
            "pdf_name": self.pdf_name_var.get()
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(data, f)

    def create_widgets(self):
        url_frame = tk.LabelFrame(self.master, text="Thông tin Ebook", padx=10, pady=10)
        url_frame.pack(padx=10, pady=5, fill="x")

        tk.Label(url_frame, text="URL trang sách:").grid(row=0, column=0, sticky="w", pady=2)
        tk.Entry(url_frame, textvariable=self.url_var, width=60).grid(row=0, column=1, sticky="ew", pady=2)

        tk.Label(url_frame, text="Tên file PDF (vd: ebook_combined.pdf):").grid(row=1, column=0, sticky="w", pady=2)
        tk.Entry(url_frame, textvariable=self.pdf_name_var, width=60).grid(row=1, column=1, sticky="ew", pady=2)

        output_frame = tk.LabelFrame(self.master, text="Thư mục Lưu", padx=10, pady=10)
        output_frame.pack(padx=10, pady=5, fill="x")

        tk.Label(output_frame, text="Chọn thư mục lưu ảnh và PDF:").grid(row=0, column=0, sticky="w", pady=2)
        tk.Entry(output_frame, textvariable=self.output_folder_var, width=50).grid(row=0, column=1, sticky="ew", pady=2)
        tk.Button(output_frame, text="Duyệt...", command=self.browse_output_folder).grid(row=0, column=2, padx=5, pady=2)

        control_frame = tk.Frame(self.master, padx=10, pady=10)
        control_frame.pack(padx=10, pady=5, fill="both", expand=True)

        tk.Button(control_frame, text="Bắt đầu Tải", command=self.start_download_thread, font=("Arial", 12, "bold")).pack(pady=10)
        tk.Button(control_frame, text="Dừng", command=self.stop_download, font=("Arial", 12)).pack(pady=5)

        self.log_text = scrolledtext.ScrolledText(control_frame, wrap=tk.WORD, height=15, state='disabled')
        self.log_text.pack(fill="both", expand=True)

    def browse_output_folder(self):
        folder_selected = filedialog.askdirectory(title="Chọn thư mục lưu")
        if folder_selected:
            self.output_folder_var.set(folder_selected)

    def log_message(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        self.master.update_idletasks()

    def start_download_thread(self):
        self.stop_flag = False
        self.download_thread = threading.Thread(target=self.download_ebook)
        self.download_thread.daemon = True
        self.download_thread.start()

    def stop_download(self):
        self.stop_flag = True
        if self.driver:
            try:
                self.driver.quit()
                self.log_message("Đã dừng quá trình tải.")
            except Exception as e:
                self.log_message(f"Lỗi khi đóng trình duyệt: {e}")
            finally:
                self.driver = None
        else:
            self.log_message("Không có quá trình tải nào đang chạy để dừng.")

    def download_image(self, url, output_path, index):
        """Hàm tải ảnh và trả về thông tin kết quả"""
        if self.stop_flag:
            return None
            
        try:
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()
            with open(output_path, 'wb') as out_file:
                shutil.copyfileobj(response.raw, out_file)
            return (True, index, output_path, url)
        except Exception as e:
            return (False, index, output_path, url, str(e))

    def download_ebook(self):
        url = self.url_var.get()
        output_folder = self.output_folder_var.get()
        pdf_output_name = self.pdf_name_var.get()

        if not url or not output_folder:
            messagebox.showerror("Lỗi", "Vui lòng nhập URL và chọn thư mục lưu.")
            return

        self.save_config()

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        pdf_output_path = os.path.join(output_folder, pdf_output_name)

        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")

        try:
            self.log_message("Đang khởi động trình duyệt...")
            self.driver = webdriver.Chrome(options=options)
            self.driver.get(url)

            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "e-book-flip__page__front__content"))
            )

            # Thiết lập lắng nghe sự kiện click
            self.driver.execute_script("""
                window._lastClicked = null;
                document.addEventListener('click', function(e) {
                    window._lastClicked = e.target;
                }, true);
            """)
            messagebox.showinfo("Chọn nút", "Hãy click vào nút 'Trang tiếp theo' trên trình duyệt, rồi nhấn OK.")

            # Chờ người dùng click rồi mới lấy phần tử
            time.sleep(0.5)
            clicked_element = self.driver.execute_script("return window._lastClicked;")
            if not clicked_element:
                messagebox.showerror("Lỗi", "Không nhận diện được nút bạn đã click.")
                return

            messagebox.showinfo("Sẵn sàng", "Hãy quay lại TRANG ĐẦU sách, sau đó nhấn OK để bắt đầu tải.")

            # ▶️ BẮT ĐẦU DUYỆT CÁC TRANG ĐỂ LẤY LINK ẢNH
            all_image_urls = []
            page_number = 1

            while not self.stop_flag:
                self.log_message(f"Đang xử lý trang {page_number}...")
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')

                img_tags = soup.select(
                    ".e-book-flip__page__front__content__image, .e-book-flip__page__back__content__image"
                )
                for img_tag in img_tags:
                    img_url = img_tag.get("src")
                    if img_url and img_url not in all_image_urls:
                        all_image_urls.append(img_url)
                        self.log_message(f"Tìm thấy ảnh: {img_url}")

                try:
                    self.driver.execute_script("arguments[0].scrollIntoView();", clicked_element)
                    time.sleep(0.8)
                    clicked_element.click()
                    time.sleep(2)
                    page_number += 1
                except Exception as e:
                    self.log_message(f"Không thể click nút tiếp theo (có thể đã hết trang): {e}")
                    break

            if self.stop_flag:
                self.log_message("Đã dừng quá trình tải theo yêu cầu.")
                return

            self.log_message(f"Tổng cộng tìm thấy {len(all_image_urls)} ảnh.")
            self.log_message("Bắt đầu tải ảnh (5 ảnh cùng lúc)...")

            # ▶️ TẢI ẢNH SONG SONG VỚI 5 LUỒNG
            downloaded_paths = [None] * len(all_image_urls)  # Giữ thứ tự các ảnh
            failed_downloads = 0
            max_workers = 5  # Số luồng tối đa

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Tạo danh sách các task tải ảnh
                futures = []
                for i, img_url in enumerate(all_image_urls):
                    img_path = os.path.join(output_folder, f"page_{i+1:04d}.jpg")
                    futures.append(executor.submit(self.download_image, img_url, img_path, i))

                # Xử lý kết quả khi các task hoàn thành
                for future in as_completed(futures):
                    result = future.result()
                    if result is None:  # Bị dừng
                        continue
                        
                    success, index, path, url, *error = result
                    if success:
                        downloaded_paths[index] = path
                        self.log_message(f"Đã tải xong ảnh {index+1}/{len(all_image_urls)}: {url}")
                    else:
                        failed_downloads += 1
                        self.log_message(f"Lỗi tải ảnh {index+1}: {url} - {error[0]}")

            # ▶️ TẠO PDF CHỈ VỚI CÁC ẢNH TẢI THÀNH CÔNG
            valid_images = [path for path in downloaded_paths if path is not None and os.path.exists(path)]
            
            if not valid_images:
                self.log_message("Không có ảnh nào được tải thành công.")
                messagebox.showwarning("Lỗi", "Không tải được ảnh nào.")
                return

            self.log_message(f"Đang tạo PDF từ {len(valid_images)} ảnh...")
            try:
                images = []
                for path in valid_images:
                    try:
                        img = Image.open(path).convert('RGB')
                        images.append(img)
                    except Exception as e:
                        self.log_message(f"Lỗi mở ảnh {path}: {e}")

                if images:
                    images[0].save(pdf_output_path, save_all=True, append_images=images[1:], quality=95)
                    self.log_message(f"Đã tạo PDF tại: {pdf_output_path}")
                    messagebox.showinfo("Hoàn tất", f"Tạo PDF thành công:\n{pdf_output_path}")

                    # Xóa các ảnh đã tải
                    for path in valid_images:
                        try:
                            os.remove(path)
                            self.log_message(f"Đã xóa ảnh: {path}")
                        except:
                            pass
                else:
                    self.log_message("Không có ảnh hợp lệ để tạo PDF.")
                    messagebox.showwarning("Lỗi", "Không có ảnh hợp lệ.")
            except Exception as e:
                self.log_message(f"Lỗi khi tạo PDF: {e}")
                messagebox.showerror("Lỗi", f"Không thể tạo PDF: {e}")

        except Exception as e:
            self.log_message(f"Lỗi nghiêm trọng: {e}")
            messagebox.showerror("Lỗi", str(e))
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
            self.log_message("Kết thúc quá trình tải.")


if __name__ == "__main__":
    root = tk.Tk()
    app = EBookDownloaderApp(root)
    root.mainloop()