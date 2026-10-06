/**
 * MBC Quản Lý Công Việc & Hiệu Suất Nhóm
 * Core JavaScript Logic - Phiên bản 2.6
 * - Hỗ trợ xem Toàn cảnh: Theo Ngày, Theo Tuần, Theo Tháng (cả năm & năm sau)
 * - Mũi tên Gantt Excel liền mạch, không đứt đoạn
 * - Cấu hình tiêu đề báo cáo Excel linh hoạt
 * - Phân cấp Công việc chính & Công việc con (Parent Task & Subtasks)
 * - Chọn nhanh công việc chưa hoàn thành để cập nhật tiến độ
 */

// ================= CONSTANTS & STATE =================
const STORAGE_KEY = 'MBC_WORK_MANAGEMENT_DATA_V2';

let appData = {
  version: '2.6',
  currentUser: {
    id: 'admin',
    name: 'Quản trị viên (Admin)',
    role: 'admin',
    dept: 'Ban Quản Trị'
  },
  employees: [],
  tasks: []
};

// View State
let viewState = {
  timeScale: 'DAY', // 'DAY', 'WEEK', 'MONTH'
  windowMode: '10', // '10', '15', 'month'
  startOffsetDate: '2026-10-01',
  filterEmp: 'ALL',
  filterMonth: '2026-10',
  filterStartDate: '',
  filterEndDate: '',
  filterYear: '2026',
  filterStatus: 'CHUA_HOAN_THANH', // Mặc định là các việc có chữ Hoàn thành sẽ không hiện ra
  filterKeyword: '',
  groupByParent: false
};

// ================= HÀM HỖ TRỢ XÁC ĐỊNH KHOẢNG NĂM & CÔNG VIỆC CHÍNH =================
function getTasksYearSpan() {
  let minY = 2026;
  let maxY = 2029;
  if (appData && Array.isArray(appData.tasks)) {
    appData.tasks.forEach(t => {
      const s = parseDate(t.startDate);
      const e = parseDate(t.actualEndDate || t.planEndDate);
      if (s) {
        minY = Math.min(minY, s.getFullYear());
        maxY = Math.max(maxY, s.getFullYear());
      }
      if (e) {
        minY = Math.min(minY, e.getFullYear());
        maxY = Math.max(maxY, e.getFullYear());
      }
    });
  }
  return { minYear: minY, maxYear: Math.max(maxY, 2029) };
}

function getMainTaskProgress(mainTaskId) {
  if (!mainTaskId || !appData || !Array.isArray(appData.tasks)) return null;
  const subtasks = appData.tasks.filter(t => t.mainTaskId === mainTaskId);
  if (subtasks.length === 0) return null;
  const completedCount = subtasks.filter(t => t.status && t.status.includes('Hoàn thành')).length;
  const totalCount = subtasks.length;
  const isAllCompleted = totalCount > 0 && completedCount === totalCount;
  return {
    mainTaskId,
    completedCount,
    totalCount,
    isAllCompleted,
    percent: Math.round((completedCount / totalCount) * 100)
  };
}

// ================= HÀM XỬ LÝ NGÀY THÁNG =================
function parseDate(dStr) {
  if (!dStr) return null;
  const parts = dStr.split('-');
  if (parts.length === 3) {
    return new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]));
  }
  return null;
}

function formatDate(d) {
  if (!d) return '';
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function formatVnDate(dStr) {
  if (!dStr) return '';
  const p = dStr.split('-');
  if (p.length === 3) {
    return `${p[2]}/${p[1]}/${p[0]}`;
  }
  return dStr;
}

function addDays(d, n) {
  const res = new Date(d);
  res.setDate(res.getDate() + n);
  return res;
}

function dateDiffInDays(d1, d2) {
  const dt1 = new Date(d1.getFullYear(), d1.getMonth(), d1.getDate());
  const dt2 = new Date(d2.getFullYear(), d2.getMonth(), d2.getDate());
  const diffTime = dt2 - dt1;
  return Math.round(diffTime / (1000 * 60 * 60 * 24));
}

// ================= LƯU TRỮ LOCALSTORAGE & NẠP DỮ LIỆU BAN ĐẦU =================
async function loadInitialData() {
  // LỚP 1: Kiểm tra LocalStorage xem người dùng đã có dữ liệu lưu trữ hợp lệ chưa
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (parsed && Array.isArray(parsed.employees) && Array.isArray(parsed.tasks) && parsed.tasks.length > 0) {
        appData = parsed;
        console.log(`[MBC Data] Nạp thành công dữ liệu từ LocalStorage: ${appData.tasks.length} công việc, ${appData.employees.length} nhân sự`);
        return;
      }
    }
  } catch (err) {
    console.warn('[MBC Data] Lỗi đọc LocalStorage:', err);
  }

  // LỚP 2: Xem xét và nạp từ window.MBC_DEFAULT_DATABASE (được nạp sẵn từ database.js qua thẻ <script>, không bị CORS chặn)
  if (typeof window !== 'undefined' && window.MBC_DEFAULT_DATABASE && Array.isArray(window.MBC_DEFAULT_DATABASE.tasks) && window.MBC_DEFAULT_DATABASE.tasks.length > 0) {
    console.log(`[MBC Data] Nạp dữ liệu mặc định từ database.js: ${window.MBC_DEFAULT_DATABASE.tasks.length} công việc`);
    appData = JSON.parse(JSON.stringify(window.MBC_DEFAULT_DATABASE));
    saveDataToStorage();
    return;
  }

  // LỚP 3: Nếu chạy trên Web Server (http/https), nạp từ file database.json
  try {
    const res = await fetch('database.json');
    if (res.ok) {
      const data = await res.json();
      if (data && Array.isArray(data.tasks) && data.tasks.length > 0) {
        console.log(`[MBC Data] Nạp dữ liệu từ database.json qua fetch: ${data.tasks.length} công việc`);
        appData = data;
        saveDataToStorage();
        return;
      }
    }
  } catch (err) {
    console.log('[MBC Data] Môi trường file:// không hỗ trợ fetch, ưu tiên dùng database.js');
  }
}

function saveDataToStorage() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(appData));
  } catch (err) {
    console.error('Lỗi lưu LocalStorage:', err);
  }
}

// ================= TÍNH TOÁN ĐIỂM HIỆU SUẤT (PERFORMANCE POINTS) =================
function calculateTaskScoreImpact(task) {
  const planDays = Math.max(1, parseInt(task.planDays) || 1);
  const planEnd = parseDate(task.planEndDate);
  if (!planEnd) return { delta: 0, reason: 'Chưa đủ dữ liệu' };

  const isCompleted = task.status === 'Hoàn thành' || task.status === 'Hoàn thành trễ';
  let actualEnd = null;

  if (isCompleted) {
    actualEnd = parseDate(task.actualEndDate) || planEnd;
  } else {
    const today = new Date(2026, 9, 5);
    if (today > planEnd) {
      actualEnd = today;
    } else {
      return { delta: 0, reason: 'Đang làm trong hạn' };
    }
  }

  const delayDays = dateDiffInDays(planEnd, actualEnd);

  if (delayDays <= 0) {
    if (isCompleted) {
      return { delta: +3, reason: 'Hoàn thành đúng hạn (+3đ)' };
    } else {
      return { delta: 0, reason: 'Đang làm trong hạn' };
    }
  }

  if (delayDays >= 30) {
    const months = Math.floor(delayDays / 30);
    const penalty = -(months * 9);
    return { delta: penalty, reason: `Trễ ${delayDays} ngày (> ${months} tháng): ${penalty}đ` };
  } else {
    const ratio = delayDays / planDays;
    if (ratio <= 0.5) {
      return { delta: -1, reason: `Trễ ${delayDays} ngày (<= 50% dự kiến): -1đ` };
    } else if (ratio <= 1.0) {
      return { delta: -2, reason: `Trễ ${delayDays} ngày (<= 100% dự kiến): -2đ` };
    } else {
      return { delta: -3, reason: `Trễ ${delayDays} ngày (> 100% dự kiến): -3đ` };
    }
  }
}

function calculateEmployeeMonthlyScores(empId, year) {
  const monthlyScores = {};
  for (let m = 1; m <= 12; m++) {
    monthlyScores[m] = 100;
  }

  const empTasks = appData.tasks.filter(t => t.empId === empId);

  empTasks.forEach(task => {
    if (!task.startDate) return;
    const d = parseDate(task.startDate);
    if (d && d.getFullYear() === year) {
      const m = d.getMonth() + 1;
      const impact = calculateTaskScoreImpact(task);
      monthlyScores[m] += impact.delta;
    }
  });

  return monthlyScores;
}

// ================= PHÂN QUYỀN VÀ TÀI KHOẢN (AUTH & ROLES) =================
function renderUserDropdown() {
  const container = document.getElementById('userListDropdown');
  if (!container) return;

  let html = `
    <button onclick="switchUser('admin')" class="w-full text-left px-3 py-2 text-xs flex items-center justify-between hover:bg-slate-100 transition ${appData.currentUser.role === 'admin' ? 'bg-sky-50 font-bold text-sky-800' : 'text-slate-700'}">
      <div class="flex items-center gap-2">
        <span class="w-6 h-6 rounded-full bg-brand-700 text-white flex items-center justify-center text-[10px] font-bold">AD</span>
        <div>
          <div class="font-bold">Quản trị viên (Admin)</div>
          <div class="text-[10px] text-slate-400">Toàn quyền hệ thống</div>
        </div>
      </div>
      ${appData.currentUser.role === 'admin' ? '<i class="fa-solid fa-check text-sky-600"></i>' : ''}
    </button>
    <div class="my-1 border-t border-slate-100"></div>
  `;

  appData.employees.forEach(emp => {
    const isCurrent = appData.currentUser.role === 'employee' && appData.currentUser.id === emp.id;
    const initials = emp.name.split(' ').map(n => n[0]).slice(-2).join('').toUpperCase();
    html += `
      <button onclick="switchUser('${emp.id}')" class="w-full text-left px-3 py-2 text-xs flex items-center justify-between hover:bg-slate-100 transition ${isCurrent ? 'bg-sky-50 font-bold text-sky-800' : 'text-slate-700'}">
        <div class="flex items-center gap-2">
          <span class="w-6 h-6 rounded-full bg-slate-600 text-white flex items-center justify-center text-[10px] font-bold">${initials}</span>
          <div>
            <div class="font-medium">${emp.name} <span class="text-[10px] text-slate-400">(${emp.id})</span></div>
            <div class="text-[10px] text-slate-400">${emp.dept || 'Nhân viên'}</div>
          </div>
        </div>
        ${isCurrent ? '<i class="fa-solid fa-check text-sky-600"></i>' : ''}
      </button>
    `;
  });

  container.innerHTML = html;
}

function switchUser(userId) {
  if (userId === 'admin') {
    appData.currentUser = {
      id: 'admin',
      name: 'Quản trị viên (Admin)',
      role: 'admin',
      dept: 'Ban Quản Trị'
    };
  } else {
    const emp = appData.employees.find(e => e.id === userId);
    if (emp) {
      appData.currentUser = {
        id: emp.id,
        name: emp.name,
        role: 'employee',
        dept: emp.dept
      };
      viewState.filterEmp = emp.id;
      document.getElementById('filterEmployee').value = emp.id;
    }
  }

  saveDataToStorage();
  updateAuthUI();
  closeUserDropdown();
  applyFilters();
}

function updateAuthUI() {
  const user = appData.currentUser;
  const avatarEl = document.getElementById('currentUserAvatar');
  const nameEl = document.getElementById('currentUserName');
  const roleEl = document.getElementById('currentUserRole');
  const btnAddTask = document.getElementById('btnAddTask');
  const btnManageEmp = document.getElementById('btnManageEmp');

  if (user.role === 'admin') {
    avatarEl.innerText = 'AD';
    avatarEl.className = 'w-7 h-7 rounded-full bg-brand-700 text-white flex items-center justify-center font-bold text-xs';
    nameEl.innerText = user.name;
    roleEl.innerText = 'Admin - Toàn quyền';
    roleEl.className = 'text-[10px] text-emerald-600 font-semibold uppercase tracking-wider';

    btnAddTask.style.display = 'inline-flex';
    btnManageEmp.style.display = 'inline-flex';
  } else {
    const initials = user.name.split(' ').map(n => n[0]).slice(-2).join('').toUpperCase();
    avatarEl.innerText = initials;
    avatarEl.className = 'w-7 h-7 rounded-full bg-slate-600 text-white flex items-center justify-center font-bold text-xs';
    nameEl.innerText = `${user.name} (${user.id})`;
    roleEl.innerText = `Nhân viên - ${user.dept}`;
    roleEl.className = 'text-[10px] text-sky-600 font-semibold uppercase tracking-wider';

    btnAddTask.style.display = 'none';
    btnManageEmp.style.display = 'none';
  }
}

function toggleUserDropdown() {
  const el = document.getElementById('userDropdown');
  el.classList.toggle('hidden');
  renderUserDropdown();
}

function closeUserDropdown() {
  const el = document.getElementById('userDropdown');
  if (el) el.classList.add('hidden');
}

// ================= GOM NHÓM & SẮP XẾP CÔNG VIỆC CÙNG DỰ ÁN LIỀN NHAU =================
function groupAndSortTasks(taskList) {
  if (!taskList || taskList.length === 0) return [];

  // Tạo Map gom nhóm: key ưu tiên theo mainTaskId, nếu không có thì mainTaskTitle, sau đó title
  const groups = new Map();
  const groupOrder = [];

  taskList.forEach(task => {
    const rawKey = (task.mainTaskId || task.mainTaskTitle || task.title || 'CV-KHAC').trim().toUpperCase();
    if (!groups.has(rawKey)) {
      groups.set(rawKey, []);
      groupOrder.push(rawKey);
    }
    groups.get(rawKey).push(task);
  });

  const sortedTasks = [];
  groupOrder.forEach(key => {
    const items = groups.get(key);
    // Sắp xếp các công việc con trong nhóm theo Ngày bắt đầu tăng dần, sau đó theo ID
    items.sort((a, b) => {
      const da = parseDate(a.startDate) || new Date(0);
      const db = parseDate(b.startDate) || new Date(0);
      if (da.getTime() !== db.getTime()) return da.getTime() - db.getTime();
      return (a.id || '').localeCompare(b.id || '');
    });
    sortedTasks.push(...items);
  });

  return sortedTasks;
}

// Tự động thu phóng Timeline vừa vặn ngày đầu đến đúng hạn cuối công việc (Không thừa, không kẹt 365 ngày)
function fitTimelineToTaskDates() {
  const currentTasks = appData.tasks.filter(t => {
    if (appData.currentUser.role === 'employee' && t.empId !== appData.currentUser.id) return false;
    if (viewState.filterEmp !== 'ALL' && t.empId !== viewState.filterEmp) return false;
    return true;
  });

  if (currentTasks.length === 0) {
    alert('Không có công việc nào để tính toán khung thời gian!');
    return;
  }

  let minStart = null;
  let maxEnd = null;

  currentTasks.forEach(t => {
    const s = parseDate(t.startDate);
    const e = parseDate(t.actualEndDate || t.planEndDate);
    if (s && (!minStart || s < minStart)) minStart = s;
    if (e && (!maxEnd || e > maxEnd)) maxEnd = e;
  });

  if (!minStart || !maxEnd) {
    alert('Các công việc chưa có đủ ngày bắt đầu và kết thúc!');
    return;
  }

  const sStr = formatDateIso(minStart);
  const eStr = formatDateIso(maxEnd);

  viewState.filterStartDate = sStr;
  viewState.filterEndDate = eStr;

  const inputStart = document.getElementById('filterStartDate');
  const inputEnd = document.getElementById('filterEndDate');
  if (inputStart) inputStart.value = sStr;
  if (inputEnd) inputEnd.value = eStr;

  viewState.timeScale = 'DAY';
  updateTimeScaleButtons('DAY');
  applyFilters();
}

// Bật/tắt nhanh trạng thái Tạm dừng cho công việc
function toggleTaskPause(taskId) {
  const task = appData.tasks.find(t => t.id === taskId);
  if (!task) return;
  if (task.status === 'Tạm dừng' || task.status === 'Dừng dự án') {
    task.status = 'Đang làm';
  } else {
    task.status = 'Tạm dừng';
  }
  saveDataToStorage();
  applyFilters();
}

// ================= TIMELINE BUILDER: GIỜ, NGÀY, TUẦN, THÁNG, NĂM =================
function getTimelineColumns() {
  const cols = [];

  if (viewState.timeScale === 'HOUR') {
    // Chế độ xem theo Giờ: Các mốc giờ từ 07:00 đến 19:00 trong ngày
    const baseDate = parseDate(viewState.filterStartDate || viewState.startOffsetDate) || new Date(2026, 9, 1);
    const y = baseDate.getFullYear();
    const m = baseDate.getMonth();
    const d = baseDate.getDate();

    for (let h = 7; h <= 19; h++) {
      const hStr = `${String(h).padStart(2, '0')}:00`;
      const sH = new Date(y, m, d, h, 0, 0);
      const eH = new Date(y, m, d, h, 59, 59);
      cols.push({
        type: 'HOUR',
        label: hStr,
        subLabel: `${String(d).padStart(2, '0')}/${String(m + 1).padStart(2, '0')}`,
        startDate: sH,
        endDate: eH,
        isWeekend: baseDate.getDay() === 0 || baseDate.getDay() === 6
      });
    }
  } else if (viewState.timeScale === 'YEAR') {
    // Chế độ xem theo Năm: các năm từ minYear đến maxYear của dữ liệu
    const { minYear, maxYear } = getTasksYearSpan();
    for (let y = minYear; y <= maxYear; y++) {
      cols.push({
        type: 'YEAR',
        year: y,
        label: `Năm ${y}`,
        subLabel: '12 Tháng',
        startDate: new Date(y, 0, 1),
        endDate: new Date(y, 11, 31, 23, 59, 59)
      });
    }
  } else if (viewState.timeScale === 'MONTH') {
    // Chế độ xem theo Tháng: hiển thị tất cả các tháng từ minYear đến maxYear (ví dụ 2026 -> 2029...)
    const { minYear, maxYear } = getTasksYearSpan();
    for (let y = minYear; y <= maxYear; y++) {
      for (let m = 1; m <= 12; m++) {
        cols.push({
          type: 'MONTH',
          year: y,
          month: m,
          label: `T${m}/${y.toString().slice(-2)}`,
          subLabel: `${y}`,
          startDate: new Date(y, m - 1, 1),
          endDate: new Date(y, m, 0, 23, 59, 59)
        });
      }
    }
  } else if (viewState.timeScale === 'WEEK') {
    // Chế độ xem theo Tuần: 12 tuần liên tiếp
    const baseDate = parseDate(viewState.startOffsetDate) || new Date(2026, 9, 1);
    for (let w = 0; w < 12; w++) {
      const wStart = addDays(baseDate, w * 7);
      const wEnd = addDays(wStart, 6);
      cols.push({
        type: 'WEEK',
        label: `Tuần ${w + 1}`,
        subLabel: `${wStart.getDate()}/${wStart.getMonth()+1} - ${wEnd.getDate()}/${wEnd.getMonth()+1}/${wEnd.getFullYear().toString().slice(-2)}`,
        startDate: wStart,
        endDate: wEnd
      });
    }
  } else {
    // Chế độ xem theo Ngày (mặc định hoặc khoảng ngày tự do)
    const dayNames = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7'];

    // Nếu người dùng chọn khoảng ngày tự do Từ ngày -> Đến ngày (Không giới hạn cứng 365 ngày)
    if (viewState.filterStartDate && viewState.filterEndDate) {
      const sDate = parseDate(viewState.filterStartDate);
      const eDate = parseDate(viewState.filterEndDate);
      if (sDate && eDate && sDate <= eDate) {
        const totalDays = dateDiffInDays(sDate, eDate) + 1;
        for (let i = 0; i < totalDays; i++) {
          const d = addDays(sDate, i);
          const isWeekend = d.getDay() === 0 || d.getDay() === 6;
          cols.push({
            type: 'DAY',
            date: d,
            label: `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}`,
            subLabel: dayNames[d.getDay()],
            yearLabel: d.getFullYear(),
            isWeekend,
            startDate: d,
            endDate: d
          });
        }
        return cols;
      }
    }

    // Nếu xem theo khung ngày chuẩn (10 ngày, 15 ngày, hoặc cả tháng)
    const baseDate = parseDate(viewState.startOffsetDate) || new Date(2026, 9, 1);
    let totalDays = 10;
    if (viewState.windowMode === '10') totalDays = 10;
    else if (viewState.windowMode === '15') totalDays = 15;
    else if (viewState.windowMode === 'month') {
      const y = baseDate.getFullYear();
      const m = baseDate.getMonth();
      totalDays = new Date(y, m + 1, 0).getDate();
    }

    for (let i = 0; i < totalDays; i++) {
      const d = addDays(baseDate, i);
      const isWeekend = d.getDay() === 0 || d.getDay() === 6;
      cols.push({
        type: 'DAY',
        date: d,
        label: `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}`,
        subLabel: dayNames[d.getDay()],
        yearLabel: d.getFullYear(),
        isWeekend,
        startDate: d,
        endDate: d
      });
    }
  }

  return cols;
}

// Cập nhật giao diện các nút chọn đơn vị thời gian
function updateTimeScaleButtons(scale) {
  const btnHour = document.getElementById('btnScaleHour');
  const btnDay = document.getElementById('btnScaleDay');
  const btnWeek = document.getElementById('btnScaleWeek');
  const btnMonth = document.getElementById('btnScaleMonth');
  const btnYear = document.getElementById('btnScaleYear');
  const dayWindowControls = document.getElementById('dayWindowControls');

  const normalClass = 'px-2 py-1 rounded font-semibold text-slate-600 hover:bg-white text-xs transition';
  const activeClass = 'px-2.5 py-1 rounded font-bold bg-white text-brand-700 shadow-sm text-xs transition';

  if (btnHour) btnHour.className = normalClass;
  if (btnDay) btnDay.className = normalClass;
  if (btnWeek) btnWeek.className = normalClass;
  if (btnMonth) btnMonth.className = normalClass;
  if (btnYear) btnYear.className = normalClass;

  if (scale === 'HOUR') {
    if (btnHour) btnHour.className = activeClass;
    if (dayWindowControls) dayWindowControls.style.display = 'none';
  } else if (scale === 'DAY') {
    if (btnDay) btnDay.className = activeClass;
    if (dayWindowControls) dayWindowControls.style.display = 'flex';
  } else if (scale === 'WEEK') {
    if (btnWeek) btnWeek.className = activeClass;
    if (dayWindowControls) dayWindowControls.style.display = 'none';
  } else if (scale === 'MONTH') {
    if (btnMonth) btnMonth.className = activeClass;
    if (dayWindowControls) dayWindowControls.style.display = 'none';
  } else if (scale === 'YEAR') {
    if (btnYear) btnYear.className = activeClass;
    if (dayWindowControls) dayWindowControls.style.display = 'none';
  }
}

// Thay đổi chế độ xem (Giờ / Ngày / Tuần / Tháng / Năm)
function setTimeScale(scale) {
  viewState.timeScale = scale;
  updateTimeScaleButtons(scale);
  renderMainTable();
}

// ================= RENDER BẢNG GANTT & TIMELINE =================
function renderMainTable() {
  const timelineCols = getTimelineColumns();
  const headerRow = document.getElementById('tableHeaderRow');

  while (headerRow.children.length > 10) {
    headerRow.removeChild(headerRow.lastChild);
  }

  timelineCols.forEach(col => {
    const th = document.createElement('th');
    const isWeekend = col.isWeekend;
    th.className = `p-1.5 border-r border-slate-300 text-center min-w-[54px] max-w-[70px] font-semibold text-[10px] ${isWeekend ? 'bg-amber-50 text-amber-900' : 'bg-slate-100 text-slate-700'}`;

    if (col.type === 'HOUR') {
      th.className = 'p-1.5 border-r border-slate-300 text-center min-w-[50px] font-semibold text-[10px] bg-slate-100 text-slate-700';
      th.innerHTML = `
        <div class="font-extrabold text-sky-700">${col.label}</div>
        <div class="text-[8px] text-slate-400 font-normal">${col.subLabel}</div>
      `;
    } else if (col.type === 'YEAR') {
      th.className = 'p-1.5 border-r border-slate-300 text-center min-w-[80px] font-semibold text-[11px] bg-slate-100 text-slate-700';
      th.innerHTML = `
        <div class="font-black text-brand-800 text-xs">${col.label}</div>
        <div class="text-[9px] text-slate-400">${col.subLabel}</div>
      `;
    } else if (col.type === 'MONTH') {
      th.className = 'p-1.5 border-r border-slate-300 text-center min-w-[65px] font-semibold text-[11px] bg-slate-100 text-slate-700';
      th.innerHTML = `
        <div class="text-[9px] text-sky-600 font-bold">${col.subLabel}</div>
        <div class="font-extrabold text-slate-800">${col.label}</div>
      `;
    } else if (col.type === 'WEEK') {
      th.className = 'p-1.5 border-r border-slate-300 text-center min-w-[75px] font-semibold text-[10px] bg-slate-100 text-slate-700';
      th.innerHTML = `
        <div class="font-bold text-slate-800">${col.label}</div>
        <div class="text-[8px] text-slate-400 font-normal">${col.subLabel}</div>
      `;
    } else {
      th.innerHTML = `
        <div class="text-[9px] text-slate-400 font-normal">${col.subLabel}</div>
        <div class="font-bold text-slate-800">${col.label}</div>
        <div class="text-[8px] text-slate-400">${col.yearLabel}</div>
      `;
    }
    headerRow.appendChild(th);
  });

  // Lọc danh sách công việc
  let filteredTasks = appData.tasks.filter(task => {
    if (appData.currentUser.role === 'employee' && task.empId !== appData.currentUser.id) return false;
    if (viewState.filterEmp !== 'ALL' && task.empId !== viewState.filterEmp) return false;

    // LỌC TÌNH TRẠNG (Yêu cầu 1: Mặc định ẩn việc có chữ Hoàn thành)
    if (viewState.filterStatus === 'CHUA_HOAN_THANH') {
      if (task.status && task.status.includes('Hoàn thành')) return false;
    } else if (viewState.filterStatus === 'HOAN_THANH_ALL') {
      if (!task.status || !task.status.includes('Hoàn thành')) return false;
    } else if (viewState.filterStatus === 'DANG_LAM') {
      if (task.status !== 'Đang làm') return false;
    } else if (viewState.filterStatus === 'Tạm dừng') {
      if (task.status !== 'Tạm dừng' && task.status !== 'Dừng dự án') return false;
    } else if (viewState.filterStatus === 'QUA_HAN') {
      const today = new Date(2026, 9, 5);
      const planEnd = parseDate(task.planEndDate);
      if (task.status && (task.status.includes('Hoàn thành') || task.status === 'Tạm dừng' || task.status === 'Dừng dự án')) return false;
      if (!planEnd || today <= planEnd) return false;
    } else if (viewState.filterStatus !== 'ALL') {
      if (task.status !== viewState.filterStatus) return false;
    }

    if (viewState.filterKeyword) {
      const kw = viewState.filterKeyword.toLowerCase().trim();
      const matchTitle = (task.title || '').toLowerCase().includes(kw);
      const matchDetail = (task.detail || '').toLowerCase().includes(kw);
      const matchEmp = (task.empName || '').toLowerCase().includes(kw);
      const matchNote = (task.note || '').toLowerCase().includes(kw);
      const matchMain = (task.mainTaskTitle || '').toLowerCase().includes(kw);
      if (!matchTitle && !matchDetail && !matchEmp && !matchNote && !matchMain) return false;
    }

    // LỌC THỜI GIAN:
    // Nếu có lọc theo khoảng ngày tự do (Từ ngày -> Đến ngày)
    if (viewState.filterStartDate && viewState.filterEndDate) {
      const rStart = parseDate(viewState.filterStartDate);
      const rEnd = parseDate(viewState.filterEndDate);
      const tStart = parseDate(task.startDate);
      const tEnd = parseDate(task.actualEndDate || task.planEndDate);
      if (rStart && rEnd && tStart && tEnd) {
        if (tStart > rEnd || tEnd < rStart) return false;
      }
    } else if (viewState.timeScale === 'DAY' && viewState.filterMonth) {
      // Nếu lọc theo tháng trong chế độ ngày
      const [fYear, fMonth] = viewState.filterMonth.split('-').map(Number);
      const tStart = parseDate(task.startDate);
      const tEnd = parseDate(task.actualEndDate || task.planEndDate);
      if (tStart && tEnd) {
        const startCheck = tStart.getFullYear() === fYear && (tStart.getMonth() + 1) === fMonth;
        const endCheck = tEnd.getFullYear() === fYear && (tEnd.getMonth() + 1) === fMonth;
        if (!startCheck && !endCheck && !(tStart < new Date(fYear, fMonth - 1, 1) && tEnd > new Date(fYear, fMonth, 0))) {
          return false;
        }
      }
    }

    return true;
  });

  // GOM NHÓM & SẮP XẾP: Các việc cùng chung công việc chính luôn xếp liền kề nhau
  filteredTasks = groupAndSortTasks(filteredTasks);

  document.getElementById('tableRecordCount').innerText = `Hiển thị: ${filteredTasks.length} công việc`;

  const tbody = document.getElementById('tableBody');
  const emptyState = document.getElementById('emptyState');
  tbody.innerHTML = '';

  if (filteredTasks.length === 0) {
    emptyState.classList.remove('hidden');
    return;
  } else {
    emptyState.classList.add('hidden');
  }

  // Render từng công việc
  filteredTasks.forEach((task, idx) => {
    const isAdmin = appData.currentUser.role === 'admin';
    const isMyTask = appData.currentUser.id === task.empId;
    const isPaused = task.status === 'Tạm dừng' || task.status === 'Dừng dự án';

    let statusBadge = '';
    if (isPaused) {
      statusBadge = '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300">⏸ Tạm dừng</span>';
    } else if (task.status === 'Hoàn thành') {
      statusBadge = '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">Hoàn Thành</span>';
    } else if (task.status === 'Hoàn thành trễ') {
      statusBadge = '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-orange-100 text-orange-800 border border-orange-300">Hoàn Thành trễ</span>';
    } else {
      const today = new Date(2026, 9, 5);
      const pEnd = parseDate(task.planEndDate);
      if (pEnd && today > pEnd) {
        statusBadge = '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-300">Quá hạn</span>';
      } else {
        statusBadge = '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-100 text-blue-800 border border-blue-300">Đang làm</span>';
      }
    }

    // Hiển thị Công việc chính & Phân cấp (Yêu cầu 2: Công việc chính hoàn thành khi toàn bộ việc con hoàn thành)
    const mainProgress = task.mainTaskId ? getMainTaskProgress(task.mainTaskId) : null;
    const mainBadge = task.mainTaskId ? `<span class="px-1.5 py-0.5 text-[9px] font-semibold bg-sky-50 text-sky-700 rounded border border-sky-200 mr-1">${task.mainTaskId}</span>` : '';
    let parentStatusBadge = '';
    if (mainProgress) {
      if (mainProgress.isAllCompleted) {
        parentStatusBadge = `<div class="mt-1"><span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300" title="Toàn bộ ${mainProgress.totalCount} công việc con đã hoàn thành"><i class="fa-solid fa-circle-check text-emerald-600"></i>Dự án Xong (100%)</span></div>`;
      } else {
        parentStatusBadge = `<div class="mt-1"><span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-semibold bg-sky-100 text-sky-800 border border-sky-300" title="Dự án đang làm: ${mainProgress.completedCount}/${mainProgress.totalCount} việc hoàn thành"><i class="fa-solid fa-spinner fa-spin-pulse text-sky-600"></i>Dự án: ${mainProgress.completedCount}/${mainProgress.totalCount} việc</span></div>`;
      }
    }

    // DÒNG 1: THÔNG TIN GỘP + KẾ HOẠCH
    const tr1 = document.createElement('tr');
    tr1.className = 'hover:bg-slate-50/80 transition group';

    const tdSTT = `<td rowspan="2" class="p-2 border-r border-b border-slate-300 text-center font-bold text-slate-500 bg-white sticky-col-left shadow-[1px_0_0_0_#cbd5e1]">${idx + 1}</td>`;
    const tdTitle = `
      <td rowspan="2" class="p-2 border-r border-b border-slate-300 bg-white sticky-col-left shadow-[1px_0_0_0_#cbd5e1]" style="left: 48px;">
        <div class="font-bold text-slate-900 leading-snug">${task.mainTaskTitle || task.title}</div>
        <div class="text-[10px] text-slate-500 flex items-center gap-1 mt-0.5">
          ${mainBadge}
          <span>${task.id}</span>
        </div>
        ${parentStatusBadge}
        ${isAdmin ? `
          <div class="mt-1 flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition">
            <button onclick="toggleTaskPause('${task.id}')" class="text-amber-600 hover:text-amber-800 text-[10px] font-semibold" title="Tạm dừng hoặc tiếp tục công việc"><i class="fa-solid fa-circle-pause"></i> ${isPaused ? 'Tiếp tục' : 'Dừng'}</button>
            <button onclick="editTask('${task.id}')" class="text-blue-600 hover:text-blue-800 text-[10px]"><i class="fa-solid fa-pen"></i> Sửa</button>
            <button onclick="deleteTask('${task.id}')" class="text-rose-600 hover:text-rose-800 text-[10px]"><i class="fa-solid fa-trash"></i> Xóa</button>
          </div>
        ` : (isMyTask ? `
          <div class="mt-1 flex items-center gap-1.5">
            <button onclick="toggleTaskPause('${task.id}')" class="text-amber-600 hover:text-amber-800 text-[10px] font-semibold"><i class="fa-solid fa-circle-pause"></i> ${isPaused ? 'Tiếp tục' : 'Dừng'}</button>
            <button onclick="openQuickUpdateModal('${task.id}')" class="text-emerald-600 hover:text-emerald-800 font-semibold text-[10px]"><i class="fa-solid fa-check-to-slot"></i> Cập nhật</button>
          </div>
        ` : '')}
      </td>
    `;
    const tdDetail = `<td rowspan="2" class="p-2 border-r border-b border-slate-300 text-slate-700 font-medium">${task.detail || task.title}</td>`;
    const tdEmp = `
      <td rowspan="2" class="p-2 border-r border-b border-slate-300 font-medium text-slate-800">
        <div class="flex items-center gap-1.5">
          <i class="fa-regular fa-user text-slate-400 text-[10px]"></i>
          <span>${task.empName}</span>
        </div>
      </td>
    `;
    const tdStart = `<td rowspan="2" class="p-2 border-r border-b border-slate-300 text-center font-medium text-slate-700">${formatVnDate(task.startDate)}</td>`;
    const tdPlanDays = `<td rowspan="2" class="p-2 border-r border-b border-slate-300 text-center font-semibold text-slate-800">${task.planDays || 1} ngày</td>`;
    const tdActualDate = `<td rowspan="2" class="p-2 border-r border-b border-slate-300 text-center font-medium ${task.actualEndDate ? 'text-emerald-700 font-bold' : 'text-slate-400'}">${formatVnDate(task.actualEndDate) || (isPaused ? 'Tạm dừng' : 'Chưa hoàn thành')}</td>`;
    const tdStatus = `<td rowspan="2" class="p-2 border-r border-b border-slate-300 text-center">${statusBadge}</td>`;
    const tdNote = `<td rowspan="2" class="p-2 border-r border-b border-slate-300 text-slate-500 italic text-[11px]">${task.note || ''}</td>`;
    const tdLabelPlan = `<td class="p-1.5 border-r border-b border-slate-300 text-center font-semibold text-slate-700 bg-sky-50/50 text-[10px]">Kế hoạch</td>`;

    tr1.innerHTML = tdSTT + tdTitle + tdDetail + tdEmp + tdStart + tdPlanDays + tdActualDate + tdStatus + tdNote + tdLabelPlan;

    const tStart = parseDate(task.startDate);
    const tPlanEnd = parseDate(task.planEndDate);

    // Vẽ thanh Kế hoạch theo các cột
    timelineCols.forEach(col => {
      const td = document.createElement('td');
      td.className = 'p-0 border-r border-b border-slate-200 text-center relative h-7 min-w-[54px] bg-slate-50/30';

      const inRange = tStart && tPlanEnd && col.startDate <= tPlanEnd && col.endDate >= tStart;

      if (inRange) {
        const isStart = col.startDate <= tStart && col.endDate >= tStart;
        const isEnd = col.startDate <= tPlanEnd && col.endDate >= tPlanEnd;

        // Nhãn ngày hoàn thành ở cuối mũi tên trong chế độ Tháng
        const dateTag = (viewState.timeScale === 'MONTH' && isEnd) ? `<span class="arrow-date-tag">${formatVnDate(task.planEndDate).slice(0, 5)}</span>` : '';

        td.innerHTML = `
          <div class="h-4 my-1.5 timeline-arrow-plan relative flex items-center justify-end text-white text-[9px] font-bold ${isStart ? 'rounded-l-sm ml-1' : ''} ${isEnd ? 'mr-0' : ''}" title="Kế hoạch: ${formatVnDate(task.startDate)} - ${formatVnDate(task.planEndDate)}">
            ${dateTag}
            ${isEnd ? `<div class="arrow-head-plan"></div>` : ''}
          </div>
        `;
      }
      tr1.appendChild(td);
    });

    // DÒNG 2: THỰC TÍCH
    const tr2 = document.createElement('tr');
    tr2.className = 'hover:bg-slate-50/80 transition group border-b border-slate-300';
    const tdLabelActual = `<td class="p-1.5 border-r border-b border-slate-300 text-center font-semibold text-emerald-800 bg-emerald-50/50 text-[10px]">Thực tích</td>`;
    tr2.innerHTML = tdLabelActual;

    let tActualEnd = parseDate(task.actualEndDate);
    if (!tActualEnd && (task.status === 'Đang làm' || isPaused)) {
      tActualEnd = new Date(2026, 9, 5);
    }

    timelineCols.forEach(col => {
      const td = document.createElement('td');
      td.className = 'p-0 border-r border-b border-slate-300 text-center relative h-7 min-w-[54px] bg-emerald-50/10';

      const inRange = tStart && tActualEnd && col.startDate <= tActualEnd && col.endDate >= tStart;

      if (inRange) {
        const isStart = col.startDate <= tStart && col.endDate >= tStart;
        const isEnd = col.startDate <= tActualEnd && col.endDate >= tActualEnd;
        const isDelayed = !isPaused && tPlanEnd && col.startDate > tPlanEnd;

        let barClass = 'timeline-arrow-actual';
        let headClass = 'arrow-head-actual';
        if (isPaused) {
          barClass = 'timeline-arrow-paused';
          headClass = 'arrow-head-paused';
        } else if (isDelayed) {
          barClass = 'timeline-arrow-late';
          headClass = 'arrow-head-late';
        }

        const dateTag = (viewState.timeScale === 'MONTH' && isEnd) ? `<span class="arrow-date-tag">${isPaused ? 'Dừng' : (task.actualEndDate ? formatVnDate(task.actualEndDate).slice(0, 5) : 'Đang làm')}</span>` : '';

        td.innerHTML = `
          <div class="h-4 my-1.5 ${barClass} relative flex items-center justify-end text-white text-[9px] font-bold ${isStart ? 'rounded-l-sm ml-1' : ''} ${isEnd ? 'mr-0' : ''}" title="Thực tích: ${formatVnDate(task.startDate)} - ${isPaused ? 'Tạm dừng' : formatVnDate(task.actualEndDate || 'Đang làm')}">
            ${dateTag}
            ${isEnd ? `<div class="${headClass}"></div>` : ''}
          </div>
        `;
      }
      tr2.appendChild(td);
    });

    tbody.appendChild(tr1);
    tbody.appendChild(tr2);
  });

  updateKPIStats();
}

// ================= CẬP NHẬT THẺ KPI =================
function updateKPIStats() {
  const allTasks = appData.tasks;
  const total = allTasks.length;
  let inProgress = 0;
  let onTime = 0;
  let late = 0;
  let overdue = 0;
  const today = new Date(2026, 9, 5);

  allTasks.forEach(t => {
    if (t.status === 'Hoàn thành') onTime++;
    else if (t.status === 'Hoàn thành trễ') late++;
    else {
      inProgress++;
      const pEnd = parseDate(t.planEndDate);
      if (pEnd && today > pEnd) overdue++;
    }
  });

  document.getElementById('kpiTotalTasks').innerText = total;
  document.getElementById('kpiInProgress').innerText = inProgress;
  document.getElementById('kpiOnTime').innerText = onTime;
  document.getElementById('kpiLate').innerText = late;
  document.getElementById('kpiOverdue').innerText = overdue;

  let totalPoints = 0;
  appData.employees.forEach(emp => {
    const scores = calculateEmployeeMonthlyScores(emp.id, 2026);
    totalPoints += scores[10] || 100;
  });
  const avg = appData.employees.length > 0 ? Math.round(totalPoints / appData.employees.length) : 100;
  document.getElementById('kpiAvgScore').innerText = `${avg} đ`;
}

// ================= BẢNG ĐIỂM HIỆU SUẤT TỔNG THỂ =================
function openPerformanceBoardModal() {
  document.getElementById('perfBoardModal').classList.remove('hidden');
  renderPerformanceBoard();
}

function closePerformanceBoardModal() {
  document.getElementById('perfBoardModal').classList.add('hidden');
}

function renderPerformanceBoard() {
  const year = parseInt(document.getElementById('perfYearSelect').value) || 2026;
  const tbody = document.getElementById('perfBoardTableBody');
  tbody.innerHTML = '';

  appData.employees.forEach(emp => {
    const scores = calculateEmployeeMonthlyScores(emp.id, year);
    let yearTotal = 0;
    let cellsHtml = '';

    for (let m = 1; m <= 12; m++) {
      const score = scores[m];
      yearTotal += score;
      let colorClass = 'text-slate-700';
      if (score > 100) colorClass = 'text-emerald-600 font-bold';
      else if (score < 100 && score >= 90) colorClass = 'text-amber-600 font-semibold';
      else if (score < 90) colorClass = 'text-rose-600 font-bold';

      cellsHtml += `<td class="p-2 border-r border-slate-200 ${colorClass}">${score}</td>`;
    }

    let rankBadge = '';
    if (yearTotal >= 1200) {
      rankBadge = '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">Xuất Sắc</span>';
    } else if (yearTotal >= 1150) {
      rankBadge = '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-sky-100 text-sky-800">Tốt</span>';
    } else if (yearTotal >= 1050) {
      rankBadge = '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800">Khá</span>';
    } else {
      rankBadge = '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800">Cần Cải Thiện</span>';
    }

    const tr = document.createElement('tr');
    tr.className = 'hover:bg-slate-50 transition';
    tr.innerHTML = `
      <td class="p-2.5 border-r border-slate-200 text-left font-bold text-slate-800">
        <div>${emp.name}</div>
        <div class="text-[10px] text-slate-400 font-normal">${emp.id} - ${emp.dept}</div>
      </td>
      ${cellsHtml}
      <td class="p-2 border-r border-slate-200 bg-amber-50/60 font-black text-amber-900 text-sm">${yearTotal}</td>
      <td class="p-2">${rankBadge}</td>
    `;
    tbody.appendChild(tr);
  });
}

// ================= QUẢN LÝ NHÂN SỰ =================
function openEmployeeModal() {
  document.getElementById('employeeModal').classList.remove('hidden');
  renderEmployeeTable();
}

function closeEmployeeModal() {
  document.getElementById('employeeModal').classList.add('hidden');
}

function renderEmployeeTable() {
  const tbody = document.getElementById('empTableBody');
  tbody.innerHTML = '';
  document.getElementById('empCountBadge').innerText = `Tổng số: ${appData.employees.length} nhân sự`;

  appData.employees.forEach(emp => {
    const empTasks = appData.tasks.filter(t => t.empId === emp.id);
    const scores = calculateEmployeeMonthlyScores(emp.id, 2026);
    const currentMonthScore = scores[10] || 100;

    const tr = document.createElement('tr');
    tr.className = 'hover:bg-slate-50 transition';
    tr.innerHTML = `
      <td class="p-3 text-center font-bold text-indigo-700">${emp.id}</td>
      <td class="p-3 font-bold text-slate-800">${emp.name}</td>
      <td class="p-3 text-slate-600">${emp.dept || '-'}</td>
      <td class="p-3 text-center font-semibold text-slate-700">${empTasks.length} CV</td>
      <td class="p-3 text-center font-bold ${currentMonthScore >= 100 ? 'text-emerald-600' : 'text-rose-600'}">${currentMonthScore} đ</td>
      <td class="p-3 text-center space-x-2">
        <button onclick="viewEmployeeTasks('${emp.id}')" class="px-2 py-1 text-[11px] font-medium rounded bg-sky-50 text-sky-700 hover:bg-sky-100 transition"><i class="fa-solid fa-eye"></i> Việc</button>
        <button onclick="editEmployee('${emp.id}')" class="px-2 py-1 text-[11px] font-medium rounded bg-indigo-50 text-indigo-700 hover:bg-indigo-100 transition"><i class="fa-solid fa-pen"></i></button>
        <button onclick="deleteEmployee('${emp.id}')" class="px-2 py-1 text-[11px] font-medium rounded bg-rose-50 text-rose-700 hover:bg-rose-100 transition"><i class="fa-solid fa-trash"></i></button>
      </td>
    `;
    tbody.appendChild(tr);
  });

  populateEmployeeSelects();
}

function populateEmployeeSelects() {
  const filterSelect = document.getElementById('filterEmployee');
  const taskEmpSelect = document.getElementById('taskEmpId');

  const curFilterVal = filterSelect.value;
  const curTaskEmpVal = taskEmpSelect ? taskEmpSelect.value : '';

  filterSelect.innerHTML = '<option value="ALL">-- Tất cả nhân sự --</option>';
  if (taskEmpSelect) taskEmpSelect.innerHTML = '';

  appData.employees.forEach(emp => {
    const opt1 = document.createElement('option');
    opt1.value = emp.id;
    opt1.textContent = `${emp.name} (${emp.id} - ${emp.dept})`;
    filterSelect.appendChild(opt1);

    if (taskEmpSelect) {
      const opt2 = document.createElement('option');
      opt2.value = emp.id;
      opt2.textContent = `${emp.name} (${emp.dept})`;
      taskEmpSelect.appendChild(opt2);
    }
  });

  filterSelect.value = curFilterVal;
  if (taskEmpSelect && curTaskEmpVal) taskEmpSelect.value = curTaskEmpVal;
}

function handleSaveEmployee(e) {
  e.preventDefault();
  const editId = document.getElementById('empEditId').value;
  const code = document.getElementById('empCode').value.trim().toUpperCase();
  const name = document.getElementById('empName').value.trim();
  const dept = document.getElementById('empDept').value.trim();

  if (!code || !name) return;

  if (editId) {
    const emp = appData.employees.find(x => x.id === editId);
    if (emp) {
      emp.id = code;
      emp.name = name;
      emp.dept = dept;
      appData.tasks.forEach(t => {
        if (t.empId === editId) {
          t.empId = code;
          t.empName = name;
        }
      });
    }
  } else {
    if (appData.employees.some(x => x.id === code)) {
      alert(`Mã nhân viên "${code}" đã tồn tại! Vui lòng chọn mã khác.`);
      return;
    }
    appData.employees.push({ id: code, name, dept });
  }

  saveDataToStorage();
  resetEmpForm();
  renderEmployeeTable();
  renderUserDropdown();
  applyFilters();
}

function editEmployee(id) {
  const emp = appData.employees.find(x => x.id === id);
  if (!emp) return;
  document.getElementById('empEditId').value = emp.id;
  document.getElementById('empCode').value = emp.id;
  document.getElementById('empName').value = emp.name;
  document.getElementById('empDept').value = emp.dept || '';

  document.getElementById('empFormTitle').innerText = 'Chỉnh Sửa Thông Tin Nhân Viên';
  document.getElementById('empBtnText').innerText = 'Cập Nhật';
  document.getElementById('empCancelEditBtn').classList.remove('hidden');
}

function resetEmpForm() {
  document.getElementById('empEditId').value = '';
  document.getElementById('empCode').value = '';
  document.getElementById('empName').value = '';
  document.getElementById('empDept').value = '';

  document.getElementById('empFormTitle').innerText = 'Thêm Nhân Viên Mới';
  document.getElementById('empBtnText').innerText = 'Thêm NV';
  document.getElementById('empCancelEditBtn').classList.add('hidden');
}

function deleteEmployee(id) {
  const emp = appData.employees.find(x => x.id === id);
  if (!emp) return;
  if (!confirm(`Bạn có chắc chắn muốn xóa nhân viên "${emp.name}" (${emp.id})?`)) return;
  appData.employees = appData.employees.filter(x => x.id !== id);
  saveDataToStorage();
  renderEmployeeTable();
  renderUserDropdown();
  applyFilters();
}

function viewEmployeeTasks(empId) {
  closeEmployeeModal();
  viewState.filterEmp = empId;
  document.getElementById('filterEmployee').value = empId;
  applyFilters();
}

// ================= LẤY DANH SÁCH CÔNG VIỆC CHÍNH (MAIN TASKS) =================
function getUniqueMainTasks() {
  const map = new Map();
  appData.tasks.forEach(t => {
    const id = t.mainTaskId || t.id;
    const title = t.mainTaskTitle || t.title;
    if (!map.has(id)) {
      map.set(id, { id, title, subtasks: [] });
    }
    map.get(id).subtasks.push(t);
  });
  return Array.from(map.values());
}

// ================= QUẢN LÝ CÔNG VIỆC (CRUD & SUBTASKS) =================
function openTaskModal(taskId = null) {
  if (appData.currentUser.role !== 'admin') {
    alert('Chỉ quản trị viên (Admin) mới có quyền tạo mới hoặc chỉnh sửa cấu trúc công việc!');
    return;
  }

  const modal = document.getElementById('taskModal');
  const titleEl = document.getElementById('taskModalTitle');
  populateEmployeeSelects();

  // Đổ danh sách công việc chính vào dropdown
  const parentSelect = document.getElementById('taskParentSelect');
  const mainTasks = getUniqueMainTasks();
  parentSelect.innerHTML = '<option value="__NEW__">+ Tạo Công Việc Chính Mới</option>';
  mainTasks.forEach(mt => {
    const opt = document.createElement('option');
    opt.value = mt.id;
    opt.textContent = `[${mt.id}] ${mt.title} (${mt.subtasks.length} hạng mục)`;
    parentSelect.appendChild(opt);
  });

  if (taskId) {
    titleEl.innerText = 'Chỉnh Sửa Công Việc';
    const task = appData.tasks.find(t => t.id === taskId);
    if (task) {
      document.getElementById('taskId').value = task.id;
      parentSelect.value = task.mainTaskId || '__NEW__';
      document.getElementById('taskMainCode').value = task.mainTaskId || '';
      document.getElementById('taskMainTitle').value = task.mainTaskTitle || task.title;
      document.getElementById('taskDetail').value = task.detail || '';
      document.getElementById('taskEmpId').value = task.empId;
      document.getElementById('taskStatus').value = task.status;
      document.getElementById('taskStartDate').value = task.startDate;
      document.getElementById('taskPlanDays').value = task.planDays || 1;
      document.getElementById('taskPlanEndDate').value = task.planEndDate || '';
      document.getElementById('taskActualEndDate').value = task.actualEndDate || '';
      document.getElementById('taskNote').value = task.note || '';
    }
  } else {
    titleEl.innerText = 'Thêm Công Việc Mới';
    document.getElementById('taskId').value = '';
    document.getElementById('taskForm').reset();
    parentSelect.value = '__NEW__';
    document.getElementById('taskMainCode').value = `CV-${Date.now().toString().slice(-4)}`;
    document.getElementById('taskStartDate').value = '2026-10-01';
    document.getElementById('taskPlanDays').value = 1;
    calculatePlanEndDate();
  }

  handleParentSelectChange();
  modal.classList.remove('hidden');
}

function handleParentSelectChange() {
  const val = document.getElementById('taskParentSelect').value;
  const codeInput = document.getElementById('taskMainCode');
  const titleInput = document.getElementById('taskMainTitle');

  if (val === '__NEW__') {
    codeInput.readOnly = false;
    titleInput.readOnly = false;
    codeInput.classList.remove('bg-slate-100');
    titleInput.classList.remove('bg-slate-100');
    if (!codeInput.value) codeInput.value = `CV-${Date.now().toString().slice(-4)}`;
  } else {
    const mainTasks = getUniqueMainTasks();
    const found = mainTasks.find(m => m.id === val);
    if (found) {
      codeInput.value = found.id;
      titleInput.value = found.title;
      codeInput.readOnly = true;
      titleInput.readOnly = true;
      codeInput.classList.add('bg-slate-100');
      titleInput.classList.add('bg-slate-100');
    }
  }
}

function closeTaskModal() {
  document.getElementById('taskModal').classList.add('hidden');
}

function calculatePlanEndDate() {
  const startStr = document.getElementById('taskStartDate').value;
  const days = parseInt(document.getElementById('taskPlanDays').value) || 1;
  if (startStr && days > 0) {
    const d = parseDate(startStr);
    if (d) {
      const end = addDays(d, days - 1);
      document.getElementById('taskPlanEndDate').value = formatDate(end);
    }
  }
}

function handleTaskStatusChange() {
  const status = document.getElementById('taskStatus').value;
  const actualInput = document.getElementById('taskActualEndDate');
  if (status === 'Hoàn thành' && !actualInput.value) {
    actualInput.value = document.getElementById('taskPlanEndDate').value || document.getElementById('taskStartDate').value;
  }
}

function handleSaveTask(e) {
  e.preventDefault();
  const id = document.getElementById('taskId').value;
  const mainTaskId = document.getElementById('taskMainCode').value.trim().toUpperCase();
  const mainTaskTitle = document.getElementById('taskMainTitle').value.trim();
  const detail = document.getElementById('taskDetail').value.trim();
  const empId = document.getElementById('taskEmpId').value;
  const status = document.getElementById('taskStatus').value;
  const startDate = document.getElementById('taskStartDate').value;
  const planDays = parseInt(document.getElementById('taskPlanDays').value) || 1;
  const planEndDate = document.getElementById('taskPlanEndDate').value;
  const actualEndDate = document.getElementById('taskActualEndDate').value;
  const note = document.getElementById('taskNote').value.trim();

  const emp = appData.employees.find(x => x.id === empId);
  const empName = emp ? emp.name : 'Chưa phân công';

  if (id) {
    const task = appData.tasks.find(t => t.id === id);
    if (task) {
      task.mainTaskId = mainTaskId;
      task.mainTaskTitle = mainTaskTitle;
      task.title = mainTaskTitle;
      task.detail = detail;
      task.empId = empId;
      task.empName = empName;
      task.status = status;
      task.startDate = startDate;
      task.planDays = planDays;
      task.planEndDate = planEndDate;
      task.actualEndDate = actualEndDate;
      task.note = note;
    }
  } else {
    const newId = `TASK-${Date.now().toString().slice(-4)}`;
    appData.tasks.push({
      id: newId,
      mainTaskId,
      mainTaskTitle,
      title: mainTaskTitle,
      detail,
      empId,
      empName,
      startDate,
      planDays,
      planEndDate,
      actualEndDate,
      status,
      note
    });
  }

  saveDataToStorage();
  closeTaskModal();
  applyFilters();
}

function editTask(taskId) {
  openTaskModal(taskId);
}

function deleteTask(taskId) {
  if (!confirm('Bạn có chắc chắn muốn xóa công việc này?')) return;
  appData.tasks = appData.tasks.filter(t => t.id !== taskId);
  saveDataToStorage();
  applyFilters();
}

// ================= CẬP NHẬT TIẾN ĐỘ NHANH & CHỌN NHANH VIỆC DỞ DANG =================
function openQuickUpdateModal(taskId = null) {
  const modal = document.getElementById('quickUpdateModal');
  const selectQuickTask = document.getElementById('quickTaskSelect');

  // Lọc các công việc dở dang (chưa xong) của nhân viên đang chọn hoặc tất cả
  const currentEmpId = appData.currentUser.role === 'employee' ? appData.currentUser.id : viewState.filterEmp;
  let pendingTasks = appData.tasks.filter(t => {
    const isPending = t.status !== 'Hoàn thành';
    if (currentEmpId && currentEmpId !== 'ALL') {
      return isPending && t.empId === currentEmpId;
    }
    return isPending;
  });

  if (pendingTasks.length === 0) {
    pendingTasks = appData.tasks;
  }

  selectQuickTask.innerHTML = '';
  pendingTasks.forEach(t => {
    const opt = document.createElement('option');
    opt.value = t.id;
    opt.textContent = `[${t.empName}] ${t.mainTaskTitle || t.title} - ${t.detail || ''} (${t.status})`;
    selectQuickTask.appendChild(opt);
  });

  if (taskId) {
    selectQuickTask.value = taskId;
  }

  handleQuickTaskSelectChange();
  modal.classList.remove('hidden');
}

function handleQuickTaskSelectChange() {
  const taskId = document.getElementById('quickTaskSelect').value;
  const task = appData.tasks.find(t => t.id === taskId);
  if (!task) return;

  document.getElementById('quickTaskId').value = task.id;
  document.getElementById('quickTaskTitle').innerText = `${task.mainTaskTitle || task.title} - ${task.detail || ''}`;
  document.getElementById('quickTaskEmp').innerText = `${task.empName} (${task.empId})`;
  document.getElementById('quickTaskStatus').value = task.status;
  document.getElementById('quickActualEndDate').value = task.actualEndDate || formatDate(new Date(2026, 9, 5));
  document.getElementById('quickTaskNote').value = task.note || '';
}

function closeQuickUpdateModal() {
  document.getElementById('quickUpdateModal').classList.add('hidden');
}

function handleSaveQuickUpdate(e) {
  e.preventDefault();
  const id = document.getElementById('quickTaskId').value;
  const task = appData.tasks.find(t => t.id === id);
  if (!task) return;

  task.status = document.getElementById('quickTaskStatus').value;
  task.actualEndDate = document.getElementById('quickActualEndDate').value;
  task.note = document.getElementById('quickTaskNote').value.trim();

  saveDataToStorage();
  closeQuickUpdateModal();
  applyFilters();
}

// ================= ĐIỀU HƯỚNG VÀ BỘ LỌC =================
function applyFilters() {
  viewState.filterEmp = document.getElementById('filterEmployee').value;
  viewState.filterMonth = document.getElementById('filterMonth').value;
  viewState.filterStatus = document.getElementById('filterStatus').value;
  viewState.filterKeyword = document.getElementById('filterKeyword').value;

  if (viewState.filterMonth && !viewState.filterStartDate) {
    viewState.startOffsetDate = `${viewState.filterMonth}-01`;
  }

  renderMainTable();
}

function handleMonthFilterChange() {
  viewState.filterMonth = document.getElementById('filterMonth').value;
  viewState.filterStartDate = '';
  viewState.filterEndDate = '';
  const sInput = document.getElementById('filterStartDate');
  const eInput = document.getElementById('filterEndDate');
  if (sInput) sInput.value = '';
  if (eInput) eInput.value = '';
  if (viewState.filterMonth) {
    viewState.startOffsetDate = `${viewState.filterMonth}-01`;
  }
  applyFilters();
}

function handleDateRangeFilterChange() {
  const s = document.getElementById('filterStartDate').value;
  const e = document.getElementById('filterEndDate').value;
  if (s && e) {
    if (s > e) {
      alert('Ngày bắt đầu không được lớn hơn ngày kết thúc!');
      return;
    }
    viewState.filterStartDate = s;
    viewState.filterEndDate = e;
    viewState.filterMonth = '';
    const mInput = document.getElementById('filterMonth');
    if (mInput) mInput.value = '';
    viewState.startOffsetDate = s;
    setTimeScale('DAY');
    applyFilters();
  }
}

function clearDateRangeFilter() {
  viewState.filterStartDate = '';
  viewState.filterEndDate = '';
  const sInput = document.getElementById('filterStartDate');
  const eInput = document.getElementById('filterEndDate');
  if (sInput) sInput.value = '';
  if (eInput) eInput.value = '';
  setCurrentMonth();
}

function setCurrentMonth() {
  document.getElementById('filterMonth').value = '2026-10';
  viewState.filterMonth = '2026-10';
  viewState.filterStartDate = '';
  viewState.filterEndDate = '';
  const sInput = document.getElementById('filterStartDate');
  const eInput = document.getElementById('filterEndDate');
  if (sInput) sInput.value = '';
  if (eInput) eInput.value = '';
  viewState.startOffsetDate = '2026-10-01';
  setTimeScale('DAY');
  applyFilters();
}

function setFullYearView() {
  document.getElementById('filterMonth').value = '';
  viewState.filterMonth = '';
  viewState.filterStartDate = '';
  viewState.filterEndDate = '';
  const sInput = document.getElementById('filterStartDate');
  const eInput = document.getElementById('filterEndDate');
  if (sInput) sInput.value = '';
  if (eInput) eInput.value = '';
  setTimeScale('MONTH');
}

function setDaysWindow(mode) {
  viewState.windowMode = mode.toString();

  document.getElementById('btnWindow10').className = 'px-2 py-0.5 rounded font-semibold text-slate-700 hover:bg-white transition text-xs';
  document.getElementById('btnWindow15').className = 'px-2 py-0.5 rounded font-semibold text-slate-700 hover:bg-white transition text-xs';
  document.getElementById('btnWindowMonth').className = 'px-2 py-0.5 rounded font-semibold text-slate-700 hover:bg-white transition text-xs';

  if (mode === 10) {
    document.getElementById('btnWindow10').className = 'px-2 py-0.5 rounded font-semibold bg-white text-brand-700 shadow-sm transition text-xs';
  } else if (mode === 15) {
    document.getElementById('btnWindow15').className = 'px-2 py-0.5 rounded font-semibold bg-white text-brand-700 shadow-sm transition text-xs';
  } else {
    document.getElementById('btnWindowMonth').className = 'px-2 py-0.5 rounded font-semibold bg-white text-brand-700 shadow-sm transition text-xs';
  }

  renderMainTable();
}

function shiftTimelineDays(days) {
  const cur = parseDate(viewState.startOffsetDate) || new Date(2026, 9, 1);
  const next = addDays(cur, days);
  viewState.startOffsetDate = formatDate(next);
  renderMainTable();
}

// ================= MODAL CẤU HÌNH XUẤT BÁO CÁO EXCEL (CONFIG TITLE) =================
function openExportConfigModal() {
  const modal = document.getElementById('exportConfigModal');
  const titleInput = document.getElementById('exportReportTitle');

  // Tự động tạo tiêu đề thông minh theo bộ lọc hiện tại
  let generatedTitle = 'BÁO CÁO KẾ HOẠCH & THỰC TÍCH CÔNG VIỆC NHÓM';
  if (viewState.filterEmp !== 'ALL') {
    const emp = appData.employees.find(e => e.id === viewState.filterEmp);
    if (emp) generatedTitle += ` - NHÂN SỰ: ${emp.name.toUpperCase()} (${emp.dept})`;
  }
  if (viewState.filterMonth) {
    generatedTitle += ` - THÁNG ${viewState.filterMonth.split('-')[1]}/${viewState.filterMonth.split('-')[0]}`;
  } else {
    generatedTitle += ' - NĂM 2026';
  }

  titleInput.value = generatedTitle;
  modal.classList.remove('hidden');
}

function closeExportConfigModal() {
  document.getElementById('exportConfigModal').classList.add('hidden');
}

// ================= XUẤT BÁO CÁO EXCEL TRỰC QUAN LIỀN MẠCH (GANTT MATRIX CHUẨN) =================
/**
 * Xuất file Excel báo cáo đẹp mắt:
 * - Tiêu đề báo cáo tùy chỉnh hoặc theo nhân viên lọc
 * - Thanh tiến độ liền mạch (border-left/right: none giữa các ngày liên tiếp)
 * - Mũi tên kết thúc ► sắc nét ở ngày cuối
 */
function executeExportExcelReport() {
  try {
    const customTitle = document.getElementById('exportReportTitle').value.trim() || 'BÁO CÁO KẾ HOẠCH & THỰC TÍCH CÔNG VIỆC NHÓM';
    const customUnit = document.getElementById('exportUnitName').value.trim() || 'MBC Group - Quản Lý Dự Án';
    const exportScale = document.getElementById('exportScaleSelect').value; // 'CURRENT', 'MONTH_ALL'

    let timelineCols = getTimelineColumns();
    if (exportScale === 'FIT_TASKS') {
      // Ôm khít từ ngày đầu đến ngày kết thúc của các công việc xuất
      let minStart = null;
      let maxEnd = null;
      tasksToExport.forEach(t => {
        const s = parseDate(t.startDate);
        const e = parseDate(t.actualEndDate || t.planEndDate);
        if (s && (!minStart || s < minStart)) minStart = s;
        if (e && (!maxEnd || e > maxEnd)) maxEnd = e;
      });
      if (minStart && maxEnd && minStart <= maxEnd) {
        timelineCols = [];
        const dayNames = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7'];
        const totalDays = dateDiffInDays(minStart, maxEnd) + 1;
        for (let i = 0; i < totalDays; i++) {
          const d = addDays(minStart, i);
          timelineCols.push({
            type: 'DAY',
            date: d,
            label: `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}`,
            subLabel: dayNames[d.getDay()],
            yearLabel: d.getFullYear(),
            isWeekend: d.getDay() === 0 || d.getDay() === 6,
            startDate: d,
            endDate: d
          });
        }
      }
    } else if (exportScale && exportScale !== 'CURRENT') {
      const origScale = viewState.timeScale;
      viewState.timeScale = exportScale;
      timelineCols = getTimelineColumns();
      viewState.timeScale = origScale;
    }

    let tasksToExport = appData.tasks.filter(task => {
      if (appData.currentUser.role === 'employee' && task.empId !== appData.currentUser.id) return false;
      if (viewState.filterEmp !== 'ALL' && task.empId !== viewState.filterEmp) return false;
      if (viewState.filterStatus === 'CHUA_HOAN_THANH') {
        if (task.status && task.status.includes('Hoàn thành')) return false;
      } else if (viewState.filterStatus === 'HOAN_THANH_ALL') {
        if (!task.status || !task.status.includes('Hoàn thành')) return false;
      } else if (viewState.filterStatus === 'DANG_LAM') {
        if (task.status !== 'Đang làm') return false;
      } else if (viewState.filterStatus === 'Tạm dừng') {
        if (task.status !== 'Tạm dừng' && task.status !== 'Dừng dự án') return false;
      } else if (viewState.filterStatus === 'QUA_HAN') {
        const today = new Date(2026, 9, 5);
        const planEnd = parseDate(task.planEndDate);
        if (task.status && (task.status.includes('Hoàn thành') || task.status === 'Tạm dừng' || task.status === 'Dừng dự án')) return false;
        if (!planEnd || today <= planEnd) return false;
      } else if (viewState.filterStatus !== 'ALL') {
        if (task.status !== viewState.filterStatus) return false;
      }
      return true;
    });

    // GOM NHÓM & SẮP XẾP: Giữ các việc cùng dự án mẹ luôn đứng liền kề nhau trong Excel
    tasksToExport = groupAndSortTasks(tasksToExport);

    // Thống kê cho thẻ KPI
    const totalExp = tasksToExport.length;
    const inProgExp = tasksToExport.filter(t => t.status === 'Đang làm').length;
    const pausedExp = tasksToExport.filter(t => t.status === 'Tạm dừng' || t.status === 'Dừng dự án').length;
    const onTimeExp = tasksToExport.filter(t => t.status === 'Hoàn thành').length;
    const lateExp = tasksToExport.filter(t => t.status === 'Hoàn thành trễ').length;
    const overdueExp = tasksToExport.filter(t => {
      const today = new Date(2026, 9, 5);
      const pe = parseDate(t.planEndDate);
      return !t.status.includes('Hoàn thành') && t.status !== 'Tạm dừng' && pe && today > pe;
    }).length;

    let tableHtml = `
      <html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">
      <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <style>
          table { border-collapse: collapse; font-family: 'Segoe UI', Arial, sans-serif; font-size: 11px; }
          th { background-color: #0f3d52; color: #ffffff; font-weight: bold; border: 1px solid #94a3b8; text-align: center; padding: 6px 4px; }
          td { border: 1px solid #cbd5e1; padding: 4px 6px; vertical-align: middle; }
          .title-row { font-size: 16px; font-weight: bold; background-color: #1e3a8a; color: #ffffff; height: 38px; text-align: center; }
          .sub-title { font-size: 11px; background-color: #f8fafc; color: #475569; text-align: center; font-style: italic; }
          .kpi-card { font-size: 11px; font-weight: bold; text-align: center; padding: 6px; border: 1px solid #cbd5e1; }
          .info-cell { background-color: #ffffff; }
          .plan-label { background-color: #eff6ff; color: #1e40af; font-weight: bold; text-align: center; font-size: 10px; }
          .actual-label { background-color: #f0fdf4; color: #15803d; font-weight: bold; text-align: center; font-size: 10px; }
          .weekend-cell { background-color: #f8fafc; }
        </style>
      </head>
      <body>
        <table>
          <tr>
            <td colspan="${11 + timelineCols.length}" class="title-row">${customTitle}</td>
          </tr>
          <tr>
            <td colspan="${11 + timelineCols.length}" class="sub-title">Đơn vị: <b>${customUnit}</b> | Thời gian xuất: <b>${new Date().toLocaleString('vi-VN')}</b> | Tổng số việc: <b>${totalExp}</b></td>
          </tr>
          <tr></tr>
          <!-- THẺ KPI TỔNG HỢP TRÊN EXCEL -->
          <tr>
            <td colspan="2" class="kpi-card" style="background-color: #eff6ff; color: #1e40af;">TỔNG VIỆC: ${totalExp}</td>
            <td colspan="2" class="kpi-card" style="background-color: #fefce8; color: #a16207;">ĐANG LÀM: ${inProgExp}</td>
            <td colspan="2" class="kpi-card" style="background-color: #f1f5f9; color: #475569;">TẠM DỪNG: ${pausedExp}</td>
            <td colspan="2" class="kpi-card" style="background-color: #f0fdf4; color: #15803d;">ĐÚNG HẠN (+3Đ): ${onTimeExp}</td>
            <td colspan="2" class="kpi-card" style="background-color: #fff7ed; color: #c2410c;">HOÀN THÀNH TRỄ: ${lateExp}</td>
            <td colspan="1" class="kpi-card" style="background-color: #fef2f2; color: #b91c1c;">QUÁ HẠN: ${overdueExp}</td>
            <td colspan="${timelineCols.length}" style="background-color: #f1f5f9; font-size: 10px; color: #334155;">
              <b>CHÚ THÍCH:</b> 
              <span style="color: #1e40af; font-weight: bold;">■ Kế hoạch (►)</span> | 
              <span style="color: #15803d; font-weight: bold;">■ Đúng hạn (✔)</span> | 
              <span style="color: #64748b; font-weight: bold;">■ Tạm dừng (⏸)</span> | 
              <span style="color: #d97706; font-weight: bold;">■ Trễ hạn (⚠)</span>
            </td>
          </tr>
          <tr></tr>
          <tr>
            <th style="width: 35px;">STT</th>
            <th style="width: 75px;">Mã Dự Án</th>
            <th style="width: 170px;">Công Việc Chính & Tiến Độ</th>
            <th style="width: 190px;">Nội Dung Chi Tiết (Giai Đoạn)</th>
            <th style="width: 110px;">Người Thực Hiện</th>
            <th style="width: 80px;">Bắt Đầu</th>
            <th style="width: 70px;">Kế Hoạch</th>
            <th style="width: 80px;">Hoàn Thành</th>
            <th style="width: 95px;">Tình Trạng</th>
            <th style="width: 115px;">Dự Án Chính</th>
            <th style="width: 65px;">Loại</th>
            ${timelineCols.map(col => `<th style="min-width: 48px;">${col.label}<br><span style="font-size: 9px; font-weight: normal; opacity: 0.8;">${col.subLabel || ''}</span></th>`).join('')}
          </tr>
    `;

    tasksToExport.forEach((task, idx) => {
      const isPaused = task.status === 'Tạm dừng' || task.status === 'Dừng dự án';
      const tStart = parseDate(task.startDate);
      const tPlanEnd = parseDate(task.planEndDate);
      let tActualEnd = parseDate(task.actualEndDate);
      if (!tActualEnd && (task.status === 'Đang làm' || isPaused)) {
        tActualEnd = new Date(2026, 9, 5);
      }

      const mainProgress = task.mainTaskId ? getMainTaskProgress(task.mainTaskId) : null;
      let mainStatusText = 'Độc lập';
      if (mainProgress) {
        mainStatusText = mainProgress.isAllCompleted ? '✔ 100% Hoàn Thành' : `Đang làm (${mainProgress.completedCount}/${mainProgress.totalCount})`;
      }

      // Xác định các cột nằm trong phạm vi Kế hoạch
      const planIndices = [];
      timelineCols.forEach((col, cIdx) => {
        if (tStart && tPlanEnd && col.startDate <= tPlanEnd && col.endDate >= tStart) {
          planIndices.push(cIdx);
        }
      });

      // Xác định các cột nằm trong phạm vi Thực tích
      const actualIndices = [];
      timelineCols.forEach((col, cIdx) => {
        if (tStart && tActualEnd && col.startDate <= tActualEnd && col.endDate >= tStart) {
          actualIndices.push(cIdx);
        }
      });

      // HÀNG 1: THÔNG TIN GỘP + KẾ HOẠCH
      let row1 = `
        <tr>
          <td rowspan="2" style="text-align: center; font-weight: bold;" class="info-cell">${idx + 1}</td>
          <td rowspan="2" style="text-align: center; font-weight: bold; color: #0284c7;" class="info-cell">${task.mainTaskId || task.id}</td>
          <td rowspan="2" style="font-weight: bold; color: #0f172a;" class="info-cell">${task.mainTaskTitle || task.title}</td>
          <td rowspan="2" class="info-cell" style="color: #334155;">↳ ${task.detail || task.title}</td>
          <td rowspan="2" class="info-cell" style="font-weight: 500;">${task.empName}</td>
          <td rowspan="2" style="text-align: center;" class="info-cell">${formatVnDate(task.startDate)}</td>
          <td rowspan="2" style="text-align: center; font-weight: bold;" class="info-cell">${task.planDays || 1} ngày</td>
          <td rowspan="2" style="text-align: center;" class="info-cell">${formatVnDate(task.actualEndDate) || (isPaused ? 'Tạm dừng' : 'Chưa xong')}</td>
          <td rowspan="2" style="text-align: center; font-weight: bold;" class="info-cell">${task.status}</td>
          <td rowspan="2" style="text-align: center; font-weight: bold; color: ${mainProgress && mainProgress.isAllCompleted ? '#15803d' : '#0369a1'};" class="info-cell">${mainStatusText}</td>
          <td class="plan-label">Kế hoạch</td>
      `;

      // Render ô Gantt Kế hoạch liền khối sắc nét
      timelineCols.forEach((col, cIdx) => {
        const inPlan = planIndices.includes(cIdx);
        if (inPlan) {
          const isFirst = cIdx === planIndices[0];
          const isLast = cIdx === planIndices[planIndices.length - 1];
          const borderStyle = `border-top: 2px solid #1e3a8a; border-bottom: 2px solid #1e3a8a; ${isFirst ? 'border-left: 2px solid #1e3a8a;' : 'border-left: none;'} ${isLast ? 'border-right: 2px solid #1e3a8a;' : 'border-right: none;'}`;
          row1 += `<td style="background-color: #1e40af; ${borderStyle} text-align: center; color: #ffffff; font-weight: bold; font-size: 11px;">${isLast ? '►' : '—'}</td>`;
        } else {
          row1 += `<td class="${col.isWeekend ? 'weekend-cell' : ''}"></td>`;
        }
      });
      row1 += `</tr>`;

      // HÀNG 2: THỰC TÍCH LIỀN KHỐI
      let row2 = `<tr><td class="actual-label">Thực tích</td>`;
      timelineCols.forEach((col, cIdx) => {
        const inActual = actualIndices.includes(cIdx);
        if (inActual) {
          const isFirst = cIdx === actualIndices[0];
          const isLast = cIdx === actualIndices[actualIndices.length - 1];
          const isDelayed = !isPaused && tPlanEnd && col.startDate > tPlanEnd;

          let barColor = '#16a34a';
          let borderColor = '#14532d';
          let symbol = isLast ? '✔' : '—';

          if (isPaused) {
            barColor = '#64748b';
            borderColor = '#334155';
            symbol = isLast ? '⏸' : '—';
          } else if (isDelayed) {
            barColor = '#d97706';
            borderColor = '#9a3412';
            symbol = isLast ? '⚠' : '—';
          }

          const borderStyle = `border-top: 2px solid ${borderColor}; border-bottom: 2px solid ${borderColor}; ${isFirst ? `border-left: 2px solid ${borderColor};` : 'border-left: none;'} ${isLast ? `border-right: 2px solid ${borderColor};` : 'border-right: none;'}`;
          row2 += `<td style="background-color: ${barColor}; ${borderStyle} text-align: center; color: #ffffff; font-weight: bold; font-size: 11px;">${symbol}</td>`;
        } else {
          row2 += `<td class="${col.isWeekend ? 'weekend-cell' : ''}"></td>`;
        }
      });
      row2 += `</tr>`;

      tableHtml += row1 + row2;
    });

    tableHtml += `
        </table>
      </body>
      </html>
    `;

    const blob = new Blob([tableHtml], { type: 'application/vnd.ms-excel;charset=utf-8' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `MBC_BaoCao_Gantt_${formatDate(new Date())}.xls`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    closeExportConfigModal();
  } catch (err) {
    alert('Lỗi xuất báo cáo Excel: ' + err.message);
  }
}

// Xuất file CSDL phẳng (.xlsx)
function exportRawDatabaseExcel() {
  try {
    const dataRows = [];
    dataRows.push([
      'STT', 'Mã CV Chính', 'Tên Công Việc Chính', 'Mã CV Chi Tiết', 'Nội Dung Chi Tiết', 'Mã NV', 'Người Thực Hiện',
      'Phòng Ban', 'Ngày Bắt Đầu', 'Ngày Kết Thúc', 'Tiến Độ (%)', 'Trạng Thái', 'Ghi Chú'
    ]);

    appData.tasks.forEach((t, idx) => {
      dataRows.push([
        idx + 1,
        t.mainTaskId || '',
        t.mainTaskName || '',
        t.id || '',
        t.name || '',
        t.assignedEmployeeId || '',
        t.assignedEmployeeName || '',
        t.assignedDepartment || '',
        t.startDate || '',
        t.endDate || '',
        t.progress ?? 0,
        t.status || '',
        t.notes || ''
      ]);
    });

    const ws = XLSX.utils.aoa_to_sheet(dataRows);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'CSDL_CongViec');
    XLSX.writeFile(wb, `CSDL_CongViec_${new Date().toISOString().slice(0, 10)}.xlsx`);
  } catch (err) {
    alert('Lỗi xuất CSDL Excel: ' + err.message);
  }
}

// ================= TẢI FILE MẪU & NHẬP DỮ LIỆU THÔNG MINH (SMART MERGE) =================
let currentImportTarget = 'TASK';
let parsedSmartImportData = null;

function openSmartImportModal(target = 'TASK') {
  currentImportTarget = target;
  parsedSmartImportData = null;
  const modal = document.getElementById('importModal');
  if (modal) modal.classList.remove('hidden');
  const fileInput = document.getElementById('smartImportFileInput');
  if (fileInput) fileInput.value = '';
  const selName = document.getElementById('smartImportSelectedFileName');
  if (selName) selName.innerText = 'Nhấn để chọn file hoặc kéo thả file vào đây';
  const btn = document.getElementById('btnExecuteSmartImport');
  if (btn) btn.disabled = true;
  const alertBox = document.getElementById('smartImportAlert');
  if (alertBox) alertBox.classList.add('hidden');
  switchSmartImportTarget(target);
}

function closeSmartImportModal() {
  const modal = document.getElementById('importModal');
  if (modal) modal.classList.add('hidden');
}

function openImportExcelModal() {
  openSmartImportModal('TASK');
}

function closeImportExcelModal() {
  closeSmartImportModal();
}

function switchSmartImportTarget(target) {
  currentImportTarget = target;
  const tabTask = document.getElementById('tabImportTask');
  const tabEmp = document.getElementById('tabImportEmp');
  const modalTitle = document.getElementById('importModalTitle');
  const modalIcon = document.getElementById('importModalIcon');
  const ruleDesc = document.getElementById('importRuleDesc');

  if (target === 'TASK') {
    if (tabTask) tabTask.className = 'flex-1 py-1.5 rounded-lg bg-white text-emerald-700 shadow-sm transition flex items-center justify-center gap-1.5';
    if (tabEmp) tabEmp.className = 'flex-1 py-1.5 rounded-lg text-slate-600 hover:text-slate-900 transition flex items-center justify-center gap-1.5';
    if (modalTitle) modalTitle.innerText = 'Nhập Công Việc Vào Hệ Thống (Chỉ Chèn Việc Chưa Có)';
    if (modalIcon) modalIcon.className = 'fa-solid fa-list-check text-lg text-emerald-300';
    if (ruleDesc) ruleDesc.innerHTML = 'Hệ thống sẽ đối soát ID và nội dung: <b>Chỉ chèn các công việc chưa có</b>. Toàn bộ công việc đã có sẽ được giữ nguyên 100%, không bị trùng lặp!';
  } else {
    if (tabEmp) tabEmp.className = 'flex-1 py-1.5 rounded-lg bg-white text-indigo-700 shadow-sm transition flex items-center justify-center gap-1.5';
    if (tabTask) tabTask.className = 'flex-1 py-1.5 rounded-lg text-slate-600 hover:text-slate-900 transition flex items-center justify-center gap-1.5';
    if (modalTitle) modalTitle.innerText = 'Nhập Nhân Sự Vào Hệ Thống (Chỉ Chèn Nhân Sự Mới)';
    if (modalIcon) modalIcon.className = 'fa-solid fa-users text-lg text-indigo-300';
    if (ruleDesc) ruleDesc.innerHTML = 'Hệ thống sẽ đối soát Mã nhân viên và Họ tên: <b>Chỉ thêm nhân sự mới</b>. Nhân sự đã có sẽ được giữ nguyên!';
  }
}

function downloadSmartImportTemplate() {
  if (currentImportTarget === 'TASK') {
    downloadExcelTemplate();
  } else {
    const templateData = [
      ['Mã Nhân Viên', 'Họ Và Tên', 'Phòng Ban / Bộ Phận'],
      ['NV06', 'Vũ Đình Trọng', 'Kỹ thuật - Bảo trì'],
      ['NV07', 'Ngô Thu Trang', 'Kiểm tra chất lượng (QC)'],
      ['NV08', 'Đỗ Mạnh Hùng', 'Kế hoạch sản xuất']
    ];
    const ws = XLSX.utils.aoa_to_sheet(templateData);
    ws['!cols'] = [{ wch: 16 }, { wch: 25 }, { wch: 25 }];
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'MauImportNhanSu');
    XLSX.writeFile(wb, 'MBC_Mau_Import_NhanSu.xlsx');
  }
}

function downloadExcelTemplate() {
  const templateData = [
    ['Mã CV Chính', 'Công việc chính', 'Nội dung chi tiết', 'Người thực hiện', 'Mã NV', 'Ngày bắt đầu (YYYY-MM-DD)', 'Thời gian dự kiến (ngày)', 'Thời gian hoàn thành (YYYY-MM-DD)', 'Tình trạng', 'Ghi chú'],
    ['CV-TUM', 'Sửa chữa máy TUM', 'Xác nhận tình trạng linh kiện', 'Nguyễn Quang Thảo', 'NV01', '2026-10-01', 1, '2026-10-01', 'Hoàn thành', 'Nghiệm thu tốt'],
    ['CV-MAY-EP', 'Bảo dưỡng định kỳ máy ép', 'Kiểm tra đường ống dầu thủy lực', 'Trần Văn Bình', 'NV02', '2026-10-03', 3, '2026-10-05', 'Hoàn thành', 'Đúng hạn'],
    ['CV-KIEM-DINH', 'Kiểm định thiết bị đo', 'Hiệu chuẩn thước kẹp điện tử', 'Lê Thị Thu', 'NV03', '2026-10-05', 2, '', 'Đang làm', 'Đang thực hiện']
  ];

  const ws = XLSX.utils.aoa_to_sheet(templateData);
  ws['!cols'] = [{ wch: 14 }, { wch: 25 }, { wch: 30 }, { wch: 20 }, { wch: 10 }, { wch: 25 }, { wch: 22 }, { wch: 28 }, { wch: 16 }, { wch: 25 }];
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, 'MauImportCongViec');
  XLSX.writeFile(wb, 'MBC_Mau_Import_CongViec.xlsx');
}

function handleSmartImportFileSelect(e) {
  const file = e.target.files[0];
  if (!file) return;

  const selName = document.getElementById('smartImportSelectedFileName');
  if (selName) selName.innerText = `Đã chọn: ${file.name} (${Math.round(file.size / 1024)} KB)`;
  const fileName = file.name.toLowerCase();

  if (fileName.endsWith('.json')) {
    const reader = new FileReader();
    reader.onload = function(evt) {
      try {
        const parsed = JSON.parse(evt.target.result);
        parsedSmartImportData = { type: 'JSON', data: parsed };
        const btn = document.getElementById('btnExecuteSmartImport');
        if (btn) btn.disabled = false;
      } catch (err) {
        alert('Lỗi định dạng JSON: ' + err.message);
      }
    };
    reader.readAsText(file);
  } else if (fileName.endsWith('.xlsx') || fileName.endsWith('.xls')) {
    const reader = new FileReader();
    reader.onload = function(evt) {
      try {
        const data = new Uint8Array(evt.target.result);
        const workbook = XLSX.read(data, { type: 'array' });
        const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
        const sheetData = XLSX.utils.sheet_to_json(firstSheet, { header: 1 });
        parsedSmartImportData = { type: 'EXCEL', data: sheetData };
        if (sheetData.length > 1) {
          const btn = document.getElementById('btnExecuteSmartImport');
          if (btn) btn.disabled = false;
        } else {
          alert('File Excel không có dòng dữ liệu hợp lệ!');
        }
      } catch (err) {
        alert('Không thể đọc file Excel: ' + err.message);
      }
    };
    reader.readAsArrayBuffer(file);
  } else {
    alert('Vui lòng chọn file định dạng .xlsx, .xls hoặc .json!');
  }
}

function processSmartImport() {
  if (!parsedSmartImportData) return;

  let addedCount = 0;
  let skippedCount = 0;

  if (currentImportTarget === 'TASK') {
    let rawTasks = [];
    if (parsedSmartImportData.type === 'JSON') {
      const d = parsedSmartImportData.data;
      if (Array.isArray(d)) rawTasks = d;
      else if (d.tasks && Array.isArray(d.tasks)) rawTasks = d.tasks;
    } else {
      const rows = parsedSmartImportData.data.slice(1);
      const header = parsedSmartImportData.data[0].map(h => String(h || '').trim().toLowerCase());
      const colMainId = header.findIndex(h => h.includes('mã cv chính') || h.includes('mã cv'));
      const colMainTitle = header.findIndex(h => h.includes('công việc chính') || h.includes('công việc'));
      const colDetail = header.findIndex(h => h.includes('chi tiết') || h.includes('nội dung'));
      const colEmp = header.findIndex(h => h.includes('người') || h.includes('thực hiện'));
      const colEmpId = header.findIndex(h => h.includes('mã nv'));
      const colStart = header.findIndex(h => h.includes('bắt đầu'));
      const colDays = header.findIndex(h => (h.includes('dự kiến') && h.includes('thời gian')) || h.includes('ngày'));
      const colActual = header.findIndex(h => h.includes('hoàn thành'));
      const colStatus = header.findIndex(h => h.includes('tình trạng'));
      const colNote = header.findIndex(h => h.includes('ghi chú'));

      rows.forEach((row, rIdx) => {
        if (!row || row.length === 0) return;
        const title = colMainTitle >= 0 ? String(row[colMainTitle] || '').trim() : '';
        if (!title) return;
        const mainTaskId = colMainId >= 0 ? String(row[colMainId] || `CV-${Date.now().toString().slice(-4)}`).trim().toUpperCase() : `CV-${Date.now().toString().slice(-4)}`;
        const detail = colDetail >= 0 ? String(row[colDetail] || '').trim() : '';
        const empName = colEmp >= 0 ? String(row[colEmp] || '').trim() : 'Nguyễn Quang Thảo';
        let empId = colEmpId >= 0 ? String(row[colEmpId] || '').trim().toUpperCase() : '';
        if (!empId) {
          const matchEmp = appData.employees.find(e => e.name.toLowerCase() === empName.toLowerCase());
          empId = matchEmp ? matchEmp.id : 'NV01';
        }
        let startDate = colStart >= 0 ? String(row[colStart] || '').trim() : '2026-10-01';
        if (startDate.includes('/')) {
          const p = startDate.split('/');
          if (p.length === 3) startDate = `${p[2]}-${p[1].padStart(2, '0')}-${p[0].padStart(2, '0')}`;
        }
        const planDays = colDays >= 0 ? (parseInt(row[colDays]) || 1) : 1;
        const sDate = parseDate(startDate) || new Date(2026, 9, 1);
        const planEndDate = formatDate(addDays(sDate, planDays - 1));
        let actualEndDate = colActual >= 0 ? String(row[colActual] || '').trim() : '';
        if (actualEndDate.includes('/')) {
          const p = actualEndDate.split('/');
          if (p.length === 3) actualEndDate = `${p[2]}-${p[1].padStart(2, '0')}-${p[0].padStart(2, '0')}`;
        }
        const status = colStatus >= 0 ? String(row[colStatus] || 'Đang làm').trim() : 'Đang làm';
        const note = colNote >= 0 ? String(row[colNote] || '').trim() : '';

        rawTasks.push({
          id: `TASK-IMP-${Date.now().toString().slice(-4)}${rIdx + 1}`,
          mainTaskId,
          mainTaskTitle: title,
          title,
          detail,
          empId,
          empName,
          startDate,
          planDays,
          planEndDate,
          actualEndDate,
          status,
          note
        });
      });
    }

    rawTasks.forEach(task => {
      const exists = appData.tasks.some(t => {
        if (task.id && t.id && t.id.toLowerCase() === task.id.toLowerCase()) return true;
        const sameTitle = (t.mainTaskTitle || t.title).toLowerCase() === (task.mainTaskTitle || task.title).toLowerCase();
        const sameEmp = t.empId === task.empId || (t.empName && task.empName && t.empName.toLowerCase() === task.empName.toLowerCase());
        const sameStart = t.startDate === task.startDate;
        const sameDetail = (t.detail || '').toLowerCase() === (task.detail || '').toLowerCase();
        return sameTitle && sameEmp && sameStart && sameDetail;
      });

      if (exists) {
        skippedCount++;
      } else {
        addedCount++;
        if (!task.id) task.id = `TASK-${Date.now().toString().slice(-4)}${addedCount}`;
        appData.tasks.push(task);
      }
    });

  } else {
    // NHẬP NHÂN SỰ
    let rawEmps = [];
    if (parsedSmartImportData.type === 'JSON') {
      const d = parsedSmartImportData.data;
      if (Array.isArray(d)) rawEmps = d;
      else if (d.employees && Array.isArray(d.employees)) rawEmps = d.employees;
    } else {
      const rows = parsedSmartImportData.data.slice(1);
      const header = parsedSmartImportData.data[0].map(h => String(h || '').trim().toLowerCase());
      const colId = header.findIndex(h => h.includes('mã nv') || h.includes('mã nhân viên'));
      const colName = header.findIndex(h => h.includes('họ và tên') || h.includes('tên') || h.includes('nhân sự'));
      const colDept = header.findIndex(h => h.includes('phòng') || h.includes('bộ phận') || h.includes('dept'));

      rows.forEach((row, rIdx) => {
        if (!row || row.length === 0) return;
        const name = colName >= 0 ? String(row[colName] || '').trim() : '';
        if (!name) return;
        const id = colId >= 0 ? String(row[colId] || `NV0${appData.employees.length + rIdx + 1}`).trim().toUpperCase() : `NV0${appData.employees.length + rIdx + 1}`;
        const dept = colDept >= 0 ? String(row[colDept] || 'Kỹ thuật').trim() : 'Kỹ thuật';
        rawEmps.push({ id, name, dept });
      });
    }

    rawEmps.forEach(emp => {
      if (!emp.name) return;
      const exists = appData.employees.some(e => {
        if (emp.id && e.id && e.id.toLowerCase() === emp.id.toLowerCase()) return true;
        return e.name.toLowerCase() === emp.name.toLowerCase();
      });

      if (exists) {
        skippedCount++;
      } else {
        addedCount++;
        if (!emp.id) emp.id = `NV0${appData.employees.length + 1}`;
        appData.employees.push(emp);
      }
    });
  }

  saveDataToStorage();
  updateAuthUI();
  renderUserDropdown();
  populateEmployeeSelects();
  renderEmployeeTable();
  applyFilters();

  const alertBox = document.getElementById('smartImportAlert');
  if (alertBox) {
    alertBox.className = 'p-3 rounded-lg text-xs bg-emerald-100 text-emerald-800 border border-emerald-300 font-semibold block';
    alertBox.innerText = `Thành công! Đã chèn thêm ${addedCount} mục mới chưa có (Bỏ qua ${skippedCount} mục đã có sẵn).`;
    alertBox.classList.remove('hidden');
  }

  setTimeout(() => {
    closeSmartImportModal();
  }, 1600);
}

// ================= SAO LƯU & XUẤT CÁC FILE JSON =================
function openSyncModal() {
  document.getElementById('syncModal').classList.remove('hidden');
}

function closeSyncModal() {
  document.getElementById('syncModal').classList.add('hidden');
}

function exportDatabaseJson() {
  downloadJsonFile(appData, 'database.json');
}

function exportTasksJson() {
  downloadJsonFile(appData.tasks, 'tasks.json');
}

function exportEmployeesJson() {
  downloadJsonFile(appData.employees, 'employees.json');
}

function downloadJsonFile(obj, filename) {
  const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(obj, null, 2));
  const downloadAnchor = document.createElement('a');
  downloadAnchor.setAttribute('href', dataStr);
  downloadAnchor.setAttribute('download', filename);
  document.body.appendChild(downloadAnchor);
  downloadAnchor.click();
  downloadAnchor.remove();
}

function importDatabaseJson(e) {
  const file = e.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = function(evt) {
    try {
      const parsed = JSON.parse(evt.target.result);
      if (parsed && (parsed.employees || parsed.tasks || Array.isArray(parsed))) {
        if (Array.isArray(parsed)) {
          if (parsed.length > 0 && parsed[0].planDays !== undefined) {
            appData.tasks = parsed;
          } else if (parsed.length > 0 && parsed[0].dept !== undefined) {
            appData.employees = parsed;
          }
        } else {
          appData = parsed;
        }

        saveDataToStorage();
        closeSyncModal();
        updateAuthUI();
        renderEmployeeTable();
        applyFilters();
        alert('Khôi phục CSDL JSON thành công!');
      } else {
        alert('File JSON không đúng cấu trúc của ứng dụng!');
      }
    } catch (err) {
      alert('Lỗi đọc file JSON: ' + err.message);
    }
  };
  reader.readAsText(file);
}

function restoreDefaultDatabase() {
  const defaultSource = (typeof window !== 'undefined' && window.MBC_DEFAULT_DATABASE) ? window.MBC_DEFAULT_DATABASE : null;
  if (!defaultSource || !defaultSource.tasks || defaultSource.tasks.length === 0) {
    alert('Không tìm thấy file database.js trong thư mục ứng dụng!');
    return;
  }
  if (!confirm('Bạn có chắc muốn nạp lại CSDL gốc từ file database.js (Mặc định 2026-2027)? Toàn bộ dữ liệu hiện tại sẽ được cập nhật đồng bộ.')) {
    return;
  }

  appData = JSON.parse(JSON.stringify(defaultSource));
  saveDataToStorage();
  closeSyncModal();
  updateAuthUI();
  renderEmployeeTable();
  populateEmployeeSelects();
  applyFilters();
  alert(`Đã nạp thành công ${appData.tasks.length} công việc và ${appData.employees.length} nhân sự từ database.js!`);
}

function resetToSampleData() {
  restoreDefaultDatabase();
}

// ================= KHỞI ĐỘNG ỨNG DỤNG =================
window.addEventListener('DOMContentLoaded', async () => {
  await loadInitialData();
  const filterMonthInput = document.getElementById('filterMonth');
  if (filterMonthInput) filterMonthInput.value = viewState.filterMonth;

  const filterStatusSelect = document.getElementById('filterStatus');
  if (filterStatusSelect) filterStatusSelect.value = viewState.filterStatus;

  updateAuthUI();
  renderUserDropdown();
  populateEmployeeSelects();
  applyFilters();

  document.addEventListener('click', (e) => {
    const userDropdown = document.getElementById('userDropdown');
    if (userDropdown && !userDropdown.contains(e.target) && !e.target.closest('button[onclick="toggleUserDropdown()"]')) {
      userDropdown.classList.add('hidden');
    }
  });
});
