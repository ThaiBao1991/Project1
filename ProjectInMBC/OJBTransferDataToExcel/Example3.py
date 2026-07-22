# import thư viện
import PySimpleGUI as sg

Layout=[
        [sg.Text('Get date from OGP to excel form',font=('Arial',18,'bold'),text_color='blue',pad=((80,0),(50,50)))],
        [sg.Button('Form1',font=('Arial',13,'bold'),pad=(5,5),size=20,enable_events=True)],
        [sg.Button('Form2',font=('Arial',13,'bold'),pad=(5,5),size=20,enable_events=True)],
        [sg.Text("Software get date from OGP to excel form Rev00 2023/11",font=('Helvetica',8),text_color='black',pad=((0,0),(200,0)))]  
]


def input_box(title):
    """
    title: Nhập tiêu đề Input box
    """ 
    layout =[
        [sg.Text('', key='-content_t-')],
        [sg.Input(key='-content-' )],
        [sg.Button('OK', bind_return_key=True)]
    ]
    window = sg.Window('Input box', layout, resizable=True,finalize=True)

    while True:
        events, values = window.read(timeout=20)
        window['-content_t-'].update(title)
        if events == sg.WINDOW_CLOSED :
            break
        elif events == 'OK' :
            value = values['-content-']
            if value == "" :
                sg.popup_ok('Bạn phải nhập dữ liệu', title= 'Thông báo')
            else:    
                break
    
    window.close()
    return value

window=sg.Window('Chương trình lấy dữ liệu từ máy OGP vào biểu ghi chép',Layout,size=(650,450),resizable=False,finalize=True)


while True:
    event, values = window.read(timeout=20)
    if event == sg.WIN_CLOSED:
        break
        
    elif event == 'Form1':
        # Y101.main()
        window.hide()
        print("test btn form1")
        a= input_box('check')
        window.un_hide()
    else:    
       
        n=3
window.close()


#pyinstaller --onefile --noconsole Example3.py