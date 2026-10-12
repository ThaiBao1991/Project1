"""
Config Manager - Quản lý cấu hình OpenCode với Key Manager tích hợp
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

# Import key manager
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from key_manager import (
    APIKey, KeyPool, GeminiCoordinator, OpenRouterCoordinator,
    DeepSeekCoordinator, GroqCoordinator, ErrorKind,
    pace, track_call, get_account_daily_calls, get_today_call_stats,
    MODEL_FALLBACKS
)


@dataclass
class ModelInfo:
    id: str
    provider: str
    is_free: bool
    supports_vision: bool
    notes: str = ""


class ConfigManager:
    def __init__(self, base_path: str = None):
        if base_path is None:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.base_path = Path(base_path)
        self.opencode_json = self.base_path.parent.parent / "opencode.json"
        self.opencode_setting = self.base_path / ".opencode"
        self.auth_json = Path(os.environ.get("LOCALAPPDATA", "")) / "opencode" / "auth.json"
        if not self.auth_json.exists():
            self.auth_json = Path.home() / ".local" / "share" / "opencode" / "auth.json"
        
        # Key manager settings file
        self.keys_setting = self.opencode_setting / "api_keys.json"
        self._key_pools: Dict[str, KeyPool] = {}

    # ========== OpenCode Config ==========
    def load_opencode_config(self) -> Dict:
        if self.opencode_json.exists():
            with open(self.opencode_json, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def save_opencode_config(self, config: Dict):
        with open(self.opencode_json, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    def get_current_model(self) -> str:
        config = self.load_opencode_config()
        return config.get("model", "opencode/nemotron-3-ultra-free")

    def set_current_model(self, model: str):
        config = self.load_opencode_config()
        config["model"] = model
        self.save_opencode_config(config)

    def get_providers(self) -> List[str]:
        config = self.load_opencode_config()
        return config.get("providers", ["opencode"])

    def set_providers(self, providers: List[str]):
        config = self.load_opencode_config()
        config["providers"] = providers
        self.save_opencode_config(config)

    # ========== Auth (OpenCode native) ==========
    def load_auth(self) -> Dict:
        if self.auth_json.exists():
            with open(self.auth_json, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def save_auth(self, auth: Dict):
        self.auth_json.parent.mkdir(parents=True, exist_ok=True)
        with open(self.auth_json, 'w', encoding='utf-8') as f:
            json.dump(auth, f, indent=2, ensure_ascii=False)

    def get_api_key(self, provider: str) -> Optional[str]:
        auth = self.load_auth()
        return auth.get(provider, {}).get("key")

    def set_api_key(self, provider: str, key: str, key_type: str = "api"):
        auth = self.load_auth()
        auth[provider] = {"type": key_type, "key": key}
        self.save_auth(auth)

    def remove_api_key(self, provider: str):
        auth = self.load_auth()
        if provider in auth:
            del auth[provider]
            self.save_auth(auth)

    # ========== Key Manager (Antigravity style) ==========
    def load_keys(self, provider: str = "google") -> List[Dict]:
        """Load keys từ api_keys.json"""
        if self.keys_setting.exists():
            with open(self.keys_setting, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get(provider, [])
        return []

    def save_keys(self, provider: str, keys: List[Dict]):
        """Lưu keys vào api_keys.json"""
        data = {}
        if self.keys_setting.exists():
            with open(self.keys_setting, 'r', encoding='utf-8') as f:
                data = json.load(f)
        data[provider] = keys
        # Tạo thư mục nếu chưa có
        self.keys_setting.parent.mkdir(parents=True, exist_ok=True)
        with open(self.keys_setting, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_key_pool(self, provider: str = "google") -> KeyPool:
        """Lấy hoặc tạo KeyPool cho provider"""
        if provider not in self._key_pools:
            pool = KeyPool()
            pool.load_from_list(self.load_keys(provider))
            self._key_pools[provider] = pool
        return self._key_pools[provider]

    def add_key(self, provider: str, key: str, email: str, project_id: str = "") -> APIKey:
        """Thêm key mới"""
        pool = self.get_key_pool(provider)
        ak = APIKey(key=key, email=email, project_id=project_id)
        ak.set_raw_key(key)
        pool._keys.append(ak)
        self.save_keys(provider, pool.to_list())
        return ak

    def remove_key(self, provider: str, key_obj: APIKey):
        """Xóa key"""
        pool = self.get_key_pool(provider)
        pool._keys = [k for k in pool._keys if k.get_raw_key() != key_obj.get_raw_key()]
        self.save_keys(provider, pool.to_list())

    def update_key_status(self, provider: str, key_obj: APIKey, status: str, error_msg: str = "", cooldown_until: int = 0):
        """Cập nhật trạng thái key"""
        pool = self.get_key_pool(provider)
        for k in pool._keys:
            if k.get_raw_key() == key_obj.get_raw_key():
                k.status = status
                k.error_msg = error_msg
                k.last_check_time = int(time.time())
                if status == "exhausted":
                    k.reset_time = int(time.time()) + 86400
                    k.next_check_time = int(time.time()) + 10800
                if cooldown_until > 0:
                    k.cooldown_until = cooldown_until
                break
        self.save_keys(provider, pool.to_list())

    def test_key(self, provider: str, key_obj: APIKey, model: str = None) -> Dict:
        """Test 1 key cụ thể"""
        import time
        if provider == "google":
            coord = GeminiCoordinator(log_fn=lambda m: None)
            return coord.request("Test ping", timeout=30)
        elif provider == "openrouter":
            coord = OpenRouterCoordinator(key_obj.get_raw_key())
            return coord.request("Test ping", model=model)
        elif provider == "deepseek":
            coord = DeepSeekCoordinator(key_obj.get_raw_key())
            return coord.request("Test ping", model=model)
        elif provider == "groq":
            coord = GroqCoordinator(key_obj.get_raw_key())
            return coord.request("Test ping", model=model)
        return {"ok": False, "error": {"kind": "unknown", "message": "Provider not supported"}}

    # ========== Skills ==========
    def list_skills(self) -> List[Dict]:
        skills_json = self.opencode_setting / "skills.json"
        if not skills_json.exists():
            return []
        with open(skills_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
        skills = []
        for entry in data.get("entries", []):
            path = Path(entry["path"])
            if path.exists():
                for skill_dir in path.iterdir():
                    if skill_dir.is_dir():
                        skill_md = skill_dir / "SKILL.md"
                        desc = ""
                        if skill_md.exists():
                            with open(skill_md, 'r', encoding='utf-8') as f:
                                lines = f.readlines()
                                for line in lines:
                                    if line.startswith("# Skill:") or line.startswith("# "):
                                        desc = line.replace("# Skill:", "").replace("#", "").strip()
                                        break
                        skills.append({
                            "name": skill_dir.name,
                            "path": str(skill_dir),
                            "description": desc,
                            "has_skill_md": skill_md.exists()
                        })
        return skills

    # ========== Rules ==========
    def load_rules(self) -> str:
        rules_file = self.opencode_setting / "AGENTS.md"
        if rules_file.exists():
            with open(rules_file, 'r', encoding='utf-8') as f:
                return f.read()
        return ""

    def save_rules(self, content: str):
        rules_file = self.opencode_setting / "AGENTS.md"
        with open(rules_file, 'w', encoding='utf-8') as f:
            f.write(content)

    # ========== Models ==========
    def get_opencode_models(self) -> List[str]:
        try:
            result = subprocess.run(
                ["opencode", "models"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                return [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
        except Exception:
            pass
        return []

    def check_model_free(self, model_id: str) -> ModelInfo:
        provider = model_id.split('/')[0] if '/' in model_id else "opencode"
        model_name = model_id.split('/')[-1] if '/' in model_id else model_id

        free_keywords = ['-free', 'free-', 'exo-free', 'big-pickle']
        is_free = any(kw in model_name.lower() for kw in free_keywords)

        vision_keywords = ['vision', 'flash', 'gemini', 'gpt-4o', 'gpt-4.1', 'claude-3.5', 'claude-3.7']
        supports_vision = any(kw in model_name.lower() for kw in vision_keywords)

        notes = ""
        if provider == "opencode" and not is_free:
            notes = "Cần tài khoản opencode có tiền"
        elif provider == "google":
            notes = "Free tier: 15 RPM, 1.5M tokens/ngày (cần API key Google AI Studio)"
        elif provider == "openrouter":
            if ":free" in model_id:
                is_free = True
                notes = "Free trên OpenRouter (cần đăng ký)"
            else:
                notes = "Trả phí hoặc cần credit"
        elif "deepseek" in model_id.lower():
            notes = "DeepSeek: free tier 50 req/ngày trên deepseek.com, hoặc qua OpenRouter"

        return ModelInfo(
            id=model_id,
            provider=provider,
            is_free=is_free,
            supports_vision=supports_vision and is_free,
            notes=notes
        )

    def get_all_models_with_status(self) -> List[ModelInfo]:
        models = self.get_opencode_models()
        return [self.check_model_free(m) for m in models]

    def get_free_models(self) -> List[ModelInfo]:
        return [m for m in self.get_all_models_with_status() if m.is_free]

    def get_vision_free_models(self) -> List[ModelInfo]:
        return [m for m in self.get_free_models() if m.supports_vision]

    def run_opencode(self, args: List[str]) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["opencode"] + args,
            capture_output=True, text=True, timeout=60
        )


# Import time for key manager
import time