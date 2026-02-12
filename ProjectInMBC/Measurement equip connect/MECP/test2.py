import PySimpleGUI as sg
import openpyxl
import os

def append_to_form_ac(data,form_path,count):
    wb = openpyxl.load_workbook(form_path)
    sheet=wb['SAMPLING_INSPECTION_EN']
        
    sheet[f'AD{0+count}'] = data[4]
    
    file_name=os.path.basename(form_path)
    
    wb.save(file_name)

 # table 1
heading1 = ['No','Data']
value1 = [
        [1,],
        [2,],
        [3,],
        [4,],
        [5,],
    ]
value2=[[2,'e']]
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

layout=[
    [sg.InputText(disabled=True,size=(50,1),key='test'),sg.FileBrowse('Browse',key="folder")],
    [table1]
]

window=sg.Window("test",layout)
data=[1,2,3,4,5,6,7]

while True:
    event,value=window.read(timeout=20)

    test_path=value['test']
    if not test_path:
        print('space')
        
        window['table1'].update(values=[['d','s'] ])
    else:
        append_to_form_ac(data,test_path,9)
        print("finished")
    if event== sg.WIN_CLOSED:
        break

   





