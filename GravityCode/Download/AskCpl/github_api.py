import os
import requests
import base64
import time

class GitHubSync:
    def __init__(self, username: str, token: str, repo_name: str, log_callback=None):
        self.username = username
        self.token = token
        self.repo_name = repo_name
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        self.api = "https://api.github.com"
        self.log_callback = log_callback
        
    def _log(self, msg):
        if self.log_callback:
            self.log_callback(msg)
        else:
            print(f"[GitHub Sync] {msg}")

    def _request_with_retry(self, method, url, **kwargs):
        max_retries = 3
        backoff = 2
        for i in range(max_retries):
            try:
                r = requests.request(method, url, **kwargs)
                if r.status_code in [500, 502, 503, 504]:
                    self._log(f"⚠️ GitHub server lỗi {r.status_code} (Quá tải). Thử lại lần {i+1} sau {backoff}s...")
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                return r
            except requests.exceptions.RequestException as e:
                self._log(f"⚠️ Lỗi kết nối: {e}. Thử lại lần {i+1} sau {backoff}s...")
                time.sleep(backoff)
                backoff *= 2
        # Lần thử cuối cùng
        return requests.request(method, url, **kwargs)

    def create_repo_if_not_exists(self):
        url = f"{self.api}/repos/{self.username}/{self.repo_name}"
        resp = self._request_with_retry("GET", url, headers=self.headers)
        if resp.status_code == 200:
            self._log(f"Repository '{self.repo_name}' đã tồn tại.")
            return True
            
        self._log(f"Đang tạo repository mới: {self.repo_name}...")
        create_url = f"{self.api}/user/repos"
        data = {
            "name": self.repo_name,
            "private": False,
            "auto_init": True
        }
        resp = self._request_with_retry("POST", create_url, headers=self.headers, json=data)
        if resp.status_code in [200, 201]:
            self._log(f"Đã tạo thành công repository '{self.repo_name}'.")
            return True
        else:
            self._log(f"Lỗi tạo repository: {resp.text}")
            return False

    def enable_pages(self, branch: str):
        self._log("Đang cấu hình GitHub Pages...")
        url = f"{self.api}/repos/{self.username}/{self.repo_name}/pages"
        payload = {"source": {"branch": branch, "path": "/"}}
        r = self._request_with_retry("POST", url, headers=self.headers, json=payload)
        if r.status_code in (200, 201):
            self._log("🌐 GitHub Pages đã được bật thành công!")
        elif r.status_code == 409:
            self._log("🌐 GitHub Pages đã được bật từ trước.")
        else:
            self._log(f"⚠️ Lỗi cấu hình GitHub Pages: {r.status_code} - {r.text}")

    def get_pages_url(self) -> str:
        url = f"{self.api}/repos/{self.username}/{self.repo_name}/pages"
        r = self._request_with_retry("GET", url, headers=self.headers)
        if r.status_code == 200:
            return r.json().get("html_url", "")
        return f"https://{self.username}.github.io/{self.repo_name}/"

    def upload_folder(self, folder_path: str):
        if not self.create_repo_if_not_exists():
            return False
            
        self._log(f"Đang bắt đầu đồng bộ thư mục: {folder_path}")
        
        url_branch = f"{self.api}/repos/{self.username}/{self.repo_name}/branches/main"
        resp = self._request_with_retry("GET", url_branch, headers=self.headers)
        branch_name = "main"
        
        if resp.status_code != 200:
            self._log("Không tìm thấy nhánh main, đang kiểm tra nhánh master...")
            url_branch = f"{self.api}/repos/{self.username}/{self.repo_name}/branches/master"
            resp = self._request_with_retry("GET", url_branch, headers=self.headers)
            if resp.status_code != 200:
                self._log("Lỗi: Không tìm thấy nhánh main hoặc master.")
                return False
            branch_name = "master"

        branch_data = resp.json()
        latest_commit_sha = branch_data["commit"]["sha"]
        base_tree_sha = branch_data["commit"]["commit"]["tree"]["sha"]
        
        tree_items = []
        has_readme = False

        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, folder_path).replace("\\", "/")
                
                if rel_path.lower() == "readme.md":
                    has_readme = True

                try:
                    with open(file_path, "rb") as f:
                        content = f.read()
                    
                    blob_url = f"{self.api}/repos/{self.username}/{self.repo_name}/git/blobs"
                    blob_data = {
                        "content": base64.b64encode(content).decode("utf-8"),
                        "encoding": "base64"
                    }
                    blob_resp = self._request_with_retry("POST", blob_url, headers=self.headers, json=blob_data)
                    
                    if blob_resp.status_code == 201:
                        blob_sha = blob_resp.json()["sha"]
                        tree_items.append({
                            "path": rel_path,
                            "mode": "100644",
                            "type": "blob",
                            "sha": blob_sha
                        })
                        self._log(f"Đã xử lý file: {rel_path}")
                    else:
                        self._log(f"Lỗi khi xử lý file {rel_path}: {blob_resp.text}")
                        
                    # Thêm khoảng nghỉ cực ngắn (0.05s) để tránh bị GitHub chặn do spam request
                    time.sleep(0.05)
                except Exception as e:
                    self._log(f"Lỗi đọc file {rel_path}: {e}")

        # Lấy cây hiện tại từ GitHub để tìm file đã xóa cục bộ
        tree_url = f"{self.api}/repos/{self.username}/{self.repo_name}/git/trees/{base_tree_sha}?recursive=1"
        resp = self._request_with_retry("GET", tree_url, headers=self.headers)
        if resp.status_code == 200:
            gh_tree = resp.json().get("tree", [])
            local_paths = {item["path"] for item in tree_items}
            for gh_item in gh_tree:
                if gh_item["type"] == "blob" and gh_item["path"] not in local_paths:
                    tree_items.append({
                        "path": gh_item["path"],
                        "mode": "100644",
                        "type": "blob",
                        "sha": None  # Đánh dấu xóa file trên GitHub
                    })
                    self._log(f"Đã đánh dấu xóa file trên GitHub: {gh_item['path']}")

        # Tự động tạo README.md nếu chưa có
        if not has_readme:
            pages_url = self.get_pages_url()
            readme_content = f"# {self.repo_name}\n\nĐược tự động đồng bộ từ **AskCpl**.\n\n🌐 **Xem trang web tại đây:** [{pages_url}]({pages_url})\n"
            
            blob_url = f"{self.api}/repos/{self.username}/{self.repo_name}/git/blobs"
            blob_data = {
                "content": base64.b64encode(readme_content.encode("utf-8")).decode("utf-8"),
                "encoding": "base64"
            }
            blob_resp = self._request_with_retry("POST", blob_url, headers=self.headers, json=blob_data)
            if blob_resp.status_code == 201:
                tree_items.append({
                    "path": "README.md",
                    "mode": "100644",
                    "type": "blob",
                    "sha": blob_resp.json()["sha"]
                })
                self._log("Đã tự động tạo README.md")

        if not tree_items:
            self._log("Không có file nào để đẩy lên hoặc tất cả đều lỗi.")
            return True

        self._log("Đang tạo Git Tree (Xây dựng phân mảnh để tránh timeout)...")
        chunk_size = 250
        current_base_tree = base_tree_sha
        
        for i in range(0, len(tree_items), chunk_size):
            chunk = tree_items[i : i + chunk_size]
            self._log(f" -> Tạo Git Tree chunk {i // chunk_size + 1} ({len(chunk)} files)...")
            
            tree_url = f"{self.api}/repos/{self.username}/{self.repo_name}/git/trees"
            tree_data = {
                "base_tree": current_base_tree,
                "tree": chunk
            }
            tree_resp = self._request_with_retry("POST", tree_url, headers=self.headers, json=tree_data)
            if tree_resp.status_code != 201:
                self._log(f"Lỗi tạo Git Tree (chunk {i // chunk_size + 1}): {tree_resp.text}")
                return False
            
            # Dùng tree sha mới làm base_tree cho lượt tiếp theo
            current_base_tree = tree_resp.json()["sha"]
            time.sleep(0.5) # Khoảng nghỉ ngắn để server kịp đồng bộ
            
        new_tree_sha = current_base_tree

        self._log("Đang tạo Git Commit...")
        commit_url = f"{self.api}/repos/{self.username}/{self.repo_name}/git/commits"
        commit_data = {
            "message": "Auto-upload from AskCpl",
            "tree": new_tree_sha,
            "parents": [latest_commit_sha]
        }
        commit_resp = self._request_with_retry("POST", commit_url, headers=self.headers, json=commit_data)
        if commit_resp.status_code != 201:
            self._log(f"Lỗi tạo Commit: {commit_resp.text}")
            return False
        new_commit_sha = commit_resp.json()["sha"]

        self._log(f"Đang cập nhật nhánh {branch_name}...")
        ref_url = f"{self.api}/repos/{self.username}/{self.repo_name}/git/refs/heads/{branch_name}"
        ref_data = {
            "sha": new_commit_sha,
            "force": True
        }
        ref_resp = self._request_with_retry("PATCH", ref_url, headers=self.headers, json=ref_data)
        if ref_resp.status_code != 200:
            self._log(f"Lỗi cập nhật Ref: {ref_resp.text}")
            return False

        self._log("Đồng bộ lên GitHub thành công!")
        
        # Bật GitHub Pages và in URL
        self.enable_pages(branch_name)
        final_url = self.get_pages_url()
        self._log("-" * 40)
        self._log(f"🚀 XEM TRANG WEB CỦA BẠN TẠI ĐÂY: {final_url}")
        self._log("-" * 40)
        
        return True
