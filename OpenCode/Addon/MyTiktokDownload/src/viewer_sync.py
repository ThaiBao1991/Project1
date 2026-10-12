# -*- coding: utf-8 -*-
"""
viewer_sync.py - Xử lý đồng bộ Web App Viewer (PWA) & Deploy GitHub Pages
- Tạo webapp/data.json từ database Extension
- Deploy an toàn lên GitHub Pages mà không để lộ token vào git config
"""

import os
import sys
import json
import re
import gzip
import base64
import time
import subprocess
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

def _safe_log(msg: str):
    try:
        print(msg)
    except Exception:
        try:
            print(msg.encode("ascii", errors="replace").decode("ascii"))
        except Exception:
            pass

from secret_vault import mask_token, unmask_token, sanitize_git_remote_url, get_git_auth_header

def gh_api(method: str, path: str, token: str, body: dict = None):
    """Gọi GitHub REST API v3 bằng urllib thuần."""
    url = f"https://api.github.com{path}"
    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
        "User-Agent": "TikTok-Viewer-Deployer",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            res_body = r.read().decode("utf-8")
            return (json.loads(res_body) if res_body else {}), r.status
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8")
            return (json.loads(err_body) if err_body else {}), e.code
        except Exception:
            return {}, e.code
    except Exception as e:
        return {"message": str(e)}, 500

def decode_db_file(filepath: Path, var_name: str):
    """Giải mã file database Extension (Base64 + Gzip)."""
    if not filepath.exists():
        return None
    try:
        content = filepath.read_text(encoding="utf-8")
        m = re.search(r'window\.' + re.escape(var_name) + r'\s*=\s*"([^"]+)"', content)
        if not m:
            return None
        raw_b64 = m.group(1)
        decompressed = gzip.decompress(base64.b64decode(raw_b64))
        return json.loads(decompressed.decode("utf-8"))
    except Exception:
        return None

def extract_video_ids(raw):
    """Trích xuất ID video từ nhiều định dạng lưu trữ myfaveTT."""
    ids = []
    if isinstance(raw, dict):
        for val in raw.values():
            if isinstance(val, list):
                ids.extend(str(v) for v in val)
            elif isinstance(val, dict):
                ids.extend(extract_video_ids(val))
    elif isinstance(raw, list):
        ids = [str(v) for v in raw]
    return ids

def build_viewer_data(ext_data_path: Path, output_file: Path, log=_safe_log) -> dict:
    """Đọc dữ liệu Extension và tạo file webapp/data.json cho Web Viewer."""
    appdata = ext_data_path
    if not (appdata / "db_videos.js").exists() and (appdata / "data" / ".appdata").exists():
        appdata = appdata / "data" / ".appdata"

    log("📂 Đang đọc dữ liệu Extension...")
    authors_raw = decode_db_file(appdata / "db_authors.js", "dba_base64") or {}
    log(f"   → {len(authors_raw):,} tác giả trong danh mục")

    videos_raw = decode_db_file(appdata / "db_videos.js", "dbv_base64") or {}
    log(f"   → {len(videos_raw):,} video metadata")

    bookmarked_raw = decode_db_file(appdata / "db_bookmarked.js", "dbb_base64") or {}
    bv_ids = extract_video_ids(bookmarked_raw)
    log(f"   → {len(bv_ids):,} video Favorites")

    likes_raw = decode_db_file(appdata / "db_likes.js", "db_base64") or {}
    lv_ids = extract_video_ids(likes_raw)
    log(f"   → {len(lv_ids):,} video Likes")

    # Xây dựng video map: vid -> (authorId, createTime)
    vm = {}
    for vid, info in videos_raw.items():
        if isinstance(info, dict):
            vm[str(vid)] = (str(info.get("authorId", "")), int(info.get("createTime", 0)))

    # Gom nhóm theo tác giả
    author_data = {}
    def add_videos(id_list, category):
        seen = set()
        for vid in id_list:
            if vid in seen:
                continue
            seen.add(vid)
            aid, ts = vm.get(vid, ("", 0))
            if not aid:
                continue
            if aid not in author_data:
                author_data[aid] = {"b": [], "l": []}
            author_data[aid][category].append([vid, ts])

    add_videos(bv_ids, "b")
    add_videos(lv_ids, "l")

    authors_list = []
    for aid, vids in author_data.items():
        ainfo = authors_raw.get(aid, {})
        unique_ids = ainfo.get("uniqueIds", [])
        nicknames = ainfo.get("nicknames", [])
        vids["b"].sort(key=lambda x: x[1], reverse=True)
        vids["l"].sort(key=lambda x: x[1], reverse=True)
        authors_list.append({
            "id": aid,
            "u": unique_ids[0] if unique_ids else "",
            "n": nicknames[0] if nicknames else "",
            "b": vids["b"],
            "l": vids["l"],
        })

    authors_list.sort(key=lambda x: len(x["b"]) + len(x["l"]), reverse=True)

    total_fav = sum(len(a["b"]) for a in authors_list)
    total_likes = sum(len(a["l"]) for a in authors_list)

    result_data = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "stats": {
            "fav": total_fav,
            "likes": total_likes,
            "authors": len(authors_list),
        },
        "authors": authors_list,
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(result_data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    sz_mb = output_file.stat().st_size / (1024 * 1024)
    log(f"✅ Đã tạo {output_file.name}: {sz_mb:.2f} MB ({len(authors_list)} tác giả, {total_fav} Favs, {total_likes} Likes)")
    return result_data

def run_git_cmd(cmd_args: list, cwd: Path, check: bool = True) -> str:
    """Chạy lệnh Git bằng subprocess."""
    r = subprocess.run(cmd_args, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8")
    if check and r.returncode != 0:
        err = r.stderr.strip() or r.stdout.strip() or f"Git command failed: {' '.join(cmd_args)}"
        raise RuntimeError(err)
    return r.stdout.strip()

def deploy_webapp_to_github(username: str, raw_token: str, reponame: str, webapp_dir: Path, log=_safe_log) -> str:
    """
    Deploy webapp lên GitHub Pages một cách an toàn:
    - Kiểm tra & tạo repo qua GitHub API
    - Dùng in-memory auth header hoặc dọn dẹp remote ngay lập tức để không lưu token vào .git/config
    - Kích hoạt GitHub Pages
    """
    token = raw_token.strip()
    if not token:
        raise ValueError("GitHub Token không được để trống!")
    if not username or not reponame:
        raise ValueError("GitHub Username và Repository Name không được để trống!")

    # 1. Kiểm tra Git đã cài đặt chưa
    try:
        ver = run_git_cmd(["git", "--version"], webapp_dir.parent)
        log(f"🔧 Git version: {ver}")
    except Exception:
        raise RuntimeError("Git chưa được cài đặt trên máy! Tải tại https://git-scm.com/download/win")

    # 2. Kiểm tra hoặc tạo Repo trên GitHub
    log(f"\n🐙 Kiểm tra repository '{username}/{reponame}' trên GitHub...")
    repo_info, status = gh_api("GET", f"/repos/{username}/{reponame}", token)
    if status == 404:
        log(f"   Chưa có repo '{reponame}', đang tự động tạo mới...")
        create_res, create_st = gh_api("POST", "/user/repos", token, {
            "name": reponame,
            "private": False,
            "description": "TikTok Archive Viewer (PWA) - Hosted on GitHub Pages",
            "auto_init": False
        })
        if create_st not in (200, 201):
            msg = create_res.get("message", "Lỗi không xác định")
            raise RuntimeError(f"Tạo repo thất bại ({create_st}): {msg}")
        log(f"   ✅ Đã tạo repo thành công: {username}/{reponame}")
        time.sleep(1)
    elif status == 200:
        log(f"   ✅ Repo đã tồn tại: {username}/{reponame}")
    elif status == 401:
        raise RuntimeError("GitHub Token không hợp lệ hoặc đã hết hạn! Vui lòng kiểm tra lại PAT.")
    else:
        raise RuntimeError(f"Lỗi GitHub API ({status}): {repo_info.get('message', '?')}")

    # 3. Khởi tạo Git trong webapp nếu chưa có
    git_dir = webapp_dir / ".git"
    if not git_dir.exists():
        run_git_cmd(["git", "init", "-b", "main"], webapp_dir, check=False)
        if not (webapp_dir / ".git").exists():
            run_git_cmd(["git", "init"], webapp_dir)
            run_git_cmd(["git", "checkout", "-b", "main"], webapp_dir, check=False)
        log("   ✅ Đã khởi tạo Git repository (branch main)")
    else:
        cur_branch = run_git_cmd(["git", "branch", "--show-current"], webapp_dir, check=False)
        if cur_branch and cur_branch != "main":
            run_git_cmd(["git", "branch", "-m", "main"], webapp_dir, check=False)

    # 4. Cấu hình user email/name cục bộ
    run_git_cmd(["git", "config", "user.email", "tiktokviewer@local.app"], webapp_dir, check=False)
    run_git_cmd(["git", "config", "user.name", "TikTok Viewer Sync"], webapp_dir, check=False)

    # 5. Đảm bảo có .nojekyll để GitHub Pages load đủ file
    nojekyll = webapp_dir / ".nojekyll"
    if not nojekyll.exists():
        nojekyll.write_text("", encoding="utf-8")

    # 6. Commit các thay đổi
    run_git_cmd(["git", "add", "-A"], webapp_dir)
    status_out = run_git_cmd(["git", "status", "--porcelain"], webapp_dir, check=False)
    if status_out:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        run_git_cmd(["git", "commit", "-m", f"sync data: {ts}"], webapp_dir)
        log("   ✅ Đã commit dữ liệu mới")
    else:
        log("   ℹ️ Dữ liệu webapp không thay đổi, chuẩn bị kiểm tra push")

    # 7. Push an toàn:
    # URL sạch trên remote (không chứa token)
    clean_url = sanitize_git_remote_url(username, reponame)
    run_git_cmd(["git", "remote", "remove", "origin"], webapp_dir, check=False)
    run_git_cmd(["git", "remote", "add", "origin", clean_url], webapp_dir)

    # Sử dụng temporary token URL để push rồi NGAY LẬP TỨC đặt lại clean_url
    temp_auth_url = f"https://{token}@github.com/{username}/{reponame}.git"
    log("📤 Đang đẩy dữ liệu lên GitHub Pages...")
    try:
        run_git_cmd(["git", "remote", "set-url", "origin", temp_auth_url], webapp_dir)
        try:
            run_git_cmd(["git", "push", "-u", "origin", "main"], webapp_dir)
        except RuntimeError:
            log("   ⚠️ Remote có nhánh khác, đang force push lên main...")
            run_git_cmd(["git", "push", "-u", "origin", "main", "--force"], webapp_dir)
        log("   ✅ Đã push dữ liệu thành công!")
    finally:
        # BẮT BUỘC: Đặt lại origin về clean URL để tuyệt đối KHÔNG lưu token vào .git/config
        run_git_cmd(["git", "remote", "set-url", "origin", clean_url], webapp_dir, check=False)

    # 8. Kích hoạt GitHub Pages qua API
    log("🌐 Đang cấu hình GitHub Pages...")
    pages_body = {"source": {"branch": "main", "path": "/"}}
    p_resp, p_st = gh_api("POST", f"/repos/{username}/{reponame}/pages", token, pages_body)
    if p_st in (200, 201):
        log("   ✅ GitHub Pages đã được kích hoạt thành công!")
    elif p_st in (409, 422):
        gh_api("PUT", f"/repos/{username}/{reponame}/pages", token, pages_body)
        log("   ✅ GitHub Pages đã được cập nhật cấu hình.")
    elif p_st == 403:
        log("   ℹ️ Quyền Pages cần kích hoạt thủ công trong Settings > Pages nếu repo mới tạo.")

    public_url = f"https://{username}.github.io/{reponame}/"
    log(f"\n🎉 HOÀN TẤT! Web Viewer của bạn:")
    log(f"   👉 {public_url}")
    log("   (Lưu ý: GitHub Pages mất khoảng 1-2 phút trong lần deploy đầu tiên để kích hoạt hoàn toàn)")
    return public_url
