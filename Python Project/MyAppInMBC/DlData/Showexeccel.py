import win32com.client
from tkinter import messagebox


def process_excel_file():
    excel = None
    try:
        excel = win32com.client.Dispatch("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = True
        excel.AskToUpdateLinks = True
        excel.ScreenUpdating = True
    except Exception as e:
        messagebox.showerror("Lỗi", f"Có lỗi xảy ra khi xử lý file Excel:\n{str(e)}")
        return False
process_excel_file