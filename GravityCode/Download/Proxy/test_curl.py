import threading
import time
import subprocess
from server import ProxyServer

def test():
    proxy = ProxyServer(port=8889, mode="DPI_BYPASS")
    proxy.start()
    time.sleep(1)
    print("Running curl...")
    try:
        # Use curl to fetch google.com via the proxy
        result = subprocess.run(["curl", "-x", "http://127.0.0.1:8889", "https://api.github.com/zen", "-s"], capture_output=True, text=True, timeout=10)
        print("CURL stdout:", result.stdout)
        print("CURL stderr:", result.stderr)
    except Exception as e:
        print("CURL Failed:", e)
    proxy.stop()

if __name__ == "__main__":
    test()

