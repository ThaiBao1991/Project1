import PySimpleGUI as sg

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
            