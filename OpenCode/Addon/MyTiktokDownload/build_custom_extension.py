#!/usr/bin/env python3
import os
import json
import zipfile
import shutil
import re
from pathlib import Path

ORIGINAL_EXT_PATH = Path(r"C:\Users\games\AppData\Local\Google\Chrome\User Data\Default\Extensions\ljglajjnnkapghbckkcmodicjhacbfhk\2.70.0.35_0")
OUTPUT_DIR = Path(r"C:\Users\games\Desktop\Project\Python\Python MyWork\Project1\OpenCode\Addon\MyTiktokDownload\custom_extension")

class ExtensionPatcher:
    def __init__(self):
        self.original_path = ORIGINAL_EXT_PATH
        self.output_dir = Path(r"C:\Users\games\Desktop\Project\Python\Python MyWork\Project1\OpenCode\Addon\MyTiktokDownload\custom_extension")
        self.unpack_dir = self.output_dir / "unpacked"
        self.dist_dir = self.output_dir / "dist"
        
    def run(self):
        print("[BUILD] Bat dau build custom extension...")
        self.clean()
        self.unpack()
        self.patch_manifest()
        self.patch_sjs()
        self.create_zip()
        self.create_crx_info()
        print(f"\n[DONE] Hoan tat! Custom extension tai: {self.dist_dir}")
        print(f"   - Folder unpacked: {self.unpack_dir}")
        print(f"   - File .zip: {self.dist_dir / 'myfaveTT-custom.zip'}")
        print(f"   - Load unpacked tu: {self.unpack_dir}")
        
    def clean(self):
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        self.unpack_dir.mkdir(parents=True)
        self.dist_dir = self.output_dir / "dist"
        self.dist_dir.mkdir(parents=True)
        
    def unpack(self):
        print("[UNPACK] Unpacking original extension...")
        shutil.copytree(self.original_path, self.unpack_dir)
        print(f"   [OK] Unpacked to: {self.unpack_dir}")
        
    def patch_manifest(self):
        print("[PATCH] Patching manifest.json...")
        manifest_path = self.unpack_dir / "manifest.json"
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        manifest["name"] = "myfaveTT Custom (Stop on Error)"
        manifest["version"] = "2.70.0.36"
        manifest["description"] = "myfaveTT with stop-on-error + error UI for failed videos"
        manifest["author"] = "Custom Build"
        
        if "web_accessible_resources" not in manifest:
            manifest["web_accessible_resources"] = []
        manifest["web_accessible_resources"].append({
            "resources": ["s.js", "rl.html"],
            "matches": ["https://www.tiktok.com/*"]
        })
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        print("   [OK] manifest.json patched")
        
    def patch_sjs(self):
        print("[PATCH] Patching s.js (adding stop-on-error)...")
        sjs_path = self.unpack_dir / "s.js"
        
        if not sjs_path.exists():
            print("   [ERR] Khong tim thay s.js")
            return
            
        content = sjs_path.read_text(encoding='utf-8')
        
        if "STOP_ON_ERROR_PATCH" in content:
            print("   [INFO] Da patched truoc do")
            return
            
        if len(content) > 50000 and content.count('\n') < 100:
            print("   [INFO] Beautifying minified JS...")
            content = self.beautify_js(content)
        
        patched_content = self.inject_stop_on_error(content)
        
        sjs_path.write_text(patched_content, encoding='utf-8')
        print("   [OK] s.js patched with stop-on-error")
        
    def beautify_js(self, js):
        js = re.sub(r'([{};,])\s*', r'\1\n', js)
        js = re.sub(r'}\s*else', '}\nelse', js)
        js = re.sub(r'}\s*catch', '}\ncatch', js)
        js = re.sub(r'\)\s*{', ')\n{', js)
        
        lines = js.split('\n')
        indent = 0
        result = []
        for line in lines:
            line = line.strip()
            if not line:
                result.append('')
                continue
            if line.startswith('}') or line.startswith('else') or line.startswith('catch') or line.startswith('finally'):
                indent = max(0, indent - 1)
            result.append('  ' * indent + line)
            if line.endswith('{') or line.endswith(':'):
                indent += 1
        return '\n'.join(result)
    
    def inject_stop_on_error(self, content):
        patterns = [
            r'(async\s+function\s+\w+\s*\([^)]*\)\s*\{[\s\S]*?)(catch\s*\([^)]*\)\s*\{[\s\S]*?)(continue\s*;)',
            r'(for\s*\([^)]+\)\s*\{[\s\S]*?try\s*\{[\s\S]*?\}catch\s*\([^)]*\)\s*\{[\s\S]*?)(continue\s*;)',
            r'(\.catch\s*\([^)]*\)\s*\{[\s\S]*?)(console\.(error|log)\s*\([^)]*\)\s*;?\s*)(return|\}\s*\))',
        ]
        
        for i, pattern in enumerate(patterns):
            match = re.search(pattern, content, re.MULTILINE)
            if match:
                print(f"   [OK] Found pattern {i+1} at position {match.start()}")
                before = match.group(1)
                catch_block = match.group(2)
                after = match.group(3)
                
                injected = before + catch_block + '\n        // ===== STOP_ON_ERROR PATCH =====\n'
                injected += '''        const errorInfo = {
            videoId: video.id,
            url: `https://www.tiktok.com/@${video.author?.uniqueId || 'unknown'}/video/${video.id}`,
            error: error.message,
            timestamp: new Date().toISOString()
        };
        
        showErrorUI(errorInfo);
        throw new Error(`STOP_ON_ERROR:${JSON.stringify(errorInfo)}`);
        // ===== END STOP_ON_ERROR PATCH =====
        '''
        injected += after
        
        content = content[:match.start()] + injected + content[match.end():]
        return content
    
    # If no pattern matched
    print("   [WARN] Khong tim thay pattern chuan, dung fallback: wrap downloadVideo")
    content = self.fallback_wrap(content)
    content += STOP_ON_ERROR_PATCH
    return content
    
    def fallback_wrap(self, content):
        patterns = [
            r'(async\s+function\s+downloadVideo\s*\([^)]*\)\s*\{)',
            r'(function\s+downloadVideo\s*\([^)]*\)\s*\{)',
            r'(const\s+downloadVideo\s*=\s*async\s*\([^)]*\)\s*=>\s*\{)',
            r'(const\s+downloadVideo\s*=\s*\([^)]*\)\s*=>\s*\{)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                pos = match.start()
                wrapper = '''
// ===== STOP_ON_ERROR WRAPPER =====
const originalDownloadVideo = downloadVideo;
async function downloadVideo(...args) {
    try {
        return await originalDownloadVideo(...args);
    } catch (error) {
        const video = args[0];
        const errorInfo = {
            videoId: video?.id || 'unknown',
            url: `https://www.tiktok.com/@${video?.author?.uniqueId || 'unknown'}/video/${video?.id || 'unknown'}`,
            error: error.message,
            timestamp: new Date().toISOString()
        };
        showErrorUI(errorInfo);
        throw new Error(`STOP_ON_ERROR:${JSON.stringify(errorInfo)}`);
    }
// ===== END WRAPPER =====
'''
        return content[:pos] + wrapper + content[pos:]
        
        print("   [WARN] Khong tim thay downloadVideo, append at end")
        return content + '\n' + STOP_ON_ERROR_PATCH
    
    def create_zip(self):
        print("[ZIP] Creating .zip for distribution...")
        zip_path = self.dist_dir / "myfaveTT-custom.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in self.unpack_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(self.unpack_dir)
                    zf.write(file_path, arcname)
        print(f"   [OK] Created: {zip_path}")
        
    def create_crx_info(self):
        info = f"""# myfaveTT Custom (Stop on Error) - Installation Guide

## Cai dat:

### Cach 1: Load Unpacked (Khuyen dung)
1. Mo Chrome -> chrome://extensions/
2. Bat Developer mode (goc tren phai)
3. Click Load unpacked
4. Chon folder: {self.unpack_dir}

### Cach 2: Cai tu .zip (can developer mode)
1. Giai nen file: {self.dist_dir / 'myfaveTT-custom.zip'}
2. Load unpacked folder giai nen

## Tinh nang moi:
[OK] Stop on error - Dung khi video loi
[OK] Hien thi UI loi tren sidebar (goc tren phai)
[OK] Hien thi: Video ID, URL, Loi chi tiet
[OK] Nut Copy Link de copy link video loi
[OK] Dung toan bo qua trinh tai khi gap loi

## So sanh voi ban goc:
| Tinh nang | Ban goc | Custom |
|-----------|---------|--------|
| Stop on error | No | Yes |
| Hien link loi tren UI | No | Yes |
| Nut Copy Link | No | Yes |
| Dung khi loi | No | Yes |
| Phan tich loi chi tiet | No | Yes |

## Files da sua:
- manifest.json: version 2.70.0.36, name myfaveTT Custom (Stop on Error)
- s.js: Injected stop-on-error patch + showErrorUI()

## Load unpacked path:
{self.unpack_dir}
"""
        info_path = self.dist_dir / "INSTALL.md"
        info_path.write_text(info, encoding='utf-8')
        print(f"   [OK] Created: {info_path}")


STOP_ON_ERROR_PATCH = '''
// ===== STOP_ON_ERROR PATCH START =====
function showErrorUI(errorInfo) {
    let container = document.getElementById('myfaveTT-error-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'myfaveTT-error-container';
        container.style.cssText = 'position:fixed;top:10px;right:10px;z-index:9999;max-width:420px;font-family:system-ui,sans-serif;';
        document.body.appendChild(container);
    }
    
    container.innerHTML = `
        <div style="background:#fff3f3;border:2px solid #f88;border-radius:8px;padding:16px;margin-bottom:10px;box-shadow:0 4px 12px rgba(0,0,0,0.15);font-family:system-ui,sans-serif;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                <h3 style="margin:0;color:#c00;font-size:16px;">Video tai that bai - DA DUNG</h3>
                <button onclick="this.parentElement.parentElement.remove()" style="background:none;border:none;font-size:20px;cursor:pointer;color:#888;">x</button>
            </div>
            <div style="font-size:13px;line-height:1.6;color:#333;">
                <div style="margin-bottom:8px;"><strong>Video ID:</strong> <code>${errorInfo.videoId}</code></div>
                <div style="margin-bottom:8px;"><strong>URL:</strong> <a href="${errorInfo.url}" target="_blank" style="color:#0066cc;word-break:break-all;">${errorInfo.url}</a></div>
                <div style="margin-bottom:12px;"><strong>Loi:</strong> <span style="color:#c00;font-family:monospace;font-size:12px;">${errorInfo.error}</span></div>
                <button onclick="navigator.clipboard.writeText('${errorInfo.url.replace(/'/g, "\\\\'")}");this.textContent='Da copy!';setTimeout(()=>this.textContent='Copy Link',2000)" style="width:100%;padding:10px;background:#0066cc;color:white;border:none;border-radius:4px;cursor:pointer;font-weight:bold;">Copy Link Video Loi</button>
            </div>
        </div>
    `;
    container.scrollIntoView({behavior: 'smooth'});
}

async function downloadWithStopOnError(video) {
    try {
        const result = await downloadVideo(video.id, video.data);
        return { success: true, videoId: video.id };
    } catch (error) {
        const errorInfo = {
            videoId: video.id,
            url: `https://www.tiktok.com/@${video.author?.uniqueId || 'unknown'}/video/${video.id}`,
            error: error.message,
            timestamp: new Date().toISOString()
        };
        
        showErrorUI(errorInfo);
        throw new Error(`STOP_ON_ERROR:${JSON.stringify(errorInfo)}`);
    }
}
// ===== STOP_ON_ERROR PATCH END =====
'''

if __name__ == "__main__":
    patcher = ExtensionPatcher()
    patcher.run()