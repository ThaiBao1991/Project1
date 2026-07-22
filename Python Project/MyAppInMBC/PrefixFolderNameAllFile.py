import PySimpleGUI as sg
import os
from pathlib import Path
def get_last_folder_name(folder):
    path = Path(folder)
    return path.name

def rename_files(folder, prefix):
    for filename in os.listdir(folder):
        if not filename.startswith(prefix):
            os.rename(os.path.join(folder, filename), os.path.join(folder, prefix + "-" +filename))

layout = [
    [sg.Text('Đường dẫn thư mục', size=(15, 1)), sg.InputText(key='folder',enable_events=True), sg.FolderBrowse()],
    [sg.Text('Tên điều chỉnh', size=(15, 1)), sg.InputText(key='foldername')],
    [sg.Button('Bắt đầu', key='start')]
]

window = sg.Window('Ứng dụng đổi tên file', layout)

while True:
    event, values = window.read()
    if event == sg.WINDOW_CLOSED:
        break
    if event == 'start':
        foldername = values['foldername']
        folder = values['folder']
        if not folder:
            sg.popup('Vui lòng chọn thư mục trước khi chạy')
        else:
            if not foldername:
                foldername = os.path.basename(folder)
            rename_files(folder, foldername)

window.close()