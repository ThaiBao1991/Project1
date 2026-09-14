/**
 * Content Script — Facebook Liked Media Downloader & Auto-Unlike (Anti-Ban Engine)
 * 
 * Thiết kế chính xác theo cấu trúc Activity Log Facebook tiếng Việt:
 * - Định vị dòng qua nút "Xem"
 * - Nút 3 chấm "..." nằm kế bên nút "Xem"
 * - Đo độ dài text bài viết trực tiếp từ nội dung dòng
 * - <= 500 ký tự: Click "Xem" lấy ảnh HD/video -> tải về image/ hoặc video/ -> Click "..." Hủy Thích
 * - > 500 ký tự: ĐỂ NGUYÊN HOÀN TOÀN
 */

// ── VÀNG: MÃ HÓA BASE64 ĐỐI XỨNG HAI CHIỀU (UTF-8) ──────────────────────────
const bytesToBinary = (bytes) => {
  let binary = "";
  for (let index = 0; index < bytes.length; index += 0x8000) {
    binary += String.fromCharCode(...bytes.subarray(index, index + 0x8000));
  }
  return binary;
};

const encodeBase64Utf8 = (obj) =>
  btoa(bytesToBinary(new TextEncoder().encode(JSON.stringify(obj))));

const decodeBase64Utf8 = (encoded) => {
  try {
    const bytes = Uint8Array.from(atob(encoded), (char) => char.charCodeAt(0));
    return JSON.parse(new TextDecoder().decode(bytes));
  } catch (e) {
    console.error('[FB-Downloader] Lỗi giải mã Base64:', e);
    return null;
  }
};

// ── TRẠNG THÁI TOÀN CỤC & CẤU HÌNH ANTI-BAN ─────────────────────────────────
let isRunning = false;
let isPaused = false;
let isCoolingDown = false;
let processedIds = new Set();
let pendingUnlikeIds = new Set();
let pendingUnlikeTriedThisSession = new Set();

let config = {
  charThreshold: 300,        // <= 300: tải & unlike; > 300: ĐỂ NGUYÊN
  minDelayMs: 4500,          // Delay tối thiểu giữa các bài (ms)
  maxDelayMs: 8500,          // Delay tối đa (ms)
  clickMinDelayMs: 900,      // Delay giữa các thao tác click
  clickMaxDelayMs: 1800,
  autoUnlike: true,          // Tự động unlike sau khi tải
  downloadVideos: true,      // Tải video vào folder video/
  downloadImages: true,      // Tải ảnh vào folder image/
  savePostInfo: true,        // Lưu file post_info.txt
  cooldownEvery: 5,          // Cứ sau 5 bài unlike thì nghỉ giải lao
  cooldownMinSec: 25,        // Nghỉ tối thiểu (giây)
  cooldownMaxSec: 45,        // Nghỉ tối đa (giây)
  maxPerSession: 30          // Giới hạn an toàn mỗi phiên chạy (bài)
};

// Tự động nạp cấu hình người dùng đã lưu từ chrome.storage.local
try {
  chrome.storage.local.get(['fb_user_config'], (res) => {
    if (res && res.fb_user_config) {
      config = { ...config, ...res.fb_user_config };
    }
  });
} catch (e) {}

let sessionProcessedCount = 0;
let sessionUnlikedCount = 0;

// ── KEEPALIVE ENGINE ─────────────────────────────────────────────────────────
let silentAudio = null;
let audioHealthInterval = null;

function startKeepAlive() {
  try {
    if (!silentAudio) {
      const silenceWav = 'data:audio/wav;base64,UklGRigAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQQAAAAAAP//';
      silentAudio = new Audio(silenceWav);
      silentAudio.loop = true;
      silentAudio.volume = 0.01;
    }
    silentAudio.play().catch(() => {});

    if (!audioHealthInterval) {
      audioHealthInterval = setInterval(() => {
        if (isRunning && silentAudio && silentAudio.paused) {
          silentAudio.play().catch(() => {});
        }
      }, 5000);
    }

    if (navigator.locks && navigator.locks.request) {
      navigator.locks.request('fb_liked_media_wakeLock', { mode: 'shared' }, () => {
        return new Promise((resolve) => {
          const checkLock = setInterval(() => {
            if (!isRunning) {
              clearInterval(checkLock);
              resolve();
            }
          }, 3000);
        });
      }).catch(() => {});
    }
    log('[KeepAlive] Đã kích hoạt bộ chống đóng băng tab.');
  } catch (e) {
    console.warn('[KeepAlive] Lỗi kích hoạt:', e);
  }
}

function stopKeepAlive() {
  if (audioHealthInterval) {
    clearInterval(audioHealthInterval);
    audioHealthInterval = null;
  }
  if (silentAudio) {
    silentAudio.pause();
  }
}

// ── TIỆN ÍCH HỖ TRỢ ──────────────────────────────────────────────────────────
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const getRandomDelay = (min, max) => Math.floor(Math.random() * (max - min + 1)) + min;

function log(msg, type = 'info') {
  const timestamp = new Date().toLocaleTimeString('vi-VN');
  const formatted = `[${timestamp}] ${msg}`;
  console.log(`%c[FB-AntiBan] ${formatted}`, type === 'warn' ? 'color: orange' : type === 'error' ? 'color: red' : 'color: #1877f2');
  try {
    chrome.runtime.sendMessage({
      action: 'LOG_MESSAGE',
      log: formatted,
      type
    }).catch(() => {});
  } catch (e) {}
}

async function naturalSmoothScroll(distance = 450) {
  const steps = 6;
  const stepDist = distance / steps;
  for (let i = 0; i < steps; i++) {
    window.scrollBy({ top: stepDist, behavior: 'smooth' });
    await sleep(getRandomDelay(80, 160));
  }
}

async function triggerCooldownBreak() {
  isCoolingDown = true;
  const breakSec = getRandomDelay(config.cooldownMinSec, config.cooldownMaxSec);
  log(`☕ [Anti-Ban] Đã unlike ${sessionUnlikedCount} bài. Nghỉ giải lao an toàn ${breakSec}s...`, 'warn');
  
  chrome.runtime.sendMessage({
    action: 'COOLDOWN_STATE',
    isCoolingDown: true,
    secondsLeft: breakSec
  }).catch(() => {});

  for (let s = breakSec; s > 0; s--) {
    if (!isRunning) break;
    while (isPaused && isRunning) await sleep(1000);
    if (s % 10 === 0 || s <= 5) {
      log(`☕ [Nghỉ giải lao an toàn] Còn ${s} giây tiếp tục...`);
    }
    await sleep(1000);
  }

  isCoolingDown = false;
  chrome.runtime.sendMessage({
    action: 'COOLDOWN_STATE',
    isCoolingDown: false,
    secondsLeft: 0
  }).catch(() => {});

  if (isRunning) {
    log(`✅ Kết thúc thời gian nghỉ giải lao. Tiếp tục tiến trình...`, 'info');
  }
}

// ── NẠP & LƯU LỊCH SỬ ĐÃ XỬ LÝ ─────────────────────────────────────────────
async function loadProcessedHistory() {
  return new Promise((resolve) => {
    chrome.storage.local.get(['fb_processed_cache', 'fb_pending_unlike_cache'], (res) => {
      if (res.fb_processed_cache) {
        const list = decodeBase64Utf8(res.fb_processed_cache);
        if (Array.isArray(list)) {
          processedIds = new Set(list);
          log(`Đã nạp ${processedIds.size} bài viết đã xử lý từ trước.`);
        }
      }
      if (res.fb_pending_unlike_cache) {
        const pendingList = decodeBase64Utf8(res.fb_pending_unlike_cache);
        if (Array.isArray(pendingList)) {
          pendingUnlikeIds = new Set(pendingList);
          log(`Loaded ${pendingUnlikeIds.size} pending video Unlike item(s) for a safe retry.`);
        }
      }
      resolve();
    });
  });
}

async function markProcessed(id) {
  if (!id) return;
  processedIds.add(id);
  const arr = Array.from(processedIds);
  const trimmed = arr.slice(-5000);
  const encoded = encodeBase64Utf8(trimmed);
  chrome.storage.local.set({ fb_processed_cache: encoded });
}

async function markUnlikePending(id) {
  if (!id) return;
  pendingUnlikeIds.add(id);
  const encoded = encodeBase64Utf8(Array.from(pendingUnlikeIds).slice(-5000));
  chrome.storage.local.set({ fb_pending_unlike_cache: encoded });
}

async function clearUnlikePending(id) {
  if (!id || !pendingUnlikeIds.delete(id)) return;
  const encoded = encodeBase64Utf8(Array.from(pendingUnlikeIds).slice(-5000));
  chrome.storage.local.set({ fb_pending_unlike_cache: encoded });
}

// ── DOM SELECTORS ĐA TẦNG (MULTI-FALLBACK) THEO GIAO DIỆN FACEBOOK THỰC TẾ ──────────────────────

/**
 * Leo ngược cây DOM để tìm container row chứa dòng hoạt động.
 * 
 * ⚠️ QUAN TRỌNG: Phải trả về container NHỎ NHẤT (đầu tiên tìm thấy) có chứa
 * post link — KHÔNG TIẾP TỤC LEO lên container lớn hơn.
 * 
 * Lý do: Nếu lấy container lớn nhất (bao trùm cả ngày), thì tất cả các nút
 * 3 chấm trong ngày đó đều map về cùng 1 container → seen.has(container) = true
 * từ bài thứ 2 → chỉ 1 bài/ngày được xử lý! (BUG NGHIÊM TRỌNG)
 */
function findActivityRowContainer(el, maxLevels = 15) {
  let cur = el;
  for (let i = 0; i < maxLevels; i++) {
    if (!cur || !cur.parentElement) break;
    const p = cur.parentElement;

    // Dừng ngay nếu phần tử cha quá lớn (bao trùm nhiều bài) hoặc là feed/main
    if (p.getAttribute('role') === 'main' || p.getAttribute('role') === 'feed') break;
    if (p.tagName === 'BODY' || p.tagName === 'HTML') break;

    // Trả về NGAY container NHỎ NHẤT (đầu tiên tìm thấy) có chứa post link
    // Đây chính là container riêng của từng bài viết cụ thể
    const postLink = p.querySelector && p.querySelector(
      'a[href*="/posts/"], a[href*="permalink.php"], a[href*="story_fbid"], a[href*="story.php"], a[href*="/reel/"], a[href*="/photo/"]'
    );
    if (postLink) {
      return p; // ← DỪNG NGAY, không leo lên nữa!
    }

    cur = p;
  }
  // Fallback nếu không tìm thấy post link
  return findRowContainer(el, maxLevels);
}


function findRowContainer(el, maxLevels = 8) {
  let cur = el;
  for (let i = 0; i < maxLevels; i++) {
    if (!cur || !cur.parentElement) break;
    const p = cur.parentElement;
    if (p.children.length >= 2 && (p.offsetHeight > 50 || p.clientHeight > 50)) {
      return cur;
    }
    cur = p;
  }
  return el.parentElement || el;
}

/**
 * Tìm tất cả các dòng hoạt động (Activity Rows) trên trang Facebook.
 * Căn cứ theo kết quả Debug DOM thực tế:
 *   1. Tìm trực tiếp qua nút 3 chấm [aria-label*="Lựa chọn khác"] (aria-haspopup="dialog")
 *   2. Tìm qua các thẻ link permalink / posts
 *   3. Tìm qua nút chữ "Xem" (View)
 */
function findActivityRows() {
  const seen = new Set();
  const rows = [];

  // ── CHIẾN LƯỢC 1 (ƯU TIÊN SỐ 1): Nút 3 chấm "Lựa chọn khác..." (Đã xác minh qua Debug DOM) ──
  const menuButtons = Array.from(document.querySelectorAll(
    'div[role="button"][aria-label*="Lựa chọn khác"], ' +
    'div[role="button"][aria-label*="More options"], ' +
    '[aria-haspopup="dialog"][aria-label*="Lựa chọn khác"], ' +
    '[aria-haspopup="dialog"][aria-label*="More options"], ' +
    '[aria-haspopup="menu"][aria-label*="Lựa chọn khác"]'
  )).filter(el => {
    const rect = el.getBoundingClientRect();
    // Bỏ qua các nút cố định trên thanh điều hướng đầu trang (top < 120)
    return rect.top > 120 || rect.top <= 0;
  });

  if (menuButtons.length > 0) {
    menuButtons.forEach(btn => {
      const container = findActivityRowContainer(btn);
      if (!container || seen.has(container)) return;
      seen.add(container);

      // Tìm nút "Xem" nếu có
      let viewBtn = null;
      const allClickables = Array.from(container.querySelectorAll('div[role="button"], a[role="button"], button, a[href]'));
      for (const el of allClickables) {
        const t = (el.innerText || el.textContent || '').trim();
        if (t === 'Xem' || t === 'View') {
          viewBtn = el;
          break;
        }
      }

      rows.push({
        actionBtn: btn,
        viewBtn: viewBtn,
        container: container,
        source: 'MenuBtn_Direct'
      });
    });
  }

  // ── CHIẾN LƯỢC 2 (FALLBACK): Tìm qua các liên kết permalink / posts ──
  if (rows.length === 0) {
    log('[Fallback 2] Tìm qua các thẻ permalink / posts...', 'warn');
    const postLinks = Array.from(document.querySelectorAll(
      'a[href*="/posts/"], a[href*="permalink.php"], a[href*="story_fbid"]'
    ));

    postLinks.forEach(link => {
      const container = findActivityRowContainer(link);
      if (!container || seen.has(container)) return;
      seen.add(container);

      const actionBtn = container.querySelector(
        '[aria-label*="Lựa chọn khác"], [aria-label*="More options"], [aria-haspopup="dialog"], [aria-haspopup="menu"]'
      );
      rows.push({
        actionBtn: actionBtn || null,
        viewBtn: null,
        container: container,
        source: 'PostLink_Fallback'
      });
    });
  }

  // ── CHIẾN LƯỢC 3 (FALLBACK): Nút "Xem" / "View" ──
  if (rows.length === 0) {
    log('[Fallback 3] Tìm qua nút "Xem" / "View"...', 'warn');
    const allClickables = Array.from(
      document.querySelectorAll('div[role="button"], a[role="button"], button')
    );
    const viewButtons = allClickables.filter(el => {
      const text = (el.innerText || el.textContent || '').trim();
      return text === 'Xem' || text === 'View';
    });

    viewButtons.forEach(viewBtn => {
      const container = findRowContainer(viewBtn);
      if (!container || seen.has(container)) return;
      seen.add(container);

      const actionBtn = container.querySelector(
        '[aria-label*="Lựa chọn khác"], [aria-haspopup="dialog"], [aria-haspopup="menu"]'
      );
      rows.push({ viewBtn, actionBtn, container, source: 'ViewBtn_Fallback' });
    });
  }

  // Sắp xếp các bài viết chuẩn xác từ trên xuống dưới theo thứ tự hiển thị trên màn hình
  rows.sort((a, b) => {
    const topA = (a.container.getBoundingClientRect().top + window.scrollY);
    const topB = (b.container.getBoundingClientRect().top + window.scrollY);
    return topA - topB;
  });

  log(`[findActivityRows] Tìm thấy ${rows.length} bài viết (Chiến lược: ${rows.length > 0 ? rows[0].source : 'N/A'}, đã sắp xếp theo thứ tự hiển thị)`);
  return rows;
}

/**
 * Giả lập click chuột đầy đủ chuỗi sự kiện React/SPA
 */
function simulateClick(el) {
  if (!el) return;
  el.scrollIntoView({ behavior: 'smooth', block: 'center' });
  const opts = { bubbles: true, cancelable: true, view: window };
  el.dispatchEvent(new MouseEvent('pointerdown', opts));
  el.dispatchEvent(new MouseEvent('mousedown', opts));
  el.dispatchEvent(new MouseEvent('pointerup', opts));
  el.dispatchEvent(new MouseEvent('mouseup', opts));
  el.click();
}

/**
 * Trích xuất timestamp giờ:phút (ví dụ 22:19, 19:27) từ container bài viết
 */
function extractPostTime(container) {
  if (!container) return '';
  const text = container.innerText || '';
  const match = text.match(/\b(\d{1,2}):(\d{2})\b/);
  if (match) {
    const hh = match[1].padStart(2, '0');
    const mm = match[2];
    return `${hh}${mm}`;
  }
  return '';
}


/**
 * Trích xuất text nội dung bài viết từ dòng hoạt động
 */
function extractPostTextFromRow(container) {
  if (!container) return '';
  const rawText = container.innerText || '';
  const lines = rawText.split('\n').map(s => s.trim()).filter(Boolean);

  // Lọc bỏ các dòng hệ thống không thuộc nội dung bài viết
  const contentLines = lines.filter(line => {
    if (line === 'Xem' || line === 'View') return false;
    if (line === 'Tất cả' || line === 'All' || line === 'Gỡ') return false;
    if (line === 'Công khai' || line === 'Public' || line === 'Bạn bè' || line === 'Friends' || line === 'Chỉ mình tôi') return false;
    if (/^\d{1,2}:\d{2}$/.test(line)) return false; // timestamp như 19:27, 18:58
    if (/^\d{1,2}\s+Tháng\s+\d{1,2}/i.test(line)) return false; // 11 Tháng 9, 2026
    if (line.includes('thích ảnh của') || line.includes('thích bài viết của') || line.includes('thích video của')) return false;
    if (line.includes('thích kỷ niệm của') || line.includes('thích liên kết của')) return false;
    if (line.includes('liked a photo') || line.includes('liked a post') || line.includes('liked a video')) return false;
    return true;
  });

  return contentLines.join('\n').trim();
}

/**
 * Lấy ID định danh duy nhất cho dòng hoạt động (hỗ trợ cả pfbid alphanumeric)
 */
function extractRowId(rowItem) {
  const { container } = rowItem;
  // Tìm liên kết bài viết / ảnh nếu có
  const link = container.querySelector('a[href*="/posts/"], a[href*="story.php"], a[href*="permalink"], a[href*="/photo"], a[href*="/reel/"], a[href*="story_fbid"], a[href*="fbid="]');
  if (link && link.href) {
    const match = link.href.match(/(?:posts\/|story_fbid=|fbid=|\/reel\/|photo\.php\?fbid=)([a-zA-Z0-9_]+)/);
    if (match && match[1]) return match[1];
    return link.href.split('?')[0].replace(/https?:\/\/(?:www\.)?facebook\.com\//, '').replace(/[^a-zA-Z0-9_]/g, '_');
  }
  const text = (container.innerText || '').slice(0, 100);
  return 'id_' + Math.abs(text.split('').reduce((a, b) => { a = ((a << 5) - a) + b.charCodeAt(0); return a & a; }, 0));
}


// ── XỬ LÝ KẾT QUẢ TỪ TAB PERMALINK (Promise resolver map) ────────────────────
const permalinkResultResolvers = new Map(); // tabId -> resolve

// Lắng nghe kết quả từ background (tab đã extract xong)
chrome.runtime.onMessage.addListener((msg) => {
  if (msg.action === 'PERMALINK_MEDIA_RESULT') {
    const resolver = permalinkResultResolvers.get(msg.tabId);
    if (resolver) {
      permalinkResultResolvers.delete(msg.tabId);
      resolver({
        images: msg.images || [],
        videos: msg.videos || [],
        postText: msg.postText || '',
        isTruncated: !!msg.isTruncated,
        textStatus: msg.textStatus || 'unverified',
        isVideoPost: !!msg.isVideoPost,
        sourceUrl: msg.sourceUrl || ''
      });
    }
  }
});

/**
 * Lấy thumbnail fallback từ container dòng Activity Log
 */
function extractThumbnailsFromContainer(container) {
  const images = [];
  const thumbImgs = container.querySelectorAll('img');
  thumbImgs.forEach(img => {
    const src = img.currentSrc || img.src || '';
    if (src && !src.includes('emoji.php') && !src.includes('/rsrc.php/') && !src.includes('static.xx')) {
      // Nâng cấp URL ảnh từ thumbnail nhỏ lên ảnh lớn hơn nếu có thể
      const hdSrc = src.replace(/_s\.(jpg|png|webp)/i, '_n.$1');
      if (!images.includes(hdSrc)) images.push(hdSrc);
    }
  });
  return images;
}

/**
 * Chờ kết quả extract từ tab permalink với timeout
 */
function waitForPermalinkResult(tabId, timeoutMs = 15000) {
  return new Promise((resolve) => {
    const timer = setTimeout(() => {
      permalinkResultResolvers.delete(tabId);
      resolve({ images: [], videos: [], postText: '', isTruncated: false, textStatus: 'unverified', isVideoPost: false });
    }, timeoutMs);

    permalinkResultResolvers.set(tabId, (result) => {
      clearTimeout(timer);
      resolve(result);
    });
  });
}

/**
 * Mở media từ bài viết — Cách C: Tab mới + Lightbox + Fallback Thumbnail
 * 
 * Luồng:
 * 1. Thu thập thumbnail fallback ngay từ container
 * 2. Tìm link permalink trong container (nếu có) → mở tab nền qua background
 * 3. Click nút "Xem" → Đợi 2.5s → Kiểm tra có lightbox mở không
 * 4a. Nếu có lightbox → Quét ảnh/video HD trong dialog → Đóng dialog
 * 4b. Nếu không có lightbox → Giả sử Facebook đã mở tab permalink → Chờ kết quả từ background
 * 5. Fallback về thumbnail nếu cả 2 đều rỗng
 */
async function openAndExtractMedia(rowItem) {
  const { viewBtn, container } = rowItem;
  const result = {
    images: [],
    videos: [],
    postUrl: ''
  };

  // BƯỚC 2: Tìm link permalink để mở tab con nền ngầm
  let permalinkUrl = '';
  const postLink = container.querySelector(
    'a[href*="/permalink.php"], a[href*="/posts/"], a[href*="story.php"], a[href*="/reel/"], a[href*="/photo/"], a[href*="/share/r/"], a[href*="/videos/"], a[href*="/watch/"]'
  );
  if (postLink && postLink.href) {
    permalinkUrl = postLink.href;
  } else if (viewBtn && viewBtn.href) {
    permalinkUrl = viewBtn.href;
  }

  // LƯU Ý SỐNG CÒN: TUYỆT ĐỐI KHÔNG CLICK viewBtn TRÊN TAB CHÍNH
  // Vì click viewBtn sẽ kích hoạt điều hướng trang hiện tại sang bài viết, làm mất tab Activity Log!
  let tabResult = { images: [], videos: [], postText: '', isTruncated: false, textStatus: 'unverified', isVideoPost: false, sourceUrl: '' };

  if (permalinkUrl && !permalinkUrl.includes('facebook.com/login')) {
    log(`🪟 Mở tab nền để tải ảnh/video HD bài viết: ${permalinkUrl.slice(0, 60)}...`);
    try {
      const tabResp = await chrome.runtime.sendMessage({
        action: 'OPEN_PERMALINK_TAB',
        url: permalinkUrl,
        parentTabId: await getMyTabId()
      });
      if (tabResp && tabResp.success && tabResp.tabId) {
        log(`⏳ Chờ tab ngầm extract media (Tab ID: ${tabResp.tabId})...`);
        tabResult = await waitForPermalinkResult(tabResp.tabId, 22000);
        log(`✅ Tab ngầm trả về: ${tabResult.images.length} ảnh bài đăng chính, ${tabResult.videos.length} video.`);
      }
    } catch (e) {
      console.warn('[FB-Downloader] Lỗi mở tab nền:', e);
    }
  }

  // Do not download arbitrary <img> nodes from an Activity Log row: they can
  // be avatars, comment images, or link previews.  A failed permalink scan
  // yields no image rather than an image from the wrong content.
  result.images = tabResult.images || [];
  result.videos = tabResult.videos || [];
  if (tabResult.postText) {
    result.postText = tabResult.postText;
  }
  result.isTruncated = !!tabResult.isTruncated;
  result.textStatus = tabResult.textStatus || 'unverified';
  result.isVideoPost = !!tabResult.isVideoPost;
  // Keep the original permalink supplied by the background tab. Reel playback
  // has no direct MP4 URL, so the local helper must receive this page URL.
  result.sourceUrl = tabResult.sourceUrl || permalinkUrl;
  result.postUrl = permalinkUrl;
  result.sourceDetail = tabResult.images.length > 0 ? 'Tab nền ngầm (Chi tiết bài viết)' : 'Không có ảnh đã xác minh từ trang chi tiết';

  log(`🎯 Kết quả media bài viết: ${result.images.length} ảnh, ${result.videos.length} video.`);
  return result;
}

// ── DEBUG MODE: SO SÁNH ẢNH VỚI MẪU LỖI ─────────────────────────────────────
let suspiciousUserDecisionResolver = null;

async function checkSuspiciousImage(imgUrl, meta) {
  try {
    const debugData = await new Promise(resolve => {
      chrome.storage.local.get(['fb_debug_sample_hash', 'fb_debug_sample_image', 'fb_debug_threshold'], resolve);
    });

    if (!debugData || !debugData.fb_debug_sample_hash) {
      return 'proceed';
    }

    const sampleHash = debugData.fb_debug_sample_hash;
    const threshold = debugData.fb_debug_threshold || 85;

    // Yêu cầu service worker tính hash của ảnh
    const hashResp = await chrome.runtime.sendMessage({
      action: 'COMPUTE_IMAGE_HASH',
      imageUrl: imgUrl
    });

    if (!hashResp || !hashResp.hash) {
      return 'proceed';
    }

    // So sánh hash
    const compResp = await chrome.runtime.sendMessage({
      action: 'COMPARE_IMAGE_HASH',
      hash1: hashResp.hash,
      hash2: sampleHash
    });

    const similarity = compResp ? Math.round(compResp.similarity * 100) : 0;
    log(`🔍 [Debug Check] Ảnh #${meta.imgIndex}/${meta.totalImgs} - Độ giống mẫu lỗi: ${similarity}% (Ngưỡng: ${threshold}%)`);

    if (similarity >= threshold) {
      log(`🚨 [DEBUG PHÁT HIỆN] Ảnh #${meta.imgIndex} có độ giống ${similarity}% (>= ${threshold}%)! DỪNG VÀ BÁO CÁO...`, 'warn');
      isPaused = true;

      const payload = {
        similarity,
        threshold,
        imageUrl: imgUrl,
        sampleImage: debugData.fb_debug_sample_image,
        postId: meta.postId,
        postUrl: meta.postUrl,
        charCount: meta.charCount,
        postText: meta.postText,
        sourceDetail: meta.sourceDetail,
        imgIndex: meta.imgIndex,
        totalImgs: meta.totalImgs
      };

      chrome.storage.local.set({ fb_last_suspicious: payload });

      chrome.runtime.sendMessage({
        action: 'SUSPICIOUS_IMAGE_DETECTED',
        data: payload
      }).catch(() => {});

      const decision = await new Promise(resolve => {
        suspiciousUserDecisionResolver = resolve;
      });

      isPaused = false;
      return decision; // 'continue' hoặc 'stop'
    }
  } catch (err) {
    console.warn('[FB-Downloader] Lỗi khi kiểm tra debug hash:', err);
  }
  return 'proceed';
}


/**
 * Lấy tabId của content script hiện tại
 */
async function getMyTabId() {
  try {
    const resp = await chrome.runtime.sendMessage({ action: 'GET_TAB_ID' });
    return resp && resp.tabId ? resp.tabId : null;
  } catch (e) {
    return null;
  }
}


/**
 * Thao tác click nút 3 chấm (...) và chọn "Bỏ thích"
 */
async function executeUnlike(rowItem) {
  const { actionBtn, viewBtn, container } = rowItem;

  // Định vị chính xác nút 3 chấm (...)
  let btn = actionBtn;
  if (!btn && viewBtn && viewBtn.parentElement) {
    const sibs = Array.from(viewBtn.parentElement.querySelectorAll('div[role="button"], button')).filter(b => b !== viewBtn);
    if (sibs.length > 0) btn = sibs[0];
  }
  if (!btn && container) {
    btn = container.querySelector('[aria-label*="Lựa chọn khác"], [aria-label*="More options"], [aria-haspopup="dialog"], [aria-haspopup="menu"]');
  }

  if (!btn) {
    log('Không tìm thấy nút 3 chấm (...) của dòng này.', 'warn');
    return false;
  }

  /**
   * Tìm nút "Bỏ thích" trong menu popup
   * 
   * Dựa trên DOM thực tế Facebook Activity Log:
   *   [role="menu"][aria-label*="lựa chọn"]
   *     └─ [role="menuitem"][tabindex="0"]  ← element cần click
   *          └─ ... └─ <span dir="auto">Bỏ thích</span>
   */
  function findUnlikeBtnInMenu(menuEl) {
    const searchRoot = menuEl || document;

    // Chiến lược 1: Tìm trực tiếp [role="menuitem"] chứa text "Bỏ thích"
    // Đây là element clickable chính xác theo DOM thực tế Facebook
    const menuItems = Array.from(searchRoot.querySelectorAll('[role="menuitem"], [tabindex="0"]'));
    for (const item of menuItems) {
      const txt = (item.innerText || item.textContent || '').trim().toLowerCase();
      if (
        txt.includes('bỏ thích') ||
        txt.includes('unlike') ||
        txt.includes('gỡ cảm xúc') ||
        txt.includes('gỡ biểu cảm') ||
        txt.includes('xóa lượt tương tác') ||
        txt.includes('remove reaction') ||
        txt.includes('remove like') ||
        txt.includes('không thích nữa')
      ) {
        log(`🎯 [findUnlikeBtn] Tìm thấy qua [role="${item.getAttribute('role')}"] text="${txt.slice(0,30)}"`, 'info');
        return item; // Trả về chính [role="menuitem"] — đây là element clickable theo DOM Facebook
      }
    }

    // Chiến lược 2: Tìm qua <span dir="auto"> rồi leo lên menuitem
    const spans = Array.from(searchRoot.querySelectorAll('span[dir="auto"]'));
    for (const span of spans) {
      const txt = (span.innerText || span.textContent || '').trim().toLowerCase();
      if (txt.length > 30) continue;
      if (
        txt.includes('bỏ thích') || txt.includes('unlike') ||
        txt.includes('gỡ cảm xúc') || txt.includes('remove reaction')
      ) {
        // Leo ngược lên tìm [role="menuitem"] hoặc [tabindex]
        let p = span.parentElement;
        for (let j = 0; j < 8 && p && p !== document.body; j++) {
          if (p.getAttribute('role') === 'menuitem' || p.getAttribute('tabindex') === '0') {
            log(`🎯 [findUnlikeBtn] Tìm thấy qua span→leo lên menuitem, text="${txt}"`, 'info');
            return p;
          }
          p = p.parentElement;
        }
        log(`🎯 [findUnlikeBtn] Tìm thấy qua span text="${txt}" (không có menuitem cha, dùng span)`, 'warn');
        return span;
      }
    }

    return null;
  }

  /**
   * Chờ menu popup xuất hiện sau khi click nút 3 chấm
   * 
   * Facebook dùng Portal pattern: menu được append vào body (không nằm trong container bài).
   * Selector chính xác từ DOM thực tế: [role="menu"][aria-label*="lựa chọn"] 
   *   hoặc [role="menu"][aria-label*="quản lý hoạt động"]
   */
  async function waitForMenuPopup(maxWaitMs = 4000) {
    const stepMs = 150;
    const steps = Math.ceil(maxWaitMs / stepMs);

    for (let i = 0; i < steps; i++) {
      await sleep(stepMs);

      // Selector chính xác từ DOM thực tế: aria-label của Activity Log menu
      const exactMenu = document.querySelector(
        '[role="menu"][aria-label*="lựa chọn"], ' +
        '[role="menu"][aria-label*="quản lý hoạt động"], ' +
        '[role="menu"][aria-label*="manage"], ' +
        '[role="menu"][aria-label*="options for"]'
      );
      if (exactMenu) {
        log(`📋 [waitForMenu] Tìm thấy menu chính xác: aria-label="${(exactMenu.getAttribute('aria-label')||'').slice(0,40)}"`, 'info');
        return exactMenu;
      }

      // Fallback: bất kỳ [role="menu"] nào đang visible trên màn hình
      const allMenus = Array.from(document.querySelectorAll('[role="menu"]'));
      const visibleMenus = allMenus.filter(m => {
        const r = m.getBoundingClientRect();
        return r.width > 0 && r.height > 0; // menu phải có kích thước thực
      });
      if (visibleMenus.length > 0) {
        const chosen = visibleMenus[visibleMenus.length - 1];
        log(`📋 [waitForMenu] Tìm thấy menu fallback (${visibleMenus.length} menus visible)`, 'info');
        return chosen;
      }
    }

    log('⚠️ [waitForMenu] Timeout — không tìm thấy menu popup sau ' + maxWaitMs + 'ms', 'warn');
    return null;
  }

  try {
    // ── VÒNG LẶP KIỂM TRA RETRY (tối đa 3 lần) ──────────────────────────────
    for (let retryAttempt = 0; retryAttempt < 3; retryAttempt++) {
      if (retryAttempt > 0) {
        log(`🔁 [Unlike] Thử lại lần ${retryAttempt + 1}/3...`, 'warn');
        await sleep(getRandomDelay(800, 1200));
      }

      // BƯỚC 1: Click nút 3 chấm và chờ popup menu xuất hiện
      log(`🖱️ Đang mở menu 3 chấm (lần ${retryAttempt + 1})...`);
      simulateClick(btn);

      // BƯỚC 2: Chờ popup menu xuất hiện (tối đa 3s)
      const menuPopup = await waitForMenuPopup(3000);

      if (menuPopup) {
        log(`📋 Menu popup xuất hiện (role="${menuPopup.getAttribute('role') || 'unknown'}"). Đang tìm nút "Bỏ thích"...`);
        await sleep(200); // Đợi animation render xong

        // BƯỚC 3: Tìm "Bỏ thích" CHỈ TRONG menu popup (không quét toàn document)
        const unlikeBtn = findUnlikeBtnInMenu(menuPopup);

        if (unlikeBtn) {
          log(`✅ Tìm thấy nút "Bỏ thích" trong menu. Đang click...`);
          await sleep(getRandomDelay(300, 500));

          // Click đủ 3 cách để đảm bảo bắt handler React/SPA
          simulateClick(unlikeBtn);
          await sleep(150);
          try { unlikeBtn.click(); } catch(e) {}
          await sleep(150);
          unlikeBtn.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));

          // BƯỚC 4: Kiểm tra (verify) menu đã biến mất chưa → xác nhận unlike thành công
          await sleep(800);
          const menuGone = document.querySelectorAll('[role="menu"], [role="listbox"]').length === 0;

          if (menuGone) {
            log(`🎉 Unlike xác nhận thành công! Menu đã biến mất (lần thử ${retryAttempt + 1}).`, 'info');

            // Kiểm tra confirm dialog (nếu Facebook hiển thị thêm)
            await sleep(400);
            const confirmDialog = document.querySelector('div[role="dialog"][aria-modal], div[aria-modal="true"]');
            if (confirmDialog) {
              const confirmButtons = Array.from(confirmDialog.querySelectorAll('div[role="button"], button'));
              for (const cBtn of confirmButtons) {
                const cTxt = (cBtn.innerText || cBtn.textContent || '').trim().toLowerCase();
                if (cTxt.includes('bỏ thích') || cTxt.includes('gỡ') || cTxt.includes('xác nhận') || cTxt.includes('confirm') || cTxt.includes('unlike')) {
                  simulateClick(cBtn);
                  log('Đã xác nhận gỡ lượt thích trong hộp thoại.', 'info');
                  await sleep(getRandomDelay(600, 1000));
                  break;
                }
              }
            }
            return true;
          } else {
            log(`⚠️ Menu chưa biến mất sau click "Bỏ thích" (lần thử ${retryAttempt + 1}). Thử lại...`, 'warn');
            // Đóng menu hiện tại trước khi retry
            document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', code: 'Escape', keyCode: 27, bubbles: true }));
            await sleep(500);
          }
        } else {
          // Dump text trong menu để debug
          const menuTexts = Array.from(menuPopup.querySelectorAll('*'))
            .map(e => (e.innerText || '').trim())
            .filter(t => t.length > 0 && t.length < 40);
          const unique = [...new Set(menuTexts)];
          log(`[Debug Menu] Menu xuất hiện nhưng không thấy "Bỏ thích". Các mục: [${unique.join(' | ')}]`, 'warn');
          document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', code: 'Escape', keyCode: 27, bubbles: true }));
          await sleep(500);
        }
      } else {
        // Fallback: Không tìm thấy popup → thử search toàn document
        log(`⚠️ Không tìm thấy popup menu. Fallback search toàn trang...`, 'warn');
        const fallbackBtn = findUnlikeBtnInMenu(null);
        if (fallbackBtn) {
          simulateClick(fallbackBtn);
          await sleep(300);
          try { fallbackBtn.click(); } catch(e) {}
          await sleep(800);
          const menuGone = document.querySelectorAll('[role="menu"], [role="listbox"]').length === 0;
          if (menuGone) {
            log(`🎉 Unlike thành công qua fallback search!`, 'info');
            return true;
          }
        }
        log(`Không tìm thấy menu popup sau khi click 3 chấm (lần ${retryAttempt + 1}).`, 'warn');
        await sleep(500);
      }
    }

    log('❌ Unlike thất bại sau 3 lần thử.', 'warn');
    return false;

  } catch (e) {
    console.error('[FB-Downloader] Lỗi khi thao tác Unlike:', e);
    return false;
  }

}



// ── VÒNG LẶP CHÍNH (MAIN PROCESSOR - ANTI-BAN ENGINE) ─────────────────────────
async function runLoop() {
  log('Bắt đầu quét danh sách bài viết đã thích (Chế độ An Toàn Chống Ban)...');
  await loadProcessedHistory();
  startKeepAlive();

  sessionProcessedCount = 0;
  sessionUnlikedCount = 0;

  // ── BIẾN TRACKING CHO KIẾN TRÚC "SCROLL UNTIL DONE" ──
  let noNewCount = 0;           // Số lần liên tiếp DOM không tăng thêm bài mới
  const MAX_NO_NEW = 10;        // Ngưỡng dừng: 10 lần liên tiếp không tăng DOM
  let lastMenuBtnCount = 0;     // Số nút 3 chấm lần cuộn trước (để phát hiện DOM mới)
  let lastScrollHeight = 0;     // scrollHeight lần trước (để phát hiện hết trang)
  let consecutiveBottomCount = 0; // Số lần liên tiếp đã chạm đáy trang

  while (isRunning) {
    while (isPaused && isRunning) await sleep(1000);
    if (!isRunning) break;

    // Kiểm tra hạn mức phiên an toàn
    if (config.maxPerSession > 0 && sessionProcessedCount >= config.maxPerSession) {
      log(`🛑 [Hạn mức an toàn] Đã xử lý đủ ${sessionProcessedCount} bài trong phiên này. Tự động dừng để bảo vệ tài khoản Facebook!`, 'warn');
      break;
    }

    // 1. Quét DOM tươi mới nhất trên màn hình hiện tại (đã sắp xếp từ trên xuống dưới)
    const allRowsOnScreen = findActivityRows();

    // 2. Lọc danh sách các bài CHƯA XỬ LÝ (chưa có trong bộ nhớ đệm)
    const pendingRows = allRowsOnScreen.filter(r => {
      const id = extractRowId(r);
      return !processedIds.has(id) || (
        config.autoUnlike &&
        pendingUnlikeIds.has(id) &&
        !pendingUnlikeTriedThisSession.has(id)
      );
    });

    // 3. Nếu trên màn hình VẪN CÒN bài chưa xử lý: Xử lý ngay bài đầu tiên, KHÔNG CUỘN TRANG
    if (pendingRows.length > 0) {
      noNewCount = 0; // Reset số lần cuộn vì vẫn còn bài trên viewport
      consecutiveBottomCount = 0;
      const rowItem = pendingRows[0];
      const rowId = extractRowId(rowItem);

      log(`──────────────────────────────────────────────────`);
      log(`🔍 [Còn ${pendingRows.length} bài trên màn hình] Đang xử lý bài ID: ${rowId}...`);

      rowItem.container.scrollIntoView({ behavior: 'smooth', block: 'center' });
      await sleep(getRandomDelay(800, 1200));

      // A previous run already downloaded this video, but Facebook's menu did
      // not accept the Unlike click. Retry only the Unlike action once in this
      // session; never reopen the permalink or download the video again.
      if (pendingUnlikeIds.has(rowId)) {
        pendingUnlikeTriedThisSession.add(rowId);
        log(`🎬 Video ${rowId} was downloaded earlier; retrying Unlike only (no redownload).`);
        const retryUnlikeSuccess = await executeUnlike(rowItem);
        if (retryUnlikeSuccess) {
          await clearUnlikePending(rowId);
          sessionUnlikedCount++;
          log(`🎉 Retry Unlike succeeded for video ${rowId}.`, 'info');
          chrome.runtime.sendMessage({ action: 'UPDATE_STATS', unlikedCount: 1 }).catch(() => {});
          if (config.cooldownEvery > 0 && sessionUnlikedCount % config.cooldownEvery === 0) {
            await triggerCooldownBreak();
          }
        } else {
          log(`⚠️ Retry Unlike for video ${rowId} did not succeed; it remains queued for a later scan.`, 'warn');
        }
        const retryDelayMs = getRandomDelay(config.minDelayMs, config.maxDelayMs);
        await sleep(retryDelayMs);
        continue;
      }

      // Lấy nội dung text của bài viết
      const postText = extractPostTextFromRow(rowItem.container);
      const textLen = postText.length;

      log(`Nội dung trích xuất: "${postText.slice(0, 60)}..." (Tổng số ký tự: ${textLen})`);

      // ── ĐIỀU KIỆN 1: > 500 KÝ TỰ -> ĐỂ NGUYÊN HOÀN TOÀN ──
      if (textLen > config.charThreshold) {
        log(`🛡️ [ĐỂ NGUYÊN] Bài viết có ${textLen} ký tự (> ${config.charThreshold}) -> KHÔNG tải ảnh/video và KHÔNG hủy thích!`, 'warn');
        await markProcessed(rowId);
        sessionProcessedCount++;
        chrome.runtime.sendMessage({
          action: 'UPDATE_STATS',
          skippedCount: 1,
          processedCount: 1
        }).catch(() => {});

        await sleep(getRandomDelay(1200, 2000));
        continue; // Tiếp tục xử lý bài tiếp theo trên màn hình!
      }

      // ── ĐIỀU KIỆN 2: Lớp 1 <= config.charThreshold -> Mở tab ngầm kiểm tra Lớp 2 ──
      log(`🔎 [Lớp 1 đạt điều kiện] Activity Log có ${textLen} ký tự (<= ${config.charThreshold}) -> Mở bài viết để đếm ký tự thực tế & quét media...`);
      sessionProcessedCount++;

      // Tạo tiền tố tên file phẳng: Post_{YYYYMMDD}_{HHmm}_{ID}
      const datePrefix = new Date().toISOString().slice(0, 10).replace(/-/g, '');
      const timeStr = extractPostTime(rowItem.container);
      const postTimePrefix = timeStr ? `${datePrefix}_${timeStr}` : datePrefix;
      const shortId = rowId.toString().slice(-8);
      const fileBaseName = `Post_${postTimePrefix}_${shortId}`;

      // Mở tab ngầm extract media HD bài viết chính (tự đóng tab khi xong)
      const mediaData = await openAndExtractMedia(rowItem);

      // ── KIỂM TRA LỚP 2: NỘI DUNG VĂN BẢN ĐẦY ĐỦ TỪ TRANG CHI TIẾT BÀI VIẾT ──
      // Phòng trường hợp Facebook rút gọn văn bản trên Activity Log khiến Lớp 1 đếm nhầm
      const hasVerifiedPermalinkText = mediaData.textStatus === 'verified';
      const isReelHelperCandidate = mediaData.isVideoPost === true && /facebook\.com\/reel\//i.test(mediaData.sourceUrl || '');
      const isVerifiedVideoOnly = mediaData.isVideoPost === true && (mediaData.videos.length > 0 || isReelHelperCandidate);
      // Once the permalink extractor verifies the primary post body, it is the
      // sole source for the threshold.  Never let a longer Activity Log row
      // (which may include UI/comment text) replace it.
      const fullPostText = hasVerifiedPermalinkText ? mediaData.postText : postText;
      const fullTextLen = fullPostText.length;
      const hasSeeMore = /\b(?:xem thêm|see more|xem tiếp)\b/i.test(fullPostText);
      const hasEllipsis = /(?:\.{3}|…|&hellip;|&#x2026;)(?:\s*(?:xem thêm|see more|xem tiếp|nh[ưu]\.\.\.))?\s*$/i.test(fullPostText);
      const isLongPost = fullTextLen > config.charThreshold || mediaData.isTruncated === true || hasSeeMore || hasEllipsis;

      // ── BÁO CÁO ĐẾM KÝ TỰ RÕ RÀNG THEO YÊU CẦU NGƯỜI DÙNG ──
      log(`📊 [Lớp 2 - Đếm ký tự bài ID ${shortId}] Đã đếm: ${fullTextLen} ký tự | ${mediaData.images.length} ảnh | ${mediaData.videos.length} video (Ngưỡng giữ bài: > ${config.charThreshold} ký tự).`);
      if (fullPostText.length > 0) {
        log(`📝 Trích đoạn: "${fullPostText.slice(0, 80).replace(/\s+/g, ' ')}..."`);
      }

      // A short Activity Log snippet must never be enough to unlike.  If the
      // permalink page cannot identify the post's primary text, leave it
      // untouched; this prevents long/truncated posts from being unliked.
      if (!hasVerifiedPermalinkText && !isVerifiedVideoOnly) {
        log(`🛡️ [ĐỂ NGUYÊN - KHÔNG ĐỦ XÁC MINH] Bài ${rowId} không có nội dung bài gốc đã xác minh từ trang chi tiết -> KHÔNG tải và KHÔNG hủy thích.`, 'warn');
        await markProcessed(rowId);
        chrome.runtime.sendMessage({ action: 'UPDATE_STATS', skippedCount: 1, processedCount: 1 }).catch(() => {});
        await sleep(getRandomDelay(1200, 2000));
        continue;
      }

      // QUY TẮC BẢO VỆ TUYỆT ĐỐI: Nếu không trích xuất được gì (0 ký tự, 0 ảnh, 0 video)
      if (fullTextLen === 0 && mediaData.images.length === 0 && mediaData.videos.length === 0 && !isReelHelperCandidate) {
        log(`🛡️ [ĐỂ NGUYÊN - BẢO VỆ] Không trích xuất được nội dung bài ID ${rowId} (0 chữ, 0 media). Để bảo vệ bài viết của bạn, tiện ích KHÔNG tải và KHÔNG hủy thích!`, 'warn');
        await markProcessed(rowId);
        chrome.runtime.sendMessage({
          action: 'UPDATE_STATS',
          skippedCount: 1,
          processedCount: 1
        }).catch(() => {});
        await sleep(getRandomDelay(1200, 2000));
        continue;
      }

      if (isLongPost) {
        const reason = hasSeeMore
          ? `chứa nút rút gọn "Xem thêm" (đoạn trích ${fullTextLen} ký tự)`
          : (mediaData.isTruncated || hasEllipsis)
            ? `bị Facebook cắt ngắn (${fullTextLen} ký tự kèm dấu ...)`
            : `${fullTextLen} ký tự (> ${config.charThreshold} ký tự)`;
        log(`🛡️ [ĐỂ NGUYÊN - LỚP 2] Bài viết ID ${rowId} ${reason} -> KHÔNG tải media và KHÔNG hủy thích!`, 'warn');
        await markProcessed(rowId);
        chrome.runtime.sendMessage({
          action: 'UPDATE_STATS',
          skippedCount: 1,
          processedCount: 1
        }).catch(() => {});
        await sleep(getRandomDelay(1200, 2000));
        continue; // Bỏ qua an toàn sang bài tiếp theo!
      }

      log(`✅ [XÁC NHẬN BÀI NGẮN] Bài viết ID ${rowId} có ${fullTextLen} ký tự (<= ${config.charThreshold}) -> Đạt điều kiện tải media & Hủy Thích.`, 'info');

      let downloadedMediaCount = 0;
      // Video-only posts have no reliable text threshold.  They may only be
      // unliked after the downloader has positively confirmed a real file.
      let successfulVideoDownloadCount = 0;

      // Tải hình ảnh phẳng vào thư mục image/: Post_..._img_01.jpg
      if (config.downloadImages && mediaData.images.length > 0) {
        log(`📸 Tìm thấy ${mediaData.images.length} ảnh bài đăng chính. Đang tải vào image/...`);
        for (let i = 0; i < mediaData.images.length; i++) {
          const imgUrl = mediaData.images[i];

          // ── KIỂM TRA DEBUG MODE: SO SÁNH ẢNH MẪU LỖI ──
          const debugDecision = await checkSuspiciousImage(imgUrl, {
            postId: rowId,
            postUrl: mediaData.postUrl || '',
            charCount: fullTextLen,
            postText: fullPostText,
            sourceDetail: mediaData.sourceDetail || 'Bài viết chính',
            imgIndex: i + 1,
            totalImgs: mediaData.images.length
          });

          if (debugDecision === 'stop') {
            log('⏹ Dừng toàn bộ tiến trình theo quyết định của bạn từ hộp thoại Debug.', 'warn');
            isRunning = false;
            stopKeepAlive();
            chrome.runtime.sendMessage({ action: 'STATE_CHANGED', isRunning: false }).catch(() => {});
            return;
          }

          if (debugDecision === 'continue') {
            log(`⏭️ [Debug] Bỏ qua không tải ảnh #${i + 1} theo lựa chọn của người dùng.`, 'warn');
            continue;
          }

          const ext = imgUrl.includes('.png') ? 'png' : 'jpg';
          const filename = `${fileBaseName}_img_${String(i + 1).padStart(2, '0')}.${ext}`;
          
          chrome.runtime.sendMessage({
            action: 'DOWNLOAD_MEDIA',
            mediaType: 'image',
            url: imgUrl,
            filename,
            subFolder: ''
          });
          downloadedMediaCount++;
        }
      }

      // Tải video phẳng vào thư mục video/: Post_..._video_01.mp4
      if (config.downloadVideos && mediaData.videos.length > 0 && !isReelHelperCandidate) {
        log(`🎬 Tìm thấy ${mediaData.videos.length} video URL. Đang kiểm tra và tải...`);
        for (let i = 0; i < mediaData.videos.length; i++) {
          const vidUrl = mediaData.videos[i];

          // Kiểm tra loại file thật sự từ URL (tránh lưu JPEG nhầm thành .mp4)
          const isImageUrl = /\.(jpg|jpeg|png|webp)(\?|$)/i.test(vidUrl);
          const isM3u8Url = /\.m3u8(\?|$)/i.test(vidUrl);

          if (isImageUrl) {
            // URL là ảnh (poster Reel) → route về image/ với đuôi đúng
            const imgExt = (vidUrl.match(/\.(jpg|jpeg|png|webp)/i) || ['', 'jpg'])[0].replace('.', '');
            const imgFilename = `${fileBaseName}_reel_thumb_${String(i + 1).padStart(2, '0')}.${imgExt}`;
            log(`🖼️ Video URL #${i + 1} thực ra là ảnh (poster/thumbnail). Lưu vào image/ thay vì video/.`);
            chrome.runtime.sendMessage({
              action: 'DOWNLOAD_MEDIA',
              mediaType: 'image',
              url: vidUrl,
              filename: imgFilename,
              subFolder: ''
            });
            downloadedMediaCount++;
            continue;
          }

          if (isM3u8Url) {
            // M3U8 manifest — không tải được trực tiếp thành file, bỏ qua
            log(`⚠️ Video URL #${i + 1} là HLS manifest (.m3u8) — bỏ qua (không tải được bằng extension).`, 'warn');
            continue;
          }

          if (!/\.mp4(?:\?|$)/i.test(vidUrl)) {
            log(`⚠️ Video URL #${i + 1} không phải MP4 trực tiếp — bỏ qua để tránh file lỗi.`, 'warn');
            continue;
          }

          // URL .mp4 hợp lệ → tải bình thường
          const filename = `${fileBaseName}_video_${String(i + 1).padStart(2, '0')}.mp4`;
          log(`🎬 Đang tải video #${i + 1}: ${vidUrl.slice(0, 60)}...`);
          const downloadResult = await chrome.runtime.sendMessage({
            action: 'DOWNLOAD_MEDIA',
            mediaType: 'video',
            url: vidUrl,
            filename,
            subFolder: ''
          }).catch(error => ({ success: false, error: error.message }));
          if (downloadResult && downloadResult.success) {
            downloadedMediaCount++;
            successfulVideoDownloadCount++;
          } else {
            log(`⚠️ Không tải video #${i + 1}: ${downloadResult?.error || 'không xác minh được MP4 hoàn chỉnh'}`, 'warn');
          }
        }
      }

      // Facebook Reels commonly expose only DASH fragments. Route the original
      // permalink to the local yt-dlp + FFmpeg helper instead of downloading a
      // fragment as .mp4. A failed helper download deliberately keeps the Like.
      if (config.downloadVideos && isReelHelperCandidate) {
        const reelFilename = `${fileBaseName}_video_01.mp4`;
        log('🎬 Reel DASH detected. Sending permalink to local FFmpeg helper...');
        const helperResult = await chrome.runtime.sendMessage({
          action: 'DOWNLOAD_REEL_WITH_HELPER',
          sourceUrl: mediaData.sourceUrl,
          filename: reelFilename
        }).catch(error => ({ success: false, error: error.message }));
        if (helperResult && helperResult.success) {
          downloadedMediaCount++;
          successfulVideoDownloadCount++;
          log(`✅ Reel downloaded and muxed as MP4: ${helperResult.path}`);
        } else {
          log(`⚠️ Reel was not downloaded; keeping Like. ${helperResult?.error || 'Local helper failed.'}`, 'warn');
        }
      }


      // Lưu file thông tin bài viết vào post_info/: Post_..._info.txt
      if (config.savePostInfo) {
        const infoContent = `BÀI VIẾT ĐÃ THÍCH TRÊN FACEBOOK
ID: ${rowId}
Thời gian đăng: ${timeStr ? `${timeStr.slice(0, 2)}:${timeStr.slice(2)}` : 'N/A'}
Thời gian quét: ${new Date().toLocaleString('vi-VN')}
Số ký tự: ${fullTextLen} (<= ${config.charThreshold} ký tự)
Số ảnh: ${mediaData.images.length}
Số video: ${mediaData.videos.length}

--- NỘI DUNG VĂN BẢN ---
${fullPostText}
`;
        chrome.runtime.sendMessage({
          action: 'SAVE_POST_INFO',
          filename: `${fileBaseName}_info.txt`,
          subFolder: '',
          postInfoText: infoContent
        });
      }

      chrome.runtime.sendMessage({
        action: 'UPDATE_STATS',
        downloadCount: downloadedMediaCount,
        processedCount: 1
      }).catch(() => {});

      // Thực hiện Hủy Thích (Unlike).  A caption-less, video-only post is an
      // exception: it can unlike only after a download was confirmed above.
      const canUnlikeAfterVideoDownload = isVerifiedVideoOnly && successfulVideoDownloadCount > 0;
      if (config.autoUnlike && (hasVerifiedPermalinkText || canUnlikeAfterVideoDownload)) {
        if (canUnlikeAfterVideoDownload && !hasVerifiedPermalinkText) {
          log('🎬 Video-only post downloaded successfully -> proceeding to Unlike.');
        }
        // CHỐT CHẶN AN TOÀN TUYỆT ĐỐI TRƯỚC KHI UNLIKE:
        if (fullTextLen > config.charThreshold || mediaData.isTruncated === true || hasSeeMore || hasEllipsis) {
          log(`🛡️ [CHẶN HỦY THÍCH AN TOÀN] Bài viết ${rowId} là bài viết dài/bị rút gọn -> TUYỆT ĐỐI KHÔNG HỦY THÍCH!`, 'warn');
          await markProcessed(rowId);
          continue;
        }

        log(`Đang thao tác Hủy Thích (Unlike) an toàn cho bài ${rowId}...`);
        const unlikeSuccess = await executeUnlike(rowItem);
        if (unlikeSuccess) {
          await clearUnlikePending(rowId);
          sessionUnlikedCount++;
          log(`🎉 Đã hủy thích thành công bài viết ${rowId}! (Tổng phiên: ${sessionUnlikedCount} bài)`, 'info');
          chrome.runtime.sendMessage({
            action: 'UPDATE_STATS',
            unlikedCount: 1
          }).catch(() => {});

          // Kiểm tra Cooldown Break sau mỗi N bài unlike
          if (config.cooldownEvery > 0 && sessionUnlikedCount % config.cooldownEvery === 0) {
            await triggerCooldownBreak();
          }
        } else if (canUnlikeAfterVideoDownload) {
          await markUnlikePending(rowId);
          pendingUnlikeTriedThisSession.add(rowId);
          log(`⚠️ Video downloaded but Unlike failed. Queued ${rowId} for a later Unlike-only retry; the video will not download again.`, 'warn');
        }
      } else if (config.autoUnlike && isVerifiedVideoOnly) {
        log(`🛡️ [GIỮ LIKE] Video-only post has no successful download yet, so it cannot Unlike.`, 'warn');
      }

      // Đánh dấu đã xử lý bài này vào bộ nhớ đệm
      await markProcessed(rowId);

      // Jitter delay an toàn giữa các bài
      const delayMs = getRandomDelay(config.minDelayMs, config.maxDelayMs);
      log(`⏳ Nghỉ an toàn ${Math.round(delayMs / 100) / 10}s trước bài tiếp theo trên màn hình...`);
      await sleep(delayMs);

      // TIẾP TỤC VÒNG LẶP ĐỂ XỬ LÝ BÀI KẾ TIẾP TRÊN MÀN HÌNH (KHÔNG CUỘN!)
      continue;
    }

    // ─────────────────────────────────────────────────────────────────────────
    // 4. KHÔNG CÒN BÀI NÀO CHƯA XỬ LÝ TRÊN VIEWPORT → CUỘN TÌM BÀI MỚI HƠN
    // Kiến trúc "Scroll Until Done":
    //   - Đo số nút 3 chấm TRƯỚC khi cuộn (lastMenuBtnCount)
    //   - Cuộn tự nhiên + chờ DOM render
    //   - Đo lại SAU khi cuộn (currentMenuBtnCount)
    //   - Nếu tăng → Facebook đã nạp thêm bài → reset noNewCount
    //   - Nếu đã cuối trang VÀ noNewCount >= MAX_NO_NEW → mới dừng
    // ─────────────────────────────────────────────────────────────────────────

    // Đo trạng thái DOM trước khi cuộn
    const menuBtnsBefore = document.querySelectorAll(
      '[aria-label*="Lựa chọn khác"], [aria-label*="More options"], [aria-haspopup="dialog"][aria-label]'
    ).length;
    const scrollHeightBefore = document.body.scrollHeight;
    const scrollPosBefore = window.scrollY + window.innerHeight;

    noNewCount++;
    log(`📜 [Cuộn ${noNewCount}/${MAX_NO_NEW}] Trên màn hình hết bài chưa xử lý (tìm thấy ${allRowsOnScreen.length} bài tổng, tất cả đã trong cache). Đang cuộn tìm bài mới hơn...`);

    // Cuộn xuống đủ để Facebook lazy-load thêm bài
    await naturalSmoothScroll(getRandomDelay(500, 800));
    // Chờ đủ lâu để Facebook render DOM mới (tăng từ 3-4.5s → 4-6s)
    await sleep(getRandomDelay(4000, 6000));

    // Đo trạng thái DOM SAU khi cuộn
    const menuBtnsAfter = document.querySelectorAll(
      '[aria-label*="Lựa chọn khác"], [aria-label*="More options"], [aria-haspopup="dialog"][aria-label]'
    ).length;
    const scrollHeightAfter = document.body.scrollHeight;
    const isAtBottom = (window.scrollY + window.innerHeight) >= (scrollHeightAfter - 300);

    log(`📊 [DOM Check] Nút 3 chấm: ${menuBtnsBefore} → ${menuBtnsAfter} | scrollHeight: ${scrollHeightBefore} → ${scrollHeightAfter} | Cuối trang: ${isAtBottom ? '✅' : '❌'}`);

    // Nếu DOM tăng thêm bài → Reset noNewCount (Facebook đang lazy-load tiếp)
    if (menuBtnsAfter > menuBtnsBefore || scrollHeightAfter > scrollHeightBefore + 100) {
      log(`🆕 DOM tăng thêm nội dung (nút: ${menuBtnsBefore}→${menuBtnsAfter}, height: ${scrollHeightBefore}→${scrollHeightAfter}). Reset bộ đếm cuộn → tiếp tục quét...`, 'info');
      noNewCount = 0;
      lastMenuBtnCount = menuBtnsAfter;
      lastScrollHeight = scrollHeightAfter;
      consecutiveBottomCount = 0;
      continue; // Quét lại DOM ngay lập tức sau khi có nội dung mới
    }

    // Cập nhật tracking
    lastMenuBtnCount = menuBtnsAfter;
    lastScrollHeight = scrollHeightAfter;

    // Nếu đã chạm đáy trang → tăng bộ đếm đáy
    if (isAtBottom) {
      consecutiveBottomCount++;
      log(`📍 [Đáy trang] Đã chạm đáy trang (lần ${consecutiveBottomCount}). noNewCount=${noNewCount}/${MAX_NO_NEW}`, 'warn');
    }

    // ── ĐIỀU KIỆN DỪNG AN TOÀN (phải thỏa CẢ HAI điều kiện) ──
    // 1. Đã cuộn nhiều lần mà DOM không tăng (noNewCount >= MAX_NO_NEW)
    // 2. ĐÃ THỰC SỰ CHẠM ĐÁY TRANG (consecutiveBottomCount >= 2) HOẶC noNewCount quá lớn
    const isDefinitelyDone = (isAtBottom && consecutiveBottomCount >= 2 && noNewCount >= Math.ceil(MAX_NO_NEW / 2))
                          || (noNewCount >= MAX_NO_NEW);

    if (isDefinitelyDone) {
      if (isAtBottom) {
        log(`🏁 Đã xác nhận hết trang: cuộn ${noNewCount} lần, chạm đáy ${consecutiveBottomCount} lần. Kết thúc phiên an toàn.`, 'warn');
      } else {
        log(`🏁 Đã cuộn ${noNewCount} lần liên tiếp nhưng không còn bài viết mới nào. Kết thúc phiên an toàn.`, 'warn');
      }
      break;
    }

    // Chỉ tiếp tục cuộn - vòng while sẽ tiếp tục ở trên
  }


  isRunning = false;
  stopKeepAlive();
  log(`🏁 Đã kết thúc phiên quét. Tổng duyệt: ${sessionProcessedCount} bài (Unlike: ${sessionUnlikedCount} bài).`);
  chrome.runtime.sendMessage({ action: 'STATE_CHANGED', isRunning: false }).catch(() => {});
}

// ── LẮNG NGHE LỆNH TỪ POPUP ──────────────────────────────────────────────────
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'START') {
    if (!isRunning) {
      isRunning = true;
      isPaused = false;
      if (request.config) {
        config = { ...config, ...request.config };
      }
      runLoop();
      sendResponse({ status: 'started' });
    } else if (isPaused) {
      isPaused = false;
      sendResponse({ status: 'resumed' });
    }
    return true;
  }

  if (request.action === 'PAUSE') {
    isPaused = true;
    log('Đã tạm dừng theo lệnh người dùng.');
    sendResponse({ status: 'paused' });
    return true;
  }

  if (request.action === 'STOP') {
    isRunning = false;
    isPaused = false;
    stopKeepAlive();
    log('Đã nhận lệnh dừng hoàn toàn.');
    sendResponse({ status: 'stopped' });
    return true;
  }

  if (request.action === 'DEBUG_DECISION') {
    if (suspiciousUserDecisionResolver) {
      const resolver = suspiciousUserDecisionResolver;
      suspiciousUserDecisionResolver = null;
      resolver(request.decision);
    }
    sendResponse({ success: true });
    return true;
  }

  if (request.action === 'GET_STATUS') {
    sendResponse({
      isRunning,
      isPaused,
      isCoolingDown,
      sessionProcessedCount,
      sessionUnlikedCount,
      processedCount: processedIds.size,
      config
    });
    return true;
  }

  // Tính năng TEST_SCAN để kiểm tra xem trên trang hiện tại tìm thấy bao nhiêu dòng
  if (request.action === 'TEST_SCAN') {
    const rows = findActivityRows();
    const samples = rows.slice(0, 3).map((r, i) => {
      const text = extractPostTextFromRow(r.container);
      return {
        index: i + 1,
        hasActionBtn: !!r.actionBtn,
        textSnippet: text.slice(0, 60),
        charCount: text.length,
        source: r.source || 'unknown'
      };
    });
    // Debug info khi không tìm thấy gì
    let debugInfo = '';
    if (rows.length === 0) {
      const viewBtnCount = document.querySelectorAll('div[role="button"], button').length;
      const menuBtnCount = document.querySelectorAll('[aria-haspopup="menu"]').length;
      const pageTitle = document.title;
      debugInfo = `Trang: "${pageTitle}" | Nút button: ${viewBtnCount} | Menu btn: ${menuBtnCount} | URL: ${location.href.slice(0, 80)}`;
    }
    sendResponse({
      rowCount: rows.length,
      samples,
      debugInfo
    });
    return true;
  }


  // DEBUG_SCAN: Dump DOM thuc te de chan doan selector
  if (request.action === 'DEBUG_SCAN') {
    const debug = {};
    debug.url = location.href.slice(0, 120);
    debug.title = document.title;
    const allBtns = Array.from(document.querySelectorAll('div[role="button"], button, a[role="button"], span[role="button"]'));
    debug.buttonTexts = [...new Set(allBtns.map(b => (b.innerText||'').trim()).filter(t => t.length > 0 && t.length <= 25))].slice(0, 40);
    debug.totalButtons = allBtns.length;
    const menuBtns = Array.from(document.querySelectorAll('[aria-haspopup]'));
    debug.ariaHaspopup = menuBtns.slice(0, 8).map(b => ({
      tag: b.tagName, haspopup: b.getAttribute('aria-haspopup'),
      label: (b.getAttribute('aria-label') || '').slice(0,30),
      text: (b.innerText||'').trim().slice(0,30),
      top: Math.round(b.getBoundingClientRect().top)
    }));
    debug.totalAriaHaspopup = menuBtns.length;
    const thichNodes = [];
    const wlkr = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let nd;
    while ((nd = wlkr.nextNode()) && thichNodes.length < 10) {
      const t = (nd.textContent||'').toLowerCase().trim();
      if (t.includes('thích') && t.length < 100) thichNodes.push(t);
    }
    debug.thichTextNodes = [...new Set(thichNodes)];
    debug.testIds = [...new Set(Array.from(document.querySelectorAll('[data-testid]')).map(e => e.getAttribute('data-testid')).filter(Boolean))].slice(0,15);
    debug.pagelets = [...new Set(Array.from(document.querySelectorAll('[data-pagelet]')).map(e => e.getAttribute('data-pagelet')).filter(Boolean))].slice(0,10);
    debug.listItems = document.querySelectorAll('[role="listitem"]').length;
    debug.feedItems = document.querySelectorAll('[role="feed"] > *').length;
    debug.activityLinks = Array.from(document.querySelectorAll('a[href]'))
      .map(a => a.href).filter(h => h.includes('permalink') || h.includes('story_fbid') || h.includes('/posts/')).slice(0, 5);
    debug.totalImgs = document.querySelectorAll('img').length;
    sendResponse({ debug });
    return true;
  }


  // DEBUG_SCAN: Dump DOM thuc te de chan doan selector
  if (request.action === 'DEBUG_SCAN') {
    const debug = {};
    debug.url = location.href.slice(0, 120);
    debug.title = document.title;
    const allBtns = Array.from(document.querySelectorAll('div[role="button"], button, a[role="button"], span[role="button"]'));
    debug.buttonTexts = [...new Set(allBtns.map(b => (b.innerText||'').trim()).filter(t => t.length > 0 && t.length <= 25))].slice(0, 40);
    debug.totalButtons = allBtns.length;
    const menuBtns = Array.from(document.querySelectorAll('[aria-haspopup]'));
    debug.ariaHaspopup = menuBtns.slice(0, 8).map(b => ({
      tag: b.tagName, haspopup: b.getAttribute('aria-haspopup'),
      label: (b.getAttribute('aria-label') || '').slice(0,30),
      text: (b.innerText||'').trim().slice(0,30),
      top: Math.round(b.getBoundingClientRect().top)
    }));
    debug.totalAriaHaspopup = menuBtns.length;
    const thichNodes = [];
    const wlkr = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let nd;
    while ((nd = wlkr.nextNode()) && thichNodes.length < 10) {
      const t = (nd.textContent||'').toLowerCase().trim();
      if (t.includes('thích') && t.length < 100) thichNodes.push(t);
    }
    debug.thichTextNodes = [...new Set(thichNodes)];
    debug.testIds = [...new Set(Array.from(document.querySelectorAll('[data-testid]')).map(e => e.getAttribute('data-testid')).filter(Boolean))].slice(0,15);
    debug.pagelets = [...new Set(Array.from(document.querySelectorAll('[data-pagelet]')).map(e => e.getAttribute('data-pagelet')).filter(Boolean))].slice(0,10);
    debug.listItems = document.querySelectorAll('[role="listitem"]').length;
    debug.feedItems = document.querySelectorAll('[role="feed"] > *').length;
    debug.activityLinks = Array.from(document.querySelectorAll('a[href]'))
      .map(a => a.href).filter(h => h.includes('permalink') || h.includes('story_fbid') || h.includes('/posts/')).slice(0, 5);
    debug.totalImgs = document.querySelectorAll('img').length;
    sendResponse({ debug });
    return true;
  }

  if (request.action === 'CLEAR_CACHE') {
    processedIds.clear();
    chrome.storage.local.remove(['fb_processed_cache', 'fb_stats'], () => {
      log('Đã xóa sạch bộ nhớ đệm và thống kê.');
      sendResponse({ status: 'cleared' });
    });
    return true;
  }
});
