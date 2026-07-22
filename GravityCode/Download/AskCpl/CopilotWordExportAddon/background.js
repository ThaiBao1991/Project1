// ============================================================
// background.js — Service Worker (Giai đoạn 16)
// THAY ĐỔI:
//   [DEBUG] dataUriDownload: log kết quả (OK / FAILED) về popup log area
//           → Người dùng thấy lỗi download ngay trong popup, không cần mở SW console
//   [KEEP]  base64 data URI thay createObjectURL (không hoạt động trong SW MV3)
//   [KEEP]  Stagger: index sau 2s, session sau 4s (tránh Download Manager ứ)
// ============================================================

// ── CSS dùng chung ────────────────────────────────────────────
const DAY_CSS = `
body { font-family: 'Segoe UI', Arial, sans-serif; max-width: 860px; margin: 40px auto; padding: 0 20px; background: #f9f9f9; color: #1a1a1a; }
header { background: #0078d4; color: #fff; padding: 16px 24px; border-radius: 8px; margin-bottom: 24px; }
header h1 { margin: 0; font-size: 1.4em; }
header p { margin: 4px 0 0; font-size: 0.85em; opacity: 0.85; }
.content { background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 24px; line-height: 1.7; }
a.back { display: inline-block; margin-top: 20px; color: #0078d4; text-decoration: none; font-size: 0.9em; }
a.back:hover { text-decoration: underline; }
h2, h3 { color: #005a9e; }
code { background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }
pre { background: #f0f0f0; padding: 12px; border-radius: 6px; overflow-x: auto; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: left; }
th { background: #0078d4; color: #fff; }
tr:nth-child(even) { background: #f5f5f5; }
`.trim();

const INDEX_CSS = `
body { font-family: 'Segoe UI', Arial, sans-serif; max-width: 700px; margin: 40px auto; padding: 0 20px; background: #f9f9f9; color: #1a1a1a; }
header { background: #0078d4; color: #fff; padding: 20px 28px; border-radius: 10px; margin-bottom: 28px; }
header h1 { margin: 0; font-size: 1.6em; }
header p { margin: 6px 0 0; opacity: 0.88; font-size: 0.9em; }
table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
th { background: #0078d4; color: #fff; padding: 12px 16px; text-align: left; }
td { padding: 10px 16px; border-bottom: 1px solid #eee; }
td a { color: #0078d4; text-decoration: none; font-weight: 500; }
td a:hover { text-decoration: underline; }
tr:last-child td { border-bottom: none; }
tr:hover td { background: #f0f6ff; }
.stats { margin-top: 20px; font-size: 0.9em; color: #555; text-align: right; }
.badge { display: inline-block; background: #0078d4; color: #fff; border-radius: 12px; padding: 2px 10px; font-size: 0.8em; margin-left: 8px; }
`.trim();

// ── Escape HTML ───────────────────────────────────────────────
function esc(str) {
    if (!str) return '';
    return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ── Nav Bar (nhúng sẵn, tự nhận biết Day từ tên file) ────────
function getNavBarScript(totalDays) {
    return `<!-- NAV-BAR-V2 -->
<style>
#askcpl-nav{position:fixed;top:0;left:0;right:0;z-index:9999;display:flex;align-items:center;justify-content:space-between;background:linear-gradient(135deg,#0f0c29,#302b63,#24243e);color:#fff;padding:8px 16px;box-shadow:0 2px 12px rgba(0,0,0,.5);font-family:'Segoe UI',Arial,sans-serif;font-size:14px;box-sizing:border-box;height:48px;}
#askcpl-nav button{background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.3);color:#fff;padding:6px 14px;border-radius:6px;cursor:pointer;font-size:15px;transition:background .2s;flex-shrink:0;}
#askcpl-nav button:hover:not([disabled]){background:rgba(255,255,255,.3);}
#askcpl-nav button[disabled]{opacity:.3;cursor:default;}
#askcpl-nav-title{flex:1;text-align:center;cursor:pointer;padding:4px 12px;border-radius:6px;transition:background .2s;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-weight:600;color:#e0d0ff;}
#askcpl-nav-title:hover{background:rgba(255,255,255,.15);}
#askcpl-nav-home{background:rgba(46,160,67,0.3);text-decoration:none;border:1px solid rgba(46,160,67,0.5);color:#fff;padding:6px 12px;border-radius:6px;font-size:14px;transition:background .2s;display:flex;align-items:center;}
#askcpl-nav-home:hover{background:rgba(46,160,67,0.5);}
#askcpl-toc{display:none;position:fixed;top:52px;left:50%;transform:translateX(-50%);background:#1e1e2e;border:1px solid rgba(167,139,250,.3);border-radius:10px;padding:8px 4px;min-width:320px;max-height:400px;overflow-y:auto;z-index:9998;box-shadow:0 8px 32px rgba(0,0,0,.7);}
#askcpl-toc a{display:block;padding:7px 16px;color:#a0a0c0;text-decoration:none;border-radius:6px;margin:1px 4px;font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
#askcpl-toc a:hover{background:rgba(167,139,250,.15);color:#e0d0ff;}
#askcpl-toc a.cur{background:linear-gradient(90deg,#7c3aed,#4f46e5)!important;color:#fff!important;font-weight:bold;}
body{padding-top:52px!important;}
</style>
<div id="askcpl-nav">
  <button id="nav-prev" onclick="askcplNav(-1)">&#9664; Prev</button>
  <a id="askcpl-nav-home" href="index.html" title="Quay lại Menu Tổng">🏠 Menu</a>
  <span id="askcpl-nav-title" onclick="askcplToggleToc()" title="Click xem Muc Luc">Day ... &#9660;</span>
  <button id="nav-next" onclick="askcplNav(1)">Next &#9654;</button>
</div>
<div id="askcpl-toc"></div>
<script>
(function(){
  var MAX_DAYS = ${totalDays};
  // Tu doc so Day tu URL hien tai
  var m = window.location.pathname.match(/day_(\\d+)\\.html/i)
       || window.location.href.match(/day_(\\d+)\\.html/i);
  var cur = m ? parseInt(m[1]) : 0;
  if(!cur) return;

  // Cap nhat title
  document.getElementById('askcpl-nav-title').textContent = 'Day ' + cur + ' \u25bc';
  
  // Cap nhat link nut Home
  document.getElementById('askcpl-nav-home').href = 'index.html#day-' + cur;

  // Prev/Next
  if(cur <= 1) document.getElementById('nav-prev').disabled = true;
  if(cur >= MAX_DAYS) document.getElementById('nav-next').disabled = true;
  
  window.askcplNav = function(d){
    var n = cur + d;
    if(n < 1 || n > MAX_DAYS) return;
    window.location.href = 'day_' + n + '.html';
  };

  // TOC: tu tao danh sach +-10 ngay (capped tai MAX_DAYS)
  var toc = document.getElementById('askcpl-toc');
  window.askcplToggleToc = function(){
    if(toc.style.display === 'block'){ toc.style.display='none'; return; }
    if(!toc.innerHTML){
      var html = '';
      var lo = Math.max(1, cur-10), hi = Math.min(MAX_DAYS, cur+10);
      for(var i=lo; i<=hi; i++){
        var cls = (i===cur) ? 'cur' : '';
        var mark = (i===cur) ? ' \u2190 Hom nay' : '';
        html += '<a class="'+cls+'" href="day_'+i+'.html">Day '+i+mark+'</a>';
      }
      toc.innerHTML = html;
    }
    toc.style.display = 'block';
    var c = toc.querySelector('.cur');
    if(c) c.scrollIntoView({block:'center'});
  };

  document.addEventListener('click', function(e){
    var nav=document.getElementById('askcpl-nav');
    if(!nav.contains(e.target) && !toc.contains(e.target)){
      toc.style.display='none';
    }
  });
  document.addEventListener('keydown', function(e){
    if(e.target.tagName==='INPUT'||e.target.tagName==='TEXTAREA') return;
    if(e.key==='ArrowLeft') askcplNav(-1);
    if(e.key==='ArrowRight') askcplNav(1);
    if(e.key==='Escape') toc.style.display='none';
  });
})();
</script>
<!-- END-NAV-BAR-V2 -->`;
}

// ── Build HTML 1 ngày học ─────────────────────────────────────
function buildDayHtml(rawContent, dayLabel, agentName, timestamp, totalDays) {
    return `<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${esc(dayLabel)} — ${esc(agentName)}</title>
  <style>${DAY_CSS}</style>
</head>
<body>
  <header>
    <h1>${esc(dayLabel)}</h1>
    <p>Agent: ${esc(agentName)} &nbsp;|&nbsp; Lưu lúc: ${esc(timestamp)}</p>
  </header>
  <div class="content">${rawContent}</div>
  <a class="back" href="index.html">← Quay lại danh sách</a>
${getNavBarScript(totalDays || 9999)}
</body>
</html>`;
}

// ── Build index.html ──────────────────────────────────────────
function buildIndexHtml(agentName, folderName, days, timestamp) {
    const rows = (days || []).map(item => {
      const dayNum = String(item.day).replace(/[^0-9]/g, '');
      return `
      <tr id="day-${dayNum}">
        <td><a href="${esc(item.filename.split('/').pop())}" target="_blank">${esc(item.day)}</a></td>
        <td>${item.timestamp ? new Date(item.timestamp).toLocaleString('vi-VN') : ''}</td>
      </tr>`;
    }).join('');

    return `<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${esc(agentName)} — Tổng hợp khóa học</title>
  <style>${INDEX_CSS}</style>
</head>
<body>
  <header>
    <h1>&#128218; ${esc(agentName)}</h1>
    <p>Tổng số bài: <strong>${days.length}</strong> &nbsp;|&nbsp; Cập nhật: ${esc(timestamp)}</p>
  </header>
  <table>
    <thead><tr><th>Bài học</th><th>Thời gian lưu</th></tr></thead>
    <tbody>${rows}</tbody>
  </table>
  <p class="stats">Folder: <code>${esc(folderName)}/</code> <span class="badge">${days.length} bài</span></p>
</body>
</html>`;
}

// ── Xử lý lỗi Edge/Firefox lờ đi thư mục khi dùng data: URI ──────────
const pendingDownloads = new Map();

chrome.downloads.onDeterminingFilename.addListener((item, suggest) => {
    if (pendingDownloads.has(item.url)) {
        const fileInfo = pendingDownloads.get(item.url);
        suggest({ filename: fileInfo.filename, conflictAction: fileInfo.conflictAction || "overwrite" });
        pendingDownloads.delete(item.url);
        return true; // Bắt buộc nếu muốn ghi đè
    }
});

// ── dataUriDownload — base64 data URI ─────────────────────────
// Lý do dùng base64 thay Blob:
//   URL.createObjectURL() KHÔNG tồn tại trong Service Worker MV3
//   → Silent fail, download không có gì xảy ra
// base64 data URI hoạt động 100% trong SW.
//
// [DEBUG] Giai đoạn 16: Log kết quả (OK/FAILED) về popup log area
//         Người dùng thấy lỗi ngay mà không cần mở SW console
function dataUriDownload(content, mimeType, filename, conflictAction = "overwrite") {
    // UTF-8 → Uint8Array → binary string (chunk 8192) → btoa
    const bytes = new TextEncoder().encode(content);
    let binary = '';
    const CHUNK = 8192;
    for (let i = 0; i < bytes.length; i += CHUNK) {
        binary += String.fromCharCode.apply(null, bytes.subarray(i, i + CHUNK));
    }
    const base64  = btoa(binary);
    const dataUri = `data:${mimeType};base64,${base64}`;

    console.debug(`[BG] Downloading: ${filename} (${bytes.length} bytes → ${base64.length} base64 chars)`);

    // Lưu tạm vào Map để onDeterminingFilename có thể ép trình duyệt dùng đúng tên file và folder
    pendingDownloads.set(dataUri, { filename, conflictAction });

    chrome.downloads.download(
        { url: dataUri, filename, saveAs: false, conflictAction },
        (downloadId) => {
            if (chrome.runtime.lastError) {
                const errMsg = chrome.runtime.lastError.message;
                console.error("[BG] FAILED:", errMsg, "->", filename);
                pendingDownloads.delete(dataUri); // Xóa khỏi bộ nhớ nếu lỗi
                // [DEBUG] Gửi lỗi về popup log area để user thấy
                chrome.runtime.sendMessage({
                    action: "add_log",
                    text: `❌ Download FAILED: ${filename}\n   Lỗi: ${errMsg}`
                }).catch(() => {});
            } else {
                console.debug("[BG] OK, ID:", downloadId, "->", filename);
                // Dọn rác bộ nhớ dự phòng trường hợp sự kiện bị nghẽn
                setTimeout(() => pendingDownloads.delete(dataUri), 10000);
                // [DEBUG] Xác nhận OK về popup
                chrome.runtime.sendMessage({
                    action: "add_log",
                    text: `✅ Download OK: ${filename} (ID: ${downloadId})`
                }).catch(() => {});
            }
        }
    );
}

// ── Message Listener ──────────────────────────────────────────
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {

    // ── Khắc phục lỗi Auto-Resume sai Tab: Trả về ID của Tab gọi lệnh ──
    if (request.action === "get_tab_id") {
        sendResponse({ tabId: sender.tab ? sender.tab.id : null });
        return true;
    }

    // ── Ping để giữ Service Worker (MV3) không ngủ ───────────────────
    if (request.action === "ping") {
        sendResponse({ status: "pong" });
        return true;
    }

    // ── Tải file HTML của 1 ngày học ──────────────────────────
    if (request.action === "download_html") {
        const fullHtml = buildDayHtml(
            request.rawContent,
            request.dayLabel,
            request.agentName,
            request.timestamp,
            request.totalDays
        );
        dataUriDownload(fullHtml, "text/html;charset=utf-8", request.filename);
        sendResponse({ status: "downloading_html" });
    }

    // ── Cập nhật index.html — stagger 2s ──────────────────────
    else if (request.action === "download_index") {
        setTimeout(() => {
            const html = buildIndexHtml(
                request.agentName,
                request.folderName,
                request.days || [],
                request.timestamp
            );
            dataUriDownload(html, "text/html;charset=utf-8", request.filename);
        }, 2000);
        sendResponse({ status: "queued_index" });
    }

    // ── Cập nhật session.json — stagger 4s ────────────────────
    else if (request.action === "download_session") {
        setTimeout(() => {
            dataUriDownload(request.data, "application/json;charset=utf-8", request.filename);
        }, 4000);
        sendResponse({ status: "queued_session" });
    }

    // ── [Legacy] Nút Recover ──────────────────────────────────
    else if (request.action === "download_json") {
        dataUriDownload(request.data, "application/json", request.filename, "uniquify");
        sendResponse({ status: "downloading" });
    }

    return true;
});
