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
  filterYear: '2026',
  filterStatus: 'ALL',
  filterKeyword: '',
  groupByParent: false
};

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
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (parsed && parsed.employees && parsed.tasks && parsed.tasks.length > 5) {
        appData = parsed;
        return;
      }
    }
  } catch (err) {
    console.warn('Lỗi đọc LocalStorage:', err);
  }

  // Nếu LocalStorage chưa có dữ liệu đầy đủ, nạp từ file database.json cùng thư mục
  try {
    const res = await fetch('database.json');
    if (res.ok) {
      const data = await res.json();
      if (data && data.tasks) {
        appData = data;
        saveDataToStorage();
        return;
      }
    }
  } catch (err) {
    console.log('Chạy offline local file, nạp dữ liệu tích hợp');
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

// ================= TIMELINE BUILDER: THEO NGÀY, THEO TUẦN, THEO THÁNG =================
function getTimelineColumns() {
  const cols = [];

  if (viewState.timeScale === 'MONTH') {
    // Chế độ xem theo Tháng: hiển thị 14 tháng từ T1/2026 đến T2/2027 (hoặc cả năm)
    const startYear = 2026;
    for (let m = 1; m <= 12; m++) {
      cols.push({
        type: 'MONTH',
        year: startYear,
        month: m,
        label: `T${m}/${startYear.toString().slice(-2)}`,
        subLabel: '2026',
        startDate: new Date(startYear, m - 1, 1),
        endDate: new Date(startYear, m, 0)
      });
    }
    // Thêm T1, T2 năm 2027 để xem tiến độ năm sau
    for (let m = 1; m <= 3; m++) {
      cols.push({
        type: 'MONTH',
        year: 2027,
        month: m,
        label: `T${m}/27`,
        subLabel: '2027',
        startDate: new Date(2027, m - 1, 1),
        endDate: new Date(2027, m, 0)
      });
    }
  } else if (viewState.timeScale === 'WEEK') {
    // Chế độ xem theo Tuần: 10 tuần liên tiếp
    const baseDate = parseDate(viewState.startOffsetDate) || new Date(2026, 9, 1);
    for (let w = 0; w < 10; w++) {
      const wStart = addDays(baseDate, w * 7);
      const wEnd = addDays(wStart, 6);
      cols.push({
        type: 'WEEK',
        label: `Tuần ${w + 1}`,
        subLabel: `${wStart.getDate()}/${wStart.getMonth()+1} - ${wEnd.getDate()}/${wEnd.getMonth()+1}`,
        startDate: wStart,
        endDate: wEnd
      });
    }
  } else {
    // Chế độ xem theo Ngày (mặc định)
    const baseDate = parseDate(viewState.startOffsetDate) || new Date(2026, 9, 1);
    let totalDays = 10;
    if (viewState.windowMode === '10') totalDays = 10;
    else if (viewState.windowMode === '15') totalDays = 15;
    else if (viewState.windowMode === 'month') {
      const y = baseDate.getFullYear();
      const m = baseDate.getMonth();
      totalDays = new Date(y, m + 1, 0).getDate();
    }

    const dayNames = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7'];
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

// Thay đổi chế độ xem (Ngày / Tuần / Tháng)
function setTimeScale(scale) {
  viewState.timeScale = scale;

  document.getElementById('btnScaleDay').className = 'px-2.5 py-1 rounded font-semibold text-slate-600 hover:bg-white text-xs transition';
  document.getElementById('btnScaleWeek').className = 'px-2.5 py-1 rounded font-semibold text-slate-600 hover:bg-white text-xs transition';
  document.getElementById('btnScaleMonth').className = 'px-2.5 py-1 rounded font-semibold text-slate-600 hover:bg-white text-xs transition';

  if (scale === 'DAY') {
    document.getElementById('btnScaleDay').className = 'px-2.5 py-1 rounded font-bold bg-white text-brand-700 shadow-sm text-xs transition';
    document.getElementById('dayWindowControls').style.display = 'flex';
  } else if (scale === 'WEEK') {
    document.getElementById('btnScaleWeek').className = 'px-2.5 py-1 rounded font-bold bg-white text-brand-700 shadow-sm text-xs transition';
    document.getElementById('dayWindowControls').style.display = 'none';
  } else {
    document.getElementById('btnScaleMonth').className = 'px-2.5 py-1 rounded font-bold bg-white text-brand-700 shadow-sm text-xs transition';
    document.getElementById('dayWindowControls').style.display = 'none';
  }

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

    if (col.type === 'MONTH') {
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

    if (viewState.filterStatus !== 'ALL') {
      if (viewState.filterStatus === 'Quá hạn') {
        const today = new Date(2026, 9, 5);
        const planEnd = parseDate(task.planEndDate);
        if (task.status === 'Hoàn thành') return false;
        if (!planEnd || today <= planEnd) return false;
      } else if (task.status !== viewState.filterStatus) {
        return false;
      }
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

    // Nếu đang xem Theo Ngày và có lọc tháng
    if (viewState.timeScale === 'DAY' && viewState.filterMonth) {
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

    let statusBadge = '';
    if (task.status === 'Hoàn thành') {
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

    // Hiển thị Công việc chính & Phân cấp
    const mainBadge = task.mainTaskId ? `<span class="px-1.5 py-0.5 text-[9px] font-semibold bg-sky-50 text-sky-700 rounded border border-sky-200 mr-1">${task.mainTaskId}</span>` : '';

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
        ${isAdmin ? `
          <div class="mt-1 flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition">
            <button onclick="editTask('${task.id}')" class="text-blue-600 hover:text-blue-800 text-[10px]"><i class="fa-solid fa-pen"></i> Sửa</button>
            <button onclick="deleteTask('${task.id}')" class="text-rose-600 hover:text-rose-800 text-[10px]"><i class="fa-solid fa-trash"></i> Xóa</button>
          </div>
        ` : (isMyTask ? `
          <div class="mt-1">
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
    const tdActualDate = `<td rowspan="2" class="p-2 border-r border-b border-slate-300 text-center font-medium ${task.actualEndDate ? 'text-emerald-700 font-bold' : 'text-slate-400'}">${formatVnDate(task.actualEndDate) || 'Chưa hoàn thành'}</td>`;
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
    if (!tActualEnd && task.status === 'Đang làm') {
      tActualEnd = new Date(2026, 9, 5);
    }

    timelineCols.forEach(col => {
      const td = document.createElement('td');
      td.className = 'p-0 border-r border-b border-slate-300 text-center relative h-7 min-w-[54px] bg-emerald-50/10';

      const inRange = tStart && tActualEnd && col.startDate <= tActualEnd && col.endDate >= tStart;

      if (inRange) {
        const isStart = col.startDate <= tStart && col.endDate >= tStart;
        const isEnd = col.startDate <= tActualEnd && col.endDate >= tActualEnd;
        const isDelayed = tPlanEnd && col.startDate > tPlanEnd;

        const dateTag = (viewState.timeScale === 'MONTH' && isEnd) ? `<span class="arrow-date-tag">${task.actualEndDate ? formatVnDate(task.actualEndDate).slice(0, 5) : 'Đang làm'}</span>` : '';

        td.innerHTML = `
          <div class="h-4 my-1.5 ${isDelayed ? 'timeline-arrow-late' : 'timeline-arrow-actual'} relative flex items-center justify-end text-white text-[9px] font-bold ${isStart ? 'rounded-l-sm ml-1' : ''} ${isEnd ? 'mr-0' : ''}" title="Thực tích: ${formatVnDate(task.startDate)} - ${formatVnDate(task.actualEndDate || 'Đang làm')}">
            ${dateTag}
            ${isEnd ? `<div class="${isDelayed ? 'arrow-head-late' : 'arrow-head-actual'}"></div>` : ''}
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

  if (viewState.filterMonth) {
    viewState.startOffsetDate = `${viewState.filterMonth}-01`;
  }

  renderMainTable();
}

function setCurrentMonth() {
  document.getElementById('filterMonth').value = '2026-10';
  viewState.filterMonth = '2026-10';
  viewState.startOffsetDate = '2026-10-01';
  setTimeScale('DAY');
  applyFilters();
}

function setFullYearView() {
  document.getElementById('filterMonth').value = '';
  viewState.filterMonth = '';
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
    if (exportScale === 'MONTH_ALL') {
      const origScale = viewState.timeScale;
      viewState.timeScale = 'MONTH';
      timelineCols = getTimelineColumns();
      viewState.timeScale = origScale;
    }

    let tasksToExport = appData.tasks.filter(task => {
      if (appData.currentUser.role === 'employee' && task.empId !== appData.currentUser.id) return false;
      if (viewState.filterEmp !== 'ALL' && task.empId !== viewState.filterEmp) return false;
      if (viewState.filterStatus !== 'ALL' && task.status !== viewState.filterStatus) return false;
      return true;
    });

    let tableHtml = `
      <html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">
      <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <style>
          table { border-collapse: collapse; font-family: 'Segoe UI', Arial, sans-serif; font-size: 11px; }
          th { background-color: #f1f5f9; color: #1e293b; font-weight: bold; border: 1px solid #94a3b8; text-align: center; padding: 6px; }
          td { border: 1px solid #cbd5e1; padding: 4px 6px; vertical-align: middle; }
          .title-row { font-size: 15px; font-weight: bold; color: #0f3d52; height: 35px; text-align: left; }
          .info-cell { background-color: #ffffff; }
          .plan-label { background-color: #e0f2fe; color: #0369a1; font-weight: bold; text-align: center; }
          .actual-label { background-color: #dcfce7; color: #15803d; font-weight: bold; text-align: center; }
        </style>
      </head>
      <body>
        <table>
          <tr>
            <td colspan="${10 + timelineCols.length}" class="title-row">${customTitle}</td>
          </tr>
          <tr>
            <td colspan="${10 + timelineCols.length}" style="color: #64748b; font-style: italic;">Thời gian xuất: ${new Date().toLocaleString('vi-VN')} | Đơn vị: ${customUnit}</td>
          </tr>
          <tr></tr>
          <tr>
            <th>STT</th>
            <th>Mã CV</th>
            <th>Công việc chính</th>
            <th>Nội dung chi tiết</th>
            <th>Người thực hiện</th>
            <th>Ngày bắt đầu</th>
            <th>Thời gian dự kiến</th>
            <th>Thời gian hoàn thành</th>
            <th>Tình trạng</th>
            <th>Phân loại</th>
            ${timelineCols.map(col => `<th>${col.label}<br><span style="font-size: 9px; font-weight: normal; color: #64748b;">${col.subLabel || ''}</span></th>`).join('')}
          </tr>
    `;

    tasksToExport.forEach((task, idx) => {
      const tStart = parseDate(task.startDate);
      const tPlanEnd = parseDate(task.planEndDate);
      let tActualEnd = parseDate(task.actualEndDate);
      if (!tActualEnd && task.status === 'Đang làm') {
        tActualEnd = new Date(2026, 9, 5);
      }

      // Xác định các cột nào nằm trong phạm vi của Kế hoạch
      const planIndices = [];
      timelineCols.forEach((col, cIdx) => {
        if (tStart && tPlanEnd && col.startDate <= tPlanEnd && col.endDate >= tStart) {
          planIndices.push(cIdx);
        }
      });

      // Xác định các cột nào nằm trong phạm vi của Thực tích
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
          <td rowspan="2" style="font-weight: bold;" class="info-cell">${task.mainTaskTitle || task.title}</td>
          <td rowspan="2" class="info-cell">${task.detail || ''}</td>
          <td rowspan="2" class="info-cell">${task.empName}</td>
          <td rowspan="2" style="text-align: center;" class="info-cell">${formatVnDate(task.startDate)}</td>
          <td rowspan="2" style="text-align: center; font-weight: bold;" class="info-cell">${task.planDays || 1} ngày</td>
          <td rowspan="2" style="text-align: center;" class="info-cell">${formatVnDate(task.actualEndDate) || 'Chưa xong'}</td>
          <td rowspan="2" style="text-align: center; font-weight: bold;" class="info-cell">${task.status}</td>
          <td class="plan-label">Kế hoạch</td>
      `;

      // Render các ô timeline Kế hoạch LIỀN MẠCH
      timelineCols.forEach((col, cIdx) => {
        const inPlan = planIndices.includes(cIdx);
        if (inPlan) {
          const isFirst = cIdx === planIndices[0];
          const isLast = cIdx === planIndices[planIndices.length - 1];

          // Loại bỏ border giữa các ô liên tiếp để tạo thanh màu liền khối
          const borderStyle = `border-top: 2px solid #0f3d52; border-bottom: 2px solid #0f3d52; ${isFirst ? 'border-left: 2px solid #0f3d52;' : 'border-left: none;'} ${isLast ? 'border-right: 2px solid #0f3d52;' : 'border-right: none;'}`;
          row1 += `<td style="background-color: #1b5e7d; ${borderStyle} text-align: right; color: #ffffff; font-weight: bold; font-size: 11px;">${isLast ? '►' : ''}</td>`;
        } else {
          row1 += `<td></td>`;
        }
      });
      row1 += `</tr>`;

      // HÀNG 2: THỰC TÍCH LIỀN MẠCH
      let row2 = `<tr><td class="actual-label">Thực tích</td>`;
      timelineCols.forEach((col, cIdx) => {
        const inActual = actualIndices.includes(cIdx);
        if (inActual) {
          const isFirst = cIdx === actualIndices[0];
          const isLast = cIdx === actualIndices[actualIndices.length - 1];
          const isDelayed = tPlanEnd && col.startDate > tPlanEnd;

          const barColor = isDelayed ? '#d97706' : '#16a34a';
          const borderColor = isDelayed ? '#9a3412' : '#14532d';

          const borderStyle = `border-top: 2px solid ${borderColor}; border-bottom: 2px solid ${borderColor}; ${isFirst ? `border-left: 2px solid ${borderColor};` : 'border-left: none;'} ${isLast ? `border-right: 2px solid ${borderColor};` : 'border-right: none;'}`;
          row2 += `<td style="background-color: ${barColor}; ${borderStyle} text-align: right; color: #ffffff; font-weight: bold; font-size: 11px;">${isLast ? '►' : ''}</td>`;
        } else {
          row2 += `<td></td>`;
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
      'Ngày Bắt Đầu', 'Thời Gian Dự Kiến (Ngày)', 'Ngày Kế Hoạch Xong', 'Thời Gian Hoàn Thành Thực Tế',
      'Tình Trạng', 'Ghi Chú', 'Điểm Đánh Giá KPI'
    ]);

    appData.tasks.forEach((t, i) => {
      const impact = calculateTaskScoreImpact(t);
      dataRows.push([
        i + 1, t.mainTaskId || '', t.mainTaskTitle || t.title, t.id, t.detail || '', t.empId, t.empName,
        formatVnDate(t.startDate), t.planDays || 1, formatVnDate(t.planEndDate),
        formatVnDate(t.actualEndDate) || 'Chưa hoàn thành', t.status, t.note || '', impact.reason
      ]);
    });

    const ws = XLSX.utils.aoa_to_sheet(dataRows);
    ws['!cols'] = [
      { wch: 6 }, { wch: 14 }, { wch: 28 }, { wch: 14 }, { wch: 35 }, { wch: 10 }, { wch: 22 },
      { wch: 14 }, { wch: 16 }, { wch: 16 }, { wch: 18 }, { wch: 16 }, { wch: 25 }, { wch: 25 }
    ];
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'CSDL_CongViec');
    XLSX.writeFile(wb, `MBC_CSDL_CongViec_${viewState.filterMonth || 'All'}.xlsx`);
  } catch (err) {
    alert('Lỗi xuất CSDL: ' + err.message);
  }
}

// ================= TẢI FILE MẪU & NHẬP EXCEL =================
function openImportExcelModal() {
  document.getElementById('importModal').classList.remove('hidden');
  document.getElementById('selectedFileName').innerText = 'Nhấn để chọn file hoặc kéo thả file vào đây';
  document.getElementById('btnExecuteImport').disabled = true;
  document.getElementById('importResultAlert').classList.add('hidden');
}

function closeImportExcelModal() {
  document.getElementById('importModal').classList.add('hidden');
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
  XLSX.utils.book_append_sheet(wb, ws, 'MauImport');
  XLSX.writeFile(wb, 'MBC_Mau_Import_CongViec.xlsx');
}

let parsedExcelData = [];

function handleExcelFileSelect(e) {
  const file = e.target.files[0];
  if (!file) return;

  document.getElementById('selectedFileName').innerText = `Đã chọn: ${file.name} (${Math.round(file.size / 1024)} KB)`;

  const reader = new FileReader();
  reader.onload = function(evt) {
    try {
      const data = new Uint8Array(evt.target.result);
      const workbook = XLSX.read(data, { type: 'array' });
      const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
      parsedExcelData = XLSX.utils.sheet_to_json(firstSheet, { header: 1 });

      if (parsedExcelData.length > 1) {
        document.getElementById('btnExecuteImport').disabled = false;
      } else {
        alert('File Excel không có dòng dữ liệu hợp lệ!');
      }
    } catch (err) {
      alert('Không thể đọc file Excel: ' + err.message);
    }
  };
  reader.readAsArrayBuffer(file);
}

function processExcelImport() {
  if (!parsedExcelData || parsedExcelData.length < 2) return;

  const header = parsedExcelData[0].map(h => String(h || '').trim().toLowerCase());
  const rows = parsedExcelData.slice(1);

  const colMainId = header.findIndex(h => h.includes('mã cv chính') || h.includes('mã cv'));
  const colMainTitle = header.findIndex(h => h.includes('công việc chính') || h.includes('công việc'));
  const colDetail = header.findIndex(h => h.includes('chi tiết') || h.includes('nội dung'));
  const colEmp = header.findIndex(h => h.includes('người') || h.includes('thực hiện'));
  const colEmpId = header.findIndex(h => h.includes('mã nv'));
  const colStart = header.findIndex(h => h.includes('bắt đầu'));
  const colDays = header.findIndex(h => h.includes('dự kiến') && h.includes('thời gian') || h.includes('ngày'));
  const colActual = header.findIndex(h => h.includes('hoàn thành'));
  const colStatus = header.findIndex(h => h.includes('tình trạng'));
  const colNote = header.findIndex(h => h.includes('ghi chú'));

  let addedCount = 0;
  let skippedCount = 0;

  rows.forEach(row => {
    if (!row || row.length === 0) return;
    const title = colMainTitle >= 0 ? String(row[colMainTitle] || '').trim() : '';
    if (!title) return;

    const mainTaskId = colMainId >= 0 ? String(row[colMainId] || `CV-${Date.now().toString().slice(-4)}`).trim().toUpperCase() : `CV-${Date.now().toString().slice(-4)}`;
    const detail = colDetail >= 0 ? String(row[colDetail] || '').trim() : '';
    const empName = colEmp >= 0 ? String(row[colEmp] || '').trim() : 'Nguyễn Quang Thảo';
    let empId = colEmpId >= 0 ? String(row[colEmpId] || '').trim().toUpperCase() : '';

    if (!empId) {
      const matchEmp = appData.employees.find(e => e.name.toLowerCase() === empName.toLowerCase());
      if (matchEmp) empId = matchEmp.id;
      else {
        empId = `NV0${appData.employees.length + 1}`;
        appData.employees.push({ id: empId, name: empName, dept: 'Kỹ thuật' });
      }
    } else if (!appData.employees.some(e => e.id === empId)) {
      appData.employees.push({ id: empId, name: empName, dept: 'Kỹ thuật' });
    }

    let startDate = colStart >= 0 ? String(row[colStart] || '').trim() : '2026-10-01';
    if (startDate.includes('/')) {
      const parts = startDate.split('/');
      if (parts.length === 3) {
        startDate = `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`;
      }
    }

    const planDays = colDays >= 0 ? (parseInt(row[colDays]) || 1) : 1;
    const sDate = parseDate(startDate) || new Date(2026, 9, 1);
    const planEndDate = formatDate(addDays(sDate, planDays - 1));

    let actualEndDate = colActual >= 0 ? String(row[colActual] || '').trim() : '';
    if (actualEndDate.includes('/')) {
      const parts = actualEndDate.split('/');
      if (parts.length === 3) {
        actualEndDate = `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`;
      }
    }

    const status = colStatus >= 0 ? String(row[colStatus] || 'Đang làm').trim() : 'Đang làm';
    const note = colNote >= 0 ? String(row[colNote] || '').trim() : '';

    // CHỐNG TRÙNG LẶP: Tên việc + Mã NV + Ngày bắt đầu + Nội dung chi tiết
    const isDuplicate = appData.tasks.some(t => {
      return (t.mainTaskTitle || t.title).toLowerCase() === title.toLowerCase() &&
             t.empId === empId &&
             t.startDate === startDate &&
             (t.detail || '').toLowerCase() === detail.toLowerCase();
    });

    if (isDuplicate) {
      skippedCount++;
    } else {
      addedCount++;
      appData.tasks.push({
        id: `TASK-${Date.now().toString().slice(-4)}${addedCount}`,
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
    }
  });

  saveDataToStorage();
  renderEmployeeTable();
  applyFilters();

  const alertBox = document.getElementById('importResultAlert');
  alertBox.className = 'p-3 rounded-lg text-xs bg-emerald-100 text-emerald-800 border border-emerald-300 block';
  alertBox.innerHTML = `
    <div class="font-bold"><i class="fa-solid fa-circle-check"></i> Hoàn tất nhập dữ liệu Excel!</div>
    <div class="mt-1">&bull; Thêm mới thành công: <b>${addedCount}</b> công việc</div>
    <div>&bull; Bỏ qua (đã trùng lặp dữ liệu): <b>${skippedCount}</b> công việc</div>
  `;
  document.getElementById('btnExecuteImport').disabled = true;
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

function resetToSampleData() {
  if (!confirm('Bạn có chắc muốn khôi phục về dữ liệu mẫu mặc định 2026-2027?')) return;
  localStorage.removeItem(STORAGE_KEY);
  location.reload();
}

// ================= KHỞI ĐỘNG ỨNG DỤNG =================
window.addEventListener('DOMContentLoaded', async () => {
  await loadInitialData();
  document.getElementById('filterMonth').value = viewState.filterMonth;

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
