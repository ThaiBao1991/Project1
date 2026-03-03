#Khai báo thư viện:
from datetime import datetime # Lib ngày giờ hệ thống
import os       # Lib xử lý tập tin, thư mục ....liên quan hệ điều hành
import openpyxl  # Lib xử lý file excel
import serial    # Lib giao tiếp cổng com
import PySimpleGUI as sg    # Lib giao diện

sg.theme_text_color('black')
options = ['Type1LAn2', 'Type2:an2', 'Type3', 'Type4', 'Type5', 'Type6', 'Type7', 'Type8', 'Type9', 'Type10']
data_copy_options_layout=[[sg.Checkbox("All-Lan2",key="All2",enable_events=True)]]
for option in options:
    data_copy_options_layout.append([sg.Checkbox(option,key=option,enable_events=True)])
Layout = [
        [sg.Text("Chọn folder lưu file: ")],
        [sg.InputText(disabled=True,size=(50, 1), key='location_save'),sg.FolderBrowse(key='folder_save'),sg.Button("Update")],
        [sg.Text("Chọn form xuất dữ liệu từ máy OJB ")],
        [sg.InputText(disabled=True,size=(50, 1), key='form_save'),sg.FilesBrowse(key='form_save_br'), sg.Button('Clear')],
        [sg.Text("Chọn form cần chuyển dữ liệu hằng ngày ")],
        [sg.InputText(default_text='10',justification='center',disabled=False,size=(50, 1), key='form_save_tt',enable_events=True),sg.FilesBrowse(key='form_save_br_tt'), sg.Button('Clear', key='Clear_tt'),sg.Text('Kiểu form báo cáo') ,sg.Combo(values=['Form1', 'Form2'], key='FormType',enable_events=True)],
        [sg.Text('Status:'),sg.Text("",font=('Helvetica', 13,'bold'), justification='center', pad=(20, 20),key='text_title', text_color='yellow',enable_events=True, expand_x=True),],
        
        [sg.Frame('Dữ liệu cần copy',[
            [sg.Checkbox('All', key='All', enable_events=True)],
            [sg.Checkbox('Type1', key='Type1', enable_events=True)],
            [sg.Checkbox('Type2', key='Type2', enable_events=True)],
         ],key='frame1',visible=False)  
        ],
        
        [[sg.Frame('Dữ liệu copy 2',[data_copy_options_layout],key='frame2',visible=False)]],

        [sg.Button('Start', size=(15, 2), button_color=('green', 'grey'), font=('Helvetica', 16,'bold'), pad=(40, 40),enable_events=True),
            sg.Button('Stop', size=(15,2),button_color=('yellow','grey'),enable_events=True,font=('Helvetica',16,'bold'),pad=(40, 40)),
            sg.Button('Close', size=(15, 2), button_color=('red', 'grey'), font=('Helvetica', 16,'bold'), pad=(40, 40),enable_events=True)],

        [sg.Text("VDM-Inspection Section 2023/11",font=('Helvetica',8))]    
    ]


# window=sg.Window('Chương trình lấy dữ liệu từ máy OGP vào biểu ghi chép',Layout,size=(650,450),resizable=False,finalize=True)
window=sg.Window('Chương trình lấy dữ liệu từ máy OGP vào biểu ghi chép',Layout,resizable=False,finalize=True)

while True:
    # event, values = window.read(timeout=20)
    event, values = window.read()
    if event == sg.WIN_CLOSED:
        break
    elif event == 'All':
        window['Type1'].update(value=values['All'])
        window['Type2'].update(value=values['All'])
    elif event in ('Type1', 'Type2'):
        if not values['Type1'] or not values['Type2']:
            window['All'].update(value=False) 
    elif event == 'All2':
        for option in options:
            window[option].update(value=values['All2'])
    elif event in options:
        if not all(values[option] for option in options):
            window['All2'].update(value=False)
        elif all(values[option] for option in options):
            window['All2'].update(value=True)
    elif event == "form_save_tt":
        print("form_save_tt")
    elif event == "FormType":
        print("FormType")
        if values['FormType'] == 'Form1':
            # Y101.main()
            # window.hide()
            # print("test btn form1")
            # window.un_hide()
            print('Form1')
            window['frame1'].update(visible=True)
            window['frame2'].update(visible=False)
        elif values['FormType']  == 'Form2':
            print("form2")
            window['frame1'].update(visible=False)
            window['frame2'].update(visible=True)
    elif event == 'Close':
        break
    else:    
        print("Not thing to do")
window.close()