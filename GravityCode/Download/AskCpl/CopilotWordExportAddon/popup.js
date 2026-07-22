// ============================================================
// popup.js — Giai đoạn 19: Advanced Memory & Multi Profiles
// ============================================================

let loadedSession = null;
let currentRoadmapData = null; // Lưu trữ JSON Roadmap đã parse

// ── QUẢN LÝ PROFILE (CONFIGS) ────────────────────────────────
let addonConfigs = {};
const DEFAULT_PROFILE = 'Default';

function loadProfiles() {
  chrome.storage.local.get(['addonConfigs', 'lastProfile'], (r) => {
    addonConfigs = r.addonConfigs || {};
    if (Object.keys(addonConfigs).length === 0) {
      addonConfigs[DEFAULT_PROFILE] = getDefaultConfig();
    }
    
    const select = document.getElementById('profileSelect');
    select.innerHTML = '';
    for (const key of Object.keys(addonConfigs)) {
      const opt = document.createElement('option');
      opt.value = key;
      opt.textContent = key;
      select.appendChild(opt);
    }
    
    const lastProfile = r.lastProfile || DEFAULT_PROFILE;
    if (addonConfigs[lastProfile]) {
      select.value = lastProfile;
      applyConfigToUI(addonConfigs[lastProfile], lastProfile);
    } else {
      const firstKey = Object.keys(addonConfigs)[0];
      select.value = firstKey;
      applyConfigToUI(addonConfigs[firstKey], firstKey);
    }
  });
}

function getDefaultConfig() {
  return {
    platform: 'copilot',
    agentName: '',
    prefix: 'Day ',
    startDay: 1,
    endDay: '',
    isAdvanced: false, // Giữ lại cho tương thích ngược
    promptMode: 'basic',
    topicPrompt: 'Cho tôi biết tên chủ đề của bài học này ngắn gọn nhất có thể (chỉ tên, không giải thích).',
    targetCount: 4,
    details: [],
    roadmapData: null
  };
}

function applyConfigToUI(config, profileKey) {
  document.getElementById('platformSelect').value = config.platform || 'copilot';
  document.getElementById('agentInput').value = config.agentName || '';
  document.getElementById('prefixInput').value = config.prefix || 'Day ';
  document.getElementById('startDayInput').value = config.startDay || 1;
  document.getElementById('endDayInput').value = config.endDay || '';
  
  const pMode = config.promptMode || (config.isAdvanced ? 'advanced' : 'basic');
  document.getElementById('promptModeSelect').value = pMode;
  updatePromptModeUI(pMode);
  
  document.getElementById('topicPromptInput').value = config.topicPrompt || '';
  document.getElementById('targetCountInput').value = config.targetCount || 4;
  
  const container = document.getElementById('detailsContainer');
  container.innerHTML = '';
  if (config.details) {
    config.details.forEach(d => addDetailUI(d.name, d.prompt));
  }

  // FIX GĐ 33: Load roadmap từ key riêng, không từ config (để tránh lưu dữ liệu khổng lồ trong addonConfigs)
  currentRoadmapData = null;
  updateRoadmapPreview(null);
  if (profileKey) {
    chrome.storage.local.get([`roadmap_${profileKey}`], (r) => {
      const saved = r[`roadmap_${profileKey}`];
      if (saved && saved.length > 0) {
        currentRoadmapData = saved;
        updateRoadmapPreview(currentRoadmapData);
      }
    });
  }
}

function buildConfigFromUI() {
  const details = [];
  document.querySelectorAll('.detail-item').forEach(el => {
    const name = el.querySelector('.detail-name').value.trim();
    const prompt = el.querySelector('.detail-prompt').value.trim();
    if (name && prompt) details.push({ name, prompt });
  });

  return {
    platform: document.getElementById('platformSelect').value,
    agentName: document.getElementById('agentInput').value.trim(),
    prefix: document.getElementById('prefixInput').value,
    startDay: parseInt(document.getElementById('startDayInput').value, 10) || 1,
    endDay: parseInt(document.getElementById('endDayInput').value, 10) || null,
    promptMode: document.getElementById('promptModeSelect').value,
    isAdvanced: document.getElementById('promptModeSelect').value === 'advanced',
    topicPrompt: document.getElementById('topicPromptInput').value.trim(),
    targetCount: parseInt(document.getElementById('targetCountInput').value, 10) || 4,
    details: details,
    roadmapData: currentRoadmapData
  };
}

document.getElementById('profileSelect').addEventListener('change', (e) => {
  const val = e.target.value;
  if (addonConfigs[val]) {
    applyConfigToUI(addonConfigs[val], val); // FIX GĐ 33: truyền profileKey để load roadmap riêng
    chrome.storage.local.set({ lastProfile: val });
  }
});

document.getElementById('saveProfileBtn').addEventListener('click', () => {
  const val = document.getElementById('profileSelect').value;
  if (!val) return;
  const cfg = buildConfigFromUI();
  // FIX GĐ 44: KHÔNG lưu roadmapData vào addonConfigs — lưu riêng key roadmap_{profile}
  addonConfigs[val] = cfg;
  chrome.storage.local.set({ addonConfigs: addonConfigs, lastProfile: val });
  if (currentRoadmapData && currentRoadmapData.length > 0) {
    chrome.storage.local.set({ [`roadmap_${val}`]: currentRoadmapData });
  }
  document.getElementById('status').innerText = `✅ Đã lưu cấu hình [${val}]`;
});

document.getElementById('addProfileBtn').addEventListener('click', () => {
  const name = prompt('Nhập tên cấu hình mới (Ví dụ: Copilot - Từ vựng):');
  if (name && name.trim() !== '') {
    const safeName = name.trim();
    if (!addonConfigs[safeName]) {
      addonConfigs[safeName] = buildConfigFromUI();
      chrome.storage.local.set({ addonConfigs: addonConfigs, lastProfile: safeName });
      loadProfiles();
    }
  }
});

document.getElementById('deleteProfileBtn').addEventListener('click', () => {
  const val = document.getElementById('profileSelect').value;
  if (Object.keys(addonConfigs).length <= 1) {
    alert("Không thể xóa cấu hình duy nhất!");
    return;
  }
  if (confirm(`Xóa cấu hình [${val}]?`)) {
    delete addonConfigs[val];
    chrome.storage.local.set({ addonConfigs: addonConfigs, lastProfile: Object.keys(addonConfigs)[0] });
    loadProfiles();
  }
});

// ── PROMPT MODE UI ─────────────────────────────────────────────
document.getElementById('promptModeSelect').addEventListener('change', (e) => {
  updatePromptModeUI(e.target.value);
});

function updatePromptModeUI(mode) {
  document.getElementById('panel-advanced').style.display = (mode === 'advanced') ? 'block' : 'none';
  document.getElementById('panel-table-md').style.display = (mode === 'table_md') ? 'block' : 'none';
  document.getElementById('panel-file-md').style.display  = (mode === 'file_md')  ? 'block' : 'none';
  
  // Update Preview Visibility
  if (mode === 'table_md' || mode === 'file_md') {
    updateRoadmapPreview(currentRoadmapData);
  } else {
    document.getElementById('roadmapPreview').style.display = 'none';
  }
}

document.getElementById('addDetailBtn').addEventListener('click', () => {
  addDetailUI('', '');
});

function addDetailUI(name, prompt) {
  const container = document.getElementById('detailsContainer');
  const div = document.createElement('div');
  div.className = 'detail-item';
  div.innerHTML = `
    <button class="remove-btn" title="Xóa">✕</button>
    <div style="margin-bottom:4px">
      <input type="text" class="detail-name" placeholder="Tên (VD: Từ vựng)" value="${escapeHtml(name)}" style="font-weight:bold">
    </div>
    <div>
      <input type="text" class="detail-prompt" placeholder="Câu hỏi cho AI (VD: Từ vựng là gì...)" value="${escapeHtml(prompt)}">
    </div>
  `;
  div.querySelector('.remove-btn').addEventListener('click', () => div.remove());
  container.appendChild(div);
}

// ── QUẢN LÝ ROADMAP ──────────────────────────────────────────
// FIX GĐ 33: Không dump toàn bộ JSON vào pre (gây treo popup khi roadmap 3000 ngày)
// Chỉ hiển thị tóm tắt nhẹ: số bài + vài mục đầu
function updateRoadmapPreview(data) {
  const pre = document.getElementById('roadmapPreview');
  if (!data || data.length === 0) {
    pre.style.display = 'none';
    pre.innerText = '';
    return;
  }
  // Đếm tổng số ngày học trong roadmap (có thể là mảng flat hoặc nested)
  let totalDays = 0;
  if (data[0] && data[0].days) {
    // Format table_md: [{main_topic, days:[]}]
    data.forEach(section => { totalDays += (section.days || []).length; });
  } else {
    // Format file_md: [{day, title, prompt}]
    totalDays = data.length;
  }
  pre.style.display = 'block';
  pre.innerText = `✅ Roadmap đã nạp: ${totalDays} bài học\n(Xem chi tiết trong file .md gốc)`;
}

document.getElementById('parseRoadmapBtn').addEventListener('click', () => {
  const text = document.getElementById('roadmapInput').value;
  const lines = text.split('\n').map(l => l.trim()).filter(l => l.startsWith('|'));
  if (lines.length < 3) {
    alert("Vui lòng dán Bảng Markdown có chứa ít nhất 1 dòng dữ liệu hợp lệ.\n(Cần có header và gạch ngang ---)");
    return;
  }
  
  const roadmap = [];
  let currentTopicObj = null;
  
  // Dòng 0: Header, Dòng 1: ---
  for (let i = 2; i < lines.length; i++) {
    const cols = lines[i].split('|').map(c => c.trim());
    if (cols.length < 5) continue;
    
    // VD: | 1 | Chương 1: JS | Biến | Học let, const |
    const day = parseInt(cols[1]);
    const chapter = cols[2];
    const topic = cols[3];
    const detail = cols[4];
    
    if (isNaN(day)) continue;

    if (!currentTopicObj || currentTopicObj.main_topic !== chapter) {
      currentTopicObj = { main_topic: chapter, days: [] };
      roadmap.push(currentTopicObj);
    }
    currentTopicObj.days.push({ day, title: topic, detail });
  }
  
  if (roadmap.length > 0) {
    currentRoadmapData = roadmap;
    updateRoadmapPreview(currentRoadmapData);
    
    // FIX GĐ 33: Lưu roadmap riêng theo key tên profile, KHÔNG nhúng vào addonConfigs
    // để tránh serialize dữ liệu khổng lồ mỗi khi gọi chrome.storage.local.set(addonConfigs)
    const val = document.getElementById('profileSelect').value;
    if (val) {
      chrome.storage.local.set({ [`roadmap_${val}`]: currentRoadmapData });
    }
    document.getElementById('status').innerText = '✅ Đã tạo Roadmap thành công!';
  } else {
    alert("Không tìm thấy dữ liệu ngày hợp lệ trong bảng.");
  }
});

// ── FILE MD ROADMAP PARSER ──────────────────────────────────
document.getElementById('loadRoadmapFileBtn').addEventListener('click', () => {
  document.getElementById('roadmapFileInput').click();
});

document.getElementById('roadmapFileInput').addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (ev) => {
    const text = ev.target.result;
    const roadmap = parseMarkdownRoadmap(text);
    
    if (roadmap && roadmap.length > 0) {
      currentRoadmapData = roadmap;
      updateRoadmapPreview(currentRoadmapData);
      document.getElementById('roadmapFileInfo').innerText = `Đã nạp file: ${file.name} (${roadmap.length} bài)`;
      
      // FIX GĐ 33: Lưu roadmap riêng theo key tên profile
      const val = document.getElementById('profileSelect').value;
      if (val) {
        chrome.storage.local.set({ [`roadmap_${val}`]: currentRoadmapData });
      }
      document.getElementById('status').innerText = `✅ Đã load ${roadmap.length} bài từ file MD!`;
    } else {
      document.getElementById('status').innerText = `❌ Lỗi: Không tìm thấy cấu trúc "## Day X" trong file.`;
    }
  };
  reader.onerror = () => {
    document.getElementById('status').innerText = `❌ Lỗi hệ thống khi đọc file MD.`;
  };
  reader.onloadend = () => { e.target.value = ''; }; // Reset chỉ sau khi đọc xong
  reader.readAsText(file, 'utf-8');
});

function parseMarkdownRoadmap(text) {
  // Tách nội dung theo "## Day "
  const blocks = text.split(/^##\s+Day\s+/gm);
  const roadmap = [];
  
  for (let i = 1; i < blocks.length; i++) { // blocks[0] là header trước "## Day" đầu tiên
    const block = blocks[i];
    
    // Lấy số ngày và tiêu đề (dòng đầu tiên của block)
    const firstLineMatch = block.match(/^(\d+)[^\n]*/);
    if (!firstLineMatch) continue;
    
    const dayNum = parseInt(firstLineMatch[1], 10);
    const dayTitle = firstLineMatch[0].replace(/^\d+/, '').replace(/^[\s—\-:]+/, '').trim();
    
    // Tách phần Prompt
    // Tìm "**Prompt:**" hoặc tương đương
    const promptMatch = block.match(/\*\*Prompt:\*\*([\s\S]*?)(?=\n\*\*|$)/i);
    let promptText = "";
    if (promptMatch && promptMatch[1]) {
      promptText = promptMatch[1].trim();
    } else {
      // Nếu không có "**Prompt:**", lấy đại khái từ sau title đến "**" tiếp theo hoặc hết block
      const afterTitle = block.substring(firstLineMatch[0].length);
      const nextSectionMatch = afterTitle.match(/\*\*/);
      if (nextSectionMatch) {
        promptText = afterTitle.substring(0, nextSectionMatch.index).trim();
      } else {
        promptText = afterTitle.trim();
      }
    }
    
    if (promptText) {
      roadmap.push({
        day: dayNum,
        title: dayTitle,
        prompt: promptText
      });
    }
  }
  return roadmap;
}

// ── Sync trạng thái khi popup mở ─────────────────────────────
async function syncRunningState() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab) return;
  chrome.storage.local.get(['runningStates'], (result) => {
    const states = result.runningStates || {};
    const state = states[tab.id]; // Chỉ lấy trạng thái của Tab hiện tại
    
    // F6b: Kiểm tra heartbeat — nếu loop đã chết (không có heartbeat trong 45s)
    // mà vẫn còn state cũ thì tự clear để không hiện nút STOP sai
    const HEARTBEAT_TIMEOUT = 45000; // 45s
    const heartbeatAge = state && state.lastHeartbeat ? (Date.now() - state.lastHeartbeat) : null;
    const isStale = heartbeatAge !== null && heartbeatAge > HEARTBEAT_TIMEOUT;
    const isAlive = state && state.isRunning && !isStale;
    
    if (isAlive) {
      showRunningBanner(state);
      document.getElementById('startBtn').style.display = 'none';
      document.getElementById('stopBtn').style.display  = 'block';
      document.getElementById('agentInput').value = state.agentName || '';
      document.getElementById('status').innerText = `Loop đang chạy ở Tab này — đóng popup không dừng. Nhấn ⏹ nếu muốn dừng.`;
    } else {
      // State cũ nhưng loop đã chết (heartbeat hết hạn) → tự clean up
      if (state && state.isRunning && isStale) {
        const age = Math.round(heartbeatAge / 1000);
        console.warn(`[AskCpl Popup] Loop state cũ (${age}s không heartbeat) — tự xóa.`);
        delete states[tab.id];
        chrome.storage.local.set({ runningStates: states });
      }
      hideRunningBanner();
      document.getElementById('startBtn').style.display = 'block';
      document.getElementById('stopBtn').style.display  = 'none';
      document.getElementById('status').innerText = 'Sẵn sàng. Chọn Agent hoặc tải phiên cũ để bắt đầu!';
    }
  });
}

function showRunningBanner(state) {
  const banner = document.getElementById('runningBanner');
  banner.style.display = 'block';
  document.getElementById('bannerAgent').textContent = 'Agent: ' + (state.agentName || 'N/A');
  document.getElementById('bannerDay').textContent = state.lastSaved
      ? `Đã lưu đến: ${state.lastSaved}`
      : `Day ${state.currentDay || '?'} đang xử lý...`;
}

function hideRunningBanner() {
  document.getElementById('runningBanner').style.display = 'none';
}

function loadPersistedLogs() {
  chrome.storage.local.get(['popup_logs', 'runningStates'], (r) => {
    const states = r.runningStates || {};
    const hasAnyRunning = Object.values(states).some(s => s && s.isRunning);

    if (r.popup_logs && hasAnyRunning) {
      // Chỉ tải log cũ nếu loop ĐANG THỰC SỰ chạy — tránh gây nhầm lẫn khi Edge restore
      const logArea = document.getElementById('logArea');
      const time = new Date().toLocaleTimeString('vi-VN');
      logArea.value = r.popup_logs.trim() + `\n── [Popup mở lại lúc ${time}] ──\n`;
      logArea.scrollTop = logArea.scrollHeight;
    } else {
      // Loop không chạy → xóa log cũ để tránh nhầm lẫn
      chrome.storage.local.remove(['popup_logs']);
      logArea.value = '';
    }
  });
}

// Init
loadProfiles();
syncRunningState();
loadPersistedLogs();

// ── Nút Start ────────────────────────────────────────────
document.getElementById('startBtn').addEventListener('click', async () => {
  const config = buildConfigFromUI();

  document.getElementById('startBtn').style.display = 'none';
  document.getElementById('stopBtn').style.display  = 'block';
  document.getElementById('status').innerText = 'Đang chạy vòng lặp...';

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab) return;

  // FIX GĐ 44: Lưu roadmapData vào key riêng TRONG storage trước khi gửi message
  // TUYỆT ĐỐI không gửi roadmapData qua IPC sendMessage (quá lớn gây drop im lặng)
  await new Promise(resolve => {
    if (currentRoadmapData && currentRoadmapData.length > 0) {
      chrome.storage.local.set({ roadmap_active: currentRoadmapData }, resolve);
    } else {
      chrome.storage.local.remove(['roadmap_active'], resolve);
    }
  });

  // Strip roadmapData + days khỏi session trước khi gửi (giảm kích thước IPC message)
  let sessionMeta = null;
  if (loadedSession) {
    sessionMeta = Object.assign({}, loadedSession);
    delete sessionMeta.roadmapData; // Đã lưu riêng ở roadmap_active
  }

  const payload = {
    action: loadedSession ? "resume_session" : "start_loop",
    tabId: tab.id,
    session: sessionMeta,         // không có roadmapData
    platform: config.platform,
    prefix: config.prefix,
    currentDay: config.startDay,
    endDay: config.endDay,
    agentName: config.agentName,
    promptMode: config.promptMode,
    isAdvanced: config.isAdvanced,
    topicPrompt: config.topicPrompt,
    targetCount: config.targetCount,
    details: config.details,
    roadmapData: currentRoadmapData
  };

  chrome.tabs.sendMessage(tab.id, payload).catch(() => {
    showError('Không tìm thấy Addon trên trang này. Hãy F5 trang Copilot.');
  });
});

// ── Nút Stop ─────────────────────────────────────────────────
document.getElementById('stopBtn').addEventListener('click', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab) return;
  
  chrome.tabs.sendMessage(tab.id, { action: "stop_loop" }).catch(() => {});
  
  document.getElementById('startBtn').style.display = 'block';
  document.getElementById('stopBtn').style.display  = 'none';
  document.getElementById('status').innerText = 'Đang lưu index & session...';
  loadedSession = null;
  hideRunningBanner();
  
  chrome.storage.local.get(['runningStates'], (res) => {
    const states = res.runningStates || {};
    delete states[tab.id];
    chrome.storage.local.set({ runningStates: states });
  });
  
  chrome.storage.local.remove(['popup_logs']);
});

// ── Nút Recover (từ chrome.storage) ──────────────────────────
document.getElementById('recoverBtn').addEventListener('click', async () => {
  chrome.storage.local.get(['autosave_data', 'autosave_name', 'autosave_day'], (result) => {
    if (!result.autosave_data || result.autosave_data.length === 0) {
      document.getElementById('status').innerText = 'Không có dữ liệu cũ nào trong storage.';
      return;
    }
    const name  = result.autosave_name || 'Copilot';
    const count = result.autosave_data.length;
    document.getElementById('status').innerText = `Đang tải lại ${count} bài từ [${name}]...`;

    const safeName = name.replace(/[^a-zA-Z0-9_\u00A0-\uFFFF]/g, '_');
    const fileName = `${safeName}_RECOVERED_${new Date().toISOString().slice(0,10).replace(/-/g,'')}.json`;
    const dataStr  = JSON.stringify(result.autosave_data, null, 2);

    chrome.runtime.sendMessage({
      action: "download_json",
      data: dataStr,
      filename: fileName
    }).then(() => {
      document.getElementById('status').innerText = `✅ Đã tải lại ${count} bài thành công!`;
      document.getElementById('recoverBtn').style.display = 'none';
      chrome.storage.local.remove(['autosave_data', 'autosave_name', 'autosave_day', 'autosave_folder']);
    }).catch(e => {
      document.getElementById('status').innerText = 'Lỗi khi tải lại: ' + e.message;
    });
  });
});

// ── File Picker: session.json ─────────────────────────────────
document.getElementById('loadSessionBtn').addEventListener('click', () => {
  document.getElementById('sessionFileInput').click();
});

document.getElementById('sessionFileInput').addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (ev) => {
    try {
      const session = JSON.parse(ev.target.result);
      
      // Fallback cho file cũ: Tự lấy agentName từ folderName, nếu không có mặc định là "Copilot"
      if (!session.agentName) {
          session.agentName = session.folderName || "Copilot";
      }
      
      // Fallback cho lastDay: Nếu undefined, tự đếm số ngày đã lưu
      if (session.lastDay === undefined) {
          session.lastDay = session.days ? session.days.length : 0;
      }
      
      // Nếu file nạp vào thực sự không chứa một format nào quen thuộc (không có mảng days, lastDay hay folderName) thì mới báo lỗi
      if (session.lastDay === undefined && !session.folderName && !session.agentName) {
        document.getElementById('status').innerText = '❌ File JSON không hợp lệ (Không nhận diện được cấu trúc).';
        return;
      }

      loadedSession = session;
      document.getElementById('platformSelect').value = session.platform || 'copilot';
      document.getElementById('agentInput').value     = session.agentName;
      document.getElementById('prefixInput').value    = session.prefix || 'Day ';
      document.getElementById('startDayInput').value  = (session.lastDay || 0) + 1;
      document.getElementById('agentInput').style.border = '2px solid #5c6bc0';

      // Restore Advanced / Prompt Mode settings
      if (session.promptMode) {
          const modeSelect = document.getElementById('promptModeSelect');
          if (modeSelect) {
              modeSelect.value = session.promptMode;
              updatePromptModeUI(session.promptMode);
          }
      } else if (session.isAdvanced) {
          document.getElementById('promptModeSelect').value = 'advanced';
          updatePromptModeUI('advanced');
      }
      
      if (session.topicPromptStr) {
          const tpInput = document.getElementById('topicPromptInput');
          if (tpInput) tpInput.value = session.topicPromptStr;
      }
      if (session.targetCount) {
          const tcInput = document.getElementById('targetCountInput');
          if (tcInput) tcInput.value = session.targetCount;
      }
      if (session.details && Array.isArray(session.details)) {
          const container = document.getElementById('detailsContainer');
          if (container) {
              container.innerHTML = ''; // clear old
              session.details.forEach(d => addDetailUI(d.name, d.prompt));
          }
      }

      // FIX GĐ 33: Roadmap từ session.json — chỉ dùng trong bộ nhớ, không dump vào HTML
      currentRoadmapData = session.roadmapData || null;
      updateRoadmapPreview(currentRoadmapData); // An toàn: chỉ hiện summary

      const infoEl = document.getElementById('sessionInfo');
      infoEl.style.display = 'block';
      infoEl.innerHTML = `
        <strong>📁 ${escapeHtml(session.agentName)}</strong><br>
        Đã lưu: <strong>${session.totalSaved || session.days?.length || 0} bài</strong>
        (đến ${session.prefix || 'Day '}${session.lastDay})<br>
        ▶ Sẽ tiếp tục từ: <strong>${session.prefix || 'Day '}${(session.lastDay || 0) + 1}</strong>
      `;
      document.getElementById('clearSessionBtn').style.display = 'block';
      document.getElementById('status').innerText = `✅ Đã tải phiên: ${session.agentName}. Nhấn Start!`;
    } catch (err) {
      document.getElementById('status').innerText = '❌ Lỗi đọc file JSON: ' + err.message;
    }
  };
  reader.onerror = () => {
    document.getElementById('status').innerText = '❌ Lỗi hệ thống: Không thể đọc file này.';
  };
  reader.onloadend = () => {
    e.target.value = ''; // Reset file input ONLY after read completes or fails
  };
  reader.readAsText(file, 'utf-8');
});

document.getElementById('clearSessionBtn').addEventListener('click', () => {
  loadedSession = null;
  document.getElementById('sessionInfo').style.display    = 'none';
  document.getElementById('clearSessionBtn').style.display = 'none';
  document.getElementById('agentInput').style.border      = '';
  document.getElementById('status').innerText = 'Đã bỏ chọn phiên. Sẵn sàng chạy mới.';
});

// ── Helpers ───────────────────────────────────────────────────
function showError(msg) {
  document.getElementById('status').innerText = 'Lỗi: ' + msg;
  document.getElementById('startBtn').style.display = 'block';
  document.getElementById('stopBtn').style.display  = 'none';
}
function escapeHtml(str) {
  if (!str) return '';
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ── Message Listener từ content script ───────────────────────
chrome.runtime.onMessage.addListener((message) => {
  if (message.action === "update_status") {
    document.getElementById('status').innerText = message.text;
  }
  if (message.action === "day_saved") {
    document.getElementById('status').innerText = `✅ Đã lưu ${message.dayLabel} — Tổng: ${message.totalSaved} bài`;
    // F6b: Fix key sai: dùng 'runningStates' (plural) thay vì 'runningState'
    chrome.storage.local.get(['runningStates'], (r) => {
      chrome.tabs.query({ active: true, currentWindow: true }, ([tab]) => {
        if (!tab) return;
        const state = (r.runningStates || {})[tab.id];
        if (state?.isRunning) showRunningBanner(state);
      });
    });
  }
  if (message.action === "update_agent_name") {
    const agentInput = document.getElementById('agentInput');
    if (agentInput && agentInput.value.trim() === '') {
      agentInput.value = message.name;
      agentInput.style.border = '2px solid #107c10';
    }
  }
  if (message.action === "loop_finished") {
    document.getElementById('startBtn').style.display = 'block';
    document.getElementById('stopBtn').style.display  = 'none';
    document.getElementById('status').innerText = message.text || '✅ Đã hoàn tất!';
    loadedSession = null;
    hideRunningBanner();
    chrome.storage.local.remove(['runningState']);
  }
  if (message.action === "has_autosave") {
    document.getElementById('recoverBtn').style.display = 'block';
    document.getElementById('startDayInput').value = message.lastDay || 1;
  }
  if (message.action === "add_log") {
    const logArea = document.getElementById('logArea');
    logArea.value += message.text + '\n';
    logArea.scrollTop = logArea.scrollHeight;
  }
});
