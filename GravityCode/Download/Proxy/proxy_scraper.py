import requests
import random

class ProxyScraper:
    def __init__(self):
        self.proxies = []

    def fetch_proxies(self):
        try:
            # Lấy danh sách proxy HTTP từ repo công khai
            url = "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                lines = resp.text.split("\n")
                self.proxies = [line.strip() for line in lines if line.strip()]
        except Exception as e:
            print(f"Lỗi khi lấy proxy: {e}")

    def get_working_proxy(self):
        # Lấy danh sách proxy
        if not self.proxies:
            self.fetch_proxies()

        if not self.proxies:
            return None

        import concurrent.futures
        random.shuffle(self.proxies)
        
        # Test 50 proxy cùng lúc để tìm cái sống sót nhanh nhất
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = {executor.submit(self.test_proxy, p): p for p in self.proxies[:50]}
            for future in concurrent.futures.as_completed(futures):
                if future.result(): # Nếu test_proxy trả về True
                    # Hủy các task còn lại (không bắt buộc nhưng tốt cho hiệu suất)
                    return futures[future]
        return None

    def test_proxy(self, proxy_addr):
        try:
            proxies = {
                "http": f"http://{proxy_addr}",
                "https": f"http://{proxy_addr}",
            }
            # Thay đổi từ github sang openai để test proxy có vượt được Cloudflare không
            res = requests.get("https://auth.openai.com", proxies=proxies, timeout=5)
            # OpenAI / Cloudflare thường trả về 403, 404, hoặc 200 nếu kết nối thành công. 
            # Bất kể mã nào, miễn là không ném ra ngoại lệ (exception) thì nghĩa là kết nối được.
            return True
        except:
            pass
        return False
