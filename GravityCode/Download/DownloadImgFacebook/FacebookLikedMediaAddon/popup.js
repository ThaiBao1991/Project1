/**
 * Popup Logic — Facebook Liked Media Downloader (Anti-Ban Safe)
 */

const TARGET_URL = 'https://www.facebook.com/100007948240441/allactivity?activity_history=false&category_key=LIKEDPOSTS&manage_mode=false&should_load_landing_page=false';

// DOM Elements
const statusBadge = document.getElementById('statusBadge');
const statProcessed = document.getElementById('statProcessed');
const statDownloaded = document.getElementById('statDownloaded');
const statSkipped = document.getElementById('statSkipped');
const statUnliked = document.getElementById('statUnliked');

const cooldownBanner = document.getElementById('cooldownBanner');
const cooldownTimerText = document.getElementById('cooldownTimerText');

const startBtn = document.getElementById('startBtn');
const pauseBtn = document.getElementById('pauseBtn');
const stopBtn = document.getElementById('stopBtn');
const runningActionRow = document.getElementById('runningActionRow');
const openActivityLogBtn = document.getElementById('openActivityLogBtn');
const testScanBtn = document.getElementById('testScanBtn');
const debugDomBtn = document.getElementById('debugDomBtn');
const quickResetCacheBtn = document.getElementById('quickResetCacheBtn');

const toggleSettings = document.getElementById('toggleSettings');
const settingsContent = document.getElementById('settingsContent');
const settingsArrow = document.getElementById('settingsArrow');

const charThreshold = document.getElementById('charThreshold');
const maxPerSession = document.getElementById('maxPerSession');
const cooldownEvery = document.getElementById('cooldownEvery');
const autoUnlike = document.getElementById('autoUnlike');
const downloadImages = document.getElementById('downloadImages');
const downloadVideos = document.getElementById('downloadVideos');
const savePostInfo = document.getElementById('savePostInfo');
const minDelay = document.getElementById('minDelay');
const maxDelay = document.getElementById('maxDelay');

const clearCacheBtn = document.getElementById('clearCacheBtn');
const clearLogBtn = document.getElementById('clearLogBtn');
const copyLogBtn = document.getElementById('copyLogBtn');
const logConsole = document.getElementById('logConsole');

// Debug Mode Elements
const toggleDebug = document.getElementById('toggleDebug');
const debugContent = document.getElementById('debugContent');
const debugArrow = document.getElementById('debugArrow');
const sampleImageInput = document.getElementById('sampleImageInput');
const sampleImageStatus = document.getElementById('sampleImageStatus');
const sampleImagePreview = document.getElementById('sampleImagePreview');
const sampleImgThumb = document.getElementById('sampleImgThumb');
const similarityThreshold = document.getElementById('similarityThreshold');
const clearSampleBtn = document.getElementById('clearSampleBtn');
const debugModeIndicator = document.getElementById('debugModeIndicator');

// Modal Elements
const suspiciousImgModal = document.getElementById('suspiciousImgModal');
const closeModalBtn = document.getElementById('closeModalBtn');
const modalContent = document.getElementById('modalContent');
const modalContinueBtn = document.getElementById('modalContinueBtn');
const modalStopBtn = document.getElementById('modalStopBtn');

let currentTabId = null;

/**
 * Force-inject content_script.js vào tab Facebook.
 * Cần thiết khi tab đã mở TRƯỚC khi cài extension (Chrome không tự inject vào tab cũ).
 */
async function injectContentScript(tabId) {
  try {
    await chrome.scripting.executeScript({
      target: { tabId },
      files: ['content_script.js']
    });
    appendLog('✅ Đã nạp script vào trang Facebook thành công.', 'info');
  } catch (e) {
    // Script có thể đã được inject từ trước — bỏ qua lỗi duplicate
    console.warn('[Popup] inject warn (có thể đã inject rồi):', e.message);
  }
}

// Thêm log vào console của popup
function appendLog(text, type = 'info') {
  const entry = document.createElement('div');
  entry.className = `log-entry log-${type}`;
  entry.textContent = text;
  logConsole.appendChild(entry);
  logConsole.scrollTop = logConsole.scrollHeight;
}

// Cập nhật giao diện trạng thái
function updateUIState(state, extra = '') {
  if (state === 'running') {
    statusBadge.textContent = 'Đang chạy';
    statusBadge.className = 'status-badge status-running';
    startBtn.style.display = 'none';
    runningActionRow.style.display = 'grid';
    pauseBtn.textContent = '⏸ Tạm Dừng';
    cooldownBanner.style.display = 'none';
  } else if (state === 'cooldown') {
    statusBadge.textContent = 'Nghỉ an toàn';
    statusBadge.className = 'status-badge status-cooldown';
    startBtn.style.display = 'none';
    runningActionRow.style.display = 'grid';
    cooldownBanner.style.display = 'flex';
    if (extra) cooldownTimerText.textContent = extra;
  } else if (state === 'paused') {
    statusBadge.textContent = 'Tạm dừng';
    statusBadge.className = 'status-badge status-paused';
    startBtn.style.display = 'none';
    runningActionRow.style.display = 'grid';
    pauseBtn.textContent = '▶ Tiếp Tục';
    cooldownBanner.style.display = 'none';
  } else {
    statusBadge.textContent = 'Sẵn sàng';
    statusBadge.className = 'status-badge status-idle';
    startBtn.style.display = 'block';
    runningActionRow.style.display = 'none';
    cooldownBanner.style.display = 'none';
  }
}

// Nạp thống kê từ bộ nhớ
function refreshStats() {
  chrome.storage.local.get(['fb_stats'], (res) => {
    const stats = res.fb_stats || {
      totalProcessed: 0,
      totalDownloaded: 0,
      totalSkipped: 0,
      totalUnliked: 0
    };
    statProcessed.textContent = stats.totalProcessed;
    statDownloaded.textContent = stats.totalDownloaded;
    statSkipped.textContent = stats.totalSkipped;
    statUnliked.textContent = stats.totalUnliked;
  });
}

// Lấy cấu hình hiện tại từ UI
function getConfig() {
  return {
    charThreshold: parseInt(charThreshold.value, 10) || 300,
    maxPerSession: parseInt(maxPerSession.value, 10) || 30,
    cooldownEvery: parseInt(cooldownEvery.value, 10) || 5,
    autoUnlike: autoUnlike.checked,
    downloadImages: downloadImages.checked,
    downloadVideos: downloadVideos.checked,
    savePostInfo: savePostInfo.checked,
    minDelayMs: Math.max(2000, (parseFloat(minDelay.value) || 4.5) * 1000),
    maxDelayMs: Math.max(3000, (parseFloat(maxDelay.value) || 8.5) * 1000)
  };
}

// Lưu cấu hình vào bộ nhớ đệm chrome.storage.local để ghi nhớ vĩnh viễn
function saveUserConfig() {
  const cfg = getConfig();
  chrome.storage.local.set({ fb_user_config: cfg });
  const hintEl = document.getElementById('hintThreshold');
  if (hintEl) hintEl.textContent = cfg.charThreshold;
}

// Tự động lưu cấu hình mỗi khi người dùng thay đổi bất kỳ ô cài đặt nào
[charThreshold, maxPerSession, cooldownEvery, autoUnlike, downloadImages, downloadVideos, savePostInfo, minDelay, maxDelay].forEach(el => {
  if (!el) return;
  el.addEventListener('change', saveUserConfig);
  el.addEventListener('input', saveUserConfig);
});

// Lấy Tab Facebook hiện tại
async function getFacebookTab() {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tabs.length > 0 && tabs[0].url && tabs[0].url.includes('facebook.com')) {
    return tabs[0];
  }
  const fbTabs = await chrome.tabs.query({ url: '*://*.facebook.com/*' });
  if (fbTabs.length > 0) {
    return fbTabs[0];
  }
  return null;
}

// Khởi tạo Popup
async function init() {
  refreshStats();

  // 1. Khôi phục cấu hình người dùng đã lưu từ chrome.storage.local trước
  chrome.storage.local.get(['fb_user_config'], (data) => {
    if (data && data.fb_user_config) {
      const uCfg = data.fb_user_config;
      if (uCfg.charThreshold !== undefined) charThreshold.value = uCfg.charThreshold;
      if (uCfg.maxPerSession !== undefined) maxPerSession.value = uCfg.maxPerSession;
      if (uCfg.cooldownEvery !== undefined) cooldownEvery.value = uCfg.cooldownEvery;
      if (uCfg.autoUnlike !== undefined) autoUnlike.checked = uCfg.autoUnlike;
      if (uCfg.downloadImages !== undefined) downloadImages.checked = uCfg.downloadImages;
      if (uCfg.downloadVideos !== undefined) downloadVideos.checked = uCfg.downloadVideos;
      if (uCfg.savePostInfo !== undefined) savePostInfo.checked = uCfg.savePostInfo;
      const hintEl = document.getElementById('hintThreshold');
      if (hintEl) hintEl.textContent = charThreshold.value;
    }
  });

  const activeTab = await getFacebookTab();
  if (activeTab) {
    currentTabId = activeTab.id;
    chrome.tabs.sendMessage(currentTabId, { action: 'GET_STATUS' }, (res) => {
      if (chrome.runtime.lastError) {
        updateUIState('idle');
      } else if (res) {
        if (res.isRunning) {
          if (res.isCoolingDown) {
            updateUIState('cooldown', 'Đang nghỉ giải lao chống bot...');
          } else {
            updateUIState(res.isPaused ? 'paused' : 'running');
          }
          // Chỉ đồng bộ cấu hình từ tab nếu tab đang chạy
          if (res.config) {
            if (res.config.charThreshold) charThreshold.value = res.config.charThreshold;
            if (res.config.maxPerSession) maxPerSession.value = res.config.maxPerSession;
            if (res.config.cooldownEvery) cooldownEvery.value = res.config.cooldownEvery;
            autoUnlike.checked = res.config.autoUnlike;
            downloadImages.checked = res.config.downloadImages;
            downloadVideos.checked = res.config.downloadVideos;
            const hintEl = document.getElementById('hintThreshold');
            if (hintEl) hintEl.textContent = charThreshold.value;
          }
        } else {
          updateUIState('idle');
        }
      }
    });
  } else {
    appendLog('⚠️ Chưa tìm thấy tab Facebook nào đang mở. Nhấn nút bên dưới để mở trang!', 'warn');
  }

  // Khôi phục trạng thái Debug Mode từ bộ nhớ
  chrome.storage.local.get(['fb_debug_sample_image', 'fb_debug_threshold', 'fb_last_suspicious'], (res) => {
    if (res.fb_debug_sample_image) {
      sampleImgThumb.src = res.fb_debug_sample_image;
      sampleImagePreview.style.display = 'block';
      sampleImageStatus.textContent = 'Đã nạp mẫu';
      sampleImageStatus.style.color = '#10b981';
      debugModeIndicator.style.display = 'block';
      if (res.fb_debug_threshold) similarityThreshold.value = res.fb_debug_threshold;
    }
    if (res.fb_last_suspicious) {
      showSuspiciousModal(res.fb_last_suspicious);
    }
  });
}

// Sự kiện nút Bắt Đầu
startBtn.addEventListener('click', async () => {
  let tab = await getFacebookTab();
  if (!tab) {
    appendLog('Đang mở trang Activity Log Liked của bạn...', 'info');
    tab = await chrome.tabs.create({ url: TARGET_URL });
    currentTabId = tab.id;
    appendLog('Vui lòng đợi trang tải xong rồi nhấn Bắt Đầu lại.', 'warn');
    return;
  }

  currentTabId = tab.id;

  // LUÔN inject lại content_script để đảm bảo code mới nhất được nạp vào tab
  appendLog('⚙️ Đang nạp script vào trang Facebook...', 'info');
  await injectContentScript(currentTabId);
  await new Promise(r => setTimeout(r, 400)); // Chờ script khởi tạo

  const cfg = getConfig();
  appendLog(`🛡️ Khởi động chế độ Anti-Ban: <= ${cfg.charThreshold}k tải & unlike; > ${cfg.charThreshold}k để nguyên. Nghỉ sau mỗi ${cfg.cooldownEvery} bài.`);

  chrome.tabs.sendMessage(currentTabId, { action: 'START', config: cfg }, (res) => {
    if (chrome.runtime.lastError) {
      appendLog('Không kết nối được với trang Facebook. Hãy F5 trang Facebook và thử lại!', 'error');
    } else {
      updateUIState('running');
    }
  });
});

// Nút Tạm Dừng / Tiếp Tục
pauseBtn.addEventListener('click', () => {
  if (!currentTabId) return;
  const isCurrentlyPaused = statusBadge.textContent === 'Tạm dừng';

  if (isCurrentlyPaused) {
    chrome.tabs.sendMessage(currentTabId, { action: 'START', config: getConfig() }, () => {
      updateUIState('running');
    });
  } else {
    chrome.tabs.sendMessage(currentTabId, { action: 'PAUSE' }, () => {
      updateUIState('paused');
    });
  }
});

// Nút Dừng Hẳn
stopBtn.addEventListener('click', () => {
  if (!currentTabId) return;
  chrome.tabs.sendMessage(currentTabId, { action: 'STOP' }, () => {
    updateUIState('idle');
    appendLog('Đã gửi lệnh dừng tiến trình an toàn.', 'info');
  });
});

// Nút mở nhanh trang Activity Log
openActivityLogBtn.addEventListener('click', () => {
  chrome.tabs.create({ url: TARGET_URL });
});

// Nút thử nghiệm quét DOM tìm bài viết
testScanBtn.addEventListener('click', async () => {
  const tab = await getFacebookTab();
  if (!tab) {
    appendLog('⚠️ Chưa tìm thấy tab Facebook nào đang mở.', 'error');
    return;
  }

  appendLog('⚙️ Đang nạp script vào trang Facebook...', 'info');
  await injectContentScript(tab.id);
  await new Promise(r => setTimeout(r, 500)); // Chờ script khởi tạo xong

  appendLog('🔍 Đang kiểm tra nhận diện các bài viết trên trang Facebook...', 'info');
  chrome.tabs.sendMessage(tab.id, { action: 'TEST_SCAN' }, (res) => {
    if (chrome.runtime.lastError || !res) {
      appendLog('❌ Không thể kết nối dù đã inject script. Hãy thử lại hoặc F5 trang Facebook!', 'error');
    } else {
      if (res.rowCount === 0) {
        appendLog(`⚠️ Tìm thấy 0 bài viết. Hãy đảm bảo đang ở đúng trang Activity Log đã thích!`, 'warn');
        appendLog(`📋 Debug: ${res.debugInfo || 'Không có thêm thông tin.'}`, 'warn');
      } else {
        appendLog(`🎉 Đã nhận diện thành công ${res.rowCount} bài viết trên màn hình!`, 'info');
      }
      if (res.samples && res.samples.length > 0) {
        res.samples.forEach(s => {
          appendLog(`• Bài ${s.index}: "${s.textSnippet}..." (${s.charCount} ký tự) | Nút 3 chấm: ${s.hasActionBtn ? '✅ Có' : '❌ Chưa thấy'}`);
        });
      }
    }
  });
});

// Nút Debug DOM thực tế trên trang Facebook
if (debugDomBtn) {
  debugDomBtn.addEventListener('click', async () => {
    const tab = await getFacebookTab();
    if (!tab) {
      appendLog('⚠️ Chưa tìm thấy tab Facebook nào đang mở.', 'error');
      return;
    }

    appendLog('⚙️ Đang nạp script vào trang Facebook...', 'info');
    await injectContentScript(tab.id);
    await new Promise(r => setTimeout(r, 500));

    appendLog('🔬 Đang phân tích chi tiết cấu trúc DOM trang Facebook hiện tại...', 'info');
    chrome.tabs.sendMessage(tab.id, { action: 'DEBUG_SCAN' }, (res) => {
      if (chrome.runtime.lastError || !res || !res.debug) {
        appendLog('❌ Không lấy được dữ liệu DOM. Hãy thử F5 lại trang Facebook!', 'error');
      } else {
        const d = res.debug;
        appendLog('=== 📊 KẾT QUẢ PHÂN TÍCH DOM ===', 'info');
        appendLog(`📍 Tiêu đề: "${d.title}"`);
        appendLog(`📍 URL: ${d.url}`);
        appendLog(`📍 Nút bấm tìm thấy: ${d.totalButtons} nút`);
        appendLog(`📍 Menu 3 chấm (aria-haspopup): ${d.totalAriaHaspopup} nút`);
        appendLog(`📍 Text nút điển hình: [${(d.buttonTexts || []).join(', ')}]`);
        if (d.ariaHaspopup && d.ariaHaspopup.length > 0) {
          appendLog(`📍 Chi tiết aria-haspopup:`);
          d.ariaHaspopup.forEach((m, idx) => {
            appendLog(`   #${idx+1}: <${m.tag}> popup="${m.haspopup}" label="${m.label}" text="${m.text}" top=${m.top}px`);
          });
        }
        if (d.thichTextNodes && d.thichTextNodes.length > 0) {
          appendLog(`📍 Chứa chữ 'thích': [${d.thichTextNodes.join(' | ')}]`);
        }
        if (d.activityLinks && d.activityLinks.length > 0) {
          appendLog(`📍 Links permalink: [${d.activityLinks.join(' , ')}]`);
        }
        appendLog(`📍 Thẻ <img>: ${d.totalImgs} ảnh | listitem: ${d.listItems} | feed: ${d.feedItems}`);
        appendLog('=== VUI LÒNG CHỤP MÀN HÌNH HOẶC COPY LOG NÀY ===', 'warn');
      }
    });
  });
}

// Toggle cấu hình nâng cao
toggleSettings.addEventListener('click', () => {
  const isOpen = settingsContent.classList.toggle('open');
  settingsArrow.textContent = isOpen ? '▲' : '▼';
});

// Xóa cache bài đã quét
clearCacheBtn.addEventListener('click', () => {
  if (confirm('Bạn có chắc muốn xóa lịch sử quét và reset bộ đếm thống kê?')) {
    if (currentTabId) {
      chrome.tabs.sendMessage(currentTabId, { action: 'CLEAR_CACHE' });
    }
    chrome.storage.local.remove(['fb_processed_cache', 'fb_stats'], () => {
      refreshStats();
      appendLog('Đã dọn dẹp bộ nhớ đệm thành công.', 'info');
    });
  }
});

// Xóa console log
clearLogBtn.addEventListener('click', () => {
  logConsole.innerHTML = '';
  appendLog('[Hệ thống] Đã xóa lịch sử log.');
});

// Sao chép toàn bộ log vào Clipboard
if (copyLogBtn) {
  copyLogBtn.addEventListener('click', async () => {
    const text = logConsole.innerText || '';
    if (!text.trim()) {
      appendLog('⚠️ Log hiện đang rỗng.', 'warn');
      return;
    }
    try {
      await navigator.clipboard.writeText(text);
      appendLog('📋 Đã sao chép toàn bộ log vào Clipboard thành công! Bạn có thể dán (Ctrl+V) gửi cho hỗ trợ.', 'info');
    } catch (err) {
      appendLog('⚠️ Không thể tự sao chép bằng API. Bạn hãy bôi đen toàn bộ log và nhấn Ctrl+C!', 'warn');
    }
  });
}

// Nút Reset Cache nhanh ngoài Quick Navigation
if (quickResetCacheBtn) {
  quickResetCacheBtn.addEventListener('click', async () => {
    if (confirm('Bạn có chắc muốn xóa sạch lịch sử quét? Tất cả các bài viết cũ sẽ được quét và tải lại từ đầu!')) {
      const tab = await getFacebookTab();
      if (tab) {
        chrome.tabs.sendMessage(tab.id, { action: 'CLEAR_CACHE' });
      }
      chrome.storage.local.remove(['fb_processed_cache', 'fb_stats'], () => {
        refreshStats();
        appendLog('🧹 [Reset Cache Thành Công] Đã xóa toàn bộ bài đã nhớ! Bạn có thể bấm "Bắt Đầu" để quét lại từ đầu.', 'info');
      });
    }
  });
}


// Toggle accordion Debug Mode
if (toggleDebug) {
  toggleDebug.addEventListener('click', () => {
    const isClosed = debugContent.style.display === 'none';
    debugContent.style.display = isClosed ? 'block' : 'none';
    debugArrow.textContent = isClosed ? '▲' : '▼';
  });
}

// Tính aHash (Average Hash 16x16) từ Image element
function computeAHashFromImage(imgEl) {
  const canvas = document.createElement('canvas');
  canvas.width = 16;
  canvas.height = 16;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(imgEl, 0, 0, 16, 16);
  const px = ctx.getImageData(0, 0, 16, 16).data;
  const gray = [];
  for (let i = 0; i < px.length; i += 4) {
    gray.push(0.299 * px[i] + 0.587 * px[i + 1] + 0.114 * px[i + 2]);
  }
  const mean = gray.reduce((a, b) => a + b, 0) / gray.length;
  return gray.map(v => v >= mean ? '1' : '0').join('');
}

// Xử lý nạp ảnh mẫu lỗi
if (sampleImageInput) {
  sampleImageInput.addEventListener('change', (e) => {
    const file = e.target.files && e.target.files[0];
    if (!file) return;

    sampleImageStatus.textContent = 'Đang xử lý...';
    sampleImageStatus.style.color = '#f59e0b';

    const reader = new FileReader();
    reader.onload = (ev) => {
      const dataUrl = ev.target.result;
      sampleImgThumb.onload = () => {
        try {
          const hash = computeAHashFromImage(sampleImgThumb);
          const threshold = parseInt(similarityThreshold.value, 10) || 85;

          chrome.storage.local.set({
            fb_debug_sample_image: dataUrl,
            fb_debug_sample_hash: hash,
            fb_debug_threshold: threshold
          }, () => {
            sampleImageStatus.textContent = `Đã nạp (${file.name.slice(0, 12)}...)`;
            sampleImageStatus.style.color = '#10b981';
            sampleImagePreview.style.display = 'block';
            debugModeIndicator.style.display = 'block';
            appendLog(`🔍 [Debug Mode Bật] Đã nạp ảnh mẫu! Nếu gặp ảnh giống >= ${threshold}% sẽ tạm dừng cảnh báo.`, 'info');
          });
        } catch (err) {
          sampleImageStatus.textContent = 'Lỗi tính hash';
          sampleImageStatus.style.color = '#ef4444';
          appendLog('⚠️ Lỗi tính hash ảnh: ' + err.message, 'error');
        }
      };
      sampleImgThumb.src = dataUrl;
    };
    reader.readAsDataURL(file);
  });
}

// Đổi ngưỡng tương đồng
if (similarityThreshold) {
  similarityThreshold.addEventListener('change', () => {
    const val = parseInt(similarityThreshold.value, 10) || 85;
    chrome.storage.local.set({ fb_debug_threshold: val });
  });
}

// Xóa ảnh mẫu lỗi
if (clearSampleBtn) {
  clearSampleBtn.addEventListener('click', () => {
    chrome.storage.local.remove(['fb_debug_sample_image', 'fb_debug_sample_hash', 'fb_last_suspicious'], () => {
      sampleImageInput.value = '';
      sampleImagePreview.style.display = 'none';
      debugModeIndicator.style.display = 'none';
      sampleImageStatus.textContent = 'Chưa chọn';
      sampleImageStatus.style.color = '#6b7280';
      appendLog('🗑️ Đã xóa ảnh mẫu lỗi. Debug Mode đã tắt.', 'info');
    });
  });
}

// Hiển thị Modal Cảnh Báo Phát Hiện Ảnh Nghi Vấn
function showSuspiciousModal(data) {
  if (!suspiciousImgModal || !modalContent) return;

  const postUrl = data.postUrl || '#';
  const postLinkHtml = postUrl !== '#'
    ? `<a href="${postUrl}" target="_blank" style="color:#60a5fa; text-decoration:underline;">Mở link bài viết 🔗</a>`
    : `<span style="color:#9ca3af;">Không có link bài</span>`;

  const imgLinkHtml = data.imageUrl
    ? `<a href="${data.imageUrl}" target="_blank" style="color:#fcd34d; text-decoration:underline; word-break:break-all;">Link ảnh Facebook 🔗</a>`
    : '';

  modalContent.innerHTML = `
    <div style="background:#111827; padding:8px 10px; border-radius:6px; margin-bottom:10px; border:1px solid #374151;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
        <span style="font-size:12px; font-weight:bold; color:#f59e0b;">Độ tương đồng: ${data.similarity}% (Ngưỡng: ${data.threshold}%)</span>
        <span style="font-size:11px; color:#9ca3af;">Bài ID: <code>${data.postId || 'N/A'}</code></span>
      </div>
      <div style="display:flex; gap:10px; align-items:center; justify-content:space-around; margin:8px 0; background:#0f172a; padding:8px; border-radius:6px;">
        <div style="text-align:center;">
          <div style="font-size:10px; color:#9ca3af; margin-bottom:4px;">Ảnh mẫu bạn đã tải nhầm:</div>
          <img src="${data.sampleImage || ''}" style="width:70px; height:70px; object-fit:cover; border-radius:4px; border:2px solid #ef4444;" alt="Ảnh mẫu">
        </div>
        <div style="font-size:18px; color:#f59e0b;">⇄</div>
        <div style="text-align:center;">
          <div style="font-size:10px; color:#9ca3af; margin-bottom:4px;">Ảnh vừa tìm thấy (${data.imgIndex || 1}/${data.totalImgs || 1}):</div>
          <img src="${data.imageUrl || ''}" style="width:70px; height:70px; object-fit:cover; border-radius:4px; border:2px solid #f59e0b;" alt="Ảnh phát hiện">
        </div>
      </div>
    </div>

    <div style="margin-bottom:8px;">
      <b>📌 Nguồn trích xuất:</b> <span style="color:#10b981;">${data.sourceDetail || 'Bài viết chính'}</span><br>
      <b>🔗 Link bài viết:</b> ${postLinkHtml}<br>
      <b>🖼️ Link ảnh gốc:</b> ${imgLinkHtml}<br>
      <b>📝 Số ký tự bài viết:</b> <span style="color:${(data.charCount || 0) <= 500 ? '#10b981' : '#ef4444'}; font-weight:bold;">${data.charCount || 0} ký tự</span>
    </div>

    <div style="margin-top:6px;">
      <div style="font-size:10px; color:#9ca3af; margin-bottom:2px;"><b>Văn bản bài viết:</b></div>
      <div style="background:#111827; padding:6px 8px; border-radius:4px; max-height:70px; overflow-y:auto; font-size:10.5px; color:#e5e7eb; border:1px solid #374151; white-space:pre-wrap;">${data.postText ? data.postText.slice(0, 300) : '(Không có văn bản)'}</div>
    </div>
  `;

  suspiciousImgModal.style.display = 'block';
}

if (closeModalBtn) {
  closeModalBtn.addEventListener('click', () => {
    suspiciousImgModal.style.display = 'none';
  });
}

if (modalContinueBtn) {
  modalContinueBtn.addEventListener('click', async () => {
    suspiciousImgModal.style.display = 'none';
    chrome.storage.local.remove(['fb_last_suspicious']);
    const tab = await getFacebookTab();
    if (tab) {
      chrome.tabs.sendMessage(tab.id, { action: 'DEBUG_DECISION', decision: 'continue' });
    }
    updateUIState('running');
    appendLog('▶ Người dùng chọn: Bỏ qua ảnh này & Tiếp tục quét.', 'info');
  });
}

if (modalStopBtn) {
  modalStopBtn.addEventListener('click', async () => {
    suspiciousImgModal.style.display = 'none';
    chrome.storage.local.remove(['fb_last_suspicious']);
    const tab = await getFacebookTab();
    if (tab) {
      chrome.tabs.sendMessage(tab.id, { action: 'DEBUG_DECISION', decision: 'stop' });
    }
    updateUIState('idle');
    appendLog('⏹ Người dùng chọn: Dừng hẳn tiến trình.', 'warn');
  });
}

// Lắng nghe tin nhắn từ Content Script & Background
chrome.runtime.onMessage.addListener((message) => {
  if (message.action === 'LOG_MESSAGE') {
    appendLog(message.log, message.type);
  }
  if (message.action === 'UPDATE_STATS') {
    refreshStats();
  }
  if (message.action === 'COOLDOWN_STATE') {
    if (message.isCoolingDown) {
      updateUIState('cooldown', `Đang nghỉ giải lao an toàn (${message.secondsLeft}s)...`);
    } else {
      updateUIState('running');
    }
  }
  if (message.action === 'STATE_CHANGED') {
    updateUIState(message.isRunning ? 'running' : 'idle');
  }
  if (message.action === 'SUSPICIOUS_IMAGE_DETECTED') {
    showSuspiciousModal(message.data);
    updateUIState('paused');
    appendLog(`🚨 [DEBUG] PHÁT HIỆN ẢNH NHẦM! Độ tương đồng: ${message.data.similarity}%`, 'warn');
  }
});

init();
