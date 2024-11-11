# Su dung selenium vs pyautogui
import os
import time
import pyautogui
from selenium import webdriver
from selenium.webdriver.common.by import By
from docx import Document
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import requests

def copy_and_paste_content(driver, document):
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(1)
    # Sao chép nội dung
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(1)
    # Mở file Word
    pyautogui.hotkey('ctrl', 'o')
    time.sleep(1)
    output_path = os.path.abspath('output.docx')
    pyautogui.write(output_path)
    pyautogui.press('enter')
    time.sleep(2)
    # Dán nội dung vào file Word
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(1)
    
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
        time.sleep(2)

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