# -*- coding: utf-8 -*-
"""ai/offline_content.py — Sinh nội dung khóa học KHÔNG CẦN Gemini (Gói 6).

BỐI CẢNH (2026-11-12): quota Gemini cạn (197 key/20 account hết quota/ngày)
⇒ mọi việc cần AI dừng. Nhưng app phải học được ⇒ cần nguồn nội dung OFFLINE:

  • BẢNG CHỮ CÁI: 46 hiragana + 46 katakana (sinh bằng code, có IPA +
    nghĩa tiếng Việt + mẹo phát âm) ⇒ bắt đầu "từ 0" đúng chuẩn.
  • TỪ VỰNG: EDICT2 (JMdict, tải 1 lần từ edrdg.org) — kanji · kana đọc ·
    từ loại · nghĩa tiếng Anh; **nghĩa tiếng Việt** lấy từ Wiktionary
    (cache `data/offline_src/wiktionary_vi.json`, KHÔNG tốn quota AI).
  • NGỮ PHÁP: bảng mục ngữ pháp N5→N3 tự soạn (`ai/offline_grammar.py`).
  • HỘI THOẠI: micro-dialogue 4 lượt ghép từ của ngày (template, không AI).
  • TRẮC NGHIỆM: đảo nghĩa 4 lựa chọn từ từ của ngày (không AI).

Thứ tự học "từ thấp lên cao" (không có danh sách tần suất ⇒ tự xếp theo độ
khó): ① 1 kana (かな) ② 1 kanji + 1-2 kana ③ 2 kanji + 2 kana ④ 2+ kanji.
"""
from __future__ import annotations

import gzip
import json
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
SRC_DIR = os.path.join(DATA_DIR, "offline_src")
EDICT_PATH = os.path.join(SRC_DIR, "edict.gz")
WIKI_CACHE = os.path.join(SRC_DIR, "wiktionary_vi.json")

# chỉ giữ mục là từ Nhật (kana hoặc kanji)
_JAPANESE = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff]")

# ── Bảng 46 kana: (kana, romaji, IPA, nghĩa tiếng Việt, mẹo phát âm) ────────
_HIRA = list("".join(
    "あいうえお かきくけこ さしすせそ たちつてと なにぬねの はひふへほ "
    "まみむめも やゆよ らりるれろ わをん".split()))
_KATA_RO = (
    "a i u e o ka ki ku ke ko sa shi su se so ta chi tsu te to na ni nu ne no ha hi fu he ho ma mi mu me mo ya yu yo ra ri ru re ro wa wo n".split()
)
_RO_IPA = {
    "a": "a", "i": "i", "u": "u", "e": "e", "o": "o",
    "ka": "ka", "ki": "ki", "ku": "ku", "ke": "ke", "ko": "ko",
    "sa": "sa", "shi": "shi", "su": "su", "se": "se", "so": "so",
    "ta": "ta", "chi": "tɕi", "tsu": "tsɯ", "te": "te", "to": "to",
    "na": "na", "ni": "ni", "nu": "nu", "ne": "ne", "no": "no",
    "ha": "ha", "hi": "hi", "fu": "fɯ", "he": "he", "ho": "ho",
    "ma": "ma", "mi": "mi", "mu": "mɯ", "me": "me", "mo": "mo",
    "ya": "ja", "yu": "jɯ", "yo": "jo",
    "ra": "ɾa", "ri": "ɾi", "ru": "ɾɯ", "re": "ɾe", "ro": "ɾo",
    "wa": "wa", "wo": "wo", "n": "n",
}
_IPA_HINT = {
    "a": "â mở, không thanh", "i": "i cười, lưỡi tụt", "u": "u tròn môi",
    "e": "e mở, nhẹ", "o": "o tròn, môi mở",
}


def _kana_rows():
    """92 hàng: (kana, romaji, ipa, nghĩa vi, mẹo phát âm)."""
    rows = []
    for ch, ro in zip(_HIRA, _KATA_RO):
        ipa = _RO_IPA.get(ro, ro)
        rows.append((ch, ro, ipa, f"âm {ro}", _IPA_HINT.get(ro[0], "âm mở, ngắn")))
    for ch, ro in zip(_HIRA, _KATA_RO):
        k = "ン" if ch == "ん" else chr(ord(ch) + 0x60)   # hiragana → katakana
        ipa = _RO_IPA.get(ro, ro)
        rows.append((k, ro, ipa, f"âm {ro} (katakana)",
                     _IPA_HINT.get(ro[0], "âm mở, ngắn")))
    return rows


KANA_ROWS = _kana_rows()


def load_edict(path: str = None) -> dict:
    """Đọc EDICT/EDICT2 → {từ: {reading, pos, glosses[]}} (chỉ từ Nhật thật).

    Hỗ trợ 2 định dạng:
      • EDICT  : "kanji [kana] /(pos) gloss1/gloss2/…"
      • EDICT2 : "kanji;kana1;kana2 /(pos) gloss1/…"
    """
    cands = [path] if path else [os.path.join(SRC_DIR, "edict.gz"),
                                  os.path.join(SRC_DIR, "edict2.gz")]
    path = next((p for p in cands if p and os.path.isfile(p)), None)
    out = {}
    if not path:
        return out
    try:
        # EDICT của EDRDG dùng EUC-JP (không phải UTF-8) — thử EUC-JP trước,
        # fallback UTF-8 cho bản EDICT2 mới.
        try:
            fh = gzip.open(path, "rt", encoding="euc_jp", errors="replace")
        except (OSError, LookupError):
            fh = gzip.open(path, "rt", encoding="utf-8", errors="replace")
    except OSError:
        return out
    with fh:
        for line in fh:
            if not line or line[0] == "#":
                continue
            line = line.rstrip("\n")
            # EDICT  : "kanji reading (pos) gloss1/gloss2/…"
            # EDICT2 : "kanji;kana1;kana2 (pos) gloss1/…"
            m = re.match(r"^(\S+)\s+(.*?)\s+(\([^)]*\))\s*(.*)$", line)
            if not m:
                continue
            kanji = m.group(1).strip()
            reading = m.group(2).strip()
            pos = m.group(3).strip("()")
            gloss_txt = m.group(4)
            if ";" in reading:
                reading = "".join(p.strip() for p in reading.split(";") if p.strip())
            reading = reading.strip("[]")
            if not kanji or len(kanji) > 8:
                continue
            if not _JAPANESE.search(kanji):
                continue          # bỏ mục không phải từ Nhật (vd "2.5D")
            if reading and (len(reading) > 8 or not _JAPANESE.search(reading)):
                reading = ""      # reading không phải kana ⇒ bỏ
            glosses = [g.strip() for g in gloss_txt.split("/") if g.strip()]
            glosses = [re.sub(r"^\((?:\w+)(?:,\s*\w+)*\)\s*", "", g).strip()
                        for g in glosses]          # bỏ "(int) (2)" ở đầu gloss
            glosses = [g for g in glosses if re.search(r"[A-Za-z]{3}", g)]
            if not glosses:
                continue
            out[kanji] = {"reading": reading, "pos": pos, "glosses": glosses[:3]}
    return out


def load_wiki_cache() -> dict:
    """Nghĩa tiếng Việt đã cache: Wiktionary + bản dịch (tools/translate_vi.py)."""
    out = {}
    for p in (WIKI_CACHE, os.path.join(SRC_DIR, "vi_meanings.json")):
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f) or {}
        except Exception:
            continue
        for w, v in data.items():
            if isinstance(v, dict) and v.get("vi"):
                out.setdefault(w, {}).update(v)
    return out


def difficulty(word: str, reading: str) -> tuple:
    """(số kanji, số kana) — dùng để xếp từ từ thấp lên cao."""
    n_kanji = sum(1 for c in word if "一" <= c <= "鿿")
    n_kana = len(reading) if reading else 0
    return (n_kanji, n_kana)


def select_words(edict: dict, limit: int = 1200, max_kanji: int = 2) -> list:
    """Chọn từ theo độ khó tăng dần (1 kana → 2 kanji), bỏ từ quá dài/lạ."""
    rows = []
    for w, info in edict.items():
        if not w or len(w) > 6:
            continue
        # chỉ nhận từ viết bằng kana/kanji thuần (bỏ "β-カロチン", "T-シャツ"…)
        if not re.fullmatch(r"[\u3040-\u30ff\u4e00-\u9fff\u30fc]+", w):
            continue
        reading = info.get("reading") or ""
        if reading and (len(reading) > 5 or "[" in reading):
            continue
        n_k, n_kana = difficulty(w, reading)
        if n_k > max_kanji:
            continue
        if not info.get("glosses"):
            continue
        rows.append((n_k, n_kana, w))
    rows.sort(key=lambda r: (r[0], r[1], r[2]))
    return [r[2] for r in rows[:limit]]


def build_kana_vocab() -> list:
    """92 kana dạng vocab item đầy đủ field (schema v4)."""
    out = []
    for ch, ro, ipa, vi, note in KANA_ROWS:
        out.append({
            "word": ch,
            "pronunciation": ro,
            "ipa": f"/{ipa}/",
            "part_of_speech": "pos",
            "meaning_vi": vi,
            "explanation": f"Ký tự {ch} ({ro}), IPA /{ipa}/.",
            "example_sentence": f"{ch} を 読みます。",
            "example_meaning_vi": f"Đọc ký tự {ch} ({ro}).",
            "phonetic_note": f"👄 {note}. {ch} đọc là \"{ro}\".",
            "syllables": [ch],
        })
    return out


def _vi_meaning(word: str, info: dict, wiki: dict) -> tuple:
    """(nghĩa tiếng Việt, ví dụ tiếng Việt) — ưu tiên Wiktionary, fallback gloss EN."""
    w = wiki.get(word) or {}
    vi = w.get("vi") or ""
    ex = w.get("vi_example") or ""
    if vi:
        return vi, ex
    en = "; ".join(info.get("glosses") or [])[:160]
    return (f"[EN] {en}" if en else ""), ex


def build_vocab_item(word: str, info: dict, wiki: dict) -> dict:
    # từ viết bằng khirana thì cách đọc chính là từ đó ("あ" → "あ")
    reading = info.get("reading") or word
    vi, vi_ex = _vi_meaning(word, info, wiki)
    ex = (info.get("glosses") or [""])[0]
    return {
        "word": word,
        "pronunciation": reading,
        "ipa": f"/{reading}/" if reading else "",
        "part_of_speech": (info.get("pos") or "").split("-")[0],
        "meaning_vi": vi,
        "explanation": f"{word} ({reading}) — {ex}" if ex else f"{word} ({reading})",
        "example_sentence": f"{word}を使います。",
        "example_meaning_vi": vi_ex or f"Dùng từ {word}.",
        "phonetic_note": f"👄 Đọc {word} là \"{reading}\".",
        "syllables": [reading] if reading else [],
    }


def build_quiz(words: list, n: int = 8) -> dict:
    """Quiz đảo nghĩa (không cần AI): 4 lựa chọn, 1 đúng."""
    vocab_q, pattern_q = [], []
    pool = [w for w in words if w.get("meaning_vi")]
    others = [w.get("meaning_vi") for w in pool]
    for i, w in enumerate(pool[:n]):
        correct = w.get("meaning_vi")
        distract = [o for o in others if o != correct]
        opts = [correct]
        for d in distract:
            if len(opts) >= 4:
                break
            opts.append(d)
        if len(opts) < 2:
            continue
        vocab_q.append({
            "question": f"Từ 「{w.get('word')}」 có nghĩa là gì?",
            "options": opts,
            "answer_index": 0,
            "explanation": f"{w.get('word')} = {correct}",
        })
    for i, w in enumerate(pool[:max(2, n // 3)]):
        correct = w.get("word")
        distract = [x.get("word") for x in pool if x.get("word") != correct]
        opts = [correct] + distract[:3]
        pattern_q.append({
            "question": f"Chọn từ đúng cho nghĩa: {w.get('meaning_vi')}",
            "options": opts,
            "answer_index": 0,
            "explanation": f"{correct} = {w.get('meaning_vi')}",
        })
    return {"vocab": vocab_q, "pattern": pattern_q, "common": [], "grammar": [],
            "mixed": []}


def build_dialogue(words: list, topic: str = "") -> list:
    """Micro-hội thoại 4 lượt ghép từ của ngày (template, không AI)."""
    ws = [w for w in words if w.get("word")][:4]
    if len(ws) < 2:
        return []
    a, b = ws[0], ws[1]
    c = ws[2] if len(ws) > 2 else ws[0]
    turns = [
        {"speaker": "A", "line_target": f"{a.get('word')}を 使います。",
         "line_vi": f"Tôi dùng {a.get('word')}.",
         "focus_words": [a.get("word")]},
        {"speaker": "B", "line_target": f"{b.get('word')} は 何ですか。",
         "line_vi": f"{b.get('word')} là cái gì?",
         "focus_words": [b.get("word")]},
        {"speaker": "A", "line_target": f"{c.get('word')}です。",
         "line_vi": f"Đó là {c.get('word')}.",
         "focus_words": [c.get("word")]},
        {"speaker": "B", "line_target": "はい、わかりました。",
         "line_vi": "Vâng, tôi hiểu rồi.",
         "focus_words": []},
    ]
    return [{
        "title": topic or "Hội thoại ngày hôm nay",
        "situation": "Hội thoại ngắn dùng từ của bài hôm nay.",
        "level_tag": "N5",
        "turns": turns,
        "cultural_note": "Hội thoại tối giản luyện phản xạ.",
        "kind": "micro",
    }]


# ── Sinh 1 ngày học offline (dùng bởi pipeline fallback + tool) ───────────────
KANA_DAYS = 10          # 10 ngày đầu: bảng chữ cái (92 kana / 10 từ/ngày)
WORDS_PER_DAY = 10


# ── Giáo trình 6 chặng (dùng chung cho pipeline offline + tool dựng khóa) ─────
PHASES = (
    ("Vỡ lòng chữ cái & phát âm", 60),
    ("Ghép âm & Từ đơn sinh tồn", 90),
    ("Sơ cấp đời sống", 280),
    ("Trung cấp công việc", 350),
    ("Cao cấp học thuật", 300),
    ("Như người bản xứ", 180),
)
LEVELS = ("N5", "N5", "N4", "N3", "N2", "N1")


# ── Nguồn từ cho MỌI ngôn ngữ (wordfreq + Wiktionary) ───────────────────────────
# slug khóa học → mã ISO để tra bảng từ đã dựng (`data/offline_src/words_<iso>.json`)
ISO_BY_LANG = {
    "tiếng_anh": "en", "tiếng_trung": "zh", "tiếng_nhật": "ja",
    "tiếng_hàn_quốc": "ko", "tiếng_pháp": "fr", "tiếng_đức": "de",
    "tiếng_tây_ban_nha": "es", "tiếng_nga": "ru", "tiếng_italia": "it",
    "tiếng_bồ_đào_nha": "pt", "tiếng_việt": "vi",
}


def load_words(iso: str) -> dict:
    """Đọc bảng từ đã dựng cho ngôn ngữ: {từ: {gloss, reading, pos}}."""
    path = os.path.join(SRC_DIR, f"words_{iso}.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception:
        return {}


def build_vocab_item_generic(word: str, gloss: str, wiki: dict = None) -> dict:
    """Vocab item cho nguồn wordfreq/Wiktionary (không có kana đọc)."""
    wiki = wiki or {}
    w = wiki.get(word) or {}
    vi = w.get("vi") or ""
    gl = (gloss or "").strip()
    return {
        "word": word,
        "pronunciation": "",
        "ipa": "",
        "part_of_speech": "",
        "meaning_vi": vi or (f"[EN] {gl}" if gl else ""),
        "explanation": gl,
        "example_sentence": "",
        "example_meaning_vi": "",
        "phonetic_note": "",
        "syllables": [],
    }


def phase_for_day(day: int, total_days: int) -> tuple:
    """(tên chặng, cấp độ, thứ tự chặng) cho ngày N theo tỉ lệ 6 chặng."""
    total_w = sum(x[1] for x in PHASES)
    acc = 0
    for i, (name, w) in enumerate(PHASES, 1):
        acc += max(1, round(w * max(1, total_days) / total_w))
        if day <= acc:
            return name, LEVELS[i - 1], i
    return PHASES[-1][0], LEVELS[-1], len(PHASES)


def build_offline_day(day: int, edict: dict = None, wiki: dict = None,
                      pool: list = None) -> dict:
    """Dựng nội dung 1 ngày KHÔNG CẦN AI (schema v4, tương thích pipeline).

    Ngày 1-10: bảng chữ cái (92 kana). Ngày sau: từ vựng cơ bản theo độ khó
    tăng dần (1 kana → 1 kanji → 2 kanji) + ngữ pháp N5→N3 + hội thoại micro
    + trắc nghiệm đảo nghĩa.
    """
    from ai.offline_grammar import grammar_for_day

    edict = edict if edict is not None else load_edict()
    wiki = wiki if wiki is not None else load_wiki_cache()
    if pool is None:
        pool = select_words(edict, limit=4000)

    if day <= KANA_DAYS:
        kana = build_kana_vocab()
        chunk = kana[(day - 1) * WORDS_PER_DAY:(day - 1) * WORDS_PER_DAY + WORDS_PER_DAY]
        phase = "Vỡ lòng chữ cái & phát âm (offline)"
        title = f"Bảng chữ cái — Ngày {day}"
    else:
        i = (day - KANA_DAYS - 1) * WORDS_PER_DAY
        chunk = pool[i:i + WORDS_PER_DAY]
        phase = "Từ vựng cơ bản (offline)"
        title = f"Từ vựng cơ bản — Ngày {day}"

    vocab = []
    for w in chunk:
        if isinstance(w, dict):
            vocab.append(w)
        else:
            vocab.append(build_vocab_item(w, edict.get(w) or {}, wiki))
    grammar = grammar_for_day(day)
    dialogue = build_dialogue(vocab, topic=title)
    quiz = build_quiz(vocab)
    return {
        "title": title, "phase": phase, "topic": title,
        "vocab": vocab, "grammar": grammar, "dialogue": dialogue, "quiz": quiz,
        "sentence_patterns": [], "common_sentences": [],
        "source": "offline",
    }
