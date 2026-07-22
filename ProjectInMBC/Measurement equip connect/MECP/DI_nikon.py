# Khai báo thư viện
import os
import PySimpleGUI as sg
import openpyxl

# Các funtions





# main:
def main():
    headings = ['A','B']
    value = [
        [1,'na'],
        [2,'nb'],
    ]
    tables = sg.Table(values=value,headings=headings,
                    auto_size_columns=True,
                    display_row_numbers=True,
                    justification='center',
                    num_rows=5,
                    alternating_row_color='',
                    selected_row_colors='red on yellow',
                    key='table',
                    enable_events=True,
                    enable_click_events=True,
                    expand_x= True,
                    expand_y= True
                    ),
                    
                      

    layout = [
        [sg.Text('Data:')],
        [sg.InputText(size=(20,1),key='data',background_color='black',font=('Arial',16,'bold'),text_color='white'),
            sg.Button('Input'),
            sg.Button('Set zero')],
        [tables],
    ]

    window = sg.Window('Digital Indicator Nikon',layout,resizable= True, size=(715,200) )
    while True:
        event,values = window.read(timeout=20)

        if event == sg.WIN_CLOSED:
            break


main()    