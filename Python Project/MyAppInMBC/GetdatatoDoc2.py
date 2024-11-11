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

    # print(element.text)
    
    # Thực hiện lệnh JavaScript để chọn phần tử
    element.click()
    time.sleep(2)

    # Sao chép nội dung
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(1)
    
    
     # Khởi động Word
    app = pywinauto.application.Application()
    app.start("C:\\Program Files (x86)\\Microsoft Office\\root\\Office16\\winword.exe")
    
    # Kiểm tra xem Word đã mở chưa, nếu chưa thì mở mới
    if not app.windows():
        app.start("C:\\Program Files (x86)\\Microsoft Office\\root\\Office16\\winword.exe")
    
    # Gửi phím tắt Ctrl+ N để mở hộp thoại New
    
    try:
        dlg = app.window(title_re=".*Word.*")
        dlg.wait('ready')
        
        # Gửi phím tắt Ctrl+N để tạo tài liệu mới
        dlg.type_keys('^n')

        # Tìm cửa sổ tài liệu mới (nếu cần)
        new_doc = app.window(title_re=".*Document.*")
        new_doc.wait('ready')

    except pywinauto.findwindows.ElementNotFoundError:
        print("Không tìm thấy cửa sổ Word")
    
    # Gửi phím tắt Ctrl+O để mở hộp thoại Open
    dlg.type_keys('^o')
    
    # Thêm thời gian chờ để đảm bảo hộp thoại mở ra
    dlg.wait('ready', timeout=10)

    # Điều hướng bằng các phím mũi tên và nhấn Enter
    dlg.type_keys('{RIGHT}{DOWN}{DOWN}{DOWN}{DOWN}{DOWN}{ENTER}')
    
    # Kết nối với hộp thoại Open mới
    dlgnew = app.window(title_re=".*Open.*")
    dlgnew.wait('ready', timeout=10)

    # Tìm hộp thoại Open và nhập đường dẫn file
    output_path = os.path.abspath('output.docx')
    edit_box = dlgnew.child_window(title="File name:", control_type="Edit")
    edit_box.type_keys(output_path)

    # Nhấn nút Open
    open_button = dlgnew.child_window(title="Open", control_type="Button")
    open_button.click()

    # Chờ một chút để Word load xong
    time.sleep(2)

    # Đặt con trỏ vào vị trí cuối cùng của tài liệu
    dlgnew.Edit.type_keys("^end")

    # Dán nội dung
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(1)
    # Lưu file (thay đổi đường dẫn và tên file nếu cần)
    dlg.menu_select("File -> Save")
    time.sleep(1)
    pyautogui.press('enter')   

    
def get_absolute_url(base_url, relative_url):
    """
    Hàm tạo URL tuyệt đối từ URL gốc và URL tương đối.

    Args:
        base_url (str): URL gốc của trang web.
        relative_url (str): URL tương đối.

    Returns:
        str: URL tuyệt đối.
    """
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

        # In ra màn hình để kiểm tra (tùy chọn)
        
        # print(f"Link: {href}")
        # print(f"Text: {text}")
        absolute_url = get_absolute_url(base_url, href)
        driver = webdriver.Chrome()
        driver.get(absolute_url)
        
        copy_and_paste_content(driver, document)
        output_path = os.path.abspath('output.docx')
        print(output_path)
        document.save(output_path)
        driver.quit()
    # Lưu file Word
    document.save('output.docx') 
    


# URL của trang web
url = "https://vi.extendoffice.com/documents/excel"  # Thay thế bằng URL thực tế

create_word_document(url)