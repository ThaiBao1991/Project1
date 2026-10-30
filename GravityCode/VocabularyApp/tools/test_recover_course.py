"""
test_recover_course.py — Test tool khôi phục 444 ngày NHẬT bằng fixture GIẢ LẬP.

Không cần data thật: tự dựng manifest tạm (2 ngày: d9001 đủ 10 từ + 10 audio,
d9002 có từ GIẢ "単語10" → phải bị chặn) + kho mp3 rỗng thật trong data/media/zzrecov
(xoá sạch sau test, không đụng index.json của app).

Chạy: python tools/test_recover_course.py
"""
import json
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.join(BASE, "tools"))
import recover_japanese_course as R  # noqa: E402

PASSED = []


def ok(name):
    PASSED.append(name)
    print(f"[OK] {name}")


# ── Fixture: 10 từ ngày d9001 (word idx 0..9 + audio idx 0..9) ────────────────
WORDS = ["あ", "い", "う", "え", "お", "ひらがな", "カタカナ", "漢字",
         "ローマ字", "日本語"]

SEED = {
    w: {"reading": "", "romaji": "", "vi": f"nghĩa {w}", "pos": "danh từ",
        "ex_ja": "", "ex_vi": ""}
    for w in WORDS
}
SEED["あ"] = {"reading": "a", "romaji": "a", "vi": "chữ a", "pos": "hiragana",
              "ex_ja": "あは最初のひらがな。", "ex_vi": "あ là chữ hiragana đầu tiên."}
SEED["い"] = {"reading": "i", "romaji": "i", "vi": "chữ i", "pos": "hiragana",
              "ex_ja": "い Rad: いい本。", "ex_vi": "い — ví dụ: sách hay."}
SEED["う"] = {"reading": "u", "romaji": "u", "vi": "chữ u", "pos": "hiragana",
              "ex_ja": "", "ex_vi": ""}
SEED["え"] = {"reading": "e", "romaji": "e", "vi": "chữ e", "pos": "hiragana",
              "ex_ja": "", "ex_vi": ""}
SEED["お"] = {"reading": "o", "romaji": "o", "vi": "chữ o", "pos": "hiragana",
              "ex_ja": "", "ex_vi": ""}
# Minh hoạ đồng bộ d9001 & d9002
SEED["ひらがな"] = {"reading": "ひらがな", "romaji": "hiragana", "vi": "chữ mềm Nhật",
                   "pos": "danh từ", "ex_ja": "ひらがなを書きます。", "ex_vi": "Viết chữ hiragana."}
SEED["カタカナ"] = {"reading": "カタカナ", "romaji": "katakana", "vi": "chữ cứng",
                   "pos": "danh từ", "ex_ja": "カタカナで書きます。", "ex_vi": "Viết bằng katakana."}
SEED["漢字"] = {"reading": "かんじ", "romaji": "kanji", "vi": "chữ Hán",
                "pos": "danh từ", "ex_ja": "漢字は難しい。", "ex_vi": "Kanji khó."}
SEED["ローマ字"] = {"reading": "ローマじ", "romaji": "rōmaji", "vi": "chữ La-tinh hóa",
                  "pos": "danh từ", "ex_ja": "ローマ字で入力します。", "ex_vi": "Nhập bằng romaji."}
SEED["日本語"] = {"reading": "にほんご", "romaji": "nihongo", "vi": "tiếng Nhật",
                 "pos": "danh từ", "ex_ja": "日本語を勉強します。", "ex_vi": "Học tiếng Nhật."}
SEED["ほん"] = {"reading": "ほん", "romaji": "hon", "vi": "sách", "pos": "danh từ",
               "ex_ja": "ほんを読みます。", "ex_vi": "Đọc sách."}
SEED["えんぴつ"] = {"reading": "えんぴつ", "romaji": "enpitsu", "vi": "bút chì",
                  "pos": "danh từ", "ex_ja": "えんぴつで書きます。", "ex_vi": "Viết bằng bút chì."}
SEED["しんぶん"] = {"reading": "しんぶん", "romaji": "shinbun", "vi": "báo",
                  "pos": "danh từ", "ex_ja": "しんぶんを読みます。", "ex_vi": "Đọc báo."}

MKEPT = {}

FAKE_AUDIO_DIR = os.path.join(BASE, "data", "media", "zzrecov", "d9001")
try:
    os.makedirs(FAKE_AUDIO_DIR, exist_ok=True)

    items = {}
    for i, w in enumerate(WORDS):
        img_rel = f"media/nhật/d9001/word_{i:02d}_h{i}aaa.webp"
        aud_rel = f"media/zzrecov/d9001/audio_vocab_{i:02d}_h{i}bbb.mp3"
        # file mp3 THẬT (rỗng bytes also được — check chỉ isfile)
        with open(os.path.join(FAKE_AUDIO_DIR, f"audio_vocab_{i:02d}_h{i}bbb.mp3"), "wb") as f:
            f.write(b"\0")
        items[f"m_img{i}"] = {"id": f"m_img{i}", "type": "image",
                              "kind": "vocab_image", "lang": "nhật", "day": 9001,
                              "rel_path": img_rel, "alt": w}
        items[f"m_aud{i}"] = {"id": f"m_aud{i}", "type": "audio",
                              "kind": "vocab_audio", "lang": "nhật", "day": 9001,
                              "rel_path": aud_rel}
    # d9002 — một từ GIẢ (checker)
    items["m_imgF"] = {"id": "m_imgF", "type": "image", "kind": "vocab_image",
                       "lang": "nhật", "day": 9002,
                       "rel_path": "media/nhật/d9002/word_00_fix.webp", "alt": "単語10"}

    tmpdir = tempfile.mkdtemp(prefix="recovtest_")
    manifest_path = os.path.join(tmpdir, "index.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({"format_version": 1, "items": items}, f, ensure_ascii=False)

    # Monkeypatch: tool đọc manifest TẠM, không phải index.json của app
    R.INDEX_PATH = manifest_path

    # ── 1. collect manifest ──
    manifest = R.load_manifest()
    days = R.collect_manifest_chunks(manifest.get("items") or {})
    assert set(days) == {9001, 9002}, f"days sai: {sorted(days)}"
    assert len(days[9001]["words"]) == 10, days[9001]["words"]
    assert days[9001]["words"][0] == "あ", "alt sai"
    assert len(days[9001]["audios"]) == 10, f"audio phải 10/10: {days[9001]['audios']}"
    assert days[9001]["audios"][0] == "m_aud0"
    ok("collect_manifest_chunks: 2 ngày · d9001 10 từ · audio 10/10")
    MKEPT.update(days[9001]["audios"])

    # ── 2. build_day_dict ──
    lesson = R.build_day_dict(9001, days[9001], SEED)
    vs = lesson["vocab"]
    assert len(vs) == 10
    assert vs[0]["word"] == "あ"
    assert vs[0]["meaning_vi"] == "chữ a"
    assert vs[0]["audio_ref"] == "m_aud0"
    assert vs[4]["audio_ref"] == "m_aud4"
    ok("build_day_dict: 10 vocab, audio_ref khớp theo idx, nghĩa lấy từ seed")

    # ── 3. Từ GIẢ bị chặn ──
    try:
        R.build_day_dict(9002, days[9002], SEED)
        raise AssertionError("build_day_dict nhận từ giả mà không văng lỗi!")
    except AssertionError as e:
        assert "単語10" in str(e), str(e)
    ok("guard từ giả '単語10' → AssertionError")

    # ── 4. quiz offline ──
    qz = R.build_quiz_offline([v["word"] for v in vs], SEED)
    vq = qz["vocab"]
    assert qz.keys() >= {"vocab", "pattern"}, f"key quiz sai: {qz.keys()}"
    assert len(vq) >= 1
    q = vq[0]
    assert len(q["options"]) == 4
    correct = q["options"][q["answer_index"]]
    assert correct == SEED[q["question"].split("'")[1]]["vi"], correct
    ok("build_quiz_offline: 4 option · answer_index trúng nghĩa · key đúng format app")

    # ── 5. recover() dry-run: thống kê + từ d9002 bị skip ──
    stat = R.recover(days, SEED, dry_run=0, sample=0)
    assert stat["days"] == 1, f"d9002 phải bị skip vì từ giả; stat={stat}"
    assert stat["words"] == 10
    assert stat["audio_ok"] == 10, f"audio_ok={stat['audio_ok']}"
    ok("recover(): 1 ngày giữ lại (d9002 skip), 10 từ, audio 10/10")

    # ── 6. is_fake_word ──
    assert R.is_fake_word("単語10")
    assert R.is_fake_word("tango34")
    assert R.is_fake_word("Nghĩa từ vựng số 3")
    assert not R.is_fake_word("日本語")
    ok("is_fake_word: khớp 3 pattern cấm, đúng từ thật thì cho qua")
finally:
    # dọn dẹp mp3 rác + thư mục zzz
    try:
        for fn in os.listdir(FAKE_AUDIO_DIR):
            os.remove(os.path.join(FAKE_AUDIO_DIR, fn))
        for d in (FAKE_AUDIO_DIR, os.path.dirname(FAKE_AUDIO_DIR)):
            try:
                os.rmdir(d)
            except OSError:
                pass
    except OSError:
        pass

print(f"\nKet qua: {len(PASSED)}/6 PASS")
if len(PASSED) < 6:
    sys.exit(1)
