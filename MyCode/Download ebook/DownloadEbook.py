import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService # THÊM DÒNG NÀY
from bs4 import BeautifulSoup
from PIL import Image # Để xử lý ảnh và tạo PDF
import os
import time
import requests
import shutil
import threading # Để chạy tác vụ nặng mà không làm đơ giao diện

class EBookDownloaderApp:
    def __init__(self, master):
        self.master = master
        master.title("Ebook Downloader")
        master.geometry("700x600")
        master.resizable(True, True)

        self.driver = None

        self.url_var = tk.StringVar()
        self.output_folder_var = tk.StringVar()
        self.webdriver_path_var = tk.StringVar()
        self.headless_var = tk.BooleanVar(value=True)
        self.pdf_name_var = tk.StringVar(value="ebook_combined.pdf")

        self.create_widgets()

    def create_widgets(self):
        # ... (Phần tạo giao diện không đổi)
        url_frame = tk.LabelFrame(self.master, text="Thông tin Ebook", padx=10, pady=10)
        url_frame.pack(padx=10, pady=5, fill="x")

        tk.Label(url_frame, text="URL trang sách:").grid(row=0, column=0, sticky="w", pady=2)
        tk.Entry(url_frame, textvariable=self.url_var, width=60).grid(row=0, column=1, sticky="ew", pady=2)

        tk.Label(url_frame, text="Tên file PDF (vd: ebook_combined.pdf):").grid(row=1, column=0, sticky="w", pady=2)
        tk.Entry(url_frame, textvariable=self.pdf_name_var, width=60).grid(row=1, column=1, sticky="ew", pady=2)
        
        driver_frame = tk.LabelFrame(self.master, text="Cấu hình WebDriver", padx=10, pady=10)
        driver_frame.pack(padx=10, pady=5, fill="x")

        tk.Label(driver_frame, text="Đường dẫn ChromeDriver.exe:").grid(row=0, column=0, sticky="w", pady=2)
        tk.Entry(driver_frame, textvariable=self.webdriver_path_var, width=50).grid(row=0, column=1, sticky="ew", pady=2)
        tk.Button(driver_frame, text="Duyệt...", command=self.browse_webdriver).grid(row=0, column=2, padx=5, pady=2)

        tk.Checkbutton(driver_frame, text="Chạy trình duyệt ẩn (Headless)", variable=self.headless_var).grid(row=1, column=0, columnspan=3, sticky="w", pady=2)

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

    def browse_webdriver(self):
        filename = filedialog.askopenfilename(
            title="Chọn ChromeDriver.exe",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
        )
        if filename:
            self.webdriver_path_var.set(filename)

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
        self.download_thread = threading.Thread(target=self.download_ebook)
        self.download_thread.daemon = True
        self.download_thread.start()

    def stop_download(self):
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

    def download_ebook(self):
        url = self.url_var.get()
        output_folder = self.output_folder_var.get()
        webdriver_path = self.webdriver_path_var.get()
        headless = self.headless_var.get()
        pdf_output_name = self.pdf_name_var.get()

        if not url:
            messagebox.showerror("Lỗi", "Vui lòng nhập URL trang sách.")
            self.log_message("Lỗi: URL trống.")
            return
        if not output_folder:
            messagebox.showerror("Lỗi", "Vui lòng chọn thư mục lưu.")
            self.log_message("Lỗi: Thư mục lưu trống.")
            return
        if not webdriver_path or not os.path.exists(webdriver_path):
            messagebox.showerror("Lỗi", "Vui lòng chọn đường dẫn ChromeDriver.exe hợp lệ.")
            self.log_message("Lỗi: Đường dẫn ChromeDriver không hợp lệ.")
            return

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            self.log_message(f"Đã tạo thư mục: {output_folder}")
        
        pdf_output_path = os.path.join(output_folder, pdf_output_name)

        # --- Khởi tạo WebDriver ---
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless")
        options.add_argument("--start-maximized")
        options.add_argument("--log-level=3")
        
        try:
            self.log_message("Đang khởi tạo trình duyệt...")
            # SỬA LỖI 'executable_path' Ở ĐÂY
            service = ChromeService(executable_path=webdriver_path)
            self.driver = webdriver.Chrome(service=service, options=options) # THAY THẾ DÒNG NÀY
            
            self.driver.get(url)
            self.log_message(f"Đang tải trang: {url}")

            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "e-book-flip__page__front__content"))
            )
            time.sleep(3)

            all_image_urls = []
            page_number = 1

            while True:
                self.log_message(f"Đang xử lý trang {page_number}...")
                
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                page_content_divs = soup.find_all('div', class_='e-book-flip__page__front__content')
                
                found_new_img = False
                for div in page_content_divs:
                    img_tag = div.find('img', class_='e-book-flip__page__front__content__image')
                    if img_tag and 'src' in img_tag.attrs:
                        img_url = img_tag['src']
                        if img_url not in all_image_urls:
                            all_image_urls.append(img_url)
                            self.log_message(f"Tìm thấy ảnh: {img_url}")
                            found_new_img = True

                next_button = None
                try:
                    # Logic tìm nút "Trang kế tiếp" - Vẫn cần bạn kiểm tra và điều chỉnh cho đúng trang web của bạn
                    if not found_new_img and page_number > 1:
                         self.log_message("Không tìm thấy ảnh mới. Có thể đã đến cuối sách hoặc lỗi tải trang.")
                         break

                    try:
                        next_button = self.driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Next page')]")
                    except:
                        try:
                            next_button = self.driver.find_element(By.CSS_SELECTOR, ".toolbar-btn[title='Next page'], .toolbar-btn.next-button")
                        except:
                            next_button = self.driver.find_element(By.XPATH, "//span[contains(text(), 'Trang sau')]/ancestor::*[@class='toolbar-btn']")
                    
                    if next_button and next_button.is_enabled() and "false" not in next_button.get_attribute("class"):
                         self.log_message("Đã tìm thấy nút 'Trang kế tiếp'.")
                    else:
                         self.log_message("Không tìm thấy nút 'Trang kế tiếp' hoặc nút bị vô hiệu hóa. Có thể đã hết trang.")
                         break
                    
                except Exception as e:
                    self.log_message(f"Không tìm thấy nút 'Trang kế tiếp' hoặc đã hết trang: {e}")
                    break

                try:
                    self.driver.execute_script("arguments[0].scrollIntoView();", next_button)
                    time.sleep(1)
                    next_button.click()
                    time.sleep(3)
                    page_number += 1
                except Exception as e:
                    self.log_message(f"Không thể click nút 'Trang kế tiếp': {e}")
                    break

            self.log_message(f"Đã thu thập được {len(all_image_urls)} URL ảnh.")

            downloaded_images_paths = []
            for i, img_url in enumerate(all_image_urls):
                try:
                    response = requests.get(img_url, stream=True, timeout=10)
                    response.raise_for_status()
                    img_name = os.path.join(output_folder, f"page_{i+1:04d}.jpg")
                    with open(img_name, 'wb') as out_file:
                        shutil.copyfileobj(response.raw, out_file)
                    downloaded_images_paths.append(img_name)
                    self.log_message(f"Đã tải {img_url} về {img_name}")
                except Exception as e:
                    self.log_message(f"Lỗi khi tải ảnh {img_url}: {e}")

            if downloaded_images_paths:
                images = []
                for img_path in downloaded_images_paths:
                    try:
                        img = Image.open(img_path).convert('RGB')
                        images.append(img)
                    except Exception as e:
                        self.log_message(f"Lỗi khi mở ảnh {img_path}: {e}")

                if images:
                    images[0].save(pdf_output_path, save_all=True, append_images=images[1:], quality=95, optimize=True)
                    self.log_message(f"Đã tạo file PDF: {pdf_output_path}")
                    messagebox.showinfo("Hoàn tất", f"Đã tải và tạo PDF thành công!\nXem tại: {pdf_output_path}")
                else:
                    self.log_message("Không có ảnh hợp lệ để tạo PDF.")
                    messagebox.showwarning("Cảnh báo", "Không có ảnh hợp lệ nào được tải để tạo PDF.")
            else:
                self.log_message("Không có ảnh nào được tải về để tạo PDF.")
                messagebox.showwarning("Cảnh báo", "Không có ảnh nào được tải về để tạo PDF.")

        except Exception as e:
            self.log_message(f"Đã xảy ra lỗi nghiêm trọng: {e}")
            messagebox.showerror("Lỗi", f"Đã xảy ra lỗi trong quá trình tải: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
            self.log_message("Hoàn tất quá trình.")

if __name__ == "__main__":
    root = tk.Tk()
    app = EBookDownloaderApp(root)
    root.mainloop()