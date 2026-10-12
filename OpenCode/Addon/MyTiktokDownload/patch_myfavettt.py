#!/usr/bin/env python3
"""Rebuild myfaveTTT custom extension from true myfaveTT source + stop-on-error patch."""
import json
import shutil
import zipfile
from pathlib import Path

BASE = Path(r"C:\Users\games\Desktop\Project\Python\Python MyWork\Project1\OpenCode\Addon\MyTiktokDownload")
SRC = Path(r"C:\Users\games\Desktop\Project\Python\Python MyWork\Project1\OpenCode\Addon\myfaveTT_ext\extracted")
OUT = BASE / "custom_extension" / "unpacked"
PATCH_JS = (BASE / "ttt_patch.js").read_text(encoding="utf-8")
ORIG_ID = "gmajiifkcmjkehmngbopoobeplhoegad"
STOP_CHECK = "if(window.__tttStop){await(window.__tttWaitResume?window.__tttWaitResume():Promise.resolve())}"
fails = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (" " + detail if detail and not cond else ""))
    if not cond:
        fails.append(name)


def rep_once(text, old, new, name):
    c = text.count(old)
    check(name + " anchor x1", c == 1, "found=%d" % c)
    if c != 1:
        return text
    return text.replace(old, new, 1)


def rep_all(text, old, new, name, expect=None):
    c = text.count(old)
    ok = (c == expect) if expect is not None else (c >= 1)
    check(name + (" anchor x%d" % expect if expect is not None else " anchor>=1"), ok, "found=%d" % c)
    return text.replace(old, new)


# ---- 1. clean + copy true source ----
junk = ["background.js", "scripts", "_locales", "_metadata",
        "PAD-ico_32.png", "PAD-ico_48.png", "PAD-ico_56.png",
        "PAD-ico_64.png", "PAD-ico_128.png", "c.js", "style.css",
        "rl.html", "s.js", "r.js", "manifest.json", "icon-256.png"]
for j in junk:
    p = OUT / j
    if p.is_dir():
        shutil.rmtree(p)
    elif p.exists():
        p.unlink()
for f in ["b.js", "c.js", "s.js", "r.js", "rl.html", "style.css", "manifest.json", "icon-256.png"]:
    shutil.copy2(SRC / f, OUT / f)
print("copied true source (8 files, no scripts/ needed)")

# ---- 2. manifest (no key/update_url, single action) ----
manifest = {
    "name": "myfaveTTT Custom (Stop on Error)",
    "version": "1.12.70.1",
    "description": "myfaveTT with stop-on-error + failing-video link (custom copy)",
    "manifest_version": 3,
    "action": {"default_title": "myfaveTTT"},
    "background": {"service_worker": "b.js"},
    "content_scripts": [{"matches": ["https://www.tiktok.com/*"], "js": ["c.js"], "css": ["style.css"]}],
    "web_accessible_resources": [{"matches": ["https://www.tiktok.com/*"], "resources": ["rl.html", "s.js"]}],
    "icons": {"256": "icon-256.png"},
    "permissions": ["webRequest"],
    "host_permissions": ["https://*.tiktok.com/api/post/item_list/"],
}
(OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
check("manifest written", True)

# ---- 3. b.js / r.js channel rename ----
b = (OUT / "b.js").read_text(encoding="utf-8")
b = rep_all(b, "BroadcastChannel(`myfaveTT`)", "BroadcastChannel(`myfaveTTT`)", "b.js channel", 1)
(OUT / "b.js").write_text(b, encoding="utf-8")

r = (OUT / "r.js").read_text(encoding="utf-8")
r = rep_all(r, "BroadcastChannel(`myfaveTT`)", "BroadcastChannel(`myfaveTTT`)", "r.js channel", 1)
(OUT / "r.js").write_text(r, encoding="utf-8")

# ---- 4. c.js renames ----
c = (OUT / "c.js").read_text(encoding="utf-8")
c = c.replace("myfaveTT-container", "myfaveTTT-container")
c = c.replace("pushed-by-myfaveTT", "pushed-by-myfaveTTT")
c = c.replace("t.id=`myfaveTT`", "t.id=`myfaveTTT`")
c = c.replace("t.name=`sidebar`", "t.name=`sidebarTTT`")
check("c.js renamed", "myfaveTT" not in c.replace("myfaveTTT", ""))
(OUT / "c.js").write_text(c, encoding="utf-8")

# ---- 5. style.css renames ----
css = (OUT / "style.css").read_text(encoding="utf-8")
css = css.replace("myfaveTT", "myfaveTTT")
check("style.css renamed", "myfaveTT" not in css.replace("myfaveTTT", ""))
(OUT / "style.css").write_text(css, encoding="utf-8")

# ---- 6. s.js patches ----
s = (OUT / "s.js").read_text(encoding="utf-8")
check("s.js is true module (~72k)", len(s) > 50000, "len=%d" % len(s))

s = rep_all(s, "new BroadcastChannel(`myfaveTT`)", "new BroadcastChannel(`myfaveTTT`)", "s.js channel", 1)
s = rep_all(s, "aside#myfaveTT-container", "aside#myfaveTTT-container", "s.js aside", 1)
s = rep_all(
    s,
    "function i(e,t){sidebar.postMessage({direction:2,type:e,payload:t},n.ce)}",
    "function i(e,t){(document.getElementById(\"myfaveTTT\")||{contentWindow:window}).contentWindow.postMessage({direction:2,type:e,payload:t},\"*\")}",
    "s.js post dir2",
    1,
)
s = rep_all(
    s,
    "function o(e,t){sidebar.postMessage({direction:6,type:e,payload:t},n.ce)}",
    "function o(e,t){(document.getElementById(\"myfaveTTT\")||{contentWindow:window}).contentWindow.postMessage({direction:6,type:e,payload:t},\"*\")}",
    "s.js post dir6",
    1,
)
s = rep_all(s, "if(t!==n.ce)return;", "if(!/^(https:\\/\\/(www\\.tiktok\\.com|myfavett-ui\\.vercel\\.app|resync\\.myfavett\\.com)|chrome-extension:\\/\\/)/.test(t))return;", "s.js Yi origin filter", 1)
s = rep_all(s, "ce:`chrome-extension://" + ORIG_ID + "`", 'ce:"*"', "s.js ce literal", 1)
s = rep_all(s, "https://chrome.google.com/webstore/detail/myfavett/" + ORIG_ID, "chrome://extensions/", "s.js webstore link", 1)
s = rep_all(s, "getElementById(`myfaveTT-container`)", 'getElementById("myfaveTTT-container")', "s.js close-app container", 1)
s = rep_all(s, "classList.remove(`pushed-by-myfaveTT`)", 'classList.remove("pushed-by-myfaveTTT")', "s.js close-app class", 1)

# X(): track current video
s = rep_once(
    s,
    "async X(){if(n.Re){this.#e();return}",
    "async X(){try{window.__tttCurrent={id:this.d.id,author:(this.d.author||{}).uniqueId||\"\",authorId:(this.d.author||{}).id||\"\",type:this.N,itemData:this.d}}catch(_){}if(n.Re){this.#e();return}",
    "s.js X track",
)

# h(): hook error overlay
s = rep_once(
    s,
    "function h(e,t,r){r?he(e,t,r):(me(e,t,r),k.se(`because of error @ ${t}`),n.P||c.Z())}",
    "function h(e,t,r){r?he(e,t,r):(me(e,t,r),k.se(`because of error @ ${t}`),n.P||c.Z());try{window.__tttOnErr&&window.__tttOnErr(t,e&&e.message||String(e))}catch(_){}}",
    "s.js h hook",
)

# driver loops: stop checks
s = rep_once(
    s,
    "for await(let t of Mr()){if(!U(t))continue;let n=new cr(t,",
    "for await(let t of Mr()){" + STOP_CHECK + "if(!U(t))continue;let n=new cr(t,",
    "s.js loop bookmarked",
)
s = rep_once(
    s,
    "for await(let n of Ei()){if(!U(n))continue;let r=new cr(n,",
    "for await(let n of Ei()){" + STOP_CHECK + "if(!U(n))continue;let r=new cr(n,",
    "s.js loop likes",
)
s = rep_once(
    s,
    "for(let[r,a]of n.entries()){if(k.s(t,`download videos from one author (old way)`))return;if(!U(a))continue;let o=new cr(a,",
    "for(let[r,a]of n.entries()){if(k.s(t,`download videos from one author (old way)`))return;if(!U(a))continue;" + STOP_CHECK + "let o=new cr(a,",
    "s.js loop following-old",
)
s = rep_once(
    s,
    "if(k.s(t,`download mp4 from one author`))return;if(!U(n))continue;let r=new cr(n,",
    "if(k.s(t,`download mp4 from one author`))return;if(!U(n))continue;" + STOP_CHECK + "let r=new cr(n,",
    "s.js loop following-new",
)

leftover = s.replace("myfaveTTT", "").replace(ORIG_ID, "")
leftover = leftover.replace("Le(`myfaveTT`", "").replace("folder:`myfaveTT`", "")
check("s.js no stray orig ids", ("myfaveTT" not in leftover) and (ORIG_ID not in s), "leftovers present" if ("myfaveTT" in leftover or ORIG_ID in s) else "")

s = s + "\n" + PATCH_JS
(OUT / "s.js").write_text(s, encoding="utf-8")
check("s.js patched+appended", "__tttOnErr" in s and "__tttPatched" in s)

# ---- 7. rebuild zip & mirror to myfaveTTT-custom ----
zip_path = BASE / "custom_extension" / "myfaveTTT-custom.zip"
import zipfile as _zf
if zip_path.exists():
    zip_path.unlink()
with _zf.ZipFile(zip_path, "w", _zf.ZIP_DEFLATED) as zf:
    for fp in sorted(OUT.rglob("*")):
        if fp.is_file():
            zf.write(fp, fp.relative_to(OUT))
check("zip built", zip_path.exists(), "size=%d" % (zip_path.stat().st_size if zip_path.exists() else 0))

# Mirror to myfaveTTT-custom
mirror_dir = BASE / "custom_extension" / "myfaveTTT-custom"
if mirror_dir.exists():
    shutil.rmtree(mirror_dir)
shutil.copytree(OUT, mirror_dir)
check("mirror built", mirror_dir.exists())

print("FAILURES:", fails if fails else "none")
