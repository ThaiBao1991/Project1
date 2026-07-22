import pandas as pd
import os
from tkinter import messagebox
from .stateMontly import data_df, original_df

DATA_DIR = os.path.join(os.getcwd(), "DATASETC", "dataMontlydata")
CSV_PATH = os.path.join(DATA_DIR, "dataMontly.csv")
DISPLAY_COLUMNS = ["Chủng loại", "Mã hàng", "Khách hàng"]

def initialize_data():
    global data_df, original_df
    if os.path.exists(CSV_PATH):
        try:
            data_df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
        except Exception:
            data_df = pd.DataFrame(columns=DISPLAY_COLUMNS)
    else:
        data_df = pd.DataFrame(columns=DISPLAY_COLUMNS)
    original_df = data_df.copy()
    return data_df

def save_status(df):
    df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")

def nen_du_lieu(df):
    # Placeholder cho chức năng nén file
    messagebox.showinfo("Thông báo", "Chức năng nén file đang phát triển!")