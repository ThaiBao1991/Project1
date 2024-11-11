import os
import time
import pyautogui
import pywinauto
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
from docx import Document
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import requests

def copy_and_paste_content(driver):
    # Tìm phần tử div cần chọn
    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "uk-margin-small-top")))
    element.click()
    time.sleep(2)

    # Sao chép nội dung
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(2)

def open_word_and_paste():
    # Đường dẫn Microsoft Word
    path1 = "C:\\Program Files (x86)\\Microsoft Office\\root\\Office16\\winword.exe"
    path2 = "C:\\Program Files\\Microsoft Office\\root\\Office16\\winword.exe"
    app_path = path1 if os.path.exists(path1) else path2

    # Khởi chạy Word
    app = pywinauto.Application().start(app_path)

    try:
        # Mở file Word đã tạo
        dlg = app.window(title_re=".*Word.*")
        dlg.wait('visible', timeout=15)
        dlg.type_keys('^o')
        time.sleep(5)
        
        # Điều hướng bằng các phím mũi tên và nhấn Enter
        # dlg.type_keys('{RIGHT}{DOWN}{DOWN}{DOWN}{DOWN}{DOWN}{ENTER}')
        
        # Kiểm tra thư mục hiện tại mà chương trình Python đang làm việc
        current_directory = os.getcwd()
        print("Thư mục hiện tại:", current_directory)
        
       # Kiểm tra xem ảnh có được nhận diện không
        try:
            browse_button_location = pyautogui.locateCenterOnScreen(r'C:\Users\games\Desktop\Project\Python\browse_button_image.png')
            if browse_button_location:
                print("Nút Browse tìm thấy tại:", browse_button_location)
            else:
                print("Không thể tìm thấy nút Browse.")
        except Exception as e:
            print("Lỗi khi tìm ảnh:", e)
        
        # Đường dẫn đến file output
        output_path = os.path.abspath('output.docx')
        dlg_open = app.window(title_re=".*Open.*")
        dlg_open.wait('ready', timeout=10)
        dlg_open.type_keys(output_path)
        time.sleep(1)
        
        # Nhấn Enter để mở file
        dlg_open.type_keys('{ENTER}')
        time.sleep(2)
        
        # Đặt con trỏ ở cuối tài liệu và dán nội dung
        dlg.type_keys("^end")
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(1)
        
        # Lưu tài liệu
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

def create_word_document(url):
    # Gửi yêu cầu HTTP và phân tích HTML
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Tìm tất cả các thẻ <a> bên trong ul có id="ul-search"
    links = soup.find('ul', id='ul-search').find_all('a')

    # Tạo mục lục
    document.add_heading('Mục lục', level=0)

    for link in links:
        text = link.text.strip()
        href = link['href']
        
        # Thêm tiêu đề vào mục lục
        document.add_paragraph(text, style='Heading 2')

        # Lưu thay đổi vào file Word
        output_path = os.path.abspath('output.docx')
        document.save(output_path)
        
        # Mở trang và sao chép nội dung
        absolute_url = get_absolute_url(base_url, href)
        driver = webdriver.Chrome()
        driver.get(absolute_url)
        
        copy_and_paste_content(driver)
        
        # Mở Word và dán nội dung
        open_word_and_paste()
        
        driver.quit()

    # Lưu file Word
    document.save('output.docx')

# URL của trang web
url = "https://vi.extendoffice.com/documents/excel"  # Thay thế bằng URL thực tế
create_word_document(url)