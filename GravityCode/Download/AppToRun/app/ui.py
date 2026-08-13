import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
from app.config import load_config, save_config
from app.builder import Builder
from app.installer import is_tool_installed, install_tool

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class PyPackGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("PyPackGUI - Python App Builder")
        self.geometry("850x700")
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1)
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="PyPackGUI", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        self.tool_label = ctk.CTkLabel(self.sidebar, text="Công cụ đóng gói:")
        self.tool_label.grid(row=1, column=0, padx=20, pady=(10, 0))
        
        self.tool_var = ctk.StringVar(value="pyinstaller")
        self.tool_menu = ctk.CTkOptionMenu(self.sidebar, values=["pyinstaller", "cx_Freeze", "nuitka"], variable=self.tool_var)
        self.tool_menu.grid(row=2, column=0, padx=20, pady=10)
        
        self.install_btn = ctk.CTkButton(self.sidebar, text="Cài đặt PyInstaller", command=self.check_install)
        self.install_btn.grid(row=3, column=0, padx=20, pady=10)
        
        # Main content
        self.main_frame = ctk.CTkScrollableFrame(self)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_columnconfigure(1, weight=1)
        
        # Script path
        ctk.CTkLabel(self.main_frame, text="File main.py:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.script_entry = ctk.CTkEntry(self.main_frame)
        self.script_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(self.main_frame, text="Browse", width=60, command=self.browse_script).grid(row=0, column=2, padx=10, pady=10)
        
        # App Name
        ctk.CTkLabel(self.main_frame, text="Tên ứng dụng:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.name_entry = ctk.CTkEntry(self.main_frame)
        self.name_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew", columnspan=2)
        
        # Output dir
        ctk.CTkLabel(self.main_frame, text="Thư mục Output:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.output_entry = ctk.CTkEntry(self.main_frame)
        self.output_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(self.main_frame, text="Browse", width=60, command=self.browse_output).grid(row=2, column=2, padx=10, pady=10)
        
        # Icon
        ctk.CTkLabel(self.main_frame, text="Icon (.ico):").grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.icon_entry = ctk.CTkEntry(self.main_frame)
        self.icon_entry.grid(row=3, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(self.main_frame, text="Browse", width=60, command=self.browse_icon).grid(row=3, column=2, padx=10, pady=10)
        
        # Checkboxes
        self.checkbox_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.checkbox_frame.grid(row=4, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
        
        self.onefile_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(self.checkbox_frame, text="Một file duy nhất (--onefile)", variable=self.onefile_var).pack(side="left", padx=10)
        
        self.noconsole_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(self.checkbox_frame, text="Ẩn cửa sổ console", variable=self.noconsole_var).pack(side="left", padx=10)
        
        # Data files section
        self.data_label = ctk.CTkLabel(self.main_frame, text="Dữ liệu đính kèm (Data / Config):", font=ctk.CTkFont(weight="bold"))
        self.data_label.grid(row=5, column=0, columnspan=3, padx=10, pady=(20,5), sticky="w")
        
        self.data_frame = ctk.CTkFrame(self.main_frame)
        self.data_frame.grid(row=6, column=0, columnspan=3, padx=10, pady=5, sticky="nsew")
        self.data_frame.grid_columnconfigure(0, weight=1)
        
        self.data_items = [] # List of dict: {"path": str, "mode": StringVar, "frame": CTkFrame}
        
        self.add_data_btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.add_data_btn_frame.grid(row=7, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
        ctk.CTkButton(self.add_data_btn_frame, text="+ Thêm File", command=self.add_data_file, width=120).pack(side="left", padx=5)
        ctk.CTkButton(self.add_data_btn_frame, text="+ Thêm Thư mục", command=self.add_data_dir, width=120).pack(side="left", padx=5)

        # Log Box
        self.log_box = ctk.CTkTextbox(self.main_frame, height=150)
        self.log_box.grid(row=8, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        self.main_frame.grid_rowconfigure(8, weight=1)
        
        # Buttons
        self.btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.btn_frame.grid(row=9, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
        
        self.build_btn = ctk.CTkButton(self.btn_frame, text="BẮT ĐẦU ĐÓNG GÓI", command=self.start_build, height=40)
        self.build_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.open_out_btn = ctk.CTkButton(self.btn_frame, text="Mở Output", command=self.open_output, height=40, state="disabled")
        self.open_out_btn.pack(side="left", fill="x", expand=True, padx=(5, 0))
        
        self.load_config_data()
        self.check_status()

    def add_data_item(self, path, mode="Chỉ đọc"):
        frame = ctk.CTkFrame(self.data_frame, fg_color="transparent")
        frame.pack(fill="x", padx=5, pady=2)
        
        path_label = ctk.CTkLabel(frame, text=path, anchor="w", width=300)
        path_label.pack(side="left", fill="x", expand=True, padx=5)
        
        mode_var = ctk.StringVar(value=mode)
        mode_menu = ctk.CTkOptionMenu(frame, values=["Chỉ đọc", "Giải nén"], variable=mode_var, width=100)
        mode_menu.pack(side="left", padx=5)
        
        del_btn = ctk.CTkButton(frame, text="X", width=30, fg_color="#D32F2F", hover_color="#B71C1C", command=lambda f=frame, p=path: self.remove_data_item(f, p))
        del_btn.pack(side="right", padx=5)
        
        self.data_items.append({
            "path": path,
            "mode": mode_var,
            "frame": frame
        })

    def remove_data_item(self, frame, path):
        frame.destroy()
        self.data_items = [item for item in self.data_items if item["path"] != path]

    def add_data_file(self):
        paths = filedialog.askopenfilenames()
        for path in paths:
            if not any(item["path"] == path for item in self.data_items):
                self.add_data_item(path)

    def add_data_dir(self):
        path = filedialog.askdirectory()
        if path:
            if not any(item["path"] == path for item in self.data_items):
                self.add_data_item(path)

    def check_status(self):
        if is_tool_installed("PyInstaller"):
            self.install_btn.configure(text="PyInstaller đã cài đặt", state="disabled")
        else:
            self.install_btn.configure(text="Cài đặt PyInstaller", state="normal")

    def check_install(self):
        self.log_msg("Đang cài đặt PyInstaller...\n")
        self.install_btn.configure(state="disabled")
        if install_tool("pyinstaller"):
            self.log_msg("Cài đặt PyInstaller thành công!\n")
            self.install_btn.configure(text="PyInstaller đã cài đặt", state="disabled")
        else:
            self.log_msg("Lỗi khi cài đặt PyInstaller.\n")
            self.install_btn.configure(state="normal")

    def browse_script(self):
        path = filedialog.askopenfilename(filetypes=[("Python Files", "*.py")])
        if path:
            self.script_entry.delete(0, 'end')
            self.script_entry.insert(0, path)

    def browse_output(self):
        path = filedialog.askdirectory()
        if path:
            self.output_entry.delete(0, 'end')
            self.output_entry.insert(0, path)

    def browse_icon(self):
        path = filedialog.askopenfilename(filetypes=[("Icon Files", "*.ico")])
        if path:
            self.icon_entry.delete(0, 'end')
            self.icon_entry.insert(0, path)

    def log_msg(self, msg):
        self.log_box.insert("end", msg)
        self.log_box.see("end")

    def load_config_data(self):
        config = load_config()
        if config.get("main_script"):
            self.script_entry.insert(0, config["main_script"])
        if config.get("app_name"):
            self.name_entry.insert(0, config["app_name"])
        if config.get("output_dir"):
            self.output_entry.insert(0, config["output_dir"])
        if config.get("icon"):
            self.icon_entry.insert(0, config["icon"])
        if "onefile" in config:
            self.onefile_var.set(config["onefile"])
        if "noconsole" in config:
            self.noconsole_var.set(config["noconsole"])
        
        if "data_items" in config:
            for item in config["data_items"]:
                self.add_data_item(item["path"], item["mode"])

    def save_current_config(self):
        data_list = []
        for item in self.data_items:
            data_list.append({"path": item["path"], "mode": item["mode"].get()})
            
        config = {
            "main_script": self.script_entry.get(),
            "app_name": self.name_entry.get(),
            "output_dir": self.output_entry.get(),
            "icon": self.icon_entry.get(),
            "onefile": self.onefile_var.get(),
            "noconsole": self.noconsole_var.get(),
            "data_items": data_list
        }
        save_config(config)
        return config

    def start_build(self):
        if not self.script_entry.get():
            messagebox.showerror("Lỗi", "Vui lòng chọn file main.py")
            return
            
        if not is_tool_installed("PyInstaller") and self.tool_var.get() == "pyinstaller":
            messagebox.showerror("Lỗi", "Vui lòng cài đặt PyInstaller trước khi build")
            return
            
        config = self.save_current_config()
        self.log_box.delete("1.0", "end")
        self.build_btn.configure(state="disabled")
        self.open_out_btn.configure(state="disabled")
        
        builder = Builder(self.log_msg, self.build_done)
        builder.build_pyinstaller(config)

    def build_done(self, success):
        self.build_btn.configure(state="normal")
        if success and self.output_entry.get():
            self.open_out_btn.configure(state="normal")

    def open_output(self):
        out_dir = self.output_entry.get()
        if out_dir and os.path.exists(out_dir):
            os.startfile(out_dir)
