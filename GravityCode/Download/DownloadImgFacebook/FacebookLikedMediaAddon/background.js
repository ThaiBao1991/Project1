/**
 * Background Service Worker — Facebook Liked Media Downloader & Auto-Unlike
 * 
 * Chức năng:
 * 1. Quản lý download file, tổ chức thư mục riêng biệt (image / video / post_info)
 * 2. Tab Watcher: Theo dõi tab mới từ permalink FB, extract media HD, gửi kết quả về
 */

// ── BỘ NHỚ ĐỆM ─────────────────────────────────────────────────────────────
const downloadFolderMap = new Map();

// Theo dõi các tab đang chờ extract media
// key: tabId, value: { resolve, parentTabId, timeout }
const pendingTabExtractions = new Map();

// ── webRequest diagnostics only ──────────────────────────────────────────────
// CDN playback requests include DASH init/index/media fragments.  They are kept
// for diagnosis only and must never become download candidates.
const capturedVideoUrls = new Map();

// Tracks successful video download requests so their state can be diagnosed
// without throwing after chrome.downloads.download has already started.
const videoDownloadTracker = new Map();

function isStreamingFragmentUrl(value) {
  const url = String(value || '').toLowerCase();
  return (
    url.includes('.m3u8') ||
    url.includes('dash') ||
    url.includes('byterange') ||
    url.includes('byte_start') ||
    url.includes('byteend') ||
    /[_/]seg[-_]?\d+/.test(url) ||
    /[_/]chunk[-_]?\d+/.test(url) ||
    /[_/]frag[-_]?\d+/.test(url) ||
    url.includes('/init-')
  );
}

function isCompleteMp4Header(bytes) {
  if (!bytes || bytes.length < 16) return false;
  const ascii = new TextDecoder('latin1').decode(bytes.slice(0, Math.min(bytes.length, 128))).toLowerCase();
  // A playable MP4 begins with an ftyp atom. DASH/CMAF fragments begin with
  // moof/sidx or advertise dash/cmfc brands; Chrome saved these fragments as
  // separate .mp4 files, which is exactly the corruption we must prevent.
  if (ascii.slice(4, 8) !== 'ftyp') return false;
  return !ascii.includes('dash') && !ascii.includes('cmfc') && !ascii.includes('moof') && !ascii.includes('sidx');
}

/**
 * Lắng nghe mọi request từ các tab nền đang chờ extract.
 * Nếu request là URL video .mp4 từ CDN fbcdn.net → lưu vào capturedVideoUrls.
 * Ưu tiên URL có chất lượng cao nhất (hd > sd > thumbnail).
 */
chrome.webRequest.onBeforeRequest.addListener(
  (details) => {
    const { tabId, url } = details;
    if (!pendingTabExtractions.has(tabId)) return;
    if (!url) return;

    // Chỉ bắt URL video .mp4 THẬT từ CDN Facebook (không phải thumbnail hay segment)
    const isVideoMp4 = /\.mp4(\?|$)/i.test(url) && (
      url.includes('fbcdn.net') || url.includes('facebook.com/video')
    );
    const isVideoM3u8 = /\.m3u8(\?|$)/i.test(url) && url.includes('fbcdn.net');

    if (!isVideoMp4 && !isVideoM3u8) return;

    // ❗ LỌC Bỏ HLS SEGMENT: Không phải file video hoàn chỉnh
    // HLS segment có dấu hiệu: seg_X, chunk, index, init-, _dashinit, frag, /seg/
    if (
      /[_\/]seg[-_]?\d+/i.test(url) ||
      /[_\/]chunk[-_]?\d+/i.test(url) ||
      /[_\/]frag[-_]?\d+/i.test(url) ||
      url.includes('_dashinit') ||
      url.includes('/init-') ||
      url.includes('_b.mp4') ||
      url.includes('preview') ||
      // Loại bỏ các đoạn ngắn (URLs có byterange param là HLS segment)
      url.includes('byterange') ||
      url.includes('byte_start')
    ) return;

    if (!capturedVideoUrls.has(tabId)) {
      capturedVideoUrls.set(tabId, []);
    }
    const existing = capturedVideoUrls.get(tabId);
    if (!existing.includes(url)) {
      existing.push(url);
      console.log('[BG webRequest] Bắt được URL video:', url.slice(0, 100));
    }
  },
  { urls: ['*://*.fbcdn.net/*', '*://*.facebook.com/*'] }
);

// ── TAB WATCHER: Theo dõi tab permalink mở từ Activity Log ────────────────────
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  // Chỉ xử lý khi tab đã load xong và đang chờ extract
  if (changeInfo.status !== 'complete') return;
  if (!pendingTabExtractions.has(tabId)) return;
  if (!tab.url || !tab.url.includes('facebook.com')) return;

  const pending = pendingTabExtractions.get(tabId);

  // Đợi 2.5s để Facebook SPA render các ảnh và bài viết đầy đủ trong DOM (đặc biệt khi tab chạy nền)
  setTimeout(() => {
    chrome.scripting.executeScript({
      target: { tabId },
      func: extractMediaFromPermalinkPage
    }).then(results => {
      const result = results && results[0] && results[0].result;
      if (result) {
        // Do not use network playback requests as downloadable files. Facebook
        // streams a Reel as many DASH fragments and each fragment may end in
        // ".mp4" even though it cannot play by itself.
        const webReqVideos = capturedVideoUrls.get(tabId) || [];
        const allVideos = result.videos || [];
        const dedupedVideos = [];
        for (const v of allVideos) {
          if (!dedupedVideos.includes(v)) dedupedVideos.push(v);
        }
        // Ưu tiên URL .mp4 trực tiếp hơn .m3u8 manifest
        const mp4Videos = dedupedVideos.filter(v => /\.mp4(?:\?|$)/i.test(v) && !isStreamingFragmentUrl(v));
        const otherVideos = dedupedVideos.filter(v => !/\.mp4/i.test(v));
        const finalVideos = mp4Videos.length > 0 ? mp4Videos : otherVideos.filter(v => !isStreamingFragmentUrl(v));

        if (webReqVideos.length > 0) {
          console.log(`[BG TabWatcher] Bỏ qua ${webReqVideos.length} request phát video dạng stream cho tab ${tabId}`);
        }
        capturedVideoUrls.delete(tabId); // Dọn dẹp

        // Gửi kết quả về content_script gốc ở Activity Log
        // A Reel page preloads neighbouring recommendations.  The first MP4
        // observed is the active Reel playback request; never queue every
        // preload as if it belonged to the current post.
        const selectedVideos = result.isVideoPost ? finalVideos.slice(0, 1) : finalVideos;

        chrome.tabs.sendMessage(pending.parentTabId, {
          action: 'PERMALINK_MEDIA_RESULT',
          tabId,
          images: result.images || [],
          videos: selectedVideos,
          postText: result.postText || '',
          isTruncated: !!result.isTruncated,
          textStatus: result.textStatus || 'unverified',
          isVideoPost: !!result.isVideoPost,
          sourceUrl: pending.url || tab.url
        }).catch(() => {});
      }
    }).catch(err => {
      console.warn('[BG TabWatcher] Lỗi inject extractor:', err.message);
      chrome.tabs.sendMessage(pending.parentTabId, {
        action: 'PERMALINK_MEDIA_RESULT',
        tabId,
        images: [],
        videos: [],
        postText: '',
        isTruncated: false,
        textStatus: 'unverified',
        isVideoPost: false,
        sourceUrl: pending.url || tab.url
      }).catch(() => {});
    }).finally(() => {
      // Dọn dẹp: đóng tab ngầm và xóa khỏi pending map
      clearTimeout(pending.timeout);
      pendingTabExtractions.delete(tabId);
      setTimeout(() => {
        chrome.tabs.remove(tabId).catch(() => {});
      }, 1000);
    });
  }, 2500);
});

/**
 * Hàm này được inject vào trang permalink để trích xuất media.
 * QUAN TRỌNG: Chỉ lấy ảnh/video của BÀI VIẾT CHÍNH, loại bỏ 100% ảnh comment.
 */
function extractMediaFromPermalinkPage() {
  // Only a primary-post selector may authorize downloading or unliking.
  // Activity Log text and generic DOM text are merely diagnostic fallbacks.
  const result = { images: [], videos: [], postText: '', isTruncated: false, textStatus: 'unverified', isVideoPost: false };

  try {
    // 0. Xác định phạm vi vùng bài viết chính (loại trừ hoàn toàn thanh bên phải, thanh điều hướng trái và header)
    const mainArea = document.querySelector('div[role="main"]') || document.body;
    // Facebook opens many post permalinks inside a dialog.  The dialog whose
    // heading starts with "Bài viết của" is the primary post surface; using
    // role=main here would include feed/reel recommendations and comments.
    const postDialog = Array.from(document.querySelectorAll('[role="dialog"]'))
      .filter(dialog => /bài viết của|post by/i.test(dialog.innerText || ''))
      .sort((a, b) => (b.innerText || '').length - (a.innerText || '').length)[0];
    const postArticle = postDialog || mainArea.querySelector('div[role="article"]') || mainArea;

    // Nhận diện bài viết Video để tránh nhầm lẫn poster thumbnail thành ảnh chụp
    const ogTypeEl = document.querySelector('meta[property="og:type"]');
    const ogType = (ogTypeEl ? ogTypeEl.getAttribute('content') || '' : '').toLowerCase();
    const isVideoType = ogType.includes('video');
    const isVideoUrl = /\/(videos|watch|reel|share\/r)\b/i.test(window.location.pathname);
    // Chỉ coi là Video nếu og:type là video hoặc URL là video/watch/reel (tránh nhầm thẻ video quảng cáo trên mainArea)
    const isVideoPost = isVideoType || isVideoUrl;
    result.isVideoPost = isVideoPost;

    // 1. Tìm thanh tương tác Thích / Bình luận / Chia sẻ trong bài viết để phân định ranh giới
    // Mọi nội dung bên dưới thanh này là khu vực bình luận
    let boundaryTop = Infinity;
    const clickables = Array.from((postArticle || mainArea).querySelectorAll('div[role="button"], span[role="button"], div[role="toolbar"]'));
    for (const b of clickables) {
      const t = (b.innerText || b.textContent || '').trim().toLowerCase();
      if (t === 'thích' || t === 'bình luận' || t === 'chia sẻ' || t === 'like' || t === 'comment' || t === 'share') {
        const rect = b.getBoundingClientRect();
        if (rect.top > 150 && rect.top < boundaryTop) {
          boundaryTop = rect.top;
        }
      }
    }

    // The comment sorter is a dependable boundary in Facebook's post dialog
    // even when Like/Comment/Share buttons have no text in the current locale.
    const commentBoundary = Array.from((postArticle || mainArea).querySelectorAll('div, span, h2, h3'))
      .map(el => ({ el, text: (el.innerText || el.textContent || '').trim().toLowerCase() }))
      .find(({ text }) => /^(phù hợp nhất|most relevant|all comments|bình luận|comments)$/.test(text));
    if (commentBoundary) {
      const top = commentBoundary.el.getBoundingClientRect().top;
      if (top > 100) boundaryTop = Math.min(boundaryTop, top);
    }

    // 2. Photo posts only.  A Reel page renders recommendation thumbnails in
    // the same surface, so a video post must never enter the image pipeline.
    const imgs = isVideoPost ? [] : Array.from((postArticle || mainArea).querySelectorAll('img'));
    imgs.forEach(img => {
      const src = img.currentSrc || img.src || '';
      if (!src) return;

      // BỎ LỌC 0 (QUAN TRỌNG): Loại trừ 100% ảnh thanh bên gợi ý, tin đề xuất, bảng tin ngoài lề, header, chat
      const isOutsidePost = img.closest(
        '[role="complementary"], [role="navigation"], [role="banner"], [data-pagelet*="RightRail"], ' +
        '[data-pagelet*="SideFeed"], [aria-label*="gợi ý" i], [aria-label*="đề xuất" i], ' +
        '[aria-label*="suggested" i], [aria-label*="stories" i], [aria-label*="người liên hệ" i], ' +
        '[aria-label*="contacts" i], [aria-label*="watch" i]'
      );
      if (isOutsidePost) return;

      // Bắt buộc ảnh phải nằm trong role="main" hoặc role="dialog" nếu trang có role="main"
      if (document.querySelector('div[role="main"]') && !img.closest('div[role="main"], div[role="dialog"]')) {
        return;
      }

      // Bỏ qua ảnh hệ thống, static, emoji
      if (src.includes('/rsrc.php') || src.includes('emoji') || src.includes('static.xx')) return;

      // Chỉ nhận ảnh từ CDN Facebook
      if (!src.includes('scontent') && !src.includes('fbcdn.net')) return;

      // BỘ LỌC 1: Nếu nằm dưới thanh tương tác -> là COMMENT -> LOẠI BỎ (chỉ áp dụng khi boundaryTop > 150)
      const rect = img.getBoundingClientRect();
      if (boundaryTop !== Infinity && boundaryTop > 150 && rect.top >= boundaryTop) {
        return;
      }

      // In a dialog, role=article descendants are comment/reply cards.  The
      // primary post media itself is outside these cards.
      const owningArticle = img.closest('[role="article"]');
      if (owningArticle && owningArticle !== postArticle) return;

      // BỘ LỌC 2: Kiểm tra phần tử cha có thuộc khu vực comment/reply không
      const isCommentSection = img.closest(
        '[aria-label*="Bình luận"], [aria-label*="Comment"], [aria-label*="bình luận"], ' +
        '[aria-label*="Trả lời"], [aria-label*="Reply"], [data-visualcompletion="ignore-dynamic"], ' +
        'ul[role="list"], div[role="article"][aria-label*="Bình luận"], div[role="article"][aria-label*="Comment"]'
      );
      if (isCommentSection) return;

      // BỘ LỌC 3: Loại bỏ sticker, nhãn dán hoạt hình, emoji, avatar
      const alt = (img.alt || '').toLowerCase();
      if (alt.includes('nhãn dán') || alt.includes('sticker') || alt.includes('biểu tượng') || alt.includes('icon') ||
          alt.includes('ảnh đại diện') || alt.includes('profile picture') || alt.includes('avatar')) {
        return;
      }

      // BỘ LỌC 4: Kích thước hiển thị (ảnh bài đăng chính thường >= 150px)
      const w = img.naturalWidth || rect.width;
      const h = img.naturalHeight || rect.height;
      // 150px is Facebook's common avatar/reaction preview size.  Post media
      // must be larger than that in both dimensions.
      if (w <= 150 || h <= 150) return;

      // BỘ LỌC 5: Loại bỏ ảnh thumbnail từ link preview bên ngoài Facebook
      const parentLink = img.closest('a[href]');
      if (parentLink) {
        const href = (parentLink.href || parentLink.getAttribute('href') || '');
        if (href.includes('l.facebook.com/l.php') || href.includes('l.fb.me')) {
          return; // Thumbnail của link ngoài được share trong bài
        }
        if (href.startsWith('http') &&
            !href.includes('facebook.com') &&
            !href.includes('fbcdn.net') &&
            !href.includes('fb.com') &&
            !href.includes('fb.watch')) {
          return; // Thumbnail link preview từ website ngoài
        }
      }

      // BỘ LỌC 6: Loại bỏ ảnh avatar/profile picture của trang/người dùng
      if (parentLink) {
        const href = (parentLink.href || parentLink.getAttribute('href') || '');
        if (href.includes('facebook.com')) {
          let pathname = '';
          try { pathname = new URL(href).pathname; } catch(e) { pathname = href; }
          // QUAN TRỌNG: Mọi link dẫn đến bài viết, ảnh, permalink, story_fbid ĐỀU LÀ NỘI DUNG, KHÔNG PHẢI AVATAR
          const isContentPath = /\/(posts|photo|photos|reel|reels|video|videos|watch|story\.php|permalink\.php)/i.test(pathname) ||
                                /[?&](story_fbid|fbid)=/i.test(href);
          
          const isProfileUrl = (
            /^\/[^\/]+\/?$/.test(pathname) ||
            /^\/profile\.php/.test(pathname) ||
            /^\/pages\//.test(pathname)
          );
          // Chỉ coi là avatar khi thực sự là profile url VÀ không chứa bất kỳ permalink/content path nào
          if (isProfileUrl && !isContentPath && !pathname.includes('permalink.php') && !href.includes('story_fbid')) {
            return; // Avatar/ảnh profile — bỏ qua
          }
        }
      }

      // Lấy phiên bản ảnh độ phân giải cao nhất
      let hdSrc = src.replace(/_s\.(jpg|png|webp)/i, '_n.$1');
      if (!result.images.includes(hdSrc)) {
        result.images.push(hdSrc);
      }
    });

    // 2b. Fallback về og:image nếu quét trong bài không tìm thấy <img> nào
    // LƯU Ý SỐNG CÒN: Chỉ fallback khi bài không phải là video
    if (result.images.length === 0 && !isVideoPost && !postDialog) {
      const ogImg = document.querySelector('meta[property="og:image"], meta[name="og:image"]');
      if (ogImg) {
        const ogSrc = ogImg.getAttribute('content') || '';
        if (ogSrc && (ogSrc.includes('scontent') || ogSrc.includes('fbcdn.net'))) {
          result.images.push(ogSrc);
        }
      }
    }

    // 3. Thu thập video của BÀI VIẾT CHÍNH
    const videos = Array.from((postArticle || mainArea).querySelectorAll('video'));
    videos.forEach(v => {
      if (v.closest('[role="complementary"], [role="navigation"], [role="banner"], [data-pagelet*="RightRail"]')) return;
      const rect = v.getBoundingClientRect();
      // Facebook injects invisible MP4 audio/sidecar players into photo posts.
      // They are not post videos and must not be downloaded as MP4 files.
      if (rect.width < 80 || rect.height < 80) return;
      if (boundaryTop !== Infinity && rect.top >= boundaryTop) return;
      if (v.closest('[aria-label*="Bình luận"], [aria-label*="Comment"]')) return;

      const src = v.currentSrc || v.src || '';
      if (src && !src.startsWith('blob:') && !result.videos.includes(src)) {
        result.videos.push(src);
      } else if (isVideoPost && src.startsWith('blob:')) {
        // A Reel poster is only a thumbnail, not post media.  Do not add it
        // to images: video-only posts must download only a verified MP4.
        // The script/webRequest extractors below resolve the actual MP4 URL.
      }
    });

    // Fallback: Nếu bài là Video mà thẻ <video> dùng blob: -> lấy link video từ thẻ meta
    if (result.videos.length === 0 && isVideoPost) {
      const ogVid = document.querySelector('meta[property="og:video"], meta[property="og:video:secure_url"], meta[property="og:video:url"]');
      if (ogVid) {
        const vidUrl = ogVid.getAttribute('content') || '';
        if (vidUrl && !result.videos.includes(vidUrl)) {
          result.videos.push(vidUrl);
        }
      }
    }

    // PHƯƠNG ÁN A: Parse <script type="application/json"> để tìm URL video .mp4 thật
    // Facebook nhúng video URL trực tiếp trong SSR data JSON của page
    if (isVideoPost) {
      try {
        const VIDEO_URL_KEYS = [
          'hd_src_no_ratelimit',    // URL HD không giới hạn tốc độ
          'sd_src_no_ratelimit',    // URL SD không giới hạn tốc độ
          'browser_native_hd_url', // URL HD cho browser
          'browser_native_sd_url', // URL SD cho browser
          'video_url',             // URL video chung
          'playable_url_quality_hd',
          'playable_url',
        ];

        /**
         * Đệ quy tìm trong object JSON các key có giá trị là URL video .mp4
         */
        function extractVideoUrlsFromObj(obj, found = new Set(), depth = 0) {
          if (!obj || typeof obj !== 'object' || depth > 12) return found;
          for (const key of Object.keys(obj)) {
            const val = obj[key];
            if (VIDEO_URL_KEYS.includes(key) && typeof val === 'string' && val.includes('.mp4') && val.startsWith('http')) {
              found.add(val);
            }
            if (val && typeof val === 'object') {
              extractVideoUrlsFromObj(val, found, depth + 1);
            }
          }
          return found;
        }

        const scriptTags = Array.from(document.querySelectorAll('script[type="application/json"], script[data-sjs]'));
        const foundMp4Urls = new Set();

        for (const script of scriptTags) {
          try {
            const raw = script.textContent || '';
            if (!raw.includes('.mp4') && !raw.includes('video_url')) continue; // Bỏ qua nhanh script không liên quan
            const parsed = JSON.parse(raw);
            extractVideoUrlsFromObj(parsed, foundMp4Urls);
          } catch (e) {
            // Script tag không phải JSON hợp lệ — bỏ qua
          }
        }

        // Fallback: dùng regex trên inline script khi JSON.parse thất bại
        if (foundMp4Urls.size === 0) {
          const inlineScripts = Array.from(document.querySelectorAll('script:not([src])'));
          for (const s of inlineScripts) {
            const raw = s.textContent || '';
            for (const key of ['hd_src_no_ratelimit', 'browser_native_hd_url', 'sd_src_no_ratelimit', 'playable_url']) {
              if (!raw.includes(key)) continue;
              const re = new RegExp(`"${key}"\\s*:\\s*"([^"]+)"`, 'g');
              let m;
              while ((m = re.exec(raw)) !== null) {
                try {
                  // Dùng JSON.parse để decode TOÀN BỘ \uXXXX, \/, \u0026 một lúc
                  const decoded = JSON.parse('"' + m[1] + '"');
                  if (decoded.startsWith('http') && decoded.includes('.mp4')) {
                    foundMp4Urls.add(decoded);
                  }
                } catch(e2) {
                  // Fallback thủ công nếu JSON.parse không hoạt động
                  const url = m[1]
                    .replace(/\\u([0-9a-fA-F]{4})/g, (_, h) => String.fromCharCode(parseInt(h, 16)))
                    .replaceAll('\\/', '/');
                  if (url.startsWith('http') && url.includes('.mp4')) {
                    foundMp4Urls.add(url);
                  }
                }
              }
            }
          }
        }

        if (foundMp4Urls.size > 0) {
          console.log('[ExtractPermalink] Phương án A tìm thấy', foundMp4Urls.size, 'URL video .mp4 từ script JSON');
          // Ưu tiên URL HD (có "hd" trong URL) hơn SD
          const hdUrls = Array.from(foundMp4Urls).filter(u => u.includes('hd') || u.includes('HD'));
          const sdUrls = Array.from(foundMp4Urls).filter(u => !u.includes('hd') && !u.includes('HD'));
          const prioritized = [...hdUrls, ...sdUrls];
          for (const u of prioritized) {
            if (!result.videos.includes(u)) result.videos.push(u);
          }
        }
      } catch (e) {
        console.warn('[ExtractPermalink] Lỗi parse script JSON:', e);
      }
    }


    // 4. Trích xuất text bài viết chính
    // 4a. Tự động click các nút "Xem thêm" / "See more" nếu có để mở rộng văn bản đầy đủ
    let hasSeeMoreBtn = false;
    try {
      const allEls = Array.from((postArticle || mainArea).querySelectorAll('div, span, a, button'));
      for (const el of allEls) {
        if (el.closest('[role="complementary"], [role="navigation"], [role="banner"]')) continue;
        const t = (el.innerText || el.textContent || '').trim().toLowerCase();
        if (t === 'xem thêm' || t === 'see more' || t === 'xem tiếp') {
          hasSeeMoreBtn = true;
          try {
            el.click();
            el.dispatchEvent(new MouseEvent('click', { bubbles: true }));
          } catch(e) {}
        }
      }
    } catch (e) {}

    // 4b. Quét theo danh sách selector phổ biến (ưu tiên selector Group Facebook)
    const postBodySelectors = [
      '[data-ad-rendering-role="story_message"]', // Facebook Groups & feed mới
      '[data-ad-comet-preview="message"]',
      '[data-ad-preview="message"]',
      'div[class*="xdj266r"][dir="auto"]',
      'div[dir="auto"][style*="text-align"]',
      'div[dir="auto"] > div[dir="auto"]',
      '.userContent',
      '[data-testid="post_message"]'
    ];

    for (const sel of postBodySelectors) {
      const els = Array.from((postArticle || mainArea).querySelectorAll(sel));
      const validEls = els.filter(el => {
        if (el.closest('[role="complementary"], [role="navigation"], [role="banner"]')) return false;
        if (el.closest('[aria-label*="Bình luận"], [aria-label*="Comment"]')) return false;
        return true;
      });
      const texts = validEls
        .map(el => (el.innerText || el.textContent || '').trim())
        .filter(t => t.length > 5);
      if (texts.length > 0) {
        result.postText = texts.join('\n\n').trim();
        result.textStatus = 'verified';
        break;
      }
    }

    // 4c. Quét generic: lấy các khối text leaf node có dir="auto" bên trong bài viết
    if (!result.postText) {
      const textBlocks = [];
      const autoEls = Array.from((postArticle || mainArea).querySelectorAll('div[dir="auto"], span[dir="auto"]'));
      autoEls.forEach(el => {
        if (el.closest('[role="complementary"], [role="navigation"], [role="banner"]')) return;
        if (el.closest('[aria-label*="Bình luận"], [aria-label*="Comment"], [data-visualcompletion="ignore-dynamic"]')) return;
        // Chỉ lấy leaf node
        if (!el.querySelector('div[dir="auto"], span[dir="auto"]')) {
          const txt = (el.innerText || el.textContent || '').trim();
          if (txt.length > 25) {
            textBlocks.push(txt);
          }
        }
      });
      if (textBlocks.length > 0) {
        result.postText = textBlocks.join('\n').trim();
        // Generic nodes can include UI/comment text, so never trust them for
        // the character threshold or the auto-unlike decision.
        result.textStatus = 'unverified';
      }
    }

    // 4d. Fallback: lấy OG description
    if (!result.postText) {
      const ogDesc = document.querySelector('meta[property="og:description"]');
      if (ogDesc) {
        result.postText = (ogDesc.getAttribute('content') || '').trim();
      }
    }

    // ── KIỂM TRA DẤU HIỆU CẮT NGẮN (TRUNCATION) ──
    // Các dấu hiệu bài viết dài bị Facebook cắt ngắn:
    // 1. Chứa từ khóa "Xem thêm", "See more", "xem tiếp" trong text
    // 2. Kết thúc bằng dấu ... hoặc ... Xem thêm
    // 3. Có nút "Xem thêm" trên DOM
    // 4. Fallback og:description kết thúc bằng dấu ba chấm và snippet dài
    const hasSeeMoreInText = /\b(?:xem thêm|see more|xem tiếp)\b/i.test(result.postText);
    const hasEllipsis = /(?:\.{3}|…|&hellip;|&#x2026;)(?:\s*(?:xem thêm|see more|xem tiếp|nh[ưu]\.\.\.))?\s*$/i.test(result.postText);
    const isTruncatedSnippet = result.postText.length >= 150 && /(?:\.{3}|…)/.test(result.postText.slice(-60));

    if (hasSeeMoreBtn || hasSeeMoreInText || hasEllipsis || isTruncatedSnippet) {
      result.isTruncated = true;
    }
  } catch (e) {
    console.error('[ExtractPermalink] Error:', e);
  }

  return result;
}


// ── LẮNG NGHE TIN NHẮN TỪ CONTENT SCRIPT & POPUP ────────────────────────────
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  const { action } = message;

  if (action === 'GET_TAB_ID') {
    sendResponse({ tabId: sender.tab ? sender.tab.id : null });
    return true;
  }

  // Mở tab permalink và đăng ký chờ kết quả extract media
  if (action === 'OPEN_PERMALINK_TAB') {
    const { url, parentTabId } = message;
    // Create an inert tab first.  Registering it as pending before navigation
    // prevents early MP4 requests from being missed by webRequest.
    chrome.tabs.create({ url: 'about:blank', active: false }, newTab => {
      if (chrome.runtime.lastError || !newTab) {
        sendResponse({ success: false, tabId: null });
        return;
      }

      // Timeout fallback: sau 20s nếu tab chưa trả kết quả → gửi rỗng và đóng tab
      const timeout = setTimeout(() => {
        if (pendingTabExtractions.has(newTab.id)) {
          console.warn('[BG] Timeout waiting for permalink tab:', newTab.id);
          chrome.tabs.sendMessage(parentTabId, {
            action: 'PERMALINK_MEDIA_RESULT',
            tabId: newTab.id,
            images: [],
            videos: [],
            postText: '',
            isTruncated: false,
            textStatus: 'unverified',
            isVideoPost: false,
            sourceUrl: url,
            isTimeout: true
          }).catch(() => {});
          pendingTabExtractions.delete(newTab.id);
          chrome.tabs.remove(newTab.id).catch(() => {});
        }
      }, 20000);

      pendingTabExtractions.set(newTab.id, { parentTabId, timeout, url });
      chrome.tabs.update(newTab.id, { url }, () => {
        if (chrome.runtime.lastError) {
          clearTimeout(timeout);
          pendingTabExtractions.delete(newTab.id);
          chrome.tabs.remove(newTab.id).catch(() => {});
          sendResponse({ success: false, tabId: null });
          return;
        }
        sendResponse({ success: true, tabId: newTab.id });
      });
    });
    return true;
  }

  // Ask the local yt-dlp + FFmpeg helper to download a Reel's DASH tracks and
  // mux them into one verified MP4. The extension never writes DASH fragments.
  if (action === 'DOWNLOAD_REEL_WITH_HELPER') {
    const { sourceUrl, filename } = message;
    (async () => {
      try {
        const response = await fetch('http://127.0.0.1:48765/download', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-FB-Media-Helper': 'local-addon-v1'
          },
          body: JSON.stringify({ sourceUrl, filename })
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok || !data.success) {
          sendResponse({ success: false, error: data.error || `Local helper HTTP ${response.status}` });
          return;
        }
        sendResponse({ success: true, path: data.path, duration: data.duration });
      } catch (error) {
        sendResponse({ success: false, error: 'Local video helper is not running. Start FacebookMediaHelper\\start_helper.cmd first.' });
      }
    })();
    return true;
  }

  // Tải media (ảnh hoặc video) vào thư mục riêng biệt
  if (action === 'DOWNLOAD_MEDIA') {
    const { url, filename, subFolder, mediaType } = message;
    const safeFileName = (filename || 'media_' + Date.now()).replace(/[\\/:*?"<>|]/g, '_').trim();
    const typeFolder = mediaType === 'video' ? 'video' : 'image';

    let fullPath = '';
    if (subFolder && subFolder.trim()) {
      const safeSubFolder = subFolder.replace(/[\\/:*?"<>|]/g, '_').trim();
      fullPath = `FB_Liked_Media/${typeFolder}/${safeSubFolder}/${safeFileName}`;
    } else {
      fullPath = `FB_Liked_Media/${typeFolder}/${safeFileName}`;
    }

    // ╔══ PRE-VALIDATION CHO VIDEO: Kiểm tra URL trước khi download ══║
    if (mediaType === 'video') {
      (async () => {
        try {
          if (isStreamingFragmentUrl(url)) {
            sendResponse({ success: false, error: 'URL is a streaming fragment, not a complete MP4' });
            return;
          }
          // HEAD request để kiểm tra Content-Type và Content-Length
          const headResp = await fetch(url, {
            method: 'HEAD',
            credentials: 'include',
            headers: { 'Referer': 'https://www.facebook.com/' }
          });

          const ct = (headResp.headers.get('content-type') || '').toLowerCase();
          const cl = parseInt(headResp.headers.get('content-length') || '0', 10);

          // Nếu HTTP lỗi hoặc trả về HTML/JSON (không phải video thật)
          if (headResp.status >= 400) {
            console.warn('[BG] Video URL HTTP lỗi:', headResp.status, url.slice(0, 80));
            sendResponse({ success: false, error: `HTTP ${headResp.status} — URL đã hết hạn hoặc yêu cầu xem thực tế` });
            return;
          }
          if (ct.includes('text/html') || ct.includes('application/json')) {
            console.warn('[BG] Video URL trả về HTML/JSON thay vì video:', ct, url.slice(0, 80));
            sendResponse({ success: false, error: `Không phải video: Content-Type = ${ct}` });
            return;
          }
          // File quá nhỏ (< 50KB) chắc là error page, không phải video thật
          if (cl > 0 && cl < 50000) {
            console.warn('[BG] Video URL trả về file quá nhỏ:', cl, 'bytes');
            sendResponse({ success: false, error: `File quá nhỏ: ${cl} bytes — không phải video` });
            return;
          }

          // URL hợp lệ → tiến hành download
          console.log('[BG] Video URL hợp lệ:', ct, cl > 0 ? `${(cl/1024/1024).toFixed(1)}MB` : 'size unknown');
          // A video MIME type can still be a standalone DASH/CMAF fragment.
          // Inspect its first bytes before creating a file in video/.
          const probeResp = await fetch(url, {
            credentials: 'include',
            headers: {
              'Range': 'bytes=0-4095',
              'Referer': 'https://www.facebook.com/'
            }
          });
          if (!probeResp.ok && probeResp.status !== 206) {
            sendResponse({ success: false, error: `Cannot read video header: HTTP ${probeResp.status}` });
            return;
          }
          const probeBytes = new Uint8Array(await probeResp.arrayBuffer());
          if (!isCompleteMp4Header(probeBytes)) {
            console.warn('[BG] Rejected DASH/CMAF fragment or incomplete MP4:', url.slice(0, 100));
            sendResponse({ success: false, error: 'Not a complete MP4 (DASH/CMAF fragment)' });
            return;
          }
          console.log('[BG] Verified complete MP4:', ct, cl > 0 ? `${(cl/1024/1024).toFixed(1)}MB` : 'size unknown');
        } catch (headErr) {
          // An unverifiable URL is intentionally skipped.  Facebook may return
          // a fragment even when a HEAD request is blocked or incomplete.
          console.warn('[BG] Video verification failed; skipping download:', headErr.message);
          sendResponse({ success: false, error: `Cannot verify complete MP4: ${headErr.message}` });
          return;
          // HEAD thất bại (CORS, server không hỗ trợ HEAD) → vẫn thử download
          console.warn('[BG] HEAD check thất bại, vẫn thử download:', headErr.message);
        }

        // Thực hiện download sau khi pass validation
        downloadFolderMap.set(url, fullPath);
        chrome.downloads.download(
          { url, filename: fullPath, saveAs: false },
          (downloadId) => {
            if (chrome.runtime.lastError) {
              console.warn('[BG] Video download error:', chrome.runtime.lastError.message);
              downloadFolderMap.delete(url);
              sendResponse({ success: false, error: chrome.runtime.lastError.message });
            } else {
              // Lưu downloadId → fullPath để watcher kiểm tra file size sau
              videoDownloadTracker.set(downloadId, { fullPath, url });
              sendResponse({ success: true, downloadId, path: fullPath });
            }
          }
        );
      })();
      return true; // async response
    }

    // Ảnh và các loại media khác: download trực tiếp không cần validation
    downloadFolderMap.set(url, fullPath);
    chrome.downloads.download(
      { url, filename: fullPath, saveAs: false },
      (downloadId) => {
        if (chrome.runtime.lastError) {
          console.warn('[BG] Download error:', chrome.runtime.lastError.message, url);
          downloadFolderMap.delete(url);
          sendResponse({ success: false, error: chrome.runtime.lastError.message });
        } else {
          sendResponse({ success: true, downloadId, path: fullPath });
        }
      }
    );
    return true;
  }

  // Lưu file thông tin bài viết vào thư mục post_info/
  if (action === 'SAVE_POST_INFO') {
    const { subFolder, filename, postInfoText } = message;
    const safeFileName = (filename || 'post_info_' + Date.now() + '.txt').replace(/[\\/:*?"<>|]/g, '_').trim();

    let fullPath = '';
    if (subFolder && subFolder.trim()) {
      const safeSubFolder = subFolder.replace(/[\\/:*?"<>|]/g, '_').trim();
      fullPath = `FB_Liked_Media/post_info/${safeSubFolder}/${safeFileName}`;
    } else {
      fullPath = `FB_Liked_Media/post_info/${safeFileName}`;
    }

    const blobUrl = 'data:text/plain;charset=utf-8,' + encodeURIComponent(postInfoText);
    downloadFolderMap.set(blobUrl, fullPath);

    chrome.downloads.download(
      { url: blobUrl, filename: fullPath, saveAs: false },
      (downloadId) => {
        if (chrome.runtime.lastError) {
          downloadFolderMap.delete(blobUrl);
          sendResponse({ success: false, error: chrome.runtime.lastError.message });
        } else {
          sendResponse({ success: true, downloadId, path: fullPath });
        }
      }
    );
    return true;
  }


  // Cập nhật thống kê toàn cục
  if (action === 'UPDATE_STATS') {
    chrome.storage.local.get(['fb_stats'], (result) => {
      const stats = result.fb_stats || {
        totalProcessed: 0,
        totalDownloaded: 0,
        totalSkipped: 0,
        totalUnliked: 0
      };
      if (message.downloadCount) stats.totalDownloaded += message.downloadCount;
      if (message.skippedCount) stats.totalSkipped += message.skippedCount;
      if (message.unlikedCount) stats.totalUnliked += message.unlikedCount;
      if (message.processedCount) stats.totalProcessed += message.processedCount;

      chrome.storage.local.set({ fb_stats: stats }, () => {
        sendResponse({ success: true, stats });
      });
    });
    return true;
  }

  // Tính aHash (Average Hash 16x16) cho một ảnh từ URL — dùng để so sánh nội dung ảnh
  // Trả về: { hash: "0101...", error: null } hoặc { hash: null, error: "..." }
  if (action === 'COMPUTE_IMAGE_HASH') {
    const { imageUrl } = message;
    (async () => {
      try {
        // Fetch ảnh về dưới dạng blob
        const resp = await fetch(imageUrl, { mode: 'cors' });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const blob = await resp.blob();

        // Tạo ImageBitmap scale về 16x16 (dùng OffscreenCanvas trong service worker)
        const bitmap = await createImageBitmap(blob, {
          resizeWidth: 16, resizeHeight: 16,
          resizeQuality: 'pixelated'
        });
        const canvas = new OffscreenCanvas(16, 16);
        const ctx = canvas.getContext('2d');
        ctx.drawImage(bitmap, 0, 0);
        bitmap.close();

        // Lấy pixel data và chuyển sang grayscale
        const imageData = ctx.getImageData(0, 0, 16, 16);
        const px = imageData.data;
        const gray = [];
        for (let i = 0; i < px.length; i += 4) {
          gray.push(0.299 * px[i] + 0.587 * px[i + 1] + 0.114 * px[i + 2]);
        }

        // Average hash: so sánh mỗi pixel với mean
        const mean = gray.reduce((a, b) => a + b, 0) / gray.length;
        const hash = gray.map(v => v >= mean ? '1' : '0').join('');

        sendResponse({ hash, error: null });
      } catch (e) {
        sendResponse({ hash: null, error: e.message });
      }
    })();
    return true; // async response
  }

  // So sánh hash ảnh mới tải với hash mẫu lỗi đã lưu
  // Trả về { similarity: 0.0-1.0, suspicious: bool }
  if (action === 'COMPARE_IMAGE_HASH') {
    const { hash1, hash2 } = message;
    if (!hash1 || !hash2 || hash1.length !== hash2.length) {
      sendResponse({ similarity: 0, suspicious: false });
      return true;
    }
    let diff = 0;
    for (let i = 0; i < hash1.length; i++) {
      if (hash1[i] !== hash2[i]) diff++;
    }
    const similarity = 1 - diff / hash1.length;
    sendResponse({ similarity, suspicious: false }); // caller tự quyết suspicious
    return true;
  }

  return false;

});

// ── XÓNG PENDING TABS KHI TAB BỊ ĐÓNG THỦ CÔNG ────────────────────────────
chrome.tabs.onRemoved.addListener((tabId) => {
  if (pendingTabExtractions.has(tabId)) {
    const pending = pendingTabExtractions.get(tabId);
    clearTimeout(pending.timeout);
    pendingTabExtractions.delete(tabId);
  }
});

// Bộ nhớ đệm tên file download (hỗ trợ Edge & Chrome)
chrome.downloads.onDeterminingFilename.addListener((item, suggest) => {
  if (downloadFolderMap.has(item.url)) {
    const customPath = downloadFolderMap.get(item.url);
    downloadFolderMap.delete(item.url);
    suggest({ filename: customPath, conflictAction: 'uniquify' });
    return true;
  }
  suggest();
  return true;
});
