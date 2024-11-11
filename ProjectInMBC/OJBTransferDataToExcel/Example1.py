import PySimpleGUI as sg

# Tạo dữ liệu ban đầu cho table
data = [[f'Cell ({i},{j})' for j in range(4)] for i in range(10)]

# Tạo layout cho window
layout = [
    [sg.Table(values=data, headings=['H1', 'H2', 'H3', 'H4'], key='-TABLE-')],
    [sg.Button('Change Data'), sg.Button('Exit')]
]

# Tạo window
window = sg.Window('Table Update Example', layout)

# Vòng lặp xử lý sự kiện
while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == 'Exit':
        print("Exit diagloge")
        break
    if event == 'Change Data':
        print("Click button Change Data")
        # Tạo dữ liệu mới cho table
        new_data = [[f'New ({i},{j})' for j in range(3)] for i in range(10)]
        # Cập nhật table với dữ liệu mới
        window['-TABLE-'].update(new_data)

# Đóng window
window.close()

#pyinstaller --onefile --noconsole connect.py