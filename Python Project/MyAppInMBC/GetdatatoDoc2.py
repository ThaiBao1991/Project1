# Su dung selenium vs pyautogui vs pywinauto new
import os
import time
import pyautogui
import pywinauto
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from docx import Document
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import requests

def copy_and_paste_content(driver, document):
    
    # Tìm phần tử div cần chọn
    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "uk-margin-small-top")))
    element.click()
    time.sleep(2)

    # Sao chép nội dung
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(2)
    
    
    # Đường dẫn mặc định đầu tiên
    path1 = "C:\\Program Files (x86)\\Microsoft Office\\root\\Office16\\winword.exe"
    # Đường dẫn thay thế
    path2 = "C:\\Program Files\\Microsoft Office\\root\\Office16\\winword.exe"

    # Kiểm tra sự tồn tại của đường dẫn
    if os.path.exists(path1):
        app_path = path1
    elif os.path.exists(path2):
        app_path = path2
    else:
        raise FileNotFoundError("Không tìm thấy Microsoft Word ở bất kỳ đường dẫn nào.")

    # Khởi chạy ứng dụng
    app = pywinauto.Application().start(app_path)

    # Kiểm tra xem Word đã mở chưa, nếu chưa thì mở mới
    if not app.windows():
        app.start(app_path)
     
    try:
        dlg = app.window(title_re=".*Word.*")
        dlg.wait('visible', timeout=10)
        
        # Gửi phím tắt Ctrl+O để mở hộp thoại Open
        dlg.type_keys('^o')
        time.sleep(2)  # Thời gian chờ để hộp thoại Open mở ra

        # Điều hướng bằng các phím mũi tên và nhấn Enter
        # dlg.type_keys('{RIGHT}{DOWN}{DOWN}{DOWN}{DOWN}{DOWN}{ENTER}')
        
        # Sử dụng pyautogui để nhấp vào nút “Browse”
        browse_button_location = pyautogui.locateCenterOnScreen('browse_button_image.png')  # Cần ảnh của nút “Browse”
        if browse_button_location:
            pyautogui.click(browse_button_location)
        else:
            print("Không tìm thấy nút 'Browse'")
            return

        # Tìm hộp thoại Open và nhập đường dẫn file
        output_path = os.path.abspath('output.docx')
        dlg_open = app.window(title_re=".*Open.*")
        dlg_open.wait('ready', timeout=10)
        dlg_open.type_keys(output_path)
        time.sleep(1)

        # Nhấn Enter để mở file
        dlg_open.type_keys('{ENTER}')
        time.sleep(2)  # Chờ để Word tải xong tài liệu

        # Đặt con trỏ vào vị trí cuối của tài liệu
        dlg.type_keys("^end")

        # Dán nội dung
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(1)

        # Lưu file (thay đổi đường dẫn và tên file nếu cần)
        dlg.menu_select("File -> Save")
        time.sleep(1)
        pyautogui.press('enter')
    except pywinauto.findwindows.ElementNotFoundError:
        print("Không tìm thấy cửa sổ Word")
    except Exception as e:
        print("Lỗi khác:", e)
    
    

    
def get_absolute_url(base_url, relative_url):
    return urljoin(base_url, relative_url)

base_url = 'https://vi.extendoffice.com'

document = Document()
document.add_paragraph('')  # Tạo một đoạn văn bản trống để dán nội dung
document.save('output.docx') 
# URL của trang web chứa danh sách các link



def create_word_document(url):
    # Gửi yêu cầu HTTP và phân tích HTML
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Tìm tất cả các thẻ <a> bên trong ul có id="ul-search"
    links = soup.find('ul', id='ul-search').find_all('a')


    # Tạo mục lục
    document.add_heading('Mục lục', level=0)

    # Xử lý lỗi lấy nội dung
    for link in links:
        text = link.text.strip()
        href = link['href']

        # Thêm vào mục lục
        document.add_paragraph(text, style='Heading 2')
        # Lưu thay đổi vào file Word
        output_path = os.path.abspath('output.docx')
        document.save(output_path)
        
        # In ra màn hình để kiểm tra (tùy chọn)
        # print(f"Link: {href}")
        # print(f"Text: {text}")
        
        absolute_url = get_absolute_url(base_url, href)
        driver = webdriver.Chrome()
        driver.get(absolute_url)
        
        copy_and_paste_content(driver, document)
        output_path = os.path.abspath('output.docx')
        print(output_path)
        document.save('output.docx')
        driver.quit()
    # Lưu file Word
    document.save('output.docx') 
    


# URL của trang web
url = "https://vi.extendoffice.com/documents/excel"  # Thay thế bằng URL thực tế

create_word_document(url)