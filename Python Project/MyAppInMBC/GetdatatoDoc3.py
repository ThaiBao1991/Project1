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
import pyautogui
import os
from tkinter import Tk, filedialog
from pathlib import Path

def select_image_file(default_path):
    root = Tk()
    root.withdraw()  # Ẩn cửa sổ chính của Tkinter
    root.attributes('-topmost', True)  # Đưa hộp thoại lên trên cùng

    # Hiển thị hộp thoại chọn file với đường dẫn mặc định
    file_path = filedialog.askopenfilename(initialdir=os.path.dirname(default_path), title="Select Image File",
                                           filetypes=(("PNG files", "*.png"), ("All files", "*.*")))
    root.destroy()  # Đóng cửa sổ Tkinter

    return file_path

def copy_and_paste_content(driver, document):
    
    # Tìm phần tử div cần chọn
    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "uk-margin-small-top")))
    element.click()
    time.sleep(2)

    # Sao chép nội dung
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(10)
    
    
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
        dlg.wait('visible', timeout=40)
        
        # Gửi phím tắt Ctrl+O để mở hộp thoại Open
        dlg.type_keys('^o')
        time.sleep(15)  # Thời gian chờ để hộp thoại Open mở ra

        # Điều hướng bằng các phím mũi tên và nhấn Enter
        # dlg.type_keys('{RIGHT}{DOWN}{DOWN}{DOWN}{DOWN}{DOWN}{ENTER}')
        
        # Sử dụng pyautogui để nhấp vào nút “Browse”
        image_path = 'Python Tutorial\\browse_button_image.png'
        if not os.path.exists(image_path):
            print(f"Không tìm thấy file ảnh tại {image_path}. Vui lòng chọn file ảnh mới.")
            image_path = select_image_file(image_path)
        if not image_path:
            print("Không có file ảnh nào được chọn.")
        
        for i in range(10):
            browse_button_location = pyautogui.locateCenterOnScreen(image_path, confidence=0.8)
            if browse_button_location:
                break
        
        if browse_button_location:
            print(f"Đã tìm thấy file ảnh tại {image_path}.")           
        else:
            print(f"Không tìm thấy file ảnh tại {image_path}. Vui lòng chọn file ảnh mới.")
            new_image_path = select_image_file(image_path)
            if new_image_path:
                imagePath = new_image_path
                browse_button_location = pyautogui.locateCenterOnScreen(image_path)
                if browse_button_location:
                    print(f"Đã tìm thấy file ảnh tại {image_path}.")
                else:
                    print("Không tìm thấy nút 'Browse' trong file ảnh mới.")
            else:
                print("Không có file ảnh nào được chọn.")
                    
        print(f"Moving to: {browse_button_location}")
        pyautogui.moveTo(browse_button_location)
        time.sleep(2)
        pyautogui.click(browse_button_location)
        # Tìm hộp thoại Open và nhập đường dẫn file
        user_dir = Path("C:/Users/12953 bao/Desktop/desktop/work/Project/Python/BasicLearnPython/W3schools")
        output_path =user_dir / "output.docx"
        print(output_path)
        dlg_open = app.window(title_re=".*Open.*")
        dlg_open.wait('ready', timeout=10)
        dlg_open.type_keys(str(output_path), with_spaces=True, pause=0.1)
        time.sleep(10)

        # Nhấn Enter để mở file
        dlg_open.type_keys('{ENTER}')
        time.sleep(10)  # Chờ để Word tải xong tài liệu

        # Đặt con trỏ vào vị trí cuối của tài liệu
        dlg = app.window(title_re=".*output.docx.*")  # Đảm bảo rằng bạn đang tham chiếu đúng cửa sổ tài liệu
        dlg.type_keys('^{END}') 
        dlg.type_keys('{ENTER}')
        
        # Dán nội dung
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(10)

        # Lưu file (thay đổi đường dẫn và tên file nếu cần)
        try:
             # Sử dụng menu_select linh hoạt hơn
            # menu_item = dlg.child_window(title="File", control_type="MenuItem")
            # menu_item.invoke()
            # save_item = dlg.child_window(title="Save", control_type="MenuItem")
            # save_item.invoke()
            
            pyautogui.hotkey('ctrl', 's') # Nhấn Ctrl+S để lưu
            time.sleep(10)
            
        except pywinauto.application.ElementNotFoundError as e:
            print(f"Không tìm thấy menu: {e}")
        except Exception as e:
            print(f"Lỗi không xác định: {e}")
        finally:
            # Đóng ứng dụng Word
            dlg.close()
    except pywinauto.findwindows.ElementNotFoundError:
        print("Không tìm thấy cửa sổ Word")
    # except Exception as e:
    #     print("Lỗi khác:", e)
    
    

    
def get_absolute_url(base_url, relative_url):
    return urljoin(base_url, relative_url)

base_url = 'https://vi.extendoffice.com'

document = Document()
document.add_paragraph('')  # Tạo một đoạn văn bản trống để dán nội dung
document.save('output.docx') 
# # URL của trang web chứa danh sách các link



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
        driver.quit()
         # Lưu lại document sau mỗi lần copy paste
        document.save(output_path)
        time.sleep(10)
    # Lưu file Word
    # document.save('output.docx') 
    


# URL của trang web
url = "https://vi.extendoffice.com/documents/excel"  # Thay thế bằng URL thực tế

create_word_document(url)