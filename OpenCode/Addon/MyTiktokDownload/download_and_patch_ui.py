"""
Script: download_and_patch_ui.py
Mục đích:
  1. Đảm bảo UI assets đã được tải về custom_extension/unpacked/ui/
  2. Patch UI JS bundle:
     - Gửi postMessage lên parent bằng targetOrigin = "*"
     - Chấp nhận message từ bất kỳ origin dạng chrome-extension:// nào
  3. Patch r.js:
     - Dùng chrome.runtime.getURL("ui/index.html") để tự động khớp với mọi extension ID
     - Gửi postMessage vào iframe với targetOrigin = "*"
     - Nhận tin nhắn từ UI và chuyển về tiktok.com mà không khóa cứng ID
  4. Đồng bộ vào custom_extension/myfaveTTT-custom và zip

Run: python download_and_patch_ui.py
"""

import sys, os, json, re, shutil, zipfile
sys.stdout.reconfigure(encoding="utf-8")
import urllib.request
from pathlib import Path

BASE_DIR      = Path(__file__).resolve().parent
UNPACKED_DIR  = BASE_DIR / "custom_extension" / "unpacked"
MIRROR_DIR    = BASE_DIR / "custom_extension" / "myfaveTTT-custom"
ZIP_PATH      = BASE_DIR / "custom_extension" / "myfaveTTT-custom.zip"
UI_DIR        = UNPACKED_DIR / "ui"
UI_ASSETS_DIR = UI_DIR / "assets"
BASE_URL      = "https://myfavett-ui.vercel.app"

def dl(url: str, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"  -> Download {url}")
    req = urllib.request.urlopen(url, timeout=30)
    data = req.read()
    dest.write_bytes(data)
    print(f"    Saved {len(data)/1024:.1f} KB -> {dest}")
    return data

# ─────────────────────────────────────────────────────────────────
# STEP 1: Download UI nếu chưa có
# ─────────────────────────────────────────────────────────────────
print("\n[1] Kiểm tra UI assets …")
if not (UI_DIR / "index.html").exists() or not list(UI_ASSETS_DIR.glob("*.js")):
    print("    Đang tải UI assets từ Vercel …")
    req = urllib.request.urlopen(BASE_URL, timeout=15)
    html_orig = req.read().decode("utf-8", errors="replace")
    js_files  = re.findall(r'src=["\'](/assets/[^"\']+\.js)',  html_orig)
    css_files = re.findall(r'href=["\'](/assets/[^"\']+\.css)', html_orig)
    
    UI_DIR.mkdir(parents=True, exist_ok=True)
    UI_ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    for js_path in js_files:
        dl(BASE_URL + js_path, UI_DIR / js_path.lstrip("/"))
    for css_path in css_files:
        dl(BASE_URL + css_path, UI_DIR / css_path.lstrip("/"))
        
    html_local = html_orig.replace('src="/assets/', 'src="./assets/').replace('href="/assets/', 'href="./assets/')
    html_local = re.sub(r'\s*<link\s+rel="canonical"[^>]*/>\s*', '\n', html_local)
    (UI_DIR / "index.html").write_text(html_local, encoding="utf-8")
else:
    print("    UI assets đã có sẵn.")

# ─────────────────────────────────────────────────────────────────
# STEP 2: Patch UI JS Bundle (loại bỏ hoàn toàn khóa cứng extension ID)
# ─────────────────────────────────────────────────────────────────
print("\n[2] Patching UI JS bundle …")
js_files = list(UI_ASSETS_DIR.glob("*.js"))
if not js_files:
    print("    [ERROR] Không tìm thấy file JS trong ui/assets/")
    sys.exit(1)

for js_path in js_files:
    js = js_path.read_text(encoding="utf-8")
    original_len = len(js)

    # 1. Patch hàm LS (gửi tin nhắn từ UI lên parent):
    # Gốc: window.parent.postMessage({type:e,payload:t},IS.chromeExtensionOrigin)
    # Patch: window.parent.postMessage({type:e,payload:t},"*")
    ls_pattern = r'window\.parent\.postMessage\(\{type:e,payload:t\},IS\.chromeExtensionOrigin\)'
    if re.search(ls_pattern, js):
        js = re.sub(ls_pattern, 'window.parent.postMessage({type:e,payload:t},"*")', js)
        print("    [OK] Đã patch hàm LS: dùng targetOrigin='*'")
    elif 'window.parent.postMessage({type:e,payload:t},"*")' in js:
        print("    [INFO] Hàm LS đã ở dạng targetOrigin='*'")
    else:
        print("    [WARN] Không tìm thấy pattern hàm LS để thay thế")

    # 2. Patch hàm kV (nhận tin nhắn từ parent):
    # Gốc: if(t!==IS.chromeExtensionOrigin&&t!==location.origin)return;
    # Hoặc nếu đã thay đổi ID
    kv_pattern = r'if\(t!==IS\.chromeExtensionOrigin&&t!==location\.origin\)return;'
    if re.search(kv_pattern, js):
        js = re.sub(kv_pattern, 'if(!t.startsWith("chrome-extension://")&&t!==location.origin&&t!=="null")return;', js)
        print("    [OK] Đã patch hàm kV: chấp nhận mọi origin chrome-extension://")
    elif 't.startsWith("chrome-extension://")' in js:
        print("    [INFO] Hàm kV đã chấp nhận chrome-extension://")
    else:
        # Thử tìm pattern biến thể
        js = re.sub(
            r'if\(!t\.startsWith\("chrome-extension://"\).*?\)return;',
            'if(!t.startsWith("chrome-extension://")&&t!==location.origin&&t!=="null")return;',
            js
        )
        print("    [INFO] Đã cập nhật pattern kiểm tra origin trong kV")

    js_path.write_text(js, encoding="utf-8")
    print(f"    Đã lưu: {js_path.name} ({len(js)} bytes)")

# ─────────────────────────────────────────────────────────────────
# STEP 3: Patch r.js (cầu nối giữa TikTok và UI iframe)
# ─────────────────────────────────────────────────────────────────
print("\n[3] Patching r.js …")
rjs_content = (
    'const e=`https://www.tiktok.com`,'
    't=(typeof chrome!=="undefined"&&chrome.runtime&&chrome.runtime.getURL)?chrome.runtime.getURL(`ui/index.html`):`ui/index.html`,'
    'n=document.createElement(`iframe`);'
    'n.src=t,n.id=`ui`,n.allow=`local-network-access *`,document.body.appendChild(n);'
    'const r=`https://resync.myfavett.com`,i=document.createElement(`iframe`);'
    'i.src=r,i.id=`resync`,document.body.appendChild(i),'
    'window.onmessage=a;'
    'function a(a){'
    'let{origin:o,data:s}=a;'
    'if(o===e)switch(s.direction){case 2:n.contentWindow?.postMessage(s,`*`);return;case 6:i.contentWindow?.postMessage(s,r);return}'
    '(o.startsWith(`chrome-extension://`)||o===location.origin||o===`null`)&&parent.postMessage({direction:3,...s},e),'
    'o===r&&parent.postMessage({direction:7,...s},e)'
    '}'
    'const o=new BroadcastChannel(`myfaveTTT`);'
    'o.onmessage=t=>{let{direction:n}=t.data;n===0&&parent.postMessage(t.data,e)};\n'
)
(UNPACKED_DIR / "r.js").write_text(rjs_content, encoding="utf-8")
print("    [OK] r.js đã được cập nhật với dynamic getURL và targetOrigin='*'")

# ─────────────────────────────────────────────────────────────────
# STEP 4: Cập nhật manifest.json
# ─────────────────────────────────────────────────────────────────
print("\n[4] Patching manifest.json …")
manifest_path = UNPACKED_DIR / "manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

# Đảm bảo web_accessible_resources có ui/*
war = manifest.get("web_accessible_resources", [])
ui_entry = any("ui/*" in r.get("resources", []) for r in war)
if not ui_entry:
    war.append({
        "matches": ["<all_urls>"],
        "resources": ["ui/*", "ui/assets/*"]
    })
    manifest["web_accessible_resources"] = war
    print("    [OK] Thêm ui/* vào web_accessible_resources")

manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

# ─────────────────────────────────────────────────────────────────
# STEP 5: Đồng bộ sang myfaveTTT-custom và đóng gói zip
# ─────────────────────────────────────────────────────────────────
print("\n[5] Mirroring & Packaging …")
if MIRROR_DIR.exists():
    shutil.rmtree(MIRROR_DIR)
shutil.copytree(UNPACKED_DIR, MIRROR_DIR)
print(f"    [OK] Đã đồng bộ sang {MIRROR_DIR.name}")

if ZIP_PATH.exists():
    ZIP_PATH.unlink()
with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
    for fp in sorted(UNPACKED_DIR.rglob("*")):
        if fp.is_file():
            zf.write(fp, fp.relative_to(UNPACKED_DIR))
print(f"    [OK] Đã tạo gói zip: {ZIP_PATH.name} ({ZIP_PATH.stat().st_size / 1024:.1f} KB)")

print("\n🎉 HOÀN TẤT: Extension UI đã hoạt động độc lập và không phụ thuộc Extension ID!")
