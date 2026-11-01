# -*- coding: utf-8 -*-
"""Test quản lý API key (ApiKeyManagerDialog + helpers) KHÔNG cần GUI, KHÔNG gọi mạng thật.

Chạy:  python tools/test_key_manager.py

Bao phủ:
  1. encode/decode ENC: (chuẩn dùng chung AskCpl/GetHtmlFromUrl — đảo + base64)
  2. mask key (không lộ full key trong UI)
  3. save/load roundtrip → key luôn lưu ENC:, khóa khác trong settings giữ nguyên,
     backup .bak1, ghi atomic (không còn file .tmp)
  4. validate key với requests GIẢ LẬP (200 → hợp lệ, 400 → lỗi có thông điệp)
  5. các method của dialog tồn tại (import VocabApp — không tạo cửa sổ)
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

fails = []
total = [0]


def ck(name, cond):
    total[0] += 1
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


def main():
    from VocabApp import (keymgr_mask_key, keymgr_decode_key,
                          keymgr_load_keys, keymgr_save_keys,
                          keymgr_validate_key, ApiKeyManagerDialog,
                          _KeyEditDialog)
    from settings import encode_token, decode_token

    # ── 1. encode/decode ENC: chuẩn dùng chung ──
    raw = "AIzaSyFAKE_KEY_DO_NOT_USE_1234567890abcd"
    enc = encode_token(raw)
    ck("encode_token -> tiền tố ENC:", enc.startswith("ENC:"))
    ck("encode KHÔNG chứa key thô", raw not in enc)
    ck("decode roundtrip = key gốc", decode_token(enc) == raw)

    # ── 2. mask key ──
    ck("mask: không lộ key đầy đủ",
       raw not in keymgr_mask_key(raw) and "…" in keymgr_mask_key(raw))
    ck("mask: key rỗng -> '(trống)'", keymgr_mask_key("") == "(trống)")
    ck("mask: key ngắn không ném lỗi", bool(keymgr_mask_key("abc")))

    # ── 3. decode key từ entry (đã mã hóa / thô) ──
    ck("decode entry ENC:", keymgr_decode_key({"key": enc}) == raw)
    ck("decode entry thô (không ENC:)", keymgr_decode_key({"key": raw}) == raw)
    ck("decode entry rỗng -> ''", keymgr_decode_key({}) == "")

    # ── 4. save/load roundtrip + backup + atomic ──
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "settings.json")
        # settings.json đã có cấu hình khác → PHẢI giữ nguyên khi lưu key
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"github": {"token": "gt-keep-me"},
                       "ai": {"adaptive_model": True}}, f, ensure_ascii=False)
        keys = [
            {"key": raw, "email": "a@gmail.com", "type": "GEMINI API",
             "status": "active"},
            {"key": enc, "email": "b@gmail.com", "status": "disabled"},
        ]
        keymgr_save_keys(path, keys)

        data = json.load(open(path, encoding="utf-8"))
        saved = data["gemini"]["api_keys"]
        ck("save: cả 2 key đều lưu dạng ENC:",
           all(k["key"].startswith("ENC:") for k in saved))
        ck("save: GIỮ nguyên cấu hình khác (github.token)",
           data.get("github", {}).get("token") == "gt-keep-me")
        ck("save: GIỮ nguyên cấu hình khác (ai.adaptive_model)",
           data.get("ai", {}).get("adaptive_model") is True)
        ck("save: ghi atomic — không còn file .tmp",
           not os.path.exists(path + ".tmp"))

        got = keymgr_load_keys(path)
        ck("load: đủ 2 key, đúng email",
           [k["email"] for k in got] == ["a@gmail.com", "b@gmail.com"])
        ck("load: giải mã được key gốc",
           keymgr_decode_key(got[0]) == raw and keymgr_decode_key(got[1]) == raw)
        ck("load: giữ status active/disabled",
           [k["status"] for k in got] == ["active", "disabled"])

        # Lưu lần 2 → backup .bak1 phải tồn tại (nội dung bản trước)
        keys.append({"key": "AIzaSySECOND_9999", "email": "c@gmail.com"})
        keymgr_save_keys(path, keys)
        bak = path + ".bak1"
        ck("save lần 2: có backup .bak1", os.path.isfile(bak))
        bak_data = json.load(open(bak, encoding="utf-8"))
        ck("backup giữ nguyên cấu hình khác",
           bak_data.get("github", {}).get("token") == "gt-keep-me")
        got2 = keymgr_load_keys(path)
        ck("save lần 2: đủ 3 key", len(got2) == 3)

        # File hỏng -> load trả [] (không ném)
        bad = os.path.join(tmp, "bad.json")
        with open(bad, "w", encoding="utf-8") as f:
            f.write("{not json")
        ck("load file hỏng -> [] (không ném)", keymgr_load_keys(bad) == [])

    # ── 5. validate key với requests GIẢ LẬP (không gọi mạng thật) ──
    import requests

    class _FakeResp:
        def __init__(self, status, data=None, text=""):
            self.status_code = status
            self._data = data or {}
            self.text = text or json.dumps(self._data)

        def json(self):
            return self._data

    orig_post = requests.post
    try:
        requests.post = lambda *a, **k: _FakeResp(200, {"ok": True})
        ok, msg, ms = keymgr_validate_key(raw)
        ck("validate 200 -> (True, 'Hợp lệ', ms)", ok is True and msg == "Hợp lệ"
           and isinstance(ms, int) and ms >= 0)

        requests.post = lambda *a, **k: _FakeResp(
            400, {"error": {"message": "API key not valid"}})
        ok2, msg2, _ = keymgr_validate_key("bad-key")
        ck("validate 400 -> False + có HTTP 400 + thông điệp",
           ok2 is False and "400" in msg2 and "not valid" in msg2)

        def _raise(*a, **k):
            raise requests.exceptions.ConnectTimeout("timed out")
        requests.post = _raise
        ok3, msg3, _ = keymgr_validate_key(raw, timeout=1)
        ck("validate timeout -> False + tên lỗi (không ném ra ngoài)",
           ok3 is False and "ConnectTimeout" in msg3)
    finally:
        requests.post = orig_post

    # ── 6. dialog đủ method (import VocabApp — không tạo cửa sổ) ──
    for m in ("_build", "_render", "_select", "_add", "_edit", "_delete",
              "_toggle", "_toggle_at", "_check", "_check_all",
              "_check_worker", "_on_check_result", "_check_done",
              "_save", "_load", "_settings_path", "_log"):
        ck(f"ApiKeyManagerDialog.{m} tồn tại", hasattr(ApiKeyManagerDialog, m))
    ck("_KeyEditDialog._ok tồn tại", hasattr(_KeyEditDialog, "_ok"))
    ck("4 helper module tồn tại",
       all(callable(f) for f in (keymgr_mask_key, keymgr_decode_key,
                                  keymgr_load_keys, keymgr_save_keys,
                                  keymgr_validate_key)))

    print()
    print(f"KẾT QUẢ: {total[0] - len(fails)}/{total[0]} pass")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
