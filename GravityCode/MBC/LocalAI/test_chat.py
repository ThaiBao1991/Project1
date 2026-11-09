"""
Local AI Test Chat Script (OpenAI API Format)
Dùng để chat trực tiếp với Local AI đang chạy tại http://127.0.0.1:8080
"""
import urllib.request
import json
import sys

API_URL = "http://127.0.0.1:8080/v1/chat/completions"

def chat(prompt: str):
    payload = {
        "messages": [
            {"role": "system", "content": "Bạn là trợ lý AI thông minh, nhiệt tình, không phán xét và trả lời bằng tiếng Việt chuẩn xác."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 1024,
        "stream": False
    }
    
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(API_URL, data=data, headers={"Content-Type": "application/json"})
    
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            content = result["choices"][0]["message"]["content"]
            return content
    except urllib.error.URLError as e:
        return f"[LỖI KẾT NỐI] Hãy đảm bảo bạn đã chạy file start_ai.bat trước! Chi tiết: {e}"

if __name__ == "__main__":
    test_prompt = "Xin chào! Bạn là ai và bạn có thể giúp gì cho tôi?"
    print(f">> Gửi câu hỏi thử nghiệm: '{test_prompt}'\n")
    print(">> Đang chờ AI phản hồi...\n")
    reply = chat(test_prompt)
    print(">> Phản hồi từ Local AI:\n")
    print(reply)

