import tkinter as tk
from tkinter import ttk, messagebox
import threading
from server import ProxyServer
from proxy_scraper import ProxyScraper

class ProxyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Anti-Block Proxy")
        self.root.geometry("480x320")
        self.root.resizable(False, False)

        self.server = None
        self.scraper = ProxyScraper()

        # Port Setting
        tk.Label(root, text="Cổng (Port):").place(x=20, y=20)
        self.port_var = tk.StringVar(value="8888")
        tk.Entry(root, textvariable=self.port_var, width=10).place(x=100, y=20)

        # Mode Selection
        tk.Label(root, text="Chế độ vượt rào:").place(x=20, y=60)
        self.mode_var = tk.StringVar(value="DPI_BYPASS")
        
        ttk.Radiobutton(root, text="DPI Bypass (Mặc định - Cắt nhỏ gói tin)", variable=self.mode_var, value="DPI_BYPASS", command=self.on_mode_change).place(x=20, y=80)
        ttk.Radiobutton(root, text="Dùng Free Proxy (Chậm, Hên xui)", variable=self.mode_var, value="FREE_PROXY", command=self.on_mode_change).place(x=20, y=100)
        ttk.Radiobutton(root, text="Không dùng Proxy (Kết nối trực tiếp)", variable=self.mode_var, value="DIRECT", command=self.on_mode_change).place(x=20, y=120)

        # Status
        self.status_lbl = tk.Label(root, text="Trạng thái Server: Đã dừng", fg="red")
        self.status_lbl.place(x=20, y=160)
        
        self.proxy_lbl = tk.Label(root, text="Proxy hiện tại: Không có", fg="gray")
        self.proxy_lbl.place(x=20, y=180)

        # Buttons
        self.btn_start = tk.Button(root, text="Bật Proxy Server", bg="#4CAF50", fg="white", command=self.start_server)
        self.btn_start.place(x=20, y=220, width=120, height=40)

        self.btn_stop = tk.Button(root, text="Tắt Server", bg="#f44336", fg="white", state=tk.DISABLED, command=self.stop_server)
        self.btn_stop.place(x=150, y=220, width=100, height=40)

        self.btn_fetch = tk.Button(root, text="Lấy Free Proxy\nvà Chuyển chế độ", command=self.fetch_proxy)
        self.btn_fetch.place(x=260, y=220, width=130, height=40)
        
        self.btn_reset = tk.Button(root, text="Khôi phục\n(Không Proxy)", command=self.reset_direct)
        self.btn_reset.place(x=400, y=220, width=70, height=40)

    def on_mode_change(self):
        if self.server and self.server.running:
            # Tự động khởi động lại với mode mới
            self.start_server()

    def start_server(self):
        port = self.port_var.get()
        mode = self.mode_var.get()
        
        if not port.isdigit():
            messagebox.showerror("Lỗi", "Cổng (Port) phải là một số!")
            return

        if self.server:
            self.server.stop()

        upstream_proxy = None
        if mode == "FREE_PROXY":
            proxy = self.proxy_lbl.cget("text").replace("Proxy hiện tại: ", "")
            if proxy == "Không có" or "Đang tìm" in proxy:
                messagebox.showwarning("Cảnh báo", "Bạn chưa có Free Proxy nào! Hãy bấm nút 'Lấy Free Proxy' trước.")
                return
            upstream_proxy = proxy

        self.server = ProxyServer(port=port, mode=mode, upstream_proxy=upstream_proxy)
        try:
            self.server.start()
            self.status_lbl.config(text=f"Trạng thái Server: Đang chạy (Cổng {port}) - {mode}", fg="green")
            self.btn_start.config(state=tk.DISABLED)
            self.btn_stop.config(state=tk.NORMAL)
            self.port_var.set(port)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể khởi động server: {e}")

    def stop_server(self):
        if self.server:
            self.server.stop()
            self.server = None
        self.status_lbl.config(text="Trạng thái Server: Đã dừng", fg="red")
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)

    def fetch_proxy(self):
        self.proxy_lbl.config(text="Proxy hiện tại: Đang cào dữ liệu... Vui lòng đợi", fg="blue")
        def run():
            proxy = self.scraper.get_working_proxy()
            if proxy:
                self.proxy_lbl.config(text=f"Proxy hiện tại: {proxy}", fg="green")
                # Chuyển qua chế độ FREE PROXY
                self.mode_var.set("FREE_PROXY")
                if self.server and self.server.running:
                    self.start_server() # Restart với mode mới
            else:
                self.proxy_lbl.config(text="Proxy hiện tại: Không có", fg="gray")
                messagebox.showerror("Lỗi", "Không tìm thấy Free Proxy nào hoạt động.")
        threading.Thread(target=run, daemon=True).start()

    def reset_direct(self):
        # Quay về chế độ DIRECT (Không proxy)
        self.mode_var.set("DIRECT")
        if self.server and self.server.running:
            self.start_server()

if __name__ == "__main__":
    root = tk.Tk()
    app = ProxyApp(root)
    root.mainloop()
