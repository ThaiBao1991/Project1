import PySimpleGUI as sg  # Import thư viện PySimpleGUI để tạo giao diện người dùng
import openpyxl  # Import thư viện openpyxl để làm việc với file Excel
import os  # Import thư viện os để làm việc với hệ thống file

# Hàm này thêm dữ liệu vào một form Excel đã tồn tại
def append_to_form_ac(data,form_path,count):
    wb = openpyxl.load_workbook(form_path)  # Mở workbook Excel
    sheet=wb['Example2']  # Chọn sheet 'Example2'
        
    sheet[f'A{0+count}'].value = data[4]  # Thêm dữ liệu vào cột A tại dòng count
    sheet[f'B{2}'] = "Thêm dữ liệu vào ô B2 từ python"
    print(sheet[f'B{1}'].value,data[4])
    file_name=os.path.basename(form_path)  # Lấy tên file từ đường dẫn
    print("Tên của file được thêm vào",file_name)
    # wb.save(file_name)  # Lưu lại workbook tại thư mục cha của project , ở đây tên file test và thư mục là PyThon Project
    # os.startfile(file_name) # Mở file tại thư mục gốc của cha
    wb.save(form_path)
    os.startfile(form_path)

# Tạo bảng với các tiêu đề và giá trị
heading1 = ['No','Data']
value1 = [
        [1,"Dữ liệu 1"],
        [2,"Dữ liệu 2"],
        [3,"Ta thử dữ liệu 3"],
        [4,"Ta phang vào dữ liệu 4"],
        [5,"Ta send vào dữ liệu 5 vì buồn đời"],
    ]

table1 = sg.Table(values=value1,headings=heading1,  # 'values' là dữ liệu của bảng, 'headings' là tiêu đề các cột
                    auto_size_columns=True,  # Tự động điều chỉnh kích thước cột theo nội dung
                    display_row_numbers=False,  # Không hiển thị số dòng
                    justification='center',  # Căn giữa nội dung
                    num_rows=10,  # Hiển thị 5 dòng
                    alternating_row_color='#536982',  # Màu xen kẽ của các dòng
                    selected_row_colors='red on yellow',  # Màu của dòng được chọn
                    
                    key='table1',  # Khóa để truy cập bảng sau này
                    enable_events=True,  # Kích hoạt sự kiện khi tương tác với bảng
                    enable_click_events=True,  # Kích hoạt sự kiện khi nhấp vào bảng
                    expand_x= True,  # Mở rộng bảng theo chiều ngang
                    ),

# Tạo layout cho cửa sổ
layout=[
    [sg.InputText(disabled=True,size=(50,1),key='test'),sg.FileBrowse('Browse',key="folder")],
    [table1],[sg.Button('Insert Data'), sg.Button('Stop')]
]

# Tạo cửa sổ với layout đã tạo
window=sg.Window("Tieu de cua chuong trinh",layout)
data=[1,2,3,4,5,6,7]

# Vòng lặp chính để xử lý sự kiện
while True:
    # event,value=window.read(timeout=20)  # Đọc sự kiện và giá trị từ cửa sổ
    event,value=window.read()
    if value is not None:
        test_path=value['test']  # Lấy giá trị từ khung nhập 'test'

    if event == "Insert Data":
        window['table1'].update(values=[['Insert Data Table 1','Insert Data Table 2'] ])  # Cập nhật bảng với giá trị mới
        if not test_path:  # Nếu không có giá trị
            print('space')
            window['table1'].update(values=[['d','s'] ])  # Cập nhật bảng với giá trị mới
        else:  # Nếu có giá trị
            print(test_path)
            append_to_form_ac(data,test_path,2)  # Gọi hàm để thêm dữ liệu vào form
            print("finished")  # In thông báo đã hoàn thành
    
    if event== sg.WIN_CLOSED:  # Nếu sự kiện là đóng cửa sổ
        break  # Thoát khỏi vòng lặp