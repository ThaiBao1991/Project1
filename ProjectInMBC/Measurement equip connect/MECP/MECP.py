# import thư viện
import PySimpleGUI as sg
import Y101
import OGPTransferDataToExceMBC


Layout=[
        [sg.Text('Measurement equip connect Programe',font=('Arial',18,'bold'),text_color='blue',pad=((80,0),(50,50)))],
        [sg.Button('Y101 Peformance equip',font=('Arial',13,'bold'),pad=(5,5),size=20,enable_events=True)],
        [sg.Button('Update Data from OGP to Excel Form',font=('Arial',13,'bold'),pad=(5,5),size=30,enable_events=True)],
        [sg.Button('Digital Indicator equip',font=('Arial',13,'bold'),pad=(5,5),size=20,enable_events=True)],
        [sg.Text("VDM-Inspection Section Rev00 2023/11",font=('Helvetica',8),text_color='black',pad=((0,0),(200,0)))]  
]
window=sg.Window('Measurement equip connect Programe',Layout,size=(650,450),resizable=False,finalize=True)


while True:
    event, values = window.read(timeout=20)
    if event == sg.WIN_CLOSED:
        break
    elif event == 'Y101 Peformance equip':
        Y101.main()
    elif event == 'Update Data from OGP to Excel Form':
        OGPTransferDataToExceMBC.main()
    else:  
        n=3
        
window.close()

