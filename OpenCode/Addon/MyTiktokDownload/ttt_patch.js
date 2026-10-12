/* ===== MYFAVETTT STOP-ON-ERROR & PYTHON QUEUE PATCH ===== */
(function(){
if(window.__tttPatched) return;
window.__tttPatched = true;

window.__tttStop = false;
window.__tttIsDownloading = false;  // TRUE khi đang tải, dùng để hiện nút Dừng/Tiếp
window.__tttCurrent = null;
window.__tttLastKey = "";
window.__tttLog = [];
window.__tttFetchLog = [];  // Riêng cho batch/fetch errors (Mar695, etc.)
window.__tttWaiters = [];

// Dừng tải an toàn: set cờ và chờ video hiện tại hoàn tất
window.__tttPauseDownload = function(){
  window.__tttStop = true;
  window.__tttIsDownloading = false;
  __renderMiniBadge();
  __tttShowToast("PAUSED", "⏸️ Đã dừng tải sau video hiện tại. Bấm ▶️ Tiếp tục để tiếp.");
};

// Tiếp tục tải: giải phóng waiters
window.__tttResumeDownload = function(){
  window.__tttIsDownloading = true;
  __tttResumeAll();
  __renderMiniBadge();
  __tttShowToast("RESUMED", "▶️ Đã tiếp tục tải.");
};

// Load settings & queue from localStorage
window.__tttAutoSkip = localStorage.getItem('ttt_auto_skip') !== 'false'; // Mặc định luôn BẬT

function __tttLoadQueue(){
  try {
    var raw = localStorage.getItem('ttt_failed_queue');
    return raw ? JSON.parse(raw) : [];
  } catch(e) {
    return [];
  }
}
window.__tttFailedQueue = __tttLoadQueue();

// Nhận diện phân loại chính xác video TikTok Shop, Private hay Lỗi link
function __detectVideoType(item){
  if(!item) return { type: "UNKNOWN", label: "❌ LỖI TẢI", isShop: false, reason: "Không có thông tin video" };
  var isShop = false;
  
  // 1. Kiểm tra anchors (giỏ hàng sản phẩm)
  if(item.anchors && item.anchors.length > 0){
    for(var i = 0; i < item.anchors.length; i++){
      var a = item.anchors[i];
      if(a.type === 3 || a.type === 28 || a.keyword === "TikTok Shop" || (a.name && /shop|product|giỏ|sản phẩm/i.test(a.name)) || (a.description && /shop/i.test(a.description))){
        isShop = true; break;
      }
    }
  }
  
  // 2. Kiểm tra commerce flags
  if(item.hasCommerceModel || item.commerceInfo || item.isCommerce || item.cart_info || item.commerce_info){
    isShop = true;
  }
  
  // 3. Kiểm tra hashtag / caption liên quan đến shop
  var desc = String(item.desc || item.title || "");
  if(/#tiktokshop|tiktok shop|giỏ hàng|mua ngay|freeship|san pham|sản phẩm/i.test(desc)){
    isShop = true;
  }
  
  // 4. Nếu video không xem được trên web do hạn chế e-commerce
  if(isShop){
    return {
      type: "TIKTOK_SHOP",
      label: "🛍️ TIKTOK SHOP",
      isShop: true,
      reason: "Video gắn giỏ hàng TikTok Shop - Web bị hạn chế (App điện thoại vẫn xem được)"
    };
  }
  
  if(item.privateItem){
    return {
      type: "PRIVATE",
      label: "🔒 RIÊNG TƯ",
      isShop: false,
      reason: "Video đặt chế độ riêng tư"
    };
  }
  
  return {
    type: "WEB_BLOCKED",
    label: "❌ LỖI WEB",
    isShop: false,
    reason: "TikTok Web không cấp link mp4 hoặc video đã bị gỡ"
  };
}
window.__detectVideoType = __detectVideoType;


// Ghi nhận video lỗi vào Python Queue với đầy đủ URL có thể click kiểm tra
window.__tttRecordFailedVideo = function(item, code, msg){
  try {
    if(!item || !item.id) return;
    var vidId = String(item.id);

    // BỘ LỌC CHẶN: Tuyệt đối không gom video đã tải xong
    if(typeof O !== 'undefined' && O && O.e){
      var bDL = (O.e.bookmarked && O.e.bookmarked.downloaded);
      var lDL = (O.e.likes && O.e.likes.downloaded);
      if(bDL && bDL.has && bDL.has(vidId)) return;
      if(lDL && lDL.has && lDL.has(vidId)) return;
    }

    var author = (item.author && (item.author.uniqueId || item.author.id)) || (item.authorId) || "";
    var authorId = (item.author && item.author.id) || (item.authorId) || "";
    var title = item.desc || item.title || "";
    var cover = (item.video && (item.video.cover || item.video.coverUrl)) || item.cover || "";
    var cat = item.type === "liked" ? "l" : (item.type === "following" ? "following" : "b");
    var url = "https://www.tiktok.com/@" + (author || "user") + "/video/" + vidId;
    
    // Kiểm tra trùng lặp trong queue
    var existingIdx = -1;
    for(var i = 0; i < window.__tttFailedQueue.length; i++){
      if(window.__tttFailedQueue[i].id === vidId){
        existingIdx = i;
        break;
      }
    }
    
    var detected = __detectVideoType(item);
    var queueItem = {
      id: vidId,
      url: url,
      author: author,
      authorId: authorId,
      category: cat,
      title: title,
      cover: cover,
      errorCode: detected.type,
      errorLabel: detected.label,
      isShop: detected.isShop,
      errorMessage: detected.reason,
      failedAt: new Date().toISOString()
    };
    
    if(existingIdx >= 0){
      window.__tttFailedQueue[existingIdx] = queueItem;
    } else {
      window.__tttFailedQueue.push(queueItem);
    }
    
    __tttSaveQueue();
    __renderMiniBadge();
    
    // Hiện Toast thông báo có video lỗi kèm link
    if(window.__tttAutoSkip){
      __tttShowToast(code || "SKIP", "Đã gom video " + vidId + " (@" + author + ") vào list Python để tải bù.");
    }
  } catch(e){}
};


// Wait / Resume mechanics
window.__tttWaitResume = function(){
  if(!window.__tttStop) return Promise.resolve();
  return new Promise(function(res){
    window.__tttWaiters.push(res);
  });
};

function __tttResumeAll(){
  window.__tttStop = false;
  var w = window.__tttWaiters;
  window.__tttWaiters = [];
  for(var i = 0; i < w.length; i++){
    try { w[i](); } catch(e){}
  }
}
window.__tttResumeAll = __tttResumeAll;

// Sync queue to localStorage and to data/.appdata/failed_videos.json
function __tttSaveQueue(){
  try {
    localStorage.setItem('ttt_failed_queue', JSON.stringify(window.__tttFailedQueue));
  } catch(e){}
  
  try {
    if(typeof O !== 'undefined' && O && O.a && typeof _ === 'function' && typeof v === 'function'){
      _(O.a, 'data/.appdata/failed_videos.json').then(function(h){
        if(h) v(h, JSON.stringify(window.__tttFailedQueue, null, 2));
      }).catch(function(){});
    }
  } catch(e){}
}
window.__tttSaveQueue = __tttSaveQueue;

// Helper cleanup: remove videos that have already been marked downloaded in O.e
function __tttCleanCompletedFromQueue(){
  if(typeof O === 'undefined' || !O || !O.e) return 0;
  var before = window.__tttFailedQueue.length;
  var bDL = (O.e.bookmarked && O.e.bookmarked.downloaded) || new Set();
  var lDL = (O.e.likes && O.e.likes.downloaded) || new Set();
  
  window.__tttFailedQueue = window.__tttFailedQueue.filter(function(item){
    var id = item.id;
    if(bDL.has && bDL.has(id)) return false;
    if(lDL.has && lDL.has(id)) return false;
    return true;
  });
  
  var removed = before - window.__tttFailedQueue.length;
  if(removed > 0){
    __tttSaveQueue();
  }
  return removed;
}
window.__tttCleanCompletedFromQueue = __tttCleanCompletedFromQueue;

function __esc(s){
  return String(s == null ? "" : s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function __vidUrl(id, author){
  return (id && author)
    ? ("https://www.tiktok.com/@" + author + "/video/" + id)
    : (id ? ("https://www.tiktok.com/video/" + id) : location.href);
}

// Download failed_videos.json directly in browser
function __tttExportFailedJson(){
  try {
    var dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(window.__tttFailedQueue, null, 2));
    var dlAnchor = document.createElement('a');
    dlAnchor.setAttribute("href", dataStr);
    dlAnchor.setAttribute("download", "failed_videos.json");
    document.body.appendChild(dlAnchor);
    dlAnchor.click();
    dlAnchor.remove();
  } catch(e){
    prompt("Copy JSON dữ liệu lỗi:", JSON.stringify(window.__tttFailedQueue));
  }
}
window.__tttExportFailedJson = __tttExportFailedJson;

var __DL = ["bi60","bi63","bi127","bi130","doa22","Shc782","ll107","dfo96"];
var __FETCH = ["Mar695","Chv322","Uhb368","Swa471","Yzy056","Qot679","Ifw969","Jsy087","ll88","Dyb767","Mcy770","Onn977"];

window.__tttOnErr = function(code, msg){
  try {
    code = String(code || "");
    msg = String(msg == null ? "" : msg);
    var isDL = __DL.indexOf(code) >= 0;
    var isFetch = __FETCH.indexOf(code) >= 0;
    if(!isDL && !isFetch) return;

    var cur = window.__tttCurrent || {};
    var vidId = cur.id || "";
    var author = cur.author || "";
    var authorId = cur.authorId || (cur.itemData && cur.itemData.author && cur.itemData.author.id) || "";
    var cat = cur.type === "liked" ? "l" : (cur.type === "bookmarked" ? "b" : "following");
    var title = (cur.itemData && (cur.itemData.desc || cur.itemData.title)) || "";
    var cover = (cur.itemData && cur.itemData.video && (cur.itemData.video.cover || cur.itemData.video.coverUrl)) || "";
    var url = vidId ? __vidUrl(vidId, author) : location.href;

    var key = code + ":" + (vidId || "page");
    if(key === window.__tttLastKey) return;
    window.__tttLastKey = key;

    // Log for immediate review
    var logEntry = {
      t: new Date().toLocaleTimeString(),
      code: code,
      msg: msg.slice(0, 300),
      url: url,
      id: vidId,
      author: author,
      isFetch: isFetch
    };
    window.__tttLog.unshift(logEntry);
    if(window.__tttLog.length > 30) window.__tttLog.length = 30;

    // Auto-record to failed queue if we have a video ID (download error)
    if(vidId){
      var existingIdx = -1;
      for(var i = 0; i < window.__tttFailedQueue.length; i++){
        if(window.__tttFailedQueue[i].id === vidId){
          existingIdx = i;
          break;
        }
      }
      var queueItem = {
        id: vidId,
        url: url,
        author: author,
        authorId: authorId,
        category: cat,
        type: cur.type || "bookmarked",
        title: title,
        cover: cover,
        errorCode: code,
        errorMessage: msg,
        failedAt: new Date().toISOString()
      };
      if(existingIdx >= 0){
        window.__tttFailedQueue[existingIdx] = queueItem;
      } else {
        window.__tttFailedQueue.push(queueItem);
      }
      __tttSaveQueue();
    }

    // For fetch errors (batch errors like Mar695): always log to fetchLog
    if(isFetch){
      window.__tttFetchLog.unshift({
        t: new Date().toLocaleTimeString(),
        ts: new Date().toISOString(),
        code: code,
        msg: msg.slice(0, 300)
      });
      if(window.__tttFetchLog.length > 20) window.__tttFetchLog.length = 20;
      // Always show toast notification for fetch errors
      __tttShowToast(code, msg);
    }

    // Determine stop behavior
    if(isDL){
      if(window.__tttAutoSkip){
        window.__tttStop = false;
        __tttShowToast(code, msg);
        __renderMiniBadge();
      } else {
        window.__tttStop = true;
        __render(code, msg, url, cur, isDL);
      }
    } else {
      // Fetch error: always render modal (not just badge) to show message clearly
      __render(code, msg, url, cur, isDL);
    }
  } catch(e){}
};

// Toast notification — hiện ở góc trên phải, tự đóng sau 8 giây
function __tttShowToast(code, msg){
  var toastId = "myfaveTTT-toast";
  var toast = document.getElementById(toastId);
  if(!toast){
    toast = document.createElement("div");
    toast.id = toastId;
    toast.style.cssText = [
      "position:fixed","top:70px","right:20px","z-index:2147483647",
      "width:370px","background:#1a1a2e","color:#eee",
      "border:2px solid #ff3b5c","border-radius:10px",
      "padding:12px 14px","font-family:system-ui,sans-serif",
      "font-size:12px","box-shadow:0 6px 25px rgba(0,0,0,0.5)",
      "transition:opacity 0.3s","cursor:pointer"
    ].join(";");
    document.body.appendChild(toast);
  }
  if(toast._hideTimer) clearTimeout(toast._hideTimer);
  toast.style.opacity = "1";
  toast.style.display = "block";
  toast.innerHTML = 
    '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">'
    + '<span style="background:#ff3b5c;color:#fff;padding:2px 8px;border-radius:5px;font-weight:700;font-size:11px;">LỖI EXTENSION [' + __esc(code) + ']</span>'
    + '<span id="ttt-toast-close" style="cursor:pointer;color:#aaa;font-size:16px;line-height:1;">✕</span>'
    + '</div>'
    + '<div style="color:#ff9f9f;word-break:break-all;margin-bottom:8px;line-height:1.5;">'
    + __esc(msg.slice(0, 200))
    + '</div>'
    + '<div style="display:flex;gap:6px;">'
    + '<button id="ttt-toast-open" style="flex:1;padding:5px;background:#ff3b5c;color:#fff;border:none;border-radius:5px;font-size:11px;font-weight:600;cursor:pointer;">📋 Xem danh sách lỗi</button>'
    + '<button id="ttt-toast-copy" style="padding:5px 10px;background:#333;color:#eee;border:none;border-radius:5px;font-size:11px;cursor:pointer;">Copy lỗi</button>'
    + '</div>'
    + '<div style="margin-top:6px;font-size:10px;color:#888;">Click bất kỳ để đóng · Tự đóng sau 8s</div>';
  var closeToast = function(){
    toast.style.opacity = "0";
    setTimeout(function(){ toast.style.display = "none"; }, 300);
  };
  var closeBtn = document.getElementById("ttt-toast-close");
  if(closeBtn) closeBtn.onclick = function(e){ e.stopPropagation(); closeToast(); };
  var openBtn = document.getElementById("ttt-toast-open");
  if(openBtn) openBtn.onclick = function(e){ e.stopPropagation(); closeToast(); __render(code, msg, location.href, window.__tttCurrent || {}, false); };
  var copyBtn = document.getElementById("ttt-toast-copy");
  if(copyBtn) copyBtn.onclick = function(e){
    e.stopPropagation();
    var b = this;
    var errText = "[" + code + "] " + msg;
    try {
      navigator.clipboard.writeText(errText).then(function(){ b.textContent = "Đã copy!"; });
    } catch(_){ prompt("Copy lỗi:", errText); }
  };
  toast._hideTimer = setTimeout(closeToast, 8000);
}
window.__tttShowToast = __tttShowToast;

// Render small floating badge in bottom-right corner
function __renderMiniBadge(){
  var badge = document.getElementById("myfaveTTT-badge");
  if(!badge){
    badge = document.createElement("div");
    badge.id = "myfaveTTT-badge";
    badge.style.cssText = "position:fixed;bottom:20px;right:20px;z-index:2147483647;cursor:pointer;font-family:system-ui,sans-serif;";
    document.body.appendChild(badge);
  }
  var count = window.__tttFailedQueue.length;
  var fetchCount = window.__tttFetchLog.length;
  var isRunning = window.__tttIsDownloading && !window.__tttStop;
  badge.style.display = "block";
  badge.innerHTML = '<div style="background:#121212;color:#fff;border:1px solid #fe2c55;padding:8px 14px;border-radius:20px;box-shadow:0 4px 15px rgba(0,0,0,0.6);font-size:12px;font-weight:600;display:flex;align-items:center;gap:8px;user-select:none;" title="Click để xem & xóa video lỗi / TikTok Shop">'
    + '<span style="color:#fe2c55;font-size:14px;">⚡</span>'
    + '<span>Video lỗi/Shop: <b style="color:' + (count > 0 ? '#fe2c55' : '#25f4ee') + ';">' + count + '</b></span>'
    + '<span style="background:' + (window.__tttAutoSkip ? '#2ed573' : '#ffa502') + ';color:#000;padding:2px 6px;border-radius:4px;font-size:10px;font-weight:bold;">' + (window.__tttAutoSkip ? 'AUTO' : 'STOP') + '</span>'
    + (fetchCount > 0 ? '<span style="color:#ffa500;font-size:11px;">(TT: ' + fetchCount + ')</span>' : '')
    + (window.__tttStop ? '<span style="background:#d63031;color:#fff;padding:2px 6px;border-radius:4px;font-size:10px;">DỪNG</span>' : '')
    + (window.__tttIsDownloading
        ? ('<span id="ttt-badge-stop-btn" style="background:' + (isRunning ? '#e74c3c' : '#00b894') + ';color:#fff;padding:3px 8px;border-radius:4px;font-size:10px;cursor:pointer;font-weight:bold;">'
           + (isRunning ? '🛑 Dừng' : '▶️ Tiếp') + '</span>')
        : '')
    + '</div>';
  badge.onclick = function(e){
    __render(window.__tttLastKey.split(":")[0] || "INFO", "Quản lý danh sách video lỗi / TikTok Shop", location.href, window.__tttCurrent || {}, window.__tttStop);
  };
  // Stop/Resume button on badge
  var stopBtn = document.getElementById("ttt-badge-stop-btn");
  if(stopBtn){
    stopBtn.onclick = function(e){
      e.stopPropagation();
      if(window.__tttIsDownloading && !window.__tttStop){
        window.__tttPauseDownload();
      } else {
        window.__tttResumeDownload();
      }
    };
  }
}
window.__renderMiniBadge = __renderMiniBadge;

// Render main Error & Queue Management Dialog
function __render(code, msg, url, cur, isDL){
  var box = document.getElementById("myfaveTTT-error-box");
  if(!box){
    box = document.createElement("div");
    box.id = "myfaveTTT-error-box";
    box.style.cssText = "position:fixed;top:15px;right:20px;z-index:2147483647;width:420px;font-family:system-ui,-apple-system,sans-serif;color:#161823;";
    document.body.appendChild(box);
  }
  box.style.display = "block";

  // Auto clean completed from O.e if available
  __tttCleanCompletedFromQueue();

  var queueCount = window.__tttFailedQueue.length;
  var isStopped = !!window.__tttStop;
  var currentVidId = (cur && cur.id) || "";
  var currentAuthor = (cur && cur.author) || "";
  var currentTitle = (cur && cur.itemData && (cur.itemData.desc || cur.itemData.title)) || "";

  var queueRows = window.__tttFailedQueue.map(function(item, idx){
    return '<div style="padding:6px 0;border-bottom:1px solid #f0f0f0;display:flex;justify-content:space-between;align-items:center;gap:6px;">'
      + '<div style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">'
      + '' + (item.errorMessage && item.errorMessage.includes("Shop") ? '<span style="background:#fff3cd;color:#856404;padding:1px 5px;border-radius:3px;font-weight:bold;font-size:10px;">🛍️ TIKTOK SHOP</span>' : '<span style="background:#ffebee;color:#d32f2f;padding:1px 5px;border-radius:3px;font-weight:bold;font-size:10px;">' + __esc(item.errorCode) + '</span>') + ' '
      + '<div style="margin-bottom:2px;"><b style="color:#fe2c55;">@' + __esc(item.author || "tiktok") + '</b> '
      + (item.title ? ('<span style="color:#666;font-size:11px;">- ' + __esc(item.title.slice(0, 45)) + '...</span>') : '') + '</div>'
      + '<div style="display:flex;align-items:center;gap:6px;">'
      + '<a href="' + __esc(item.url) + '" target="_blank" style="color:#0084ff;font-weight:600;text-decoration:underline;word-break:break-all;font-size:11px;" title="Click để mở kiểm tra trên TikTok">' + __esc(item.url) + '</a>'
      + '<button class="ttt-copy-one-link" data-url="' + __esc(item.url) + '" style="padding:2px 6px;border:1px solid #ccc;background:#f8f9fa;border-radius:4px;font-size:10px;cursor:pointer;">Copy</button>'
      + '</div>'
      + '<div style="font-size:10px;color:#888;margin-top:2px;">Lý do: ' + __esc(item.errorMessage || item.errorCode) + '</div>'
      + '</div>'
      + '<button class="ttt-remove-item" data-id="' + __esc(item.id) + '" style="border:none;background:none;color:#999;cursor:pointer;font-size:15px;padding:4px 6px;" title="Xóa khỏi list">✕</button>'
      + '</div>';
  }).join("");

  box.innerHTML = '<div style="background:#ffffff;border:1px solid #e0e0e0;border-radius:12px;padding:16px;box-shadow:0 8px 30px rgba(0,0,0,0.22);max-height:85vh;display:flex;flex-direction:column;">'
    // Header
    + '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;padding-bottom:8px;border-bottom:1px solid #eee;">'
    + '<div style="display:flex;align-items:center;gap:6px;">'
    + '<span style="font-size:16px;">⚡</span>'
    + '<b style="color:' + (isStopped ? '#d32f2f' : '#222') + ';font-size:14px;">'
    + (isStopped ? ('LỖI DOWNLOAD - ĐÃ DỪNG [' + __esc(code) + ']') : 'QUẢN LÝ VIDEO LỖI (PYTHON QUEUE)')
    + '</b></div>'
    + '<div style="display:flex;align-items:center;gap:6px;">'
    + (window.__tttIsDownloading
        ? ('<button id="ttt-modal-stop-btn" style="padding:4px 10px;border:none;border-radius:6px;font-size:11px;font-weight:bold;cursor:pointer;background:' + (!window.__tttStop ? '#e74c3c' : '#00b894') + ';color:#fff;">'
           + (!window.__tttStop ? '🛑 Dừng tải' : '▶️ Tiếp tục') + '</button>')
        : '')
    + '<button id="ttt-btn-close" style="border:none;background:none;font-size:18px;cursor:pointer;color:#888;padding:0 4px;">✕</button>'
    + '</div></div>'

    // Mode Toggle: Auto-skip vs Stop-on-error
    + '<div style="background:#f8f9fa;border-radius:6px;padding:8px 10px;margin-bottom:10px;display:flex;align-items:center;justify-content:space-between;">'
    + '<label style="font-size:12px;font-weight:500;display:flex;align-items:center;gap:6px;cursor:pointer;user-select:none;">'
    + '<input type="checkbox" id="ttt-chk-autoskip" ' + (window.__tttAutoSkip ? 'checked' : '') + ' style="cursor:pointer;" />'
    + '<span>Tự động bỏ qua lỗi & gom vào list Python</span>'
    + '</label>'
    + '<span style="font-size:11px;color:#666;">' + (window.__tttAutoSkip ? 'Auto' : 'Stop') + '</span>'
    + '</div>'

    // Current Error Card (only if actively stopped or has current error)
    + (isStopped ? (
      '<div style="background:#fff5f5;border:1px solid #ffcdd2;border-radius:8px;padding:10px;margin-bottom:12px;">'
      + '<div style="font-size:11px;color:#c62828;font-weight:bold;margin-bottom:4px;">VIDEO ĐANG BỊ LỖI:</div>'
      + (currentTitle ? ('<div style="font-size:12px;color:#222;font-weight:600;margin-bottom:4px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="' + __esc(currentTitle) + '">' + __esc(currentTitle) + '</div>') : '')
      + '<div style="font-size:11px;color:#555;margin-bottom:4px;">ID: <b>' + __esc(currentVidId) + '</b> ' + (currentAuthor ? ('| @' + __esc(currentAuthor)) : '') + '</div>'
      + '<div style="font-size:11px;color:#d32f2f;margin-bottom:8px;word-break:break-all;">Lý do: ' + __esc(msg) + '</div>'
      + '<div style="display:flex;gap:6px;margin-bottom:4px;">'
      + '<button id="ttt-btn-skip-queue" style="flex:1;padding:7px;background:#ff3b5c;color:#fff;border:none;border-radius:6px;font-weight:600;font-size:11px;cursor:pointer;">⏭️ Bỏ qua & Gom vào Python</button>'
      + '<button id="ttt-btn-resume" style="flex:1;padding:7px;background:#00b894;color:#fff;border:none;border-radius:6px;font-weight:600;font-size:11px;cursor:pointer;">▶️ Tiếp tục tải</button>'
      + '<button id="ttt-btn-copy" style="padding:7px 10px;background:#f1f2f6;color:#2f3542;border:none;border-radius:6px;font-weight:600;font-size:11px;cursor:pointer;">📋 Copy</button>'
      + '</div>'
      + '</div>'
    ) : '')

    // Fetch Error Log Section (Mar695, etc.)
    + (window.__tttFetchLog.length > 0 ? (
      '<div style="background:#1a1a2e;border-radius:8px;padding:8px 10px;margin-bottom:10px;">'
      + '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;">'
      + '<b style="font-size:11px;color:#ff9f9f;">⚡ Lỗi TikTok Server (' + window.__tttFetchLog.length + '):</b>'
      + '<button id="ttt-btn-clear-fetch" style="border:none;background:#333;color:#aaa;padding:2px 6px;border-radius:3px;font-size:10px;cursor:pointer;">Xóa log</button>'
      + '</div>'
      + '<div style="max-height:90px;overflow-y:auto;font-size:10px;color:#ccc;">'
      + window.__tttFetchLog.map(function(e){
          return '<div style="border-bottom:1px solid #333;padding:3px 0;">'
            + '<span style="color:#ffa500;font-weight:bold;">[' + __esc(e.code) + ']</span> '
            + '<span style="color:#888;">' + __esc(e.t) + '</span> '
            + '<span style="color:#eee;word-break:break-all;">' + __esc(e.msg.slice(0,120)) + '</span>'
            + '</div>';
        }).join('')
      + '</div>'
      + '</div>'
    ) : '')

    // Failed Queue List Section
    + '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">'
    + '<b style="font-size:12px;color:#333;">📦 Danh sách video chờ tải bằng Python (<span style="color:#ff3b5c;">' + queueCount + '</span>):</b>'
    + '<div style="display:flex;gap:4px;">'
    + '<button id="ttt-btn-clean" style="border:none;background:#f1f2f6;color:#555;padding:2px 6px;border-radius:4px;font-size:10px;cursor:pointer;" title="Dọn dẹp các video đã được Python tải">🔄 Tự dọn video xong</button><button id="ttt-btn-clear-shop" style="border:none;background:#fff3cd;color:#856404;padding:2px 6px;border-radius:4px;font-size:10px;cursor:pointer;" title="Xóa các video TikTok Shop không cần tải">🛍️ Xóa video Shop</button>'
    + '<button id="ttt-btn-clear" style="border:none;background:#ffebee;color:#c62828;padding:2px 6px;border-radius:4px;font-size:10px;cursor:pointer;" title="Xóa toàn bộ list lỗi">🗑️ Xóa hết</button>'
    + '</div></div>'

    + '<div style="max-height:160px;overflow-y:auto;border:1px solid #f0f0f0;border-radius:6px;padding:4px 8px;margin-bottom:10px;font-size:11px;">'
    + (queueRows || '<div style="color:#999;text-align:center;padding:12px 0;">Chưa có video lỗi nào trong danh sách.</div>')
    + '</div>'

    // Export / Action buttons
    + '<div style="display:flex;gap:6px;margin-top:auto;">'
    + '<button id="ttt-btn-export" style="flex:1;padding:8px;background:#2f3542;color:#fff;border:none;border-radius:6px;font-weight:600;font-size:11px;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:4px;">💾 Tải file failed_videos.json</button>'
    + '<button id="ttt-btn-copy-all" style="padding:8px 12px;background:#dfe4ea;color:#2f3542;border:none;border-radius:6px;font-weight:600;font-size:11px;cursor:pointer;">Copy All</button>'
    + '</div>'

    + '<div style="margin-top:8px;font-size:10px;color:#888;text-align:center;">'
    + 'Chạy tool Python: <code>sync_and_download.py --mode download-failed</code>'
    + '</div>'
    + '</div>';

  // Attach event handlers
  document.getElementById("ttt-btn-close").onclick = function(){
    box.style.display = "none";
    __renderMiniBadge();
  };
  var modalStopBtn = document.getElementById("ttt-modal-stop-btn");
  if(modalStopBtn){
    modalStopBtn.onclick = function(){
      if(window.__tttIsDownloading && !window.__tttStop){
        window.__tttPauseDownload();
      } else {
        window.__tttResumeDownload();
      }
      __render(code, msg, url, cur, isDL);
    };
  }

  var chkAuto = document.getElementById("ttt-chk-autoskip");
  if(chkAuto){
    chkAuto.onchange = function(){
      window.__tttAutoSkip = this.checked;
      localStorage.setItem('ttt_auto_skip', String(this.checked));
      if(window.__tttAutoSkip && window.__tttStop){
        __tttResumeAll();
      }
      __render(code, msg, url, cur, isDL);
    };
  }

  var btnSkip = document.getElementById("ttt-btn-skip-queue");
  if(btnSkip){
    btnSkip.onclick = function(){
      __tttResumeAll();
      window.__tttLastKey = "";
      box.style.display = "none";
      __renderMiniBadge();
    };
  }

  var btnResume = document.getElementById("ttt-btn-resume");
  if(btnResume){
    btnResume.onclick = function(){
      __tttResumeAll();
      window.__tttLastKey = "";
      box.style.display = "none";
      __renderMiniBadge();
    };
  }

  var btnCopy = document.getElementById("ttt-btn-copy");
  if(btnCopy){
    btnCopy.onclick = function(){
      var b = this;
      try {
        if(navigator.clipboard && navigator.clipboard.writeText){
          navigator.clipboard.writeText(url).then(function(){ b.textContent = "Đã copy!"; });
        } else {
          prompt("Copy link:", url);
        }
      } catch(e){
        prompt("Copy link:", url);
      }
    };
  }

  var btnExport = document.getElementById("ttt-btn-export");
  if(btnExport){
    btnExport.onclick = function(){
      __tttExportFailedJson();
    };
  }

  var btnCopyAll = document.getElementById("ttt-btn-copy-all");
  if(btnCopyAll){
    btnCopyAll.onclick = function(){
      var b = this;
      var text = JSON.stringify(window.__tttFailedQueue, null, 2);
      try {
        if(navigator.clipboard && navigator.clipboard.writeText){
          navigator.clipboard.writeText(text).then(function(){ b.textContent = "Đã copy!"; });
        } else {
          prompt("Copy JSON:", text);
        }
      } catch(e){
        prompt("Copy JSON:", text);
      }
    };
  }

    var btnClearShop = document.getElementById("ttt-btn-clear-shop");
  if(btnClearShop){
    btnClearShop.onclick = function(){
      var before = window.__tttFailedQueue.length;
      window.__tttFailedQueue = window.__tttFailedQueue.filter(function(item){
        if(item.isShop || item.errorCode === 'TIKTOK_SHOP') return false;
        var msg = (item.errorMessage || "").toLowerCase();
        var code = (item.errorCode || "").toLowerCase();
        return !msg.includes("shop") && !code.includes("shop");
      });
      var removed = before - window.__tttFailedQueue.length;
      __tttSaveQueue();
      alert("Đã xóa " + removed + " video TikTok Shop / Unplayable khỏi danh sách.");
      __render(code, msg, url, cur, isDL);
    };
  }

  var btnClean = document.getElementById("ttt-btn-clean");
  if(btnClean){
    btnClean.onclick = function(){
      var removed = __tttCleanCompletedFromQueue();
      alert("Đã tự động loại bỏ " + removed + " video đã được tải xong khỏi danh sách.");
      __render(code, msg, url, cur, isDL);
    };
  }

  var btnClear = document.getElementById("ttt-btn-clear");
  if(btnClear){
    btnClear.onclick = function(){
      if(confirm("Bạn có chắc muốn xóa toàn bộ danh sách video lỗi không?")){
        window.__tttFailedQueue = [];
        __tttSaveQueue();
        __render(code, msg, url, cur, isDL);
      }
    };
  }

  var btnClearFetch = document.getElementById("ttt-btn-clear-fetch");
  if(btnClearFetch){
    btnClearFetch.onclick = function(){
      window.__tttFetchLog = [];
      __render(code, msg, url, cur, isDL);
    };
  }

  // Remove individual item
  
  var copyOneBtns = box.querySelectorAll(".ttt-copy-one-link");
  for(var cIdx = 0; cIdx < copyOneBtns.length; cIdx++){
    copyOneBtns[cIdx].onclick = function(){
      var u = this.getAttribute("data-url");
      var btn = this;
      try {
        if(navigator.clipboard && navigator.clipboard.writeText){
          navigator.clipboard.writeText(u).then(function(){ btn.textContent = "OK!"; setTimeout(function(){ btn.textContent = "Copy"; }, 1500); });
        } else { prompt("Copy link:", u); }
      } catch(_){ prompt("Copy link:", u); }
    };
  }

  var removeBtns = box.querySelectorAll(".ttt-remove-item");
  for(var r = 0; r < removeBtns.length; r++){
    removeBtns[r].onclick = function(){
      var idToRemove = this.getAttribute("data-id");
      window.__tttFailedQueue = window.__tttFailedQueue.filter(function(item){
        return item.id !== idToRemove;
      });
      __tttSaveQueue();
      __render(code, msg, url, cur, isDL);
    };
  }

  __renderMiniBadge();
}

// Initial render mini badge if there are already items in queue
__renderMiniBadge();

})();


// Lắng nghe lệnh mở modal từ sidebar iframe (TikTok CUSTOM)
window.addEventListener("message", function(e){
  try {
    if(e && e.data && e.data.type === 999){
      __render("INFO", "Quản lý danh sách video lỗi / TikTok Shop", location.href, window.__tttCurrent || {}, false);
    }
  } catch(_){}
});
