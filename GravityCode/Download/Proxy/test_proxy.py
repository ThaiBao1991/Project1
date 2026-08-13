import time
import requests
import socket
from server import ProxyServer

def test():
    proxy = ProxyServer(port=9999, mode="DPI_BYPASS")
    proxy.start()
    time.sleep(1)
    print("Testing DPI Bypass Mode...")
    proxies = {"http": "http://127.0.0.1:9999", "https": "http://127.0.0.1:9999"}
    try:
        res = requests.get("https://api.github.com", proxies=proxies, timeout=10)
        print("DPI Bypass Status:", res.status_code)
    except Exception as e:
        print("DPI Bypass Failed:", e)
    proxy.stop()

if __name__ == "__main__":
    test()

