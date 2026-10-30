# tools/test_adaptive_model.py — Unit test cho logic probe/adaptive model (api/gemini_safe.py).
# KHONG goi API thuc. Chay: python tools/test_adaptive_model.py
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import api.gemini_safe as gs  # noqa: E402


def make_coord(models):
    c = gs.GeminiCoordinator(models=models, log_fn=lambda m: None, key_loader=lambda: [])
    return c


PASSED = []


def ok(name):
    PASSED.append(name)
    print("[OK] " + name)


# 1. _model_score: chua probe -> 0; co ket qua -> diem phu hop
c = make_coord(["m-a", "m-b"])
assert c._model_score("m-a") == 0.0, c._model_score("m-a")
c._record_model_result("m-a", True, 400)
c._record_model_result("m-a", True, 600)
c._record_model_result("m-a", False)
sc = c._model_score("m-a")
# rate=2/3*1000=666.7 - avg_ms 500/10=50 - consec_fail 1*100=100 => 516.7
assert 500 < sc < 530, sc
ok("_model_score: chua probe=0; co ket qua tinh dung rate/latency/consec_fail")

# consec_fail day diem xuong
c._record_model_result("m-a", False)
c._record_model_result("m-a", False)
sc2 = c._model_score("m-a")
assert sc2 < sc, (sc2, sc)
ok("_model_score: fail lien tiep giam diem (consec_fail)")

# 2. _record_model_result: dem ok/fail/latency/chuyen vao probe_done
c2 = make_coord(["x"])
c2._record_model_result("x", True, 100)
c2._record_model_result("x", True, 200)
c2._record_model_result("x", False)
s = c2._model_stats["x"]
assert s["ok"] == 2 and s["fail"] == 1 and s["count"] == 3 and s["total_ms"] == 300, s
assert "x" in c2._probe_done
ok("_record_model_result: ok/fail/count/total_ms/probe_done dung")

# 3. get_model_ranking: tot nhat dau, chua probe ve cuoi
c3 = make_coord(["slow-ok", "fast-ok", "untested"])
c3._record_model_result("slow-ok", True, 2000)   # rate 1, avg 2000 -> 1000-200=800
c3._record_model_result("fast-ok", True, 300)    # rate 1, avg 300  -> 1000-30=970
c3._record_model_result("untested", False)
rank = c3.get_model_ranking()
assert rank[0] == "fast-ok", rank
assert rank[1] == "slow-ok", rank
assert rank[2] == "untested", rank
ok("get_model_ranking: tot nhat dau, chua probe ve cuoi")

# 4. _adaptive_model_order: exploitation + exploration (choc model moi)
c4 = make_coord(["best", "ok2", "new1", "new2"])
c4._record_model_result("best", True, 100)
c4._record_model_result("ok2", True, 500)
orders = []
for i in range(12):
    orders.append(c4._adaptive_model_order())
challenger_seen = any(o[2] in ("new1", "new2") for o in orders[5:])
assert challenger_seen, orders
ok("_adaptive_model_order: moi 6 lan choc 1 model chua probe len vi tri cao (exploration)")
assert orders[0][0] == "best", orders[0]
ok("_adaptive_model_order: exploitation — model tot nhat (best) dung dau")

# 5. Tat adaptive -> tra nguyen self._models (khong sort)
c5 = make_coord(["a", "b", "c"])
c5._adaptive = False
assert c5._adaptive_model_order() == ["a", "b", "c"]
ok("adaptive=False -> nguyen thu tu self._models")

print("\nKet qua: %d/5 PASS" % len(PASSED))
if len(PASSED) < 5:
    sys.exit(1)

print("\nLuu ý: stats da duoc gui vao settings.json (ai.model_probe_stats) do _stats_pending.")
