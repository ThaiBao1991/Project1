# -*- coding: utf-8 -*-
"""tools/add_ipa_english.py — Chuẩn hoá & bổ sung IPA cho từ vựng tiếng Anh.

VẤN ĐỀ (19/11/2026):
  • 22.610/25.200 mục từ vựng tiếng Anh thiếu `ipa`/`pronunciation`.
  • Một số `pronunciation` đã có dấu `/…/` ⇒ web bọc thêm `/` thành `//…//`.
  • 2 ngày (95, 261) có "reasoning trace" tiếng Hàn trong trường `tone`.

CÁCH LÀM (0 quota AI):
  • Dùng CMUdict (126.052 từ) → ARPAbet → IPA có trọng âm/âm tiết.
  • Từ ghép/viết hoa: thử lowercase, bỏ 's, tách CamelCase, ghép IPA từng phần.
  • Bảng tay cho từ vay tiếng Pháp + viết tắt thương mại (KPI, ROI, FOB…).
  • Chuẩn hoá `pronunciation` (bỏ `/` đầu/cuối) và `ipa` (có `/…/`).
  • KHÔNG đổi `word`, `audio_ref`, `image_ref`, `media`.

CÁCH DÙNG:
  python -X utf8 tools/add_ipa_english.py --dry-run
  python -X utf8 tools/add_ipa_english.py
  python -X utf8 tools/add_ipa_english.py --no-export
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CD = os.path.join(BASE, "data", "ai_courses")
SLUG = "tiếng_anh"

try:
    import cmudict
    _CMU = cmudict.dict()
except Exception:  # pragma: no cover
    _CMU = {}

VOWELS = {"AA", "AE", "AH", "AO", "AW", "AY", "EH", "ER", "EY",
          "IH", "IY", "OW", "OY", "UH", "UW"}
ONSETS = {
    "", "B", "CH", "D", "DH", "F", "G", "HH", "JH", "K", "L", "M", "N",
    "NG", "P", "R", "S", "SH", "T", "TH", "V", "W", "Y", "Z", "ZH",
    "B L", "B R", "B Y", "CH R", "D R", "D W", "D Y", "F L", "F R", "F Y",
    "G L", "G R", "G W", "G Y", "HH Y", "K L", "K R", "K W", "K Y",
    "P L", "P R", "P Y", "S K", "S L", "S M", "S N", "S P", "S T", "S W",
    "S Y", "SH R", "T R", "T W", "T Y", "TH R", "V Y", "Z W",
    "S K R", "S P L", "S P R", "S T R", "S K W",
}
V_IPA = {"AA": "ɑː", "AE": "æ", "AH": "ʌ", "AO": "ɔː", "AW": "aʊ", "AY": "aɪ",
         "EH": "e", "ER": "ɜː", "EY": "eɪ", "IH": "ɪ", "IY": "iː", "OW": "oʊ",
         "OY": "ɔɪ", "UH": "ʊ", "UW": "uː"}
C_IPA = {"B": "b", "CH": "tʃ", "D": "d", "DH": "ð", "F": "f", "G": "ɡ",
         "HH": "h", "JH": "dʒ", "K": "k", "L": "l", "M": "m", "N": "n",
         "NG": "ŋ", "P": "p", "R": "r", "S": "s", "SH": "ʃ", "T": "t",
         "TH": "θ", "V": "v", "W": "w", "Y": "j", "Z": "z", "ZH": "ʒ"}

# Từ vay / viết tắt phổ biến mà CMUdict thiếu hoặc đọc sai trong ngữ cảnh bài học.
MANUAL = {
    "kpi": "/ˌkeɪ.piːˈaɪ/", "roi": "/ˌɑːr.oʊˈaɪ/", "diy": "/ˌdiː.aɪˈwaɪ/",
    "eta": "/ˌiː.tiːˈeɪ/", "ebitda": "/ɪˈbɪt.də/", "btw": "/ˌbiː.tiːˈdʌb.əl.juː/",
    "fob": "/ˌef.oʊˈbiː/", "cif": "/ˌsiː.aɪˈef/", "hr": "/ˌeɪtʃˈɑːr/",
    "aob": "/ˌeɪ.oʊˈbiː/", "cliché": "/ˈkliː.ʃeɪ/", "café": "/kæˈfeɪ/",
    "résumé": "/ˈrez.ə.meɪ/", "naïve": "/naɪˈiːv/", "fiancé": "/fiˈɒn.seɪ/",
    "entrée": "/ˈɒn.treɪ/", "déjà vu": "/ˌdeɪ.ʒɑː ˈvuː/",
    "lmao": "/ˌel.em.eɪˈoʊ/", "wtf": "/ˌdʌb.əl.juː.tiːˈef/",
    "omg": "/ˌoʊ.emˈdʒiː/", "idk": "/ˌaɪ.diːˈkeɪ/",
    "tbh": "/ˌtiː.biːˈeɪtʃ/", "fomo": "/ˈfoʊ.moʊ/",
    "iykyk": "/ˌaɪ.waɪ.keɪ.waɪˈkeɪ/", "tgif": "/ˌtiː.dʒiː.aɪˈef/",
    "rizz": "/rɪz/", "delulu": "/dɪˈluː.luː/", "lowkey": "/ˈloʊ.kiː/",
    "highkey": "/ˈhaɪ.kiː/", "knackered": "/ˈnæk.ərd/", "chuffed": "/tʃʌft/",
    "schlep": "/ʃlep/", "gaslighting": "/ˈɡæs.laɪ.tɪŋ/",
    "mindfulness": "/ˈmaɪnd.fəl.nəs/", "reframe": "/ˌriːˈfreɪm/",
    "backstory": "/ˈbæk.stɔːr.i/", "crowdfunding": "/ˈkraʊd.fʌn.dɪŋ/",
    "cybersecurity": "/ˌsaɪ.bər.sɪˈkjʊr.ə.ti/",
    "macronutrient": "/ˌmæk.roʊˈnuː.tri.ənt/",
    "counterargument": "/ˈkaʊn.tər.ˌɑːr.ɡjə.mənt/",
    "self-actualization": "/ˌself.æk.tʃu.ə.ləˈzeɪ.ʃən/",
    "monolid": "/ˈmɑː.noʊ.lɪd/", "adjudicator": "/əˈdʒuː.dɪ.keɪ.tər/",
    "bootstrapping": "/ˈbuːt.stræp.ɪŋ/", "ethnography": "/eθˈnɑː.ɡrə.fi/",
    "severability": "/ˌsev.ər.əˈbɪl.ə.ti/", "incoterms": "/ˈɪn.koʊ.tɜːrmz/",
    "haha": "/ˈhɑː.hɑː/", "hmm": "/həm/", "aww": "/ɔː/", "awww": "/ɔː/",
    "ahhh": "/ɑː/", "cuz": "/kəz/", "dawg": "/dɔːɡ/", "boi": "/bɔɪ/",
}
CONTRACTIONS = {
    "thats": "/ðæts/", "didnt": "/ˈdɪd.ənt/", "doesnt": "/ˈdʌz.ənt/",
    "ive": "/aɪv/", "im": "/aɪm/", "youre": "/jʊr/", "dont": "/doʊnt/",
    "cant": "/kænt/", "wont": "/woʊnt/", "isnt": "/ˈɪz.ənt/",
    "wasnt": "/ˈwʌz.ənt/", "werent": "/ˈwɜːr.ənt/",
    "havent": "/ˈhæv.ənt/", "hasnt": "/ˈhæz.ənt/",
    "couldnt": "/ˈkʊd.ənt/", "shouldnt": "/ˈʃʊd.ənt/",
    "wouldnt": "/ˈwʊd.ənt/", "aint": "/eɪnt/",
    "aswell": "/əz ˈwel/", "atleast": "/ət ˈliːst/",
}
UK_US = {
    "organised": "organized", "analysed": "analyzed", "analysing": "analyzing",
    "authorised": "authorized", "behavioural": "behavioral", "calibre": "caliber",
    "centred": "centered", "characterised": "characterized", "colourful": "colorful",
    "counselling": "counseling", "counsellor": "counselor", "criticise": "criticize",
    "criticised": "criticized", "criticising": "criticizing", "defences": "defenses",
    "ageing": "aging", "artefacts": "artifacts", "chilli": "chili",
    "civilisation": "civilization", "customisation": "customization",
    "emphasise": "emphasize", "emphasised": "emphasized", "favour": "favor",
    "favourite": "favorite", "honour": "honor", "labour": "labor",
    "neighbour": "neighbor", "organise": "organize", "practise": "practice",
    "programmes": "programs", "realise": "realize", "realised": "realized",
    "recognise": "recognize", "recognised": "recognized", "rumour": "rumor",
    "saviour": "savior", "theatre": "theater", "travelling": "traveling",
    "travelled": "traveled", "offence": "offense", "jewellery": "jewelry",
    "flavour": "flavor", "flavours": "flavors", "colour": "color",
    "colours": "colors", "favour": "favor", "honour": "honor",
    "labour": "labor", "neighbour": "neighbor", "rumours": "rumors",
    "councillor": "councilor", "offences": "offenses",
}
WORD_FIXES = {
    "comin": "coming", "doin": "doing", "goin": "going", "nothin": "nothing",
    "somethin": "something", "prof": "professor", "pics": "pictures",
    "vol": "volume", "dept": "department", "approx": "approximately",
    "avg": "average", "cont": "continued", "def": "definitely",
    "adm": "administration", "ans": "answer", "apr": "april",
    "mins": "minutes", "hahaha": "/hɑː.hɑː.hɑː/", "gif": "/ɡɪf/",
    "covid": "/ˈkoʊ.vɪd/", "brexit": "/ˈbrek.sɪt/", "vii": "/ˈsev.ən/",
    "e.g": "/ˌiːˈdʒiː/", "i.e": "/ˌaɪˈiː/",
    "https": "/ˌeɪtʃ.tiː.tiː.piːˈes/", "remix": "/ˈriː.mɪks/",
    "hes": "/hiːz/", "theres": "/ðerz/", "midfielder": "/ˈmɪd.fiːl.dər/",
    "pokémon": "/ˈpoʊ.keɪ.mɒn/", "ebook": "/ˈiː.bʊk/", "viii": "/eɪt/",
    "capt": "captain", "govt": "government", "int": "international",
    "dem": "democrat", "dems": "democrats", "eds": "editors",
    "hrs": "hours", "pls": "please", "ppl": "people", "exp": "experience",
    "tha": "the", "hmmm": "/həm/", "footballer": "/ˈfʊt.bɔː.lər/",
    "midfield": "/ˈmɪd.fiːld/", "jul": "july",
}
LETTER_IPA = {
    "A": "eɪ", "B": "biː", "C": "siː", "D": "diː", "E": "iː", "F": "ef",
    "G": "dʒiː", "H": "eɪtʃ", "I": "aɪ", "J": "dʒeɪ", "K": "keɪ", "L": "el",
    "M": "em", "N": "en", "O": "oʊ", "P": "piː", "Q": "kjuː", "R": "ɑːr",
    "S": "es", "T": "tiː", "U": "juː", "V": "viː", "W": "ˈdʌb.əl.juː",
    "X": "eks", "Y": "waɪ", "Z": "ziː",
}
DIGIT_IPA = {"0": "ˈzɪr.oʊ", "1": "ˈwʌn", "2": "ˈtuː", "3": "ˈθriː",
             "4": "ˈfɔːr", "5": "ˈfaɪv", "6": "ˈsɪks", "7": "ˈsev.ən",
             "8": "ˈeɪt", "9": "ˈnaɪn"}

TRACE = re.compile(r"부탁해|Let'?s use focus_words|wait keep it simple|"
                   r"here'?s a thinking process|here is a thinking process", re.I)
HANGUL = re.compile(r"[\uac00-\ud7af]")
HAN = re.compile(r"[\u4e00-\u9fff]")


def _log(m: str) -> None:
    print(m, flush=True)


def _bs(p: str):
    m = re.match(r"^([A-Z]+)([0-2])?$", p)
    return (m.group(1), m.group(2) or "") if m else (p, "")


def arpabet_to_ipa(phones: list) -> str:
    seq = [_bs(p) for p in phones]
    sylls = []
    pos = 0
    for vi in [i for i, (b, _s) in enumerate(seq) if b in VOWELS]:
        cluster = [b for b, _s in seq[pos:vi]]
        onset = []
        coda_prev = []
        for k in range(len(cluster), -1, -1):
            if " ".join(cluster[len(cluster) - k:]) in ONSETS:
                onset = cluster[len(cluster) - k:]
                coda_prev = cluster[:len(cluster) - k]
                break
        if sylls:
            sylls[-1]["coda"].extend(coda_prev)
        sylls.append({"onset": onset, "vowel": seq[vi], "coda": []})
        pos = vi + 1
    if not sylls:
        return ""
    sylls[-1]["coda"].extend([b for b, _s in seq[pos:]])
    out = []
    for sy in sylls:
        b, st = sy["vowel"]
        vtxt = V_IPA.get(b, b.lower())
        if b == "AH" and st == "0":
            vtxt = "ə"
        if b == "ER" and st == "0":
            vtxt = "ɚ"
        txt = ("".join(C_IPA.get(x, x.lower()) for x in sy["onset"]) + vtxt
               + "".join(C_IPA.get(x, x.lower()) for x in sy["coda"]))
        if st == "1":
            txt = "ˈ" + txt
        elif st == "2":
            txt = "ˌ" + txt
        out.append(txt)
    return "/" + ".".join(out) + "/"


ACRONYMS = {"gop", "mps", "nyc", "nhl", "nhs", "usd", "wwe", "apr", "acl",
            "afc", "anc", "aps", "atc", "atl", "aws", "bmi", "cpr", "cbc",
            "cdc", "ceo", "cfo", "cio", "cto", "cpi", "cpa", "cpc", "cpl",
            "cpr", "csa", "csr", "css", "cvs", "dhs", "dmv", "dod", "doj",
            "fbi", "fda", "fifa", "gdp", "gmt", "gps", "hiv", "html", "ibm",
            "imf", "ios", "iso", "lgbt", "nasa", "nato", "nba", "nfl", "ngo",
            "nhs", "nra", "nrl", "nsa", "nsw", "nt", "nz", "oecd", "opec",
            "phd", "pr", "ps", "pta", "rspca", "suv", "tv", "ucl", "uefa",
            "ufc", "ufo", "uk", "un", "usa", "usb", "usd", "ussr", "vip",
            "wto", "wwf", "yha", "ymca", "mvp", "ncaa", "mlb", "mls",
            "ucla", "usc", "uae", "utc", "xxx", "nba", "nfl", "nhl",
            "icc", "snp", "plc", "wwii", "nsfw", "cbd", "var"}


def _spell_out(w: str) -> str | None:
    out = []
    for ch in w:
        if ch.isalpha():
            out.append(LETTER_IPA[ch.upper()])
        elif ch.isdigit():
            out.append(DIGIT_IPA[ch])
    return "/" + " ".join(out) + "/" if out else None


def _ipa_single(w: str) -> str | None:
    w = w.strip()
    if not w:
        return None
    low = w.lower()
    if low in MANUAL:
        return MANUAL[low]
    if low in CONTRACTIONS:
        return CONTRACTIONS[low]
    if low in UK_US:
        return _ipa_single(UK_US[low])
    if low in WORD_FIXES:
        v = WORD_FIXES[low]
        return v if v.startswith("/") else _ipa_single(v)
    # CamelCase / compound: AutoCorrect → Auto + Correct
    parts = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])", w)
    if len(parts) > 1:
        subs = [_ipa_single(p) for p in parts]
        if all(subs):
            return "/" + ".".join(s.strip("/") for s in subs) + "/"
    for cand in (low, re.sub(r"'s$", "", low)):
        prons = _CMU.get(cand)
        if prons:
            return arpabet_to_ipa(prons[0])
    # Danh từ số nhiều / -s: bros, thrones, avengers…
    if low.endswith("s") and len(low) > 3 and low[:-1] in _CMU:
        base_phones = _CMU[low[:-1]][0]
        ipa = arpabet_to_ipa(base_phones)
        last = base_phones[-1].rstrip("012")
        if last in ("P", "T", "K", "F", "TH"):
            suf = "s"
        elif last in ("S", "Z", "SH", "ZH", "CH", "JH"):
            suf = "ɪz"
        else:
            suf = "z"
        return ipa.rstrip("/") + suf + "/"
    # g-dropping: comin → coming, doin → doing
    if low.endswith("in") and (low[:-2] + "ing") in _CMU:
        return arpabet_to_ipa(_CMU[low[:-2] + "ing"][0])
    # Viết tắt / chữ + số: 8gb, b2b, 3ds, NHL…
    if re.search(r"\d", w):
        return _spell_out(w)
    if w.isupper() and 2 <= len(w) <= 6:
        return _spell_out(w)
    if low in ACRONYMS:
        return _spell_out(low)
    return None


def ipa_for(word: str) -> str | None:
    w = str(word or "").strip()
    if not w:
        return None
    if w.lower() in MANUAL:
        return MANUAL[w.lower()]
    if w.lower() in CONTRACTIONS:
        return CONTRACTIONS[w.lower()]
    if w.lower() in WORD_FIXES:
        v = WORD_FIXES[w.lower()]
        return v if v.startswith("/") else ipa_for(v)
    # Bỏ chú thích trong ngoặc, chuẩn hoá gạch nối/khoảng trắng.
    base = re.sub(r"\([^)]*\)", "", w).strip()
    parts = [p for p in re.split(r"[\s/–—-]+", base) if p]
    if len(parts) > 1:
        subs = [_ipa_single(re.sub(r"[^A-Za-zÀ-ÿ']", "", p).strip("'")) for p in parts]
        if all(subs):
            return "/" + " ".join(s.strip("/") for s in subs) + "/"
        return None
    return _ipa_single(re.sub(r"[^A-Za-zÀ-ÿ']", "", base).strip("'"))


def _norm_pron(s: str) -> str:
    return str(s or "").strip().strip("/").strip()


def clean_traces(course: dict) -> int:
    n = 0
    for d in course.get("days") or []:
        for dl in d.get("dialogue") or []:
            for t in dl.get("turns") or []:
                for k in ("tone", "emotion"):
                    s = str(t.get(k) or "")
                    if s and (TRACE.search(s) or HANGUL.search(s) or HAN.search(s)):
                        t[k] = str(t.get("emotion") or "bình thường")
                        n += 1
                        break
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-export", action="store_true")
    args = ap.parse_args()
    path = os.path.join(CD, SLUG, "course.json")
    course = json.load(open(path, encoding="utf-8"))

    fixed_trace = clean_traces(course)
    total = already = filled = missing = normalized = 0
    missing_words = []
    for d in course.get("days") or []:
        for v in d.get("vocab") or []:
            total += 1
            w = str(v.get("word") or "").strip()
            pron = _norm_pron(v.get("pronunciation"))
            ipa = str(v.get("ipa") or "").strip()
            if ipa and not ipa.startswith("/"):
                ipa = "/" + ipa.strip("/") + "/"
            if pron and v.get("pronunciation") != pron:
                v["pronunciation"] = pron
                normalized += 1
            if ipa and not pron:
                v["pronunciation"] = ipa.strip("/")
                normalized += 1
            if pron and not ipa:
                ipa = "/" + pron + "/"
                v["ipa"] = ipa
            if ipa:
                already += 1
                continue
            if not w:
                missing += 1
                continue
            new = ipa_for(w)
            if new:
                v["ipa"] = new
                v["pronunciation"] = new.strip("/")
                filled += 1
            else:
                missing += 1
                if len(missing_words) < 30:
                    missing_words.append(w)

    _log(f"{SLUG}: tổng {total} từ | đã có IPA {already} | điền mới {filled} | "
         f"còn thiếu {missing} | chuẩn hoá {normalized} | xử lý trace {fixed_trace}")
    _log(f"   ví dụ thiếu: {missing_words}")
    if args.dry_run:
        _log("   (DRY-RUN — chưa ghi)")
        return 0
    course["updated_at"] = __import__("datetime").datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(course, f, ensure_ascii=False, indent=2)
    bak = path + ".bak_ipa"
    if not os.path.isfile(bak):
        try:
            os.replace(path, bak)
        except OSError:
            pass
    os.replace(tmp, path)
    _log("   đã ghi course.json")
    if not args.no_export:
        import subprocess
        r = subprocess.run([sys.executable, "-X", "utf8",
                            "tools/export_days_keep_media.py", "--lang", SLUG],
                           cwd=BASE)
        if r.returncode != 0:
            _log("⚠ export web lỗi")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
