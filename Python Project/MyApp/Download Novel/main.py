import tkinter as tk
from dlnoveltext.guidlnoveltext import NovelScraperGUI

class MainApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Web Novel Scraper")
        self.url_entry = tk.StringVar(value="https://metruyencv.com/truyen/chuyen-sinh-than-thu-ta-che-tao-am-binh-gia-toc")
        self.create_menu()

    def create_menu(self):
        menubar = tk.Menu(self.master)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Tùy chọn tải truyện chữ", command=self.open_novel_scraper)
        menubar.add_cascade(label="File", menu=file_menu)
        self.master.config(menu=menubar)

    def open_novel_scraper(self):
        NovelScraperGUI(self.master, self.url_entry)

if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()