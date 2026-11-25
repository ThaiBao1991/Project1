# -*- coding: utf-8 -*-
"""tools/audit_all.py — Kiểm tra toàn bộ tiến độ, dung lượng, nội dung, media.

MỘT LỆNH:
  python -X utf8 tools/audit_all.py
  python -X utf8 tools/audit_all.py --no-online --no-tests

Tạo:
  • docs/AUDIT_REPORT.md   — báo cáo đọc được
  • data/logs/audit.json   — dữ liệu thô

Nội dung kiểm:
  1. Tiến độ media từng khóa (2.520 ngày).
  2. Dung lượng: media/audio/ai_courses/web/publish + file rác + bitrate MP3.
  3. Nội dung 8 khóa: mẫu câu, câu thông dụng, ngữ pháp, hội thoại, quiz,
     template cũ, đúng hệ chữ, IPA tiếng Anh, bảng chữ cái Nhật.
  4. Toàn vẹn media_map ↔ manifest.
  5. Online: verify_online, sw.js, mẫu 1 ngày/khóa.
  6. Test: test_web_contract.py + test_content_quality.py.
  7. Git: trạng thái VocabularyApp + commit gần nhất.
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from tools.enrich_course_content import _valid_target  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(BASE))  # Project1
WEB = os.path.join(BASE, "web", "data")
MEDIA = os.path.join(BASE, "data", "media")
AI = os.path.join(BASE, "data", "ai_courses")
LOGS = os.path.join(BASE, "data", "logs")
REPORT = os.path.join(BASE, "docs", "AUDIT_REPORT.md")
JSON_OUT = os.path.join(LOGS, "audit.json")
LANGS = ["tiếng_nhật", "tiếng_anh", "tiếng_hàn_quốc", "tiếng_nga",
         "tiếng_pháp", "tiếng_tây_ban_nha", "tiếng_đức", "tiếng_trung"]
TOTAL = 2520
FAILS, WARNS = [], []


def log(m: str) -> None:
    print(m, flush=True)


def size_dir(p: str):
    s = n = 0
    for dp, _d, fs in os.walk(p):
        for f in fs:
            try:
                s += os.path.getsize(os.path.join(dp, f))
                n += 1
            except OSError:
                pass
    return s, n


def add_fail(msg: str) -> None:
    FAILS.append(msg); log("FAIL " + msg)


def add_warn(msg: str) -> None:
    WARNS.append(msg); log("WARN " + msg)


def progress() -> dict:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import statefile  # noqa: E402

    fin = statefile.load("finalize_done.json")
    clean = statefile.load("cleanup_done_media.json")
    out = {}
    for slug in LANGS:
        p = os.path.join(MEDIA, slug)
        if os.path.isdir(p):
            days = sum(1 for d in os.listdir(p)
                       if os.path.isdir(os.path.join(p, d))
                       and os.listdir(os.path.join(p, d)))
        else:
            days = 0
        uploaded = bool((fin.get(slug) or {}).get("status") == "done" or slug in clean)
        out[slug] = {"days": days, "remaining": TOTAL - days,
                     "pct": round(days / TOTAL * 100, 2),
                     "uploaded": uploaded}
    return out


_MANIFEST_CACHE = None


def _manifest(include_overlay: bool = False) -> dict:
    """Đọc manifest một lần; overlay ref bù vào nếu cần."""
    global _MANIFEST_CACHE
    if _MANIFEST_CACHE is None:
        with open(os.path.join(MEDIA, "index.json"), encoding="utf-8") as f:
            _MANIFEST_CACHE = json.load(f)
    items = dict((_MANIFEST_CACHE.get("items") or {}))
    if include_overlay:
        ovp = os.path.join(MEDIA, "webmap_overlay.json")
        if os.path.isfile(ovp):
            try:
                with open(ovp, encoding="utf-8") as f:
                    ov = json.load(f)
                items.update(ov.get("items") or {})
            except Exception:
                pass
    return {"items": items}


def storage(full: bool = False) -> dict:
    man = _manifest(False)
    items = man.get("items") or {}
    # Dung lượng media theo manifest (nhanh; không walk 169k file trên F:).
    media_bytes = 0
    per_lang = collections.defaultdict(lambda: {"bytes": 0, "files": 0, "days": 0})
    ext = collections.defaultdict(lambda: [0, 0])
    for ref, e in items.items():
        if not isinstance(e, dict):
            continue
        b = int(e.get("bytes") or 0)
        media_bytes += b
        slug = e.get("lang") or ""
        if slug:
            per_lang[slug]["bytes"] += b
            per_lang[slug]["files"] += 1
        rel = e.get("rel_path") or ""
        ex = os.path.splitext(rel)[1].lower() or "(none)"
        ext[ex][0] += 1
        ext[ex][1] += b
    for slug in list(per_lang) + ["_cards"]:
        p = os.path.join(MEDIA, slug)
        if os.path.isdir(p):
            per_lang[slug]["days"] = sum(
                1 for d in os.listdir(p)
                if os.path.isdir(os.path.join(p, d)) and os.listdir(os.path.join(p, d)))
    if full:
        # Chế độ đầy đủ: walk file thật (chậm trên ổ F:).
        media_bytes, media_files = size_dir(MEDIA)
        ext = collections.defaultdict(lambda: [0, 0])
        for dp, _d, fs in os.walk(MEDIA):
            for f in fs:
                ex = os.path.splitext(f)[1].lower() or "(none)"
                try:
                    sz = os.path.getsize(os.path.join(dp, f))
                except OSError:
                    sz = 0
                ext[ex][0] += 1
                ext[ex][1] += sz
        for slug in list(per_lang) + ["_cards"]:
            p = os.path.join(MEDIA, slug)
            if os.path.isdir(p):
                b, n = size_dir(p)
                per_lang[slug]["bytes"] = b
                per_lang[slug]["files"] = n
    cats = {
        "data/media": {"bytes": media_bytes,
                       "files": sum(v["files"] for v in per_lang.values())},
    }
    cats["data/audio"] = dict(zip(("bytes", "files"),
                                  size_dir(os.path.join(BASE, "data", "audio"))))
    if full:
        cats["data/ai_courses"] = dict(zip(("bytes", "files"), size_dir(AI)))
    else:
        # Nhanh: chỉ course.json/.gz + file cấp 1; _pipeline bỏ qua.
        ab = an = 0
        for dp, _ds, fs in os.walk(AI):
            if os.path.basename(dp) == "_pipeline":
                _ds[:] = []
                continue
            for f in fs:
                if f.startswith("course.json") or f.endswith(".tmp"):
                    try:
                        ab += os.path.getsize(os.path.join(dp, f)); an += 1
                    except OSError:
                        pass
        cats["data/ai_courses"] = {"bytes": ab, "files": an,
                                   "note": "chưa gồm _pipeline (fast)"}
    for name, p in (("web/data", WEB), ("web", os.path.join(BASE, "web")),
                    ("publish", os.path.join(BASE, "publish"))):
        cats[name] = dict(zip(("bytes", "files"), size_dir(p)))
    # bitrate mẫu: chỉ đọc vài thư mục ngày đầu, không glob toàn bộ.
    bitrates = collections.Counter()
    try:
        from mutagen.mp3 import MP3
        mp3s = []
        for slug in ("tiếng_anh", "tiếng_hàn_quốc", "tiếng_tây_ban_nha"):
            for day in ("d0001", "d0500", "d1000"):
                p = os.path.join(MEDIA, slug, day)
                if os.path.isdir(p):
                    mp3s += [os.path.join(p, f) for f in sorted(os.listdir(p))
                             if f.endswith(".mp3")][:5]
        for p in mp3s[:200]:
            try:
                bitrates[MP3(p).info.bitrate // 1000] += 1
            except Exception:
                pass
    except Exception:
        pass
    junk = []
    for p in glob.glob(os.path.join(MEDIA, "index.json.tmp.*")):
        junk.append({"path": os.path.relpath(p, BASE), "bytes": os.path.getsize(p)})
    for p in glob.glob(os.path.join(tempfile.gettempdir(), "vocab_pages_*")):
        b, _n = size_dir(p)
        junk.append({"path": p, "bytes": b})
    for p in glob.glob(os.path.join(AI, "*", "course.json.tmp.*")):
        junk.append({"path": os.path.relpath(p, BASE), "bytes": os.path.getsize(p)})
    mp3 = ext.get(".mp3", [0, 0])
    avg_bps = 0
    if bitrates:
        total_n = sum(bitrates.values())
        avg_bps = sum(k * v for k, v in bitrates.items()) / total_n * 1000
    projected = int(mp3[1] * max(0.0, 1 - 32000 / avg_bps)) if avg_bps > 32000 else 0
    repo = {}
    try:
        sys.path.insert(0, os.path.join(BASE, "tools"))
        from gh_token import get_token
        tok = get_token()
        for r in ("ThaiBao1991/VocabularyData", "ThaiBao1991/Project1"):
            req = urllib.request.Request(
                f"https://api.github.com/repos/{r}",
                headers={"Authorization": f"Bearer {tok}",
                         "Accept": "application/vnd.github+json",
                         "User-Agent": "audit"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                j = json.load(resp)
            repo[r] = round(j.get("size", 0) / 1024 / 1024, 2)
    except Exception as e:
        repo["error"] = str(e)
    git = {}
    try:
        git["count"] = subprocess.run(
            ["git", "-C", REPO_ROOT, "count-objects", "-vH"],
            capture_output=True, text=True, timeout=60).stdout.strip()
        git["status"] = subprocess.run(
            ["git", "-C", REPO_ROOT, "status", "--porcelain", "--",
             "GravityCode/VocabularyApp"],
            capture_output=True, text=True, timeout=60).stdout.strip()
        git["last"] = subprocess.run(
            ["git", "-C", REPO_ROOT, "log", "--oneline", "-3"],
            capture_output=True, text=True, timeout=60).stdout.strip()
    except Exception as e:
        git["error"] = str(e)
    return {"categories": cats,
            "per_lang": {k: v for k, v in per_lang.items()},
            "ext": {k: {"files": v[0], "bytes": v[1]} for k, v in ext.items()},
            "bitrate_khz": dict(bitrates), "avg_bitrate_bps": round(avg_bps),
            "projected_32k_saving_bytes": projected,
            "junk": junk, "repo_gb": repo, "git": git,
            "fast": not full}


def content() -> dict:
    out = {}
    for slug in LANGS:
        d = os.path.join(WEB, slug, "day")
        rec = {"files": 0, "min": {"pat": 99, "com": 99, "gram": 99, "dia": 99,
                                   "qg": 99, "qc": 99},
               "low": collections.Counter(), "template": 0, "script_bad": 0,
               "ipa": 0, "vocab": 0, "alphabet1": 0, "alphabet2": 0}
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".json"):
                continue
            try:
                j = json.load(open(os.path.join(d, fn), encoding="utf-8"))
            except Exception:
                continue
            rec["files"] += 1
            p = len(j.get("sentence_patterns") or [])
            c = len(j.get("common_sentences") or [])
            g = len(j.get("grammar") or [])
            dl = len(j.get("dialogue") or [])
            q = j.get("quiz") or {}
            qg = len(q.get("grammar") or [])
            qc = len(q.get("common") or [])
            for k, v in (("pat", p), ("com", c), ("gram", g), ("dia", dl),
                         ("qg", qg), ("qc", qc)):
                rec["min"][k] = min(rec["min"][k], v)
            if p < 4: rec["low"]["pat<4"] += 1
            if c < 5: rec["low"]["com<5"] += 1
            if g < 2: rec["low"]["gram<2"] += 1
            if dl < 1: rec["low"]["dia<1"] += 1
            if qg < 3: rec["low"]["qg<3"] += 1
            if qc < 3: rec["low"]["qc<3"] += 1
            for x in j.get("dialogue") or []:
                txt = " ".join(str(t.get("line_target") or "") for t in (x.get("turns") or []))
                if "を 使います" in txt or "は 何ですか" in txt:
                    rec["template"] += 1
            for x in j.get("sentence_patterns") or []:
                if not _valid_target(slug, x.get("example_sentence")):
                    rec["script_bad"] += 1
            for x in j.get("common_sentences") or []:
                if not _valid_target(slug, x.get("sentence")):
                    rec["script_bad"] += 1
            for x in j.get("dialogue") or []:
                for t in x.get("turns") or []:
                    if not _valid_target(slug, t.get("line_target")):
                        rec["script_bad"] += 1
            for v in j.get("vocab") or []:
                rec["vocab"] += 1
                if str(v.get("ipa") or v.get("pronunciation") or "").strip():
                    rec["ipa"] += 1
            if fn == "0001.json":
                rec["alphabet1"] = len([r for r in ((j.get("alphabet") or {}).get("rows") or [])
                                        if r.get("kana")])
            if fn == "0002.json":
                rec["alphabet2"] = len([r for r in ((j.get("alphabet") or {}).get("rows") or [])
                                        if r.get("kana")])
        out[slug] = rec
    return out


def integrity() -> dict:
    m = _manifest(True)
    refs = {}
    for ref, e in (m.get("items") or {}).items():
        if not isinstance(e, dict):
            continue
        lang, day = e.get("lang"), e.get("day")
        if lang and day:
            refs.setdefault((lang, int(day)), set()).add(ref)
    missing = days_map = 0
    total_refs = 0
    examples = []
    for slug in LANGS:
        d = os.path.join(WEB, slug, "day")
        for fn in os.listdir(d):
            if not fn.endswith(".json"):
                continue
            j = json.load(open(os.path.join(d, fn), encoding="utf-8"))
            mm = j.get("media_map") or {}
            if not mm:
                continue
            days_map += 1
            day = int(j.get("day") or fn.split(".")[0])
            have = refs.get((slug, day), set())
            for ref in mm:
                total_refs += 1
                if ref not in have:
                    missing += 1
                    if len(examples) < 5:
                        examples.append((slug, day, ref))
    return {"manifest_items": len(m.get("items") or {}),
            "days_with_map": days_map, "refs": total_refs,
            "missing": missing, "examples": examples}


def online() -> dict:
    out = {}
    try:
        r = subprocess.run([sys.executable, "-X", "utf8", "tools/verify_online.py"],
                           cwd=BASE, capture_output=True, text=True, timeout=600)
        out["verify_rc"] = r.returncode
        out["verify_tail"] = (r.stdout or "").strip().splitlines()[-1:]
    except Exception as e:
        out["verify_error"] = str(e)
    try:
        sw = urllib.request.urlopen(
            "https://thaibao1991.github.io/Project1/sw.js?v=" + str(int(time.time())),
            timeout=30).read().decode("utf-8", "replace")
        mm = re.search(r'VERSION\s*=\s*"([^"]+)"', sw)
        out["sw"] = mm.group(1) if mm else "?"
    except Exception as e:
        out["sw_error"] = str(e)
    days = {}
    for slug in LANGS:
        try:
            u = ("https://thaibao1991.github.io/Project1/data/"
                 + urllib.parse.quote(slug)
                 + f"/day/2509.json?v={int(time.time())}")
            j = json.loads(urllib.request.urlopen(u, timeout=45)
                           .read().decode("utf-8", "replace"))
            days[slug] = {
                "pat": len(j.get("sentence_patterns") or []),
                "common": len(j.get("common_sentences") or []),
                "gram": len(j.get("grammar") or []),
                "turns": len(((j.get("dialogue") or [{}])[0].get("turns") or [])),
                "quiz": sum(len(v) for v in (j.get("quiz") or {}).values()
                            if isinstance(v, list)),
            }
        except Exception as e:
            days[slug] = {"error": str(e)}
    out["days"] = days
    return out


def tests() -> dict:
    out = {}
    for name in ("test_web_contract.py", "test_content_quality.py"):
        try:
            r = subprocess.run([sys.executable, "-X", "utf8", "tools/" + name],
                               cwd=BASE, capture_output=True, text=True, timeout=1800)
            out[name] = {"rc": r.returncode,
                         "tail": (r.stdout or "").strip().splitlines()[-1:]}
        except Exception as e:
            out[name] = {"error": str(e)}
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-online", action="store_true")
    ap.add_argument("--no-tests", action="store_true")
    ap.add_argument("--no-integrity", action="store_true")
    ap.add_argument("--full-storage", action="store_true",
                    help="walk toàn bộ media (chậm trên ổ F:)")
    args = ap.parse_args()
    t0 = time.time()
    if os.path.isfile(os.path.join(MEDIA, "index_full.json")):
        add_warn("manifest đang ở chế độ SHARD (index_full.json tồn tại) — "
                 "chạy `python -X utf8 tools/media_index_swap.py end` trước khi "
                 "audit/publish để thấy đủ entry của 8 khóa")
    prog = progress()
    store = storage(args.full_storage)
    cont = content()
    integ = {} if args.no_integrity else integrity()
    online_data = {} if args.no_online else online()
    test_data = {} if args.no_tests else tests()

    # đánh giá
    for slug, v in prog.items():
        if v["days"] < TOTAL and not v.get("uploaded"):
            add_warn(f"{slug}: mới {v['days']}/{TOTAL} ngày media")
    for slug, v in cont.items():
        if v["template"] or v["script_bad"]:
            add_fail(f"{slug}: template={v['template']} script_bad={v['script_bad']}")
        if any(k in v["low"] for k in ("pat<4", "com<5", "dia<1", "qg<3", "qc<3")):
            add_fail(f"{slug}: thiếu mục {dict(v['low'])}")
    if "missing" in integ and integ["missing"]:
        if integ["missing"] > 50:
            add_fail(f"media_map: {integ['missing']} ref không có trong manifest/overlay")
        else:
            add_warn(f"media_map: {integ['missing']} ref mới chưa kịp vào manifest (đang fill)")
    if store["projected_32k_saving_bytes"] > 200e6:
        add_warn("Audio có thể giảm thêm ~"
                 f"{store['projected_32k_saving_bytes']/1e9:.2f} GB nếu nén 32 kbps")
    junk = sum(x["bytes"] for x in store["junk"])
    if junk > 50e6:
        add_warn(f"File tạm/rác: {junk/1e9:.2f} GB có thể xoá")
    if online_data:
        if online_data.get("verify_rc") not in (0, None):
            add_fail("verify_online thất bại")
        for slug, d in (online_data.get("days") or {}).items():
            if "error" in d:
                add_warn(f"online {slug}: {d['error']}")
            elif d["pat"] < 4 or d["common"] < 5:
                add_warn(f"online {slug}: nội dung mẫu câu/câu thông dụng chưa đủ")
    for name, d in test_data.items():
        if d.get("rc") not in (0, None):
            add_fail(f"{name} FAIL")
    if store["git"].get("status"):
        add_warn("VocabularyApp còn file chưa commit")
    dt = time.time() - t0

    # JSON + Markdown
    data = {"at": f"{datetime.now():%Y-%m-%d %H:%M:%S}",
            "progress": prog, "storage": store, "content": cont,
            "integrity": integ, "online": online_data, "tests": test_data,
            "fails": FAILS, "warns": WARNS, "seconds": round(dt)}
    os.makedirs(LOGS, exist_ok=True)
    with open(JSON_OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    lines = [f"# Audit toàn bộ — {data['at']}", "",
             f"Thời gian chạy: **{dt:.0f}s** · FAIL: **{len(FAILS)}** · WARN: **{len(WARNS)}**",
             "", "## 1. Tiến độ media", "",
             "| Khóa | Ngày local | Còn | % | Uploaded |", "|---|---:|---:|---:|---|"]
    for slug, v in prog.items():
        lines.append(f"| {slug} | {v['days']}/{TOTAL} | {v['remaining']} | {v['pct']}% | "
                     f"{'✅' if v.get('uploaded') else '—'} |")
    lines += ["", "## 2. Dung lượng", "",
              "| Nhóm | GB | File |", "|---|---:|---:|"]
    for name, v in store["categories"].items():
        lines.append(f"| {name} | {v['bytes']/1e9:.2f} | {v['files']} |")
    for name, v in store["per_lang"].items():
        lines.append(f"| media/{name} | {v['bytes']/1e9:.2f} | {v['files']} |")
    if store.get("fast"):
        lines.append("")
        lines.append("- Ghi chú: dung lượng media lấy từ manifest (fast); "
                     "dùng `--full-storage` để walk toàn bộ file.")
    lines += ["", f"- MP3: {store['ext'].get('.mp3',{}).get('files',0)} file, "
              f"{store['ext'].get('.mp3',{}).get('bytes',0)/1e9:.2f} GB; "
              f"bitrate mẫu: {store['bitrate_khz']}",
              f"- Tiết kiệm dự kiến khi nén 32 kbps: **{store['projected_32k_saving_bytes']/1e9:.2f} GB**",
              f"- File tạm/rác: **{junk/1e9:.2f} GB**",
              f"- Repo GitHub: {store['repo_gb']}",
              "", "## 3. Nội dung", "",
              "| Khóa | Ngày | Mẫu câu | Câu thông dụng | Ngữ pháp | Hội thoại | Quiz G/C | Template | Script lỗi |",
              "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for slug, v in cont.items():
        lines.append(f"| {slug} | {v['files']} | {v['min']['pat']} | {v['min']['com']} | "
                     f"{v['min']['gram']} | {v['min']['dia']} | {v['min']['qg']}/{v['min']['qc']} | "
                     f"{v['template']} | {v['script_bad']} |")
    lines += ["", "## 4. Toàn vẹn media", "", f"```\n{json.dumps(integ, ensure_ascii=False)[:2000]}\n```",
              "", "## 5. Online", "", f"```\n{json.dumps(online_data, ensure_ascii=False)[:3000]}\n```",
              "", "## 6. Test", "", f"```\n{json.dumps(test_data, ensure_ascii=False)}\n```",
              "", "## 7. Git", "", f"```\n{store['git']}\n```",
              "", "## 8. Kết luận", ""]
    lines += [f"- FAIL: {x}" for x in FAILS] or ["- Không có FAIL."]
    lines += [f"- WARN: {x}" for x in WARNS] or ["- Không có WARN."]
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    log(f"\nBáo cáo: {REPORT}")
    log(f"JSON: {JSON_OUT}")
    log(f"FAIL={len(FAILS)} WARN={len(WARNS)} ({dt:.0f}s)")
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())
