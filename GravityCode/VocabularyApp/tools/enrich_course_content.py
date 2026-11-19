# -*- coding: utf-8 -*-
"""tools/enrich_course_content.py — BỔ SUNG MẪU CÂU / CÂU THÔNG DỤNG /
HỘI THOẠI / CÂU HỎI NGỮ PHÁP cho các ngày bị thiếu (2026-11-19).

VẤN ĐỀ ĐO ĐƯỢC (19/11/2026):
  • 2.074–2.417 ngày mỗi khóa (tùy ngôn ngữ) có `sentence_patterns` và
    `common_sentences` RỖNG.
  • 2.104–2.504 ngày có `dialogue` là template tiếng Nhật
    ("Xを 使います" / "Y は 何ですか") — kể cả khóa Anh/Trung/Hàn/Pháp/Đức…
  • Quiz chỉ có vocab + pattern; `common` và `grammar` rỗng.
  • Khóa không phải Nhật bị gán ngữ pháp tiếng Nhật (Trợ từ は, 〜ます…).

CÁCH SỬA (0 quota AI):
  1. Rút thư viện NỘI DUNG BẢN NGỮ từ chính các ngày đã có nội dung tốt
     (mẫu câu, câu thông dụng, hội thoại thật, mini_quiz ngữ pháp).
  2. Ngày thiếu → chọn mục theo cấp độ (N5→N1) + độ dài câu (cấp cao dùng
     câu dài/phức tạp hơn), xoay vòng theo ngày để không lặp liền nhau.
  3. Riêng tiếng Nhật: ngữ pháp lấy từ `ai/offline_grammar*.py` (đúng cấp độ,
     có ví dụ tiếng Nhật); mẫu câu lấy từ chính ví dụ ngữ pháp.
  4. Hội thoại: dùng hội thoại thật cùng ngôn ngữ nếu đủ; nếu ít thì dựng
     hội thoại Q&A từ mẫu câu + câu thông dụng của ngày.
  5. Quiz: thêm 2–3 câu ngữ pháp + 2–3 câu thông dụng, trộn đáp án cố định.

KHÔNG đụng vào: vocab, media_map, audio từ vựng, media bundle.
Hội thoại mới được bỏ `audio_ref` (audio cũ không còn khớp); web sẽ chỉ hiện
phần chữ. Các khóa đang bù media sẽ tự sinh audio mới ở lần chạy sau.

CÁCH DÙNG:
  python -X utf8 tools/enrich_course_content.py --lang tiếng_nhật --dry-run
  python -X utf8 tools/enrich_course_content.py --lang tiếng_nhật
  python -X utf8 tools/enrich_course_content.py --lang all
  python -X utf8 tools/enrich_course_content.py --lang tiếng_nhật --limit 30
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from ai.offline_content import phase_for_day  # noqa: E402

CD = os.path.join(BASE, "data", "ai_courses")
JP = "tiếng_nhật"

_JP_SCRIPT = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff]")
_JP_KANA = re.compile(r"[\u3040-\u30ff]")
_VI_CHARS = re.compile(
    r"[đĐơƠưƯăĂạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ]")
# Từ tiếng Việt thường xuất hiện trong phần giải thích lẫn vào câu ngoại ngữ.
_VI_WORDS = re.compile(
    r"\b(của|không|người|được|tiếng|nghĩa|nguyên âm|phụ âm|dài|ngắn|đọc|câu|từ|và|là)\b",
    re.I)
_LATIN_WORD = re.compile(r"[A-Za-z]{2,}")
# Lỗi thường gặp trong nội dung AI cũ (romaji/ngữ pháp sai) — sửa khi bổ sung.
_JP_FIXES = [
    (re.compile(r"いくですか"), "いくらですか"),
    (re.compile(r"お(飲み|食べ|行き|見|読み|書き|買い|使い|待ち|話し|聞き)ます"), r"\1ます"),
    (re.compile(r"を\s*(すき|好き|ほしい|欲しい|じょうず|上手|わかります|分かります)"),
     r"が \1"),
]
_TARGET_SCRIPT = {
    "tiếng_nhật": _JP_SCRIPT,
    "tiếng_trung": re.compile(r"[\u4e00-\u9fff]"),
    "tiếng_hàn_quốc": re.compile(r"[\uac00-\ud7af]"),
    "tiếng_nga": re.compile(r"[\u0400-\u04ff]"),
}


def _looks_vietnamese(text: str) -> bool:
    s = str(text or "")
    return bool(_VI_CHARS.search(s) or _VI_WORDS.search(s))


def _valid_example_text(slug: str, text: str) -> bool:
    """Ví dụ ngữ pháp: đúng hệ chữ của ngôn ngữ đích, không lẫn tiếng Việt.

    Khác `_valid_target` (dùng cho câu/mẫu câu): cho phép 1 từ, vì ví dụ
    ngữ pháp có thể chỉ là một từ (vd. "cat", "네", "А").
    """
    s = str(text or "").strip()
    if not s or _looks_vietnamese(s):
        return False
    rx = _TARGET_SCRIPT.get(slug)
    if rx is None:
        return bool(re.search(r"[A-Za-zÀ-ÿ]", s))
    return bool(rx.search(s))


def _fix_text(slug: str, text: str) -> str:
    s = str(text or "")
    if slug == JP:
        for rx, rep in _JP_FIXES:
            s = rx.sub(rep, s)
    return s


def _fix_obj(slug: str, obj):
    """Sửa lỗi văn bản trong toàn bộ object (đệ quy)."""
    if isinstance(obj, str):
        return _fix_text(slug, obj)
    if isinstance(obj, list):
        return [_fix_obj(slug, x) for x in obj]
    if isinstance(obj, dict):
        return {k: _fix_obj(slug, v) for k, v in obj.items()}
    return obj


def _valid_target(slug: str, text: str) -> bool:
    """Câu có thực sự viết bằng ngôn ngữ đích (không phải tiếng Việt/romaji lẫn)."""
    text = str(text or "").strip()
    if not text:
        return False
    if slug == JP:
        if _looks_vietnamese(text) or _LATIN_WORD.search(text):
            return False
        jp = len(_JP_SCRIPT.findall(text))
        return jp >= 2 and jp / max(1, len(text)) >= 0.3
    if slug == "tiếng_trung":
        if _looks_vietnamese(text):
            return False
        return len(re.findall(r"[\u4e00-\u9fff]", text)) >= 2
    if slug == "tiếng_hàn_quốc":
        return len(re.findall(r"[\uac00-\ud7af]", text)) >= 2
    if slug == "tiếng_nga":
        return len(re.findall(r"[\u0400-\u04ff]", text)) >= 2
    # Ngôn ngữ Latin (Anh/Pháp/Đức/Tây Ban Nha): ít nhất 2 từ, không phải tiếng Việt.
    if _looks_vietnamese(text):
        return False
    return len(_LATIN_WORD.findall(text)) >= 2

# Câu kết thúc hội thoại theo ngôn ngữ (dùng cho hội thoại dựng Q&A).
_CLOSING = {
    "tiếng_nhật": ("ありがとうございます。また連絡します。", "はい、よろしくお願いします。"),
    "tiếng_anh": ("Thank you. I'll get back to you soon.", "Sounds good. Talk to you later."),
    "tiếng_trung": ("谢谢，我稍后再联系你。", "好的，回头见。"),
    "tiếng_hàn_quốc": ("감사합니다. 나중에 다시 연락할게요.", "네, 그렇게 해요."),
    "tiếng_pháp": ("Merci. Je vous recontacte bientôt.", "Très bien, à bientôt."),
    "tiếng_đức": ("Danke. Ich melde mich bald wieder.", "Alles klar, bis später."),
    "tiếng_tây_ban_nha": ("Gracias. Te contacto pronto.", "Muy bien, hasta luego."),
    "tiếng_nga": ("Спасибо. Я скоро свяжусь с вами.", "Хорошо, до связи."),
}
_ACK = {
    "tiếng_nhật": "なるほど、そうですか。",
    "tiếng_anh": "I see.",
    "tiếng_trung": "原来如此。",
    "tiếng_hàn_quốc": "그렇군요.",
    "tiếng_pháp": "Je vois.",
    "tiếng_đức": "Ich verstehe.",
    "tiếng_tây_ban_nha": "Ya veo.",
    "tiếng_nga": "Понятно.",
}


def _log(msg: str) -> None:
    print(msg, flush=True)


def _has_script(slug: str, text: str) -> bool:
    rx = _TARGET_SCRIPT.get(slug)
    if rx is None:
        return bool(re.search(r"[A-Za-zÀ-ÿ\u0400-\u04ff]", text or ""))
    return bool(rx.search(text or ""))


def _is_template_dialogue(dlg: dict) -> bool:
    text = " ".join(str(t.get("line_target") or "") for t in (dlg.get("turns") or []))
    if not text:
        return True
    return ("を 使います" in text or "は 何ですか" in text
            or ("使います" in text and "です。" in text))


def _level_of(day: dict) -> str:
    """Cấp độ theo chặng (N5→N1), không tin `day.level` kiểu 'Trọn gói'."""
    try:
        return phase_for_day(int(day.get("day") or 0), 2520)[1]
    except Exception:
        lv = str(day.get("level") or "")
        m = re.search(r"\bN[1-5]\b", lv)
        return m.group(0) if m else "N5"


def _complexity(text: str) -> int:
    return len(re.sub(r"\s+", " ", str(text or "")))


def _key_item(x: dict) -> str:
    if x.get("turns"):
        return "|".join(str(t.get("line_target") or "") for t in x["turns"])
    return (x.get("title") or x.get("pattern") or x.get("sentence")
            or x.get("question") or json.dumps(x, ensure_ascii=False, sort_keys=True))


def _add_lib(lib: list, seen: set, item: dict, level: str, slug: str,
             cx_text: str = "") -> None:
    if item.get("_gen"):
        return
    key = _key_item(item)
    if not key or key in seen:
        return
    it = _fix_obj(slug, dict(item))
    it["_level"] = level
    it["_cx"] = _complexity(cx_text or it.get("example_sentence")
                            or it.get("sentence") or it.get("question"))
    seen.add(key)
    lib.append(it)


def _fix_example(slug: str, e: dict) -> dict | None:
    """Đổi chỗ sentence/meaning nếu bị ngược, bỏ ví dụ không đúng ngôn ngữ."""
    if not isinstance(e, dict):
        return None
    s = _fix_text(slug, e.get("sentence")).strip()
    vi = str(e.get("meaning_vi") or "").strip()
    if not _valid_example_text(slug, s) and _valid_example_text(slug, vi):
        s, vi = vi, s
    if not _valid_example_text(slug, s):
        return None
    out = dict(e)
    out["sentence"] = s
    out["meaning_vi"] = vi
    return out


def _bad_dialogue(slug: str, dlg: dict) -> bool:
    """Hội thoại template / thiếu lượt / câu không đúng ngôn ngữ đích."""
    if _is_template_dialogue(dlg):
        return True
    turns = [t for t in (dlg.get("turns") or []) if isinstance(t, dict)]
    if len(turns) < 2:
        return True
    return any(not _valid_target(slug, t.get("line_target")) for t in turns)


def build_libraries(course: dict, slug: str) -> dict:
    """Rút thư viện bản ngữ từ các ngày đã có nội dung tốt."""
    libs = {"grammar": [], "pattern": [], "common": [], "dialogue": [],
            "grammar_quiz": [], "common_quiz": []}
    seen = {k: set() for k in libs}
    for d in course.get("days") or []:
        # Chỉ rút từ ngày có nội dung GỐC (AI/offline gốc), không rút từ ngày
        # đã được công cụ này bổ sung — tránh tự nhân bản khi chạy lại.
        if str(d.get("source") or "").strip().lower() == "offline":
            continue
        lv = _level_of(d)
        for g in d.get("grammar") or []:
            if not isinstance(g, dict):
                continue
            # Bỏ mục ngữ pháp tiếng Nhật lẫn trong khóa khác.
            if slug != JP and _JP_KANA.search(json.dumps(g, ensure_ascii=False)):
                continue
            exs = [x for x in (_fix_example(slug, e) for e in (g.get("examples") or [])) if x]
            if not exs:
                continue
            gg = {k: v for k, v in g.items() if k != "examples"}
            gg["examples"] = exs
            _add_lib(libs["grammar"], seen["grammar"], gg, lv, slug,
                     cx_text=max((e["sentence"] for e in exs), key=len))
        for p in d.get("sentence_patterns") or []:
            if not isinstance(p, dict):
                continue
            s = str(p.get("example_sentence") or "").strip()
            vi = str(p.get("example_meaning_vi") or "").strip()
            if not _valid_target(slug, s) and _valid_target(slug, vi):
                s, vi = vi, s
            if not _valid_target(slug, s):
                continue
            pp = dict(p)
            pp["example_sentence"] = s
            pp["example_meaning_vi"] = vi
            _add_lib(libs["pattern"], seen["pattern"], pp, lv, slug, cx_text=s)
        for c in d.get("common_sentences") or []:
            if not isinstance(c, dict):
                continue
            s = str(c.get("sentence") or "").strip()
            vi = str(c.get("meaning_vi") or "").strip()
            if not _valid_target(slug, s) and _valid_target(slug, vi):
                s, vi = vi, s
            if not _valid_target(slug, s):
                continue
            cc = dict(c)
            cc["sentence"] = s
            cc["meaning_vi"] = vi
            _add_lib(libs["common"], seen["common"], cc, lv, slug, cx_text=s)
        for dl in d.get("dialogue") or []:
            if not isinstance(dl, dict) or _is_template_dialogue(dl):
                continue
            if str(dl.get("title") or "").startswith("Hội thoại mẫu — Ngày"):
                continue  # hội thoại do công cụ này sinh, không đưa vào thư viện
            turns = [t for t in (dl.get("turns") or []) if isinstance(t, dict)]
            if len(turns) < 2:
                continue
            if any(not _valid_target(slug, t.get("line_target")) for t in turns):
                continue
            ddl = {k: v for k, v in dl.items() if k != "audio_ref"}
            ddl["turns"] = [{k: v for k, v in t.items() if k != "audio_ref"}
                            for t in turns]
            _add_lib(libs["dialogue"], seen["dialogue"], ddl, lv, slug,
                     cx_text=max((str(t.get("line_target") or "") for t in turns), key=len))
        q = d.get("quiz") or {}
        for gq in q.get("grammar") or []:
            if isinstance(gq, dict) and gq.get("question") and len(gq.get("options") or []) >= 2:
                _add_lib(libs["grammar_quiz"], seen["grammar_quiz"], gq, lv, slug,
                         cx_text=" ".join(str(x) for x in gq.get("options") or []))
        for cq in q.get("common") or []:
            if isinstance(cq, dict) and cq.get("question") and len(cq.get("options") or []) >= 2:
                _add_lib(libs["common_quiz"], seen["common_quiz"], cq, lv, slug,
                         cx_text=" ".join(str(x) for x in cq.get("options") or []))
    return libs


_LV_ORDER = ["N5", "N4", "N3", "N2", "N1"]


def _lv_dist(a: str, b: str) -> int:
    try:
        return abs(_LV_ORDER.index(a) - _LV_ORDER.index(b))
    except ValueError:
        return 9


def pick_items(pool: list, n: int, level: str, day: int, salt: int = 0) -> list:
    """Chọn n mục: ưu tiên cùng cấp, cấp cao dùng câu dài hơn, xoay theo ngày."""
    if not pool or n <= 0:
        return []
    same = [x for x in pool if x.get("_level") == level]
    if len(same) >= n:
        cand = same
    else:
        cand = sorted(pool, key=lambda x: (_lv_dist(x.get("_level", "N5"), level), x.get("_cx", 0)))
        # giữ các mục cùng cấp trước, sau đó mới đến gần cấp
        cand = same + [x for x in cand if x not in same]
    # Cấp càng cao càng ưu tiên câu dài (chia 4 khoảng độ dài).
    cand = sorted(cand, key=lambda x: (x.get("_cx", 0), _key_item(x)))
    if len(cand) > n:
        try:
            band = _LV_ORDER.index(level)
        except ValueError:
            band = 0
        lo = int(len(cand) * band / 5)
        hi = max(lo + n, int(len(cand) * (band + 1) / 5))
        window = cand[lo:hi] or cand
        start = (day * 7 + salt) % len(window)
        out = []
        for i in range(len(window)):
            x = window[(start + i) % len(window)]
            if x not in out:
                out.append(x)
            if len(out) >= n:
                break
        if len(out) < n:
            for x in cand:
                if x not in out:
                    out.append(x)
                if len(out) >= n:
                    break
        return out
    start = (day * 7 + salt) % len(cand)
    return [cand[(start + i) % len(cand)] for i in range(min(n, len(cand)))]


def _shuffle_q(q: dict, seed: str) -> dict:
    """Trộn đáp án cố định theo seed, cập nhật answer_index."""
    out = dict(q)
    opts = list(out.get("options") or [])
    if len(opts) < 2:
        return out
    correct = opts[int(out.get("answer_index") or 0)] if 0 <= int(out.get("answer_index") or 0) < len(opts) else opts[0]
    rnd = random.Random(seed)
    rnd.shuffle(opts)
    out["options"] = opts
    try:
        out["answer_index"] = opts.index(correct)
    except ValueError:
        out["answer_index"] = 0
    return out


def _grammar_from_offline(day: int, level: str) -> list:
    try:
        from ai.offline_grammar import grammar_for_day
        gs = grammar_for_day(day, level=level)
    except Exception:
        return []
    out = []
    for g in gs:
        exs = [x for x in (_fix_example(JP, e) for e in (g.get("examples") or [])) if x]
        if not exs:
            continue
        gg = dict(g)
        gg["examples"] = exs
        gg["level"] = g.get("level") or level
        gg["_gen"] = True
        out.append(gg)
    return out


def _patterns_from_grammar(slug: str, grammar: list, n: int = 4) -> list:
    out = []
    for g in grammar:
        exs = [e for e in (g.get("examples") or [])
               if isinstance(e, dict) and _valid_target(slug, e.get("sentence"))]
        for e in exs[:2]:
            s = _fix_text(slug, e.get("sentence")).strip()
            if not s:
                continue
            out.append({
                "pattern": g.get("title") or "Mẫu câu",
                "meaning_vi": (g.get("explanation") or "")[:180],
                "structure_note": g.get("pronunciation_focus") or "",
                "example_sentence": s,
                "example_meaning_vi": e.get("meaning_vi") or "",
                "_gen": True,
            })
            if len(out) >= n:
                return out
    return out


def _patterns_from_lib(lib: list, n: int, level: str, day: int) -> list:
    picked = pick_items(lib, n, level, day, salt=1)
    out = []
    for p in picked:
        out.append({k: v for k, v in p.items() if not k.startswith("_")})
    return out


def _common_from_lib(lib: list, n: int, level: str, day: int) -> list:
    picked = pick_items(lib, n, level, day, salt=2)
    return [{k: v for k, v in c.items() if not k.startswith("_")} for c in picked]


def _closing(slug: str) -> tuple:
    return _CLOSING.get(slug, _CLOSING["tiếng_anh"])


def _is_question(slug: str, s: str) -> bool:
    s = (s or "").strip()
    if not s:
        return False
    if s.endswith("?") or s.endswith("？"):
        return True
    if slug == JP and re.search(r"(か|の|ですか|ますか)[。？?]?$", s):
        return True
    if slug == "tiếng_trung" and re.search(r"(吗|呢|什么|怎么|为什么|哪|谁)[。？?]?$", s):
        return True
    if slug == "tiếng_hàn_quốc" and re.search(r"(까|나요|세요|어디|무엇|누구)[。？?]?$", s):
        return True
    return False


def _build_dialogue(day: int, slug: str, level: str, patterns: list,
                    commons: list, real_lib: list) -> list:
    """Hội thoại thật nếu đủ; nếu ít thì dựng Q&A từ mẫu câu + câu thông dụng."""
    n_real = len(real_lib)
    use_real = bool(n_real) and (
        n_real >= 80 or (n_real >= 40 and day % 3 == 0) or (n_real >= 20 and day % 5 == 0))
    if use_real:
        dlg = {k: v for k, v in pick_items(real_lib, 1, level, day, salt=3)[0].items()
               if not k.startswith("_")}
        dlg.pop("audio_ref", None)
        dlg["kind"] = dlg.get("kind") or "scene"
        dlg["turns"] = [{k: v for k, v in t.items() if k != "audio_ref"}
                        for t in (dlg.get("turns") or [])]
        return [dlg]

    lines = []
    for p in patterns:
        if p.get("example_sentence"):
            lines.append((p["example_sentence"], p.get("example_meaning_vi") or ""))
    for c in commons:
        if c.get("sentence"):
            lines.append((c["sentence"], c.get("meaning_vi") or ""))
    if len(lines) < 2:
        return []
    qs = [x for x in lines if _is_question(slug, x[0])]
    ss = [x for x in lines if x not in qs]
    ack = _ACK.get(slug, _ACK["tiếng_anh"])
    close_a, close_b = _closing(slug)
    seq = []

    def _add(line):
        # Xen kẽ tuyệt đối A/B: A ở vị trí chẵn, B ở vị trí lẻ.
        seq.append(("A" if len(seq) % 2 == 0 else "B", line))

    qi = si = 0
    while len(seq) < 6 and (qi < len(qs) or si < len(ss)):
        if len(seq) % 2 == 0 and qi < len(qs):
            _add(qs[qi])
            qi += 1
        elif len(seq) % 2 == 1 and si < len(ss):
            _add(ss[si])
            si += 1
        elif qi < len(qs):
            _add(qs[qi])
            qi += 1
        elif si < len(ss):
            _add(ss[si])
            si += 1
        else:
            break
    if not seq:
        seq = [("A", lines[0]), ("B", lines[1])]
    _add((ack, ""))
    _add((close_a, ""))
    _add((close_b, ""))
    turns = [{"speaker": sp, "line_target": s, "line_vi": vi, "focus_words": []}
             for sp, (s, vi) in seq]
    return [{
        "title": f"Hội thoại mẫu — Ngày {day}",
        "situation": "Luyện phản xạ với mẫu câu và câu thông dụng của ngày.",
        "level_tag": level,
        "turns": turns,
        "cultural_note": "Đọc to theo vai A/B; thay từ của ngày để luyện nói.",
        "kind": "micro",
        "_gen": True,
    }]


def _make_common_quiz(commons: list, lib: list, day: int, slug: str, n: int = 3) -> list:
    out = []
    pool = [c for c in lib if c.get("sentence")]
    for i, c in enumerate(commons[:n]):
        sit = c.get("situation") or c.get("meaning_vi") or ""
        if not sit:
            continue
        correct = c.get("sentence")
        distract = [x.get("sentence") for x in pool if x.get("sentence") != correct]
        if len(distract) < 3:
            continue
        rnd = random.Random(f"{slug}|{day}|common|{i}")
        opts = [correct] + rnd.sample(distract, 3)
        q = {"question": f"Câu nào phù hợp với tình huống: “{sit}”?",
             "options": opts, "answer_index": 0,
             "explanation": f"{correct} — {c.get('meaning_vi') or ''}",
             "_gen": True}
        out.append(_shuffle_q(q, f"{slug}|{day}|common|{i}"))
    return out


def _make_grammar_quiz(grammar: list, lib: list, day: int, slug: str, n: int = 3) -> list:
    out = []
    seen = set()
    for g in grammar:
        for q in (g.get("mini_quiz") or []):
            if not isinstance(q, dict) or not q.get("question") or not q.get("options"):
                continue
            key = q["question"]
            if key in seen:
                continue
            seen.add(key)
            out.append(_shuffle_q(q, f"{slug}|{day}|grammar|{len(out)}"))
            if len(out) >= n:
                return out
    for q in pick_items(lib, n - len(out), _level_of({"day": day}), day, salt=4):
        if q.get("question") in seen:
            continue
        seen.add(q.get("question"))
        out.append(_shuffle_q({k: v for k, v in q.items() if not k.startswith("_")},
                              f"{slug}|{day}|gq|{len(out)}"))
        if len(out) >= n:
            break
    # Fallback: hỏi ví dụ đúng của ngữ pháp.
    for i, g in enumerate(grammar):
        if len(out) >= n:
            break
        exs = [e.get("sentence") for e in (g.get("examples") or []) if e.get("sentence")]
        if not exs:
            continue
        others = [e.get("sentence") for gg in grammar if gg is not g
                  for e in (gg.get("examples") or []) if e.get("sentence")]
        if len(others) < 3:
            continue
        rnd = random.Random(f"{slug}|{day}|gex|{i}")
        correct = exs[0]
        q = {"question": f"Câu nào là ví dụ của ngữ pháp “{g.get('title')}”?",
             "options": [correct] + rnd.sample(others, 3), "answer_index": 0,
             "explanation": f"{correct} — {g.get('title')}",
             "_gen": True}
        out.append(_shuffle_q(q, f"{slug}|{day}|gex|{i}"))
    return out


def _pattern_quiz(patterns: list, day: int, slug: str, n: int = 3) -> list:
    out = []
    pool = [p for p in patterns if p.get("example_sentence")]
    for i, p in enumerate(pool[:n]):
        correct = p.get("example_sentence")
        others = [x.get("example_sentence") for x in pool if x.get("example_sentence") != correct]
        if len(others) < 2:
            continue
        rnd = random.Random(f"{slug}|{day}|pat|{i}")
        opts = [correct] + rnd.sample(others, min(3, len(others)))
        q = {"question": f"Chọn câu đúng với mẫu: “{p.get('pattern')}”",
             "options": opts, "answer_index": 0,
             "explanation": f"{correct} — {p.get('meaning_vi') or ''}",
             "_gen": True}
        out.append(_shuffle_q(q, f"{slug}|{day}|pat|{i}"))
    return out


def _grammar_has_japanese(g: dict) -> bool:
    return bool(_JP_KANA.search(json.dumps(g, ensure_ascii=False)))


def enrich_day(d: dict, slug: str, libs: dict) -> dict:
    """Bổ sung 1 ngày. Trả về dict thống kê thay đổi."""
    day = int(d.get("day") or 0)
    level = _level_of(d)
    st = {"day": day, "pattern": 0, "common": 0, "grammar": 0, "dialogue": 0,
          "grammar_clean": 0, "quiz_g": 0, "quiz_c": 0, "quiz_p": 0}

    # ── NGỮ PHÁP ──
    old_g = [g for g in (d.get("grammar") or []) if isinstance(g, dict)]
    need_g = (not old_g)
    if slug == JP:
        # 103 ngày đầu đã có ngữ pháp AI riêng — giữ nguyên nếu có title/giải thích.
        good_ai = bool(old_g) and all(
            g.get("title") and g.get("explanation") for g in old_g)
        if day > 103 or not good_ai:
            need_g = True
        if need_g:
            new_g = _grammar_from_offline(day, level)
            if new_g and new_g != old_g:
                d["grammar"] = new_g
                st["grammar"] = len(new_g)
                old_g = new_g
    else:
        # Khóa khác: bỏ ngữ pháp tiếng Nhật / sai cấp.
        if any(_grammar_has_japanese(g) for g in old_g):
            need_g = True
        if old_g and all(g.get("level") in _LV_ORDER for g in old_g) \
                and any(g.get("level") != level for g in old_g):
            need_g = True
        if need_g:
            new_g = [{k: v for k, v in g.items() if not k.startswith("_")}
                     for g in pick_items(libs["grammar"], 4, level, day, salt=5)]
            if new_g and new_g != old_g:
                d["grammar"] = new_g
                st["grammar"] = len(new_g)
                old_g = new_g

    # Sửa/lọc ví dụ ngữ pháp còn tiếng Việt/romaji hoặc sai ngôn ngữ
    # (giữ nguyên mục ngữ pháp, chỉ bỏ ví dụ không hợp lệ).
    if old_g:
        cleaned = []
        fixed = 0
        for g in old_g:
            exs = [x for x in (_fix_example(slug, e) for e in (g.get("examples") or [])) if x]
            if exs != (g.get("examples") or []):
                fixed += 1
                gg = dict(g)
                gg["examples"] = exs
                cleaned.append(gg)
            else:
                cleaned.append(g)
        if fixed:
            d["grammar"] = cleaned
            old_g = cleaned
            st["grammar_clean"] = fixed

    # ── MẪU CÂU ──
    old_p = [p for p in (d.get("sentence_patterns") or []) if isinstance(p, dict)]
    bad_p = (not old_p) or any(
        not _valid_target(slug, p.get("example_sentence")) for p in old_p)
    if bad_p:
        if slug == JP:
            new_p = (_patterns_from_grammar(slug, old_g, n=4)
                     or _patterns_from_lib(libs["pattern"], 4, level, day))
        else:
            new_p = _patterns_from_lib(libs["pattern"], 4, level, day)
            if not new_p:
                new_p = _patterns_from_grammar(slug, old_g, n=4)
        if new_p:
            if new_p != old_p:
                d["sentence_patterns"] = new_p
                st["pattern"] = len(new_p)
            old_p = new_p

    # ── CÂU THÔNG DỤNG ──
    old_c = [c for c in (d.get("common_sentences") or []) if isinstance(c, dict)]
    bad_c = (not old_c) or any(
        not _valid_target(slug, c.get("sentence")) for c in old_c)
    if bad_c:
        new_c = _common_from_lib(libs["common"], 5, level, day)
        if not new_c and old_g:
            new_c = [{"sentence": e.get("sentence"), "meaning_vi": e.get("meaning_vi") or "",
                      "situation": f"Mẫu câu ngữ pháp: {g.get('title')}"}
                     for g in old_g for e in (g.get("examples") or []) if e.get("sentence")][:5]
        if new_c:
            if new_c != old_c:
                d["common_sentences"] = new_c
                st["common"] = len(new_c)
            old_c = new_c

    # ── HỘI THOẠI ──
    old_d = [x for x in (d.get("dialogue") or []) if isinstance(x, dict)]
    if not old_d or any(_bad_dialogue(slug, x) for x in old_d):
        new_d = _build_dialogue(day, slug, level, old_p, old_c, libs["dialogue"])
        if new_d and new_d != old_d:
            d["dialogue"] = new_d
            st["dialogue"] = len(new_d)
            # Audio cũ không còn khớp nội dung mới.
            if isinstance(d.get("media"), dict):
                d["media"]["dialogue_audio"] = {}

    # ── QUIZ ──
    q = d.get("quiz")
    if not isinstance(q, dict):
        q = {}
    for k in ("vocab", "pattern", "common", "grammar", "mixed"):
        if not isinstance(q.get(k), list):
            q[k] = []
    if not q["grammar"]:
        gq = _make_grammar_quiz(old_g, libs["grammar_quiz"], day, slug, n=3)
        if gq:
            q["grammar"] = gq
            st["quiz_g"] = len(gq)
    if not q["common"]:
        cq = _make_common_quiz(old_c, libs["common"], day, slug, n=3)
        if cq:
            q["common"] = cq
            st["quiz_c"] = len(cq)
    if len(q["pattern"]) < 2 and old_p:
        pq = _pattern_quiz(old_p, day, slug, n=3)
        if pq:
            q["pattern"] = pq + q["pattern"]
            st["quiz_p"] = len(pq)
    d["quiz"] = q

    # Bỏ dấu vết template cũ trong dialogue.
    for x in d.get("dialogue") or []:
        if isinstance(x, dict) and _is_template_dialogue(x):
            x["kind"] = "micro"
    return st


def enrich_course(slug: str, apply: bool, limit: int = 0) -> dict:
    path = os.path.join(CD, slug, "course.json")
    if not os.path.isfile(path):
        return {"slug": slug, "error": "no_course"}
    with open(path, encoding="utf-8") as f:
        course = json.load(f)
    libs = build_libraries(course, slug)
    days = course.get("days") or []
    stats = {"slug": slug, "days": len(days), "changed": 0, "pattern": 0,
             "common": 0, "grammar": 0, "dialogue": 0, "grammar_clean": 0,
             "quiz_g": 0, "quiz_c": 0, "quiz_p": 0,
             "lib": {k: len(v) for k, v in libs.items()}}
    for d in days[:limit] if limit else days:
        st = enrich_day(d, slug, libs)
        if any(st[k] for k in ("pattern", "common", "grammar", "dialogue",
                               "grammar_clean", "quiz_g", "quiz_c", "quiz_p")):
            stats["changed"] += 1
            for k in ("pattern", "common", "grammar", "dialogue", "grammar_clean",
                      "quiz_g", "quiz_c", "quiz_p"):
                stats[k] += st[k]
    if apply and stats["changed"]:
        course["updated_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(course, f, ensure_ascii=False, indent=2)
        # Giữ 1 bản dự phòng ở lần chạy đầu.
        bak = path + ".bak"
        if not os.path.isfile(bak):
            try:
                os.replace(path, bak)
            except OSError:
                pass
        os.replace(tmp, path)
    return stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="all")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    langs = ([args.lang] if args.lang != "all" else
             sorted(s for s in os.listdir(CD)
                    if not s.startswith("_")
                    and os.path.isfile(os.path.join(CD, s, "course.json"))))
    for slug in langs:
        r = enrich_course(slug, apply=not args.dry_run, limit=args.limit)
        if r.get("error"):
            _log(f"  {slug:22} LỖI: {r['error']}")
            continue
        _log(f"  {slug:22} ngày {r['days']:5} | đổi {r['changed']:5} | "
             f"+mẫu câu {r['pattern']:5} | +câu thông dụng {r['common']:5} | "
             f"+ngữ pháp {r['grammar']:5} | +hội thoại {r['dialogue']:5} | "
             f"sửa ví dụ {r['grammar_clean']:3} | "
             f"+quiz G {r['quiz_g']:4}/C {r['quiz_c']:4}/P {r['quiz_p']:4}"
             + ("" if not args.dry_run else "  (DRY-RUN)"))
        _log(f"      thư viện: {r['lib']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
