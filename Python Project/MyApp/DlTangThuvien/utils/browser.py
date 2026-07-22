import os
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class BrowserManager:
    def __init__(self, headless=False, user_data_dir=None, cookie_file=None):
        self.headless = headless
        self.user_data_dir = user_data_dir
        self.cookie_file = cookie_file
        self.driver = None
    
    def __enter__(self):
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        if self.user_data_dir:
            chrome_options.add_argument(f'--user-data-dir={self.user_data_dir}')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        
        # Load cookies nếu có
        if self.cookie_file and os.path.exists(self.cookie_file):
            self.load_cookies()
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.driver:
            self.driver.quit()
    
    def navigate(self, url):
        """Điều hướng đến URL"""
        self.driver.get(url)
        time.sleep(2)  # Đợi trang load
    
    def get_page_content(self, url):
        """Lấy nội dung trang"""
        self.navigate(url)
        
        # Đợi content load
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except:
            pass
        
        return self.driver.page_source
    
    def get_cookies(self):
        """Lấy cookies hiện tại"""
        return self.driver.get_cookies()
    
    def load_cookies(self):
        """Load cookies từ file"""
        if os.path.exists(self.cookie_file):
            with open(self.cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
                for cookie in cookies:
                    try:
                        self.driver.add_cookie(cookie)
                    except:
                        pass
    def wait_for_content(self, selector, timeout=10):
        """Đợi content load bằng JavaScript"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
        except:
            pass
        return self.driver.page_source