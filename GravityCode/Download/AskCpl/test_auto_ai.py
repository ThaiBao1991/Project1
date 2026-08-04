import sys
import os
sys.path.append(r"c:\Users\12953 bao\Desktop\desktop\work\Project\Python\BasicLearnPython\W3schools\Python Tutorial\GravityCode\Download\AskCpl")
import base64
import time
from settings import load_settings
from auto_ai_worker import run_auto_ai

def get_active_api_keys():
    state = load_settings()
    keys = state.get("gemini", {}).get("api_keys", [])
    active_keys = [k for k in keys if k.get("status") == "active"]
    return active_keys

def logger(msg):
    print(msg)

def test_run_ai():
    api_keys = get_active_api_keys()
    if not api_keys:
        print("Không tìm thấy API Key nào đang active.")
        return
        
    roadmap_path = r"c:\Users\12953 bao\Desktop\desktop\work\Project\Python\BasicLearnPython\W3schools\Python Tutorial\GravityCode\Download\AskCpl\test_roadmap.md"
    doc_dir = r"c:\Users\12953 bao\Desktop\desktop\work\Project\Python\BasicLearnPython\W3schools\Python Tutorial\GravityCode\Download\AskCpl\docs"
    out_dir = r"c:\Users\12953 bao\Desktop\desktop\work\Project\Python\BasicLearnPython\W3schools\Python Tutorial\GravityCode\Download\AskCpl\test_output"
    
    os.makedirs(doc_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)
    
    # Clean previous output
    session_file = os.path.join(out_dir, "session.json")
    if os.path.exists(session_file):
        os.remove(session_file)

    print("=== BẮT ĐẦU CHẠY AUTO AI WORKER ===")
    run_auto_ai(
        api_keys_list=api_keys, 
        roadmap_path=roadmap_path, 
        doc_dir=doc_dir, 
        out_dir=out_dir, 
        log_callback=logger,
        force=True, 
        enable_followup=False, 
        max_followup=0, 
        start_day=1,
        adaptive_mode=False,
        generate_visuals=False
    )
    
    # Read output
    if os.path.exists(session_file):
        print("\n=== KẾT QUẢ ĐÃ LƯU VÀO SESSION.JSON ===")
        import urllib.parse
        import json
        with open(session_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content.startswith('"') and content.endswith('"'):
                content = content[1:-1]
                decoded_bytes = base64.b64decode(content)
                decoded_latin = decoded_bytes.decode('latin-1')
                json_str = urllib.parse.unquote(decoded_latin)
                data = json.loads(json_str)
                print(json.dumps(data, ensure_ascii=False, indent=2))
            else:
                print(content)
                
    # In ra the markdown output generated
    md_file = os.path.join(out_dir, "Day1.md")
    if os.path.exists(md_file):
        print("\n=== KẾT QUẢ CỦA BÀI HỌC DAY 1 ===")
        with open(md_file, "r", encoding="utf-8") as f:
            print(f.read()[:2000] + "\n... [TRUNCATED] ...")

if __name__ == "__main__":
    test_run_ai()
