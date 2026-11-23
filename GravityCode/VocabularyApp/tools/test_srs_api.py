# -*- coding: utf-8 -*-
"""tools/test_srs_api.py — Test API trang học: khóa học theo NGÀY + ôn tập SM-2.

Xem docs/UPGRADE_17.md mục 7.21 (Gói 3). 12 case, dùng Flask test client
(KHÔNG mở cổng thật, KHÔNG gọi mạng).

  1. GET  /api/vocab/course/<slug>/index   → danh sách ngày
  2. GET  /api/vocab/course/<slug>/day/<n>  → lesson đúng ngày
  3. GET  /api/vocab/srs/queue              → hàng đợi từ + thống kê
  4. POST /api/vocab/srs/review (good)      → state đổi, có lịch ôn tới
  5. POST /api/vocab/srs/review (bad grade) → 400
  6. Origin lạ (CSRF)                      → 403
  7. gzip cho JSON lớn                     → Content-Encoding: gzip
  8. review KHÔNG ghi vào khóa học khác     → file review tách riêng theo slug

Chạy: python tools/test_srs_api.py
"""
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from ai import course_db                      # noqa: E402
from ai.paths import canonical_slug           # noqa: E402
from ai.bridge_server import VocabBridge      # noqa: E402

LANG = "zz_srs_api_test"
PASS = [0]
FAIL = [0]


def ck(name, cond, detail=""):
    if cond:
        PASS[0] += 1
        print(f"[OK] {name}")
    else:
        FAIL[0] += 1
        print(f"[FAIL] {name} — {detail!r}")


def _course():
    return {
        "language": LANG,
        "days": [
            {"day": 1, "title": "Bài 1", "phase": "P", "level": "L", "topic": "T1",
             "vocab": [{"word": "猫", "meaning_vi": "mèo", "pronunciation": "neko",
                        "audio_ref": "m_a1", "image_ref": "m_i1"},
                       {"word": "犬", "meaning_vi": "chó", "pronunciation": "inu"}],
             "quiz": {"vocab": [{"question": "q", "options": ["a", "b"],
                                 "answer_index": 0, "explanation": "e"}]},
             "dialogue": []},
            {"day": 2, "title": "Bài 2", "phase": "P", "level": "L", "topic": "T2",
             "vocab": [{"word": "鳥", "meaning_vi": "chim"}],
             "quiz": {}, "dialogue": []},
        ],
    }


def main() -> int:
    course_db.delete_course(LANG)
    try:
        course_db.save_course(LANG, _course())
        br = VocabBridge()
        app = br._build_app()
        c = app.test_client()
        slug = canonical_slug(LANG)

        # 1. index khóa học
        r = c.get(f"/api/vocab/course/{slug}/index")
        j = r.get_json() or {}
        ck("index khóa học trả 2 ngày",
           r.status_code == 200 and j.get("total_days") == 2,
           (r.status_code, j.get("total_days")))
        ck("index có tiêu đề ngày",
           bool((j.get("days") or [{}])[0].get("title")), j.get("days"))

        # 2. lesson 1 ngày
        r = c.get(f"/api/vocab/course/{slug}/day/1")
        j = r.get_json() or {}
        ck("day/1 trả lesson đúng",
           r.status_code == 200 and len((j.get("lesson") or {}).get("vocab") or []) == 2,
           (r.status_code, j.get("lesson", {}).get("day")))
        r = c.get(f"/api/vocab/course/{slug}/day/99")
        ck("day không tồn tại → 404", r.status_code == 404, r.status_code)

        # 3. hàng đợi SRS
        r = c.get(f"/api/vocab/srs/queue?lang={slug}&limit=10")
        j = r.get_json() or {}
        items = j.get("items") or []
        ck("queue trả từ của khóa học", r.status_code == 200 and len(items) == 3,
           (r.status_code, len(items)))
        ck("item có nghĩa + audio_ref",
           bool(items) and items[0].get("meaning_vi") is not None,
           items[:1])
        ck("stats có số từ", int((j.get("stats") or {}).get("total") or 0) >= 3,
           j.get("stats"))

        # 4. review good
        r = c.post("/api/vocab/srs/review",
                   json={"lang": slug, "word": "猫", "grade": "good",
                         "correct": True})
        j = r.get_json() or {}
        ck("review good trả ok + lịch ôn tới",
           r.status_code == 200 and j.get("ok") and (j.get("info") or {}).get("due_iso"),
           (r.status_code, j))
        r2 = c.get(f"/api/vocab/srs/queue?lang={slug}&limit=10")
        j2 = r2.get_json() or {}
        after = [i for i in (j2.get("items") or []) if i.get("word") == "猫"]
        ck("từ đã ôn không còn 'new'",
           after and after[0].get("state") != "new",
           after[:1])

        # 5. grade sai → 400
        r = c.post("/api/vocab/srs/review",
                   json={"lang": slug, "word": "猫", "grade": "perfect"})
        ck("grade không hợp lệ → 400", r.status_code == 400, r.status_code)
        r = c.post("/api/vocab/srs/review", json={"lang": slug, "grade": "good"})
        ck("thiếu word → 400", r.status_code == 400, r.status_code)

        # 6. Origin lạ → 403 (CSRF)
        r = c.post("/api/vocab/srs/review",
                   json={"lang": slug, "word": "犬", "grade": "good"},
                   headers={"Origin": "https://evil.example.com"})
        ck("Origin lạ → 403", r.status_code == 403, r.status_code)
        r = c.get(f"/api/vocab/srs/queue?lang={slug}",
                  headers={"Origin": "https://evil.example.com"})
        ck("queue với Origin lạ → 403", r.status_code == 403, r.status_code)
        r = c.get(f"/api/vocab/srs/queue?lang={slug}",
                  headers={"Origin": f"http://127.0.0.1:{br.port}"})
        ck("Origin của chính trang học → 200", r.status_code == 200, r.status_code)

        # 7. gzip (cần payload > 1 KB)
        big = _course()
        big["days"].append({"day": 3, "title": "Bài 3", "phase": "P", "level": "L",
                            "topic": "T3",
                            "vocab": [{"word": f"w{i}", "meaning_vi": "nghĩa " * 12,
                                       "pronunciation": "pr"} for i in range(60)],
                            "quiz": {}, "dialogue": []})
        course_db.save_course(LANG, big)
        r = c.get(f"/api/vocab/course/{slug}/day/3",
                  headers={"Accept-Encoding": "gzip"})
        ck("JSON lớn được gzip",
           r.headers.get("Content-Encoding") == "gzip",
           r.headers.get("Content-Encoding"))

        # 8. file review tách theo slug (không lẫn khóa khác)
        from database import review_store as rs
        ck("file review dùng slug chuẩn",
           os.path.basename(rs.reviews_path(LANG)) == f"{slug}.json",
           rs.reviews_path(LANG))
        ck("không sinh file review cho slug khác",
           not os.path.exists(rs.reviews_path("zz_srs_api_other")),
           rs.reviews_path("zz_srs_api_other"))
    finally:
        course_db.delete_course(LANG)
        try:
            from database import review_store as rs
            p = rs.reviews_path(LANG)
            if os.path.exists(p):
                os.remove(p)
        except Exception:
            pass

    print(f"\nKết quả: {PASS[0]} PASS / {FAIL[0]} FAIL (tổng {PASS[0] + FAIL[0]})")
    return 1 if FAIL[0] else 0


if __name__ == "__main__":
    sys.exit(main())
