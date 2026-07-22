# inport thư viện
import serial.tools.list_ports
import PySimpleGUI as sg
import re

# các funtion

# Kết nối cổng rs232
def connect_rs232():
    ser = serial.Serial()
    try:
        com_ports = list(serial.tools.list_ports.comports())
        for port in com_ports:
            ser.port = port.device
            ser.baudrate = 4800 #4800/9600
            ser.parity = 'N'
            ser.stopbits = 2
            ser.timeout = 1
            try:
                ser.open()
                print(f'Connect success with {port}')
                return ser
            except serial.SerialException as e:
                sg.popup_error(f"Error: {e}")
       
        sg.popup_error("Unable to connect to any COM port.")
        return None


    except serial.SerialException as e:
        sg.popup_error(f"Error: {e}")
        return None

# Reset zero 
def send_reset(ser):
    try:
        command = 'RX\r\n'.encode('ascii')
        print('Reset Data')
        ser.write(command)


    except serial.SerialException as e:
        sg.popup_error(f"Error: {e}")

# read data
def send_read(ser, input_element):
    try:
        command = 'QX\r\n'.encode('ascii')
        print('Read Data from Digimicro Nikon')
        ser.write(command)

        value = ser.read(20)
        print(value) # Print DATA ASCII

        decode_value = value.decode('utf-8').strip()

        result = re.match(r'[+-]?\d*\.\d+', decode_value)
        if result:
            value = result.group()
            if value[1:6] == '00000':
                value = value[0] + value[5:]
                input_element.update(value)
            else:    
                value = value[0] + value[1:].lstrip('0') 
                input_element.update(value)
                return value
        else:
            input_element.update('Invalid Format')
            return None

    except serial.SerialException as e:
        sg.popup_error(f"Error: {e}")
        return None
def uptable(value, update_element):
    update_element.update(value)

def main():
    ser = connect_rs232()

    if ser is None:
        return

    sg.theme_text_color('black') # thiết định màu chữ trên form màu black
    

    # table 1
    heading1 = ['No','Data']
    data=[]
    for i in range (10):
        data.append(i)
    value1 = [[data,],
              [data]
              ]
        
    
    table1 = sg.Table(values=value1,headings=heading1,
                    auto_size_columns=True,
                    display_row_numbers=False,
                    justification='center',
                    num_rows=10,
                    alternating_row_color='#536982',
                    selected_row_colors='red on yellow',
                    
                    key='table1',
                    enable_events=True,
                    enable_click_events=True,
                    expand_x= True,
                    #expand_y= True
                    ),
    # table2
    heading2 = ['No','Data']
    value2 = [
        [1,],
        [2,],
        [3,],
        [4,],
        [5,],
    ]
    table2 = sg.Table(values=value2,headings=heading2,
                    auto_size_columns=True,
                    display_row_numbers=False,
                    justification='center',
                    num_rows=10,
                    alternating_row_color='#536982',
                    
                    selected_row_colors='red on yellow',
                    key='table2',
                    enable_events=True,
                    enable_click_events=True,
                    expand_x= True,
                    #expand_y= True
                    ),
    
    # form
    layout = [
        [sg.Text('VALUES:')],
        [sg.InputText(size=(20,2),key='-VALUE-',background_color='black',font=('Arial',16,'bold'),text_color='white'),
            sg.Button('Input',key='-INPUT-', size=(10,2),button_color=('white','blue'),font=('Arial',10,'bold')),
            sg.Button('Set zero',key='-RESET-',size=(10,2),button_color=('white','blue'),font=('Arial',10,'bold'))],
        
        #[sg.Button('Reset', key='-RESET-', size=(15, 2), button_color=('white', 'blue'), font=('Helvetica', 16), pad=(20, 20)),
        # sg.Button('Read', key='-READ-', size=(15, 2), button_color=('white', 'blue'), font=('Helvetica', 16), pad=(20, 20)),
        # sg.Text("Value:"), sg.Input(size=(20, 4), key='-VALUE-')],
        [sg.Combo(values=['Max','Min','Max & Min', 'Trung bình','None'],size=(15,1))],
        #[sg.Frame('Data in',[table1],expand_x=True),sg.Button('Export'),sg.Frame('Data out',[table2],expand_x=True)],
        [sg.Text("VDM-Inspection Section 2023/11",font=('Helvetica',8))]
    ]  

    window = sg.Window('Measurement equip connect Programe - Digital Indicator Nikon', layout, resizable=False, finalize=True)

    while True:
        event, values = window.read()

        if event == sg.WINDOW_CLOSED:
            break
        elif event == '-RESET-':
            send_reset(ser)
            window['-VALUE-'].update('0.000')
        elif event == '-INPUT-':
            value= send_read(ser, window['-VALUE-'])
            uptable(value,window['table1'])

    if ser.is_open:
        ser.close()
    window.close()


if __name__ == '__main__':
    main()
