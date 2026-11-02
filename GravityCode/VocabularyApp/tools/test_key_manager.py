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
  6. đồng bộ 2 chiều GetHtmlFromUrl ↔ AskCpl (dedup theo key thô, 2 chiều,
     file thiếu/khỏng không ném, id tự sinh, .bak1, roundtrip, giữ khóa khác)
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
                          _KeyEditDialog, keymgr_gethtml_keys_path,
                          keymgr_load_gethtml_keys, keymgr_save_gethtml_keys,
                          keymgr_sync_from_gethtml, keymgr_sync_to_gethtml,
                          _keymgr_merge)
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
              "_save", "_load", "_settings_path", "_log",
              "_sync_from_gethtml", "_sync_to_gethtml"):
        ck(f"ApiKeyManagerDialog.{m} tồn tại", hasattr(ApiKeyManagerDialog, m))
    ck("_KeyEditDialog._ok tồn tại", hasattr(_KeyEditDialog, "_ok"))
    ck("helper module tồn tại",
       all(callable(f) for f in (keymgr_mask_key, keymgr_decode_key,
                                  keymgr_load_keys, keymgr_save_keys,
                                  keymgr_validate_key,
                                  keymgr_gethtml_keys_path,
                                  keymgr_load_gethtml_keys,
                                  keymgr_save_gethtml_keys,
                                  keymgr_sync_from_gethtml,
                                  keymgr_sync_to_gethtml, _keymgr_merge)))

    # ── 7. đồng bộ 2 chiều GetHtmlFromUrl ↔ AskCpl (file tạm — không đụng file thật) ──
    ck("gethtml path: trả về đường dẫn tuyệt đối",
       os.path.isabs(keymgr_gethtml_keys_path()))
    ck("gethtml path: trỏ tới gemini_keys.json",
       keymgr_gethtml_keys_path().replace("\\", "/").endswith(
           "GetHtmlFromUrl_Python/config/gemini_keys.json"))

    with tempfile.TemporaryDirectory() as tmp:
        gpath = os.path.join(tmp, "gemini_keys.json")
        apath = os.path.join(tmp, "settings.json")

        # load gethtml: thiếu file / file hỏng / sai kiểu → [] không ném
        ck("load gethtml: thiếu file → []",
           keymgr_load_gethtml_keys(os.path.join(tmp, "nope.json")) == [])
        bad = os.path.join(tmp, "bad.json")
        with open(bad, "w", encoding="utf-8") as f:
            f.write("{oops")
        ck("load gethtml: file hỏng → []", keymgr_load_gethtml_keys(bad) == [])
        objf = os.path.join(tmp, "obj.json")
        with open(objf, "w", encoding="utf-8") as f:
            json.dump({"a": 1}, f)
        ck("load gethtml: JSON không phải mảng → []",
           keymgr_load_gethtml_keys(objf) == [])

        # save gethtml: atomic + .bak1 (1 lần)
        g1 = {"id": "g1", "key": encode_token("AIza_G1"),
              "email": "g1@gmail.com", "status": "active",
              "note": "gc", "cooldown_until": 0}
        keymgr_save_gethtml_keys([g1], gpath)
        ck("save gethtml: ghi file, không sót .tmp",
           os.path.isfile(gpath) and not os.path.exists(gpath + ".tmp"))
        keymgr_save_gethtml_keys(
            [g1, dict(g1, id="g2", key=encode_token("AIza_G2"))], gpath)
        ck("save gethtml: lần 2 có backup .bak1", os.path.isfile(gpath + ".bak1"))

        # _keymgr_merge: dedup theo key THÔ (khác encoding vẫn trùng)
        dst = [{"id": "a1", "key": encode_token("AIza_SHARED"),
                "email": "", "status": "disabled", "note": "",
                "cooldown_until": 123},
               {"id": "a2", "key": encode_token("AIza_DST"),
                "email": "d@gmail.com", "status": "active", "note": "n"}]
        src = [{"id": "g1", "key": "AIza_SHARED",          # trùng (thô vs ENC:)
                "email": "s@gmail.com", "status": "active", "note": "from g"},
               {"id": "g2", "key": encode_token("AIza_SRC"),  # mới
                "email": "n@gmail.com", "status": "active", "note": "new"},
               {"id": "", "key": "AIza_AUTOID", "email": "auto@gmail.com"}]
        merged, added = _keymgr_merge(src, dst)
        ck("merge: dedup theo key thô (thô vs ENC:) → chỉ +2",
           added == 2 and len(merged) == 4)
        ck("merge: key trùng GIỮ bản dst (status disabled, cooldown)",
           merged[0]["status"] == "disabled"
           and merged[0]["cooldown_until"] == 123)
        ck("merge: lấp email/note TRỐNG từ src",
           merged[0]["email"] == "s@gmail.com"
           and merged[0]["note"] == "from g")
        ck("merge: dst KHÔNG bị đụng (email dst[0] vẫn trống)",
           dst[0]["email"] == "")
        ck("merge: key mới encode ENC: đúng key thô",
           merged[2]["key"].startswith("ENC:")
           and keymgr_decode_key(merged[2]) == "AIza_SRC")
        ck("merge: id tự sinh khi thiếu → có id bắt đầu bằng key_",
           str(merged[3].get("id", "")).startswith("key_"))
        # id trùng với dst → tự đổi khác
        m2, a2 = _keymgr_merge([{"id": "a1", "key": "AIza_DUPID"}], dst)
        ck("merge: id trùng dst → tự đổi id khác", a2 == 1 and m2[-1]["id"] != "a1")
        # key rỗng/không phải dict → bỏ qua
        m3, a3 = _keymgr_merge([{"id": "x", "key": ""}, "not-a-dict", None], dst)
        ck("merge: entry rỗng/không phải dict → bỏ qua, không ném",
           a3 == 0 and len(m3) == 2)

        # đồng bộ thật trên 2 file tạm
        with open(apath, "w", encoding="utf-8") as f:
            json.dump({"github": {"token": "gt-keep"},
                       "gemini": {"api_keys": [
                           {"id": "a1", "key": encode_token("AIza_SHARED"),
                            "email": "", "status": "disabled", "note": "",
                            "error_msg": "HTTP 400", "latency_ms": 99},
                           {"id": "a2", "key": encode_token("AIza_ASK"),
                            "email": "ask@gmail.com", "status": "active"},
                           {"id": "a4", "key": encode_token("AIza_G2"),
                            "email": "diff-g2@gmail.com",
                            "status": "active"}]}},
                      f, ensure_ascii=False)
        with open(gpath, "w", encoding="utf-8") as f:
            json.dump([{"id": "g1", "key": encode_token("AIza_SHARED"),
                        "email": "g-shared@gmail.com", "status": "active",
                        "note": "n1", "cooldown_until": 0},
                       {"id": "g2", "key": encode_token("AIza_G1"),
                        "email": "g-g1@gmail.com", "status": "active",
                        "note": "n2", "cooldown_until": 0},
                       {"id": "g3", "key": encode_token("AIza_G2"),
                        "email": "g-g2@gmail.com", "status": "active",
                        "note": "n3", "cooldown_until": 0}],
                      f, ensure_ascii=False)

        added, tot, changed = keymgr_sync_from_gethtml(apath, gpath)
        ck("sync_from: +1 key mới (AIza_G1) → tổng 4, có đổi",
           added == 1 and tot == 4 and changed is True)
        adata = json.load(open(apath, encoding="utf-8"))
        ck("sync_from: GIỮ khóa khác trong settings (github.token)",
           adata.get("github", {}).get("token") == "gt-keep")
        akeys = adata["gemini"]["api_keys"]
        ck("sync_from: key trùng giữ bản AskCpl (disabled + error_msg)",
           akeys[0]["status"] == "disabled"
           and akeys[0].get("error_msg") == "HTTP 400")
        ck("sync_from: lấp email TRỐNG từ source (a1 ← g1)",
           akeys[0]["email"] == "g-shared@gmail.com")
        ck("sync_from: email khác KHÔNG bị source ghi đè (a4 giữ diff-g2)",
           [k["email"] for k in akeys if k["id"] == "a4"]
           == ["diff-g2@gmail.com"])
        ck("sync_from: đủ 4 key, mọi key dạng ENC:",
           len(akeys) == 4 and all(k["key"].startswith("ENC:") for k in akeys))
        ck("sync_from: file gethtml KHÔNG bị sửa",
           len(keymgr_load_gethtml_keys(gpath)) == 3)
        ck("sync_from: backup .bak1 cho settings.json",
           os.path.isfile(apath + ".bak1"))
        ck("sync_from: atomic — không sót .tmp",
           not os.path.exists(apath + ".tmp"))
        added2, tot2, changed2 = keymgr_sync_from_gethtml(apath, gpath)
        ck("sync_from lần 2: idempotent → +0, không đổi file",
           added2 == 0 and tot2 == 4 and changed2 is False)
        # file gethtml thiếu → không ném, báo không đổi
        added3, tot3, changed3 = keymgr_sync_from_gethtml(
            apath, os.path.join(tmp, "nope.json"))
        ck("sync_from: file gethtml thiếu → +0, không đổi, không ném",
           added3 == 0 and changed3 is False and tot3 == 4)
        # settings.json thiếu → (0, 0, False)
        added4, tot4, changed4 = keymgr_sync_from_gethtml(
            os.path.join(tmp, "nope2.json"), gpath)
        ck("sync_from: settings.json thiếu → (0,0,False), không ném",
           added4 == 0 and tot4 == 0 and changed4 is False)

        # sync_to: askcpl(4) → gethtml(3): chỉ +AIza_ASK, field lạ bị lọc
        added5, tot5, changed5 = keymgr_sync_to_gethtml(apath, gpath)
        ck("sync_to: +1 key mới (AIza_ASK) → tổng 4, có đổi",
           added5 == 1 and tot5 == 4 and changed5 is True)
        gdata = json.load(open(gpath, encoding="utf-8"))
        ck("sync_to: gethtml đủ 4 key, dạng ENC:",
           len(gdata) == 4 and all(k["key"].startswith("ENC:") for k in gdata))
        ck("sync_to: entry mới chỉ có field chuẩn (lọc error_msg/latency_ms)",
           all(set(k) <= {"id", "key", "email", "status", "note",
                          "cooldown_until"} for k in gdata))
        ck("sync_to: key trùng GIỮ bản GetHtmlFromUrl (g3 giữ g-g2, "
           "không bị a4 diff-g2 đè)",
           [k["email"] for k in gdata if k["id"] == "g3"] == ["g-g2@gmail.com"])
        ck("sync_to: entry mới nhận email từ askcpl (AIza_ASK ← ask@)",
           [k["email"] for k in gdata if k["id"] == "a2"] == ["ask@gmail.com"])
        ck("sync_to: có backup .bak1 cho gemini_keys.json",
           os.path.isfile(gpath + ".bak1"))
        added6, _, changed6 = keymgr_sync_to_gethtml(apath, gpath)
        ck("sync_to lần 2: idempotent → +0, không đổi",
           added6 == 0 and changed6 is False)

        # roundtrip: 2 chiều liên tiếp → tập key thô bằng nhau
        raws_a = {keymgr_decode_key(k) for k in keymgr_load_keys(apath)}
        raws_g = {keymgr_decode_key(k) for k in keymgr_load_gethtml_keys(gpath)}
        ck("roundtrip: tập key thô 2 file bằng nhau (4 key)",
           raws_a == raws_g == {"AIza_SHARED", "AIza_ASK",
                                "AIza_G1", "AIza_G2"})

        # sync_to khi settings KHÔNG có gemini.api_keys → không ném
        plain = os.path.join(tmp, "plain.json")
        with open(plain, "w", encoding="utf-8") as f:
            json.dump({"other": 1}, f)
        p_added, p_total, p_changed = keymgr_sync_to_gethtml(plain, gpath)
        ck("sync_to: settings thiếu gemini.api_keys → +0, không đổi, không ném",
           p_added == 0 and p_changed is False)

    print()
    print(f"KẾT QUẢ: {total[0] - len(fails)}/{total[0]} pass")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
