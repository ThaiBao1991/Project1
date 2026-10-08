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
const DB_VERSION  = '3.7'; // Bump này khi muốn xóa cache LocalStorage & nạp lại từ database.js

let appData = {
  version: '3.7',
  currentUser: {
    id: 'admin',
    name: 'Quản trị viên (Admin)',
    role: 'admin',
    dept: 'Ban Quản Trị'
  },
  employees: [],
  tasks: [],
  holidays: []
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
  filterPriority: 'ALL',
  filterSortBy: 'EMP_START',
  filterMainTask: 'ALL',
  filterKeyword: '',
  groupByParent: false
};

// ================= HÀM HỖ TRỢ XÁC ĐỊNH KHOẢNG NĂM & CÔNG VIỆC CHÍNH =================
function getTasksYearSpan() {
  // Ưu tiên khoảng lọc tự do nếu người dùng đã chọn
  if (viewState.filterStartDate && viewState.filterEndDate) {
    const fs = parseDate(viewState.filterStartDate);
    const fe = parseDate(viewState.filterEndDate);
    if (fs && fe) {
      return { minYear: fs.getFullYear(), maxYear: fe.getFullYear() };
    }
  }

  let minY = 9999;
  let maxY = 2026;
  const tasks = appData && Array.isArray(appData.tasks) ? appData.tasks : [];
  // Chỉ xét tasks theo bộ lọc nhân viên đang active
  const src = viewState.filterEmp !== 'ALL' ? tasks.filter(t => t.empId === viewState.filterEmp) : tasks;
  src.forEach(t => {
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
  if (minY === 9999) minY = 2026;
  return { minYear: minY, maxYear: Math.max(maxY, minY) };
}

/**
 * Tính khoảng tháng thực tế của danh sách task (dùng cho MONTH view).
 * Trả về { startYear, startMonth, endYear, endMonth } — chỉ trải đúng từ
 * tháng bắt đầu sớm nhất → tháng kết thúc muộn nhất trong tập task.
 */
function getTasksMonthSpan(taskList) {
  const now = new Date();
  let minDate = null;
  let maxDate = null;

  const source = (taskList && taskList.length > 0) ? taskList : (appData.tasks || []);
  source.forEach(t => {
    const s = parseDate(t.startDate);
    const e = parseDate(t.actualEndDate || t.planEndDate);
    if (s && (!minDate || s < minDate)) minDate = s;
    if (e && (!maxDate || e > maxDate)) maxDate = e;
  });

  if (!minDate) minDate = new Date(now.getFullYear(), now.getMonth(), 1);
  if (!maxDate) maxDate = new Date(now.getFullYear(), 11, 31);

  return {
    startYear:  minDate.getFullYear(),
    startMonth: minDate.getMonth() + 1,
    endYear:    maxDate.getFullYear(),
    endMonth:   maxDate.getMonth() + 1
  };
}

/**
 * Sinh mã công việc theo chuẩn CV-YYYY-XXXX.
 * Tự động tìm số thứ tự lớn nhất trong năm year để tăng dần tuần tự.
 */
function generateNextTaskId(year) {
  const y = year || new Date().getFullYear();
  const prefix = `CV-${y}-`;
  let maxNum = 0;
  (appData.tasks || []).forEach(t => {
    if (t.id && t.id.startsWith(prefix)) {
      const num = parseInt(t.id.slice(prefix.length), 10);
      if (!isNaN(num) && num > maxNum) maxNum = num;
    }
    if (t.mainTaskId && t.mainTaskId.startsWith(prefix)) {
      const num = parseInt(t.mainTaskId.slice(prefix.length), 10);
      if (!isNaN(num) && num > maxNum) maxNum = num;
    }
  });
  return `${prefix}${String(maxNum + 1).padStart(4, '0')}`;
}

/**
 * Hiển thị thời gian dự kiến linh hoạt theo đơn vị (giờ, ngày, tuần, tháng)
 */
function formatPlanDuration(task) {
  if (!task) return '1 ngày';
  if (task.planDuration && task.planUnit) {
    return `${task.planDuration} ${task.planUnit}`;
  }
  if (task.planDays) {
    return `${task.planDays} ngày`;
  }
  return '1 ngày';
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

// Kiểm tra ngày có thuộc Lịch nghỉ đặc biệt / Ngày lễ không
function getHolidayInfo(d) {
  if (!d || !appData || !Array.isArray(appData.holidays)) return null;
  const dStr = formatDate(d);
  return appData.holidays.find(h => h.date === dStr) || null;
}

// Huy hiệu màu sắc theo nguồn yêu cầu (Giám đốc, Trưởng phòng, Đối ứng, Cải tiến, Khác)
function getSourceBadge(source) {
  if (!source) return '';
  const s = source.trim();
  if (s.includes('Giám đốc')) {
    return '<span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-bold bg-purple-100 text-purple-800 border border-purple-300 shadow-sm" title="Yêu cầu từ: Giám đốc"><i class="fa-solid fa-crown text-[8px] text-purple-600"></i> Giám đốc</span>';
  } else if (s.includes('Trưởng phòng')) {
    return '<span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-bold bg-blue-100 text-blue-800 border border-blue-300 shadow-sm" title="Yêu cầu từ: Trưởng phòng"><i class="fa-solid fa-user-tie text-[8px] text-blue-600"></i> Trưởng phòng</span>';
  } else if (s.includes('Đối ứng')) {
    return '<span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-bold bg-amber-100 text-amber-800 border border-amber-300 shadow-sm" title="Yêu cầu: Đối ứng sự cố"><i class="fa-solid fa-bolt text-[8px] text-amber-600"></i> Đối ứng</span>';
  } else if (s.includes('Cải thiện') || s.includes('Cải tiến')) {
    return '<span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 shadow-sm" title="Yêu cầu: Cải thiện nội bộ"><i class="fa-solid fa-arrow-trend-up text-[8px] text-emerald-600"></i> Cải tiến</span>';
  } else if (s.includes('Chiến lược')) {
    return '<span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-bold bg-rose-100 text-rose-800 border border-rose-300 shadow-sm" title="Dự án chiến lược"><i class="fa-solid fa-chess text-[8px] text-rose-600"></i> Chiến lược</span>';
  } else {
    return `<span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-medium bg-slate-100 text-slate-700 border border-slate-300">${s}</span>`;
  }
}

// ================= LƯU TRỮ LOCALSTORAGE & NẠP DỮ LIỆU BAN ĐẦU =================
async function loadInitialData() {
  // Kiểm tra version: nếu DB_VERSION khác version đang lưu -> xóa cache nạp lại mới
  try {
    const savedVer = localStorage.getItem(STORAGE_KEY + '_VER');
    if (savedVer !== DB_VERSION) {
      localStorage.removeItem(STORAGE_KEY);
      localStorage.setItem(STORAGE_KEY + '_VER', DB_VERSION);
      console.log(`[MBC Data] Phiên bản DB mới (${DB_VERSION}), đã xóa cache cũ và sẽ nạp lại dữ liệu...`);
    }
  } catch(e) {}

  // LỚP 1: Kiểm tra LocalStorage xem người dùng đã có dữ liệu lưu trữ hợp lệ chưa
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (parsed && Array.isArray(parsed.employees) && Array.isArray(parsed.tasks) && parsed.tasks.length > 0) {
        appData = parsed;
        if (!appData.holidays || !Array.isArray(appData.holidays) || appData.holidays.length === 0) {
          if (window.MBC_DEFAULT_DATABASE && Array.isArray(window.MBC_DEFAULT_DATABASE.holidays)) {
            appData.holidays = JSON.parse(JSON.stringify(window.MBC_DEFAULT_DATABASE.holidays));
          }
        }
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

  // Chuẩn hóa trạng thái nếu có dữ liệu cũ lưu không dấu
  normalizeTaskStatuses();
}

function normalizeTaskStatuses() {
  if (!appData || !Array.isArray(appData.tasks)) return;
  appData.tasks.forEach(t => {
    if (!t.status) return;
    const s = t.status.trim();
    if (s === 'Dang lam') t.status = 'Đang làm';
    else if (s === 'Tam dung' || s === 'Dung du an') t.status = 'Tạm dừng';
    else if (s === 'Hoan thanh') t.status = 'Hoàn thành';
    else if (s === 'Hoan thanh tre') t.status = 'Hoàn thành trễ';
  });
}

function saveDataToStorage() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(appData));
    renderFilterMainTasksSelect();
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

// ================= BỐ TRÍ & SẮP XẾP CÔNG VIỆC THEO NHIỀU TIÊU CHÍ =================
function groupAndSortTasks(taskList) {
  if (!taskList || taskList.length === 0) return [];

  const sortBy = viewState.filterSortBy || (document.getElementById('filterSortBy') ? document.getElementById('filterSortBy').value : 'EMP_START');

  // 1. Thứ tự mã việc (Mã CV tăng dần)
  if (sortBy === 'TASK_ID') {
    return [...taskList].sort((a, b) => (a.id || '').localeCompare(b.id || '', undefined, { numeric: true, sensitivity: 'base' }));
  }

  // 2. Ngày bắt đầu (Sớm nhất trước)
  if (sortBy === 'START_DATE') {
    return [...taskList].sort((a, b) => {
      const da = parseDate(a.startDate) || new Date(0);
      const db = parseDate(b.startDate) || new Date(0);
      if (da.getTime() !== db.getTime()) return da.getTime() - db.getTime();
      return (a.id || '').localeCompare(b.id || '');
    });
  }

  // 3. Hạn hoàn thành / Deadline (Deadline gấp nhất lên trước)
  if (sortBy === 'DEADLINE') {
    return [...taskList].sort((a, b) => {
      const da = parseDate(a.planEndDate) || new Date(9999, 0, 1);
      const db = parseDate(b.planEndDate) || new Date(9999, 0, 1);
      if (da.getTime() !== db.getTime()) return da.getTime() - db.getTime();
      return (a.id || '').localeCompare(b.id || '');
    });
  }

  // 4. Mức độ ưu tiên (Giám đốc ➔ Trưởng phòng ➔ Đối ứng ➔ Cải tiến ➔ Chiến lược ➔ Khác)
  if (sortBy === 'PRIORITY') {
    const getPriorityWeight = (src) => {
      if (!src) return 99;
      const s = src.toLowerCase();
      if (s.includes('giám đốc')) return 1;
      if (s.includes('trưởng phòng')) return 2;
      if (s.includes('đối ứng')) return 3;
      if (s.includes('cải tiến') || s.includes('cải thiện')) return 4;
      if (s.includes('chiến lược')) return 5;
      return 6;
    };
    return [...taskList].sort((a, b) => {
      const wa = getPriorityWeight(a.taskSource);
      const wb = getPriorityWeight(b.taskSource);
      if (wa !== wb) return wa - wb;
      const da = parseDate(a.startDate) || new Date(0);
      const db = parseDate(b.startDate) || new Date(0);
      return da.getTime() - db.getTime();
    });
  }

  // 5. Quá hạn / Cần cập nhật tình trạng lên đầu
  if (sortBy === 'OVERDUE') {
    const systemToday = new Date(2026, 9, 7);
    const getOverdueScore = (task) => {
      const isCompleted = task.status === 'Hoàn thành' || task.status === 'Hoàn thành trễ' || !!task.actualEndDate;
      const isPaused = task.status === 'Tạm dừng' || task.status === 'Dừng dự án';
      if (isCompleted) return 100;
      if (isPaused) return 80;
      const pEnd = parseDate(task.planEndDate);
      const isOverdue = pEnd && systemToday > pEnd;
      const lastUpdate = parseDate(task.lastStatusUpdate || task.startDate);
      const daysSinceUpdate = lastUpdate ? Math.floor((systemToday - lastUpdate) / (1000 * 60 * 60 * 24)) : 3;
      const needUpdate = daysSinceUpdate >= 3;
      if (isOverdue && needUpdate) return 1;
      if (isOverdue) return 2;
      if (needUpdate) return 3;
      return 10;
    };
    return [...taskList].sort((a, b) => {
      const sa = getOverdueScore(a);
      const sb = getOverdueScore(b);
      if (sa !== sb) return sa - sb;
      const da = parseDate(a.planEndDate) || new Date(9999, 0, 1);
      const db = parseDate(b.planEndDate) || new Date(9999, 0, 1);
      return da.getTime() - db.getTime();
    });
  }

  // 6. MẶC ĐỊNH (EMP_START): Gom nhóm tổng thể theo Người (empId), trong mỗi người sắp xếp theo Ngày nhận việc (startDate) tăng dần
  const empOrder = [];
  const empMap = new Map();

  // Khởi tạo thứ tự nhân sự theo appData.employees để giữ thứ tự chuẩn ban đầu
  if (appData && Array.isArray(appData.employees)) {
    appData.employees.forEach(emp => {
      empMap.set(emp.id, []);
      empOrder.push(emp.id);
    });
  }

  // Phân loại task vào từng người
  taskList.forEach(task => {
    const empKey = task.empId || 'UNASSIGNED';
    if (!empMap.has(empKey)) {
      empMap.set(empKey, []);
      empOrder.push(empKey);
    }
    empMap.get(empKey).push(task);
  });

  const sortedTasks = [];
  empOrder.forEach(empId => {
    const tasks = empMap.get(empId) || [];
    if (tasks.length === 0) return;
    // Với mỗi người: sắp xếp theo Ngày nhận việc (startDate) tăng dần, sau đó theo ID
    tasks.sort((a, b) => {
      const da = parseDate(a.startDate) || new Date(0);
      const db = parseDate(b.startDate) || new Date(0);
      if (da.getTime() !== db.getTime()) return da.getTime() - db.getTime();
      return (a.id || '').localeCompare(b.id || '');
    });
    sortedTasks.push(...tasks);
  });

  return sortedTasks;
}

// Tự động thu phóng Timeline vừa vặn ngày đầu đến đúng hạn cuối công việc (Không thừa, không kẹt 365 ngày)
function fitTimelineToTaskDates() {
  const currentTasks = appData.tasks.filter(t => {
    if (appData.currentUser.role === 'employee' && t.empId !== appData.currentUser.id) return false;
    if (viewState.filterEmp !== 'ALL' && t.empId !== viewState.filterEmp) return false;
    if (viewState.filterMainTask && viewState.filterMainTask !== 'ALL') {
      const mId = viewState.filterMainTask.toLowerCase();
      const taskMain = (t.mainTaskId || '').toLowerCase();
      const taskTitle = (t.mainTaskTitle || t.title || '').toLowerCase();
      if (taskMain !== mId && taskTitle !== mId && (t.id || '').toLowerCase() !== mId) return false;
    }
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
    // Chế độ xem theo Tháng: Chỉ hiện từ tháng bắt đầu sớm nhất đến tháng kết thúc muộn nhất của dữ liệu
    // Nếu có lọc theo khoảng ngày tự do thì ưu tiên khoảng đó
    let mStart, mEnd;
    if (viewState.filterStartDate && viewState.filterEndDate) {
      const fs = parseDate(viewState.filterStartDate);
      const fe = parseDate(viewState.filterEndDate);
      mStart = { y: fs.getFullYear(), m: fs.getMonth() + 1 };
      mEnd   = { y: fe.getFullYear(), m: fe.getMonth() + 1 };
    } else {
      // Lọc task hiện tại theo emp nếu đang filter
      let srcTasks = appData.tasks || [];
      if (viewState.filterEmp !== 'ALL') srcTasks = srcTasks.filter(t => t.empId === viewState.filterEmp);
      const span = getTasksMonthSpan(srcTasks);
      mStart = { y: span.startYear, m: span.startMonth };
      mEnd   = { y: span.endYear,   m: span.endMonth   };
    }

    let cy = mStart.y, cm = mStart.m;
    while (cy < mEnd.y || (cy === mEnd.y && cm <= mEnd.m)) {
      cols.push({
        type: 'MONTH',
        year: cy,
        month: cm,
        label: `T${cm}/${cy.toString().slice(-2)}`,
        subLabel: `${cy}`,
        startDate: new Date(cy, cm - 1, 1),
        endDate: new Date(cy, cm, 0, 23, 59, 59)
      });
      cm++;
      if (cm > 12) { cm = 1; cy++; }
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
          const hol = getHolidayInfo(d);
          cols.push({
            type: 'DAY',
            date: d,
            label: `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}`,
            subLabel: dayNames[d.getDay()],
            yearLabel: d.getFullYear(),
            isWeekend,
            isHoliday: !!hol,
            holidayType: hol ? hol.type : null,
            holidayName: hol ? hol.name : '',
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
      const hol = getHolidayInfo(d);
      cols.push({
        type: 'DAY',
        date: d,
        label: `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}`,
        subLabel: dayNames[d.getDay()],
        yearLabel: d.getFullYear(),
        isWeekend,
        isHoliday: !!hol,
        holidayType: hol ? hol.type : null,
        holidayName: hol ? hol.name : '',
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

  while (headerRow.children.length > 12) {
    headerRow.removeChild(headerRow.lastChild);
  }

  timelineCols.forEach(col => {
    const th = document.createElement('th');
    const isWeekend = col.isWeekend;
    let thClass = isWeekend ? 'col-weekend text-amber-900' : 'bg-slate-100 text-slate-700';

    if (col.isHoliday) {
      if (col.holidayType === 'NATIONAL') {
        thClass = 'col-holiday-national text-red-900 font-bold';
      } else {
        thClass = 'col-holiday-special text-purple-900 font-bold';
      }
      th.title = `Ngày nghỉ: ${col.holidayName}`;
    }

    th.className = `p-1.5 border-r border-slate-300 text-center min-w-[54px] max-w-[70px] font-semibold text-[10px] ${thClass}`;

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

    // LỌC THEO NGUỒN YÊU CẦU / ƯU TIÊN
    const priFilter = viewState.filterPriority || (document.getElementById('filterPriority') ? document.getElementById('filterPriority').value : 'ALL');
    if (priFilter && priFilter !== 'ALL') {
      const tSource = (task.taskSource || '').toLowerCase();
      const fPri = priFilter.toLowerCase();
      if (!tSource.includes(fPri)) return false;
    }

    // LỌC THEO DỰ ÁN / CÔNG VIỆC CHÍNH
    if (viewState.filterMainTask && viewState.filterMainTask !== 'ALL') {
      const mId = viewState.filterMainTask.toLowerCase();
      const taskMain = (task.mainTaskId || '').toLowerCase();
      const taskTitle = (task.mainTaskTitle || task.title || '').toLowerCase();
      if (taskMain !== mId && taskTitle !== mId && (task.id || '').toLowerCase() !== mId) {
        return false;
      }
    }

    return true;
  });

  // Cập nhật Banner dự án đang chọn
  const banner = document.getElementById('activeProjectBanner');
  if (banner) {
    if (viewState.filterMainTask && viewState.filterMainTask !== 'ALL') {
      const mTasks = getUniqueMainTasks();
      const foundM = mTasks.find(m => m.id === viewState.filterMainTask);
      const displayTitle = foundM ? `[${foundM.id}] ${foundM.title}` : viewState.filterMainTask;
      const titleEl = document.getElementById('activeProjectTitle');
      const badgeEl = document.getElementById('activeProjectBadge');
      if (titleEl) titleEl.innerText = displayTitle;
      if (badgeEl) badgeEl.innerText = `${filteredTasks.length} công việc`;
      banner.classList.remove('hidden');
    } else {
      banner.classList.add('hidden');
    }
  }

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

  // Ngày tham chiếu hệ thống (10/2026 hoặc ngày thực tế nếu đang ở 2026)
  const realNow = new Date();
  const systemToday = (realNow.getFullYear() === 2026)
    ? new Date(realNow.getFullYear(), realNow.getMonth(), realNow.getDate())
    : new Date(2026, 9, 8);
  let prevEmpId = null;

  // Render từng công việc
  filteredTasks.forEach((task, idx) => {
    const isAdmin = appData.currentUser.role === 'admin';
    const isMyTask = appData.currentUser.id === task.empId;
    const rawStatus = (task.status || '').trim();
    const isPaused = rawStatus === 'Tạm dừng' || rawStatus === 'Tam dung' || rawStatus === 'Dừng dự án' || rawStatus === 'Dung du an';
    const isCompleted = rawStatus === 'Hoàn thành' || rawStatus === 'Hoan thanh' || rawStatus === 'Hoàn thành trễ' || rawStatus === 'Hoan thanh tre' || !!task.actualEndDate;
    const isInProgress = !isCompleted && !isPaused;

    // Ngày hiệu lực kết thúc cho việc đang làm (lấy ngày lớn nhất giữa systemToday và lastStatusUpdate)
    let taskEffectiveToday = new Date(systemToday);
    if (task.lastStatusUpdate) {
      const lastUp = parseDate(task.lastStatusUpdate);
      if (lastUp && lastUp > taskEffectiveToday) {
        taskEffectiveToday = lastUp;
      }
    }

    const currentSortBy = viewState.filterSortBy || (document.getElementById('filterSortBy') ? document.getElementById('filterSortBy').value : 'EMP_START');

    // Phân cách nhóm nhân sự (chỉ khi đang sắp xếp theo Người => Thứ tự việc)
    if (currentSortBy === 'EMP_START' && task.empId !== prevEmpId) {
      prevEmpId = task.empId;
      const empTaskCount = filteredTasks.filter(t => t.empId === task.empId).length;
      const trGroup = document.createElement('tr');
      trGroup.className = 'emp-group-header bg-slate-100/90 text-slate-800 border-y border-slate-300 font-bold text-xs select-none';
      trGroup.innerHTML = `
        <td colspan="${12 + timelineCols.length}" class="px-3 py-1.5 text-left sticky-col-left bg-gradient-to-r from-slate-100 via-indigo-50/60 to-transparent">
          <div class="flex items-center gap-2">
            <span class="inline-flex items-center justify-center w-5 h-5 rounded-full bg-indigo-600 text-white text-[10px]"><i class="fa-solid fa-user"></i></span>
            <span class="text-indigo-950 font-bold text-xs">${task.empName || 'Chưa phân công'} (${task.empId})</span>
            <span class="text-[10px] font-normal text-slate-500">• ${empTaskCount} công việc (xếp theo ngày nhận việc)</span>
          </div>
        </td>
      `;
      tbody.appendChild(trGroup);
    }

    // Kiểm tra quá 3 ngày chưa cập nhật tình trạng hoặc quá hạn kế hoạch đối với việc chưa hoàn tất
    let isOverdueUpdate = false;
    let daysSinceUpdate = 0;
    let overdueReason = '';

    if (!isCompleted && !isPaused) {
      const pEnd = parseDate(task.planEndDate);
      const sDate = parseDate(task.startDate);

      if (!task.lastStatusUpdate) {
        // CHƯA CẬP NHẬT LẦN NÀO:
        if (pEnd && taskEffectiveToday > pEnd) {
          // Đã quá ngày kết thúc kế hoạch mà chưa cập nhật gì!
          isOverdueUpdate = true;
          daysSinceUpdate = Math.max(1, Math.floor((taskEffectiveToday - pEnd) / (1000 * 60 * 60 * 24)));
          overdueReason = `Quá hạn KH (${daysSinceUpdate} ngày) & chưa cập nhật lần nào`;
        } else if (sDate && taskEffectiveToday >= sDate) {
          // Đã qua ngày bắt đầu mà chưa cập nhật: nếu quá 3 ngày thì báo
          const diffFromStart = Math.max(0, Math.floor((taskEffectiveToday - sDate) / (1000 * 60 * 60 * 24)));
          if (diffFromStart >= 3) {
            isOverdueUpdate = true;
            daysSinceUpdate = diffFromStart;
            overdueReason = `${diffFromStart} ngày chưa cập nhật tình trạng`;
          }
        } else if (!pEnd && !sDate) {
          isOverdueUpdate = true;
          daysSinceUpdate = 3;
          overdueReason = 'Chưa cập nhật tình trạng';
        }
      } else {
        // ĐÃ TỪNG CẬP NHẬT TRƯỚC ĐÓ:
        const lastUpdateDate = parseDate(task.lastStatusUpdate);
        if (lastUpdateDate) {
          daysSinceUpdate = Math.max(0, Math.floor((taskEffectiveToday - lastUpdateDate) / (1000 * 60 * 60 * 24)));
          if (daysSinceUpdate >= 3) {
            isOverdueUpdate = true;
            overdueReason = `Quá ${daysSinceUpdate} ngày chưa cập nhật`;
          } else if (pEnd && taskEffectiveToday > pEnd && lastUpdateDate < pEnd) {
            // Đã quá hạn kế hoạch nhưng lần cập nhật cuối là từ trước khi hết hạn
            isOverdueUpdate = true;
            const overdueDays = Math.max(1, Math.floor((taskEffectiveToday - pEnd) / (1000 * 60 * 60 * 24)));
            overdueReason = `Quá hạn KH (${overdueDays} ngày) & cần cập nhật lại`;
          }
        } else {
          isOverdueUpdate = true;
          daysSinceUpdate = 3;
          overdueReason = 'Chưa cập nhật tình trạng';
        }
      }
    }

    let statusBadge = '';
    if (isPaused) {
      statusBadge = '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300">⏸ Tạm dừng</span>';
    } else if (rawStatus === 'Hoàn thành' || rawStatus === 'Hoan thanh') {
      statusBadge = '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">Hoàn Thành</span>';
    } else if (rawStatus === 'Hoàn thành trễ' || rawStatus === 'Hoan thanh tre') {
      statusBadge = '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-orange-100 text-orange-800 border border-orange-300">Hoàn Thành trễ</span>';
    } else {
      const pEnd = parseDate(task.planEndDate);
      if (pEnd && taskEffectiveToday > pEnd) {
        statusBadge = '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-300">Quá hạn</span>';
      } else {
        statusBadge = '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-100 text-blue-800 border border-blue-300">Đang làm</span>';
      }
    }

    // Nguồn yêu cầu & Tiến độ công việc chính
    const sourceBadge = getSourceBadge(task.taskSource);
    const mainProgress = task.mainTaskId ? getMainTaskProgress(task.mainTaskId) : null;
    const mainBadge = task.mainTaskId ? `
      <button type="button" onclick="filterByMainTask('${task.mainTaskId}')" class="px-1.5 py-0.5 text-[9px] font-semibold bg-sky-50 hover:bg-sky-100 text-sky-700 rounded border border-sky-200 mr-1 transition cursor-pointer" title="Nhấn để lọc xem các việc của dự án [${task.mainTaskId}] và tự căn chỉnh biểu đồ">
        <i class="fa-solid fa-diagram-project text-[8px] mr-0.5"></i>${task.mainTaskId}
      </button>
    ` : '';
    let parentStatusBadge = '';
    if (mainProgress) {
      if (mainProgress.isAllCompleted) {
        parentStatusBadge = `<div class="mt-1"><span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300" title="Toàn bộ ${mainProgress.totalCount} công việc con đã hoàn thành"><i class="fa-solid fa-circle-check text-emerald-600"></i>Dự án Xong (100%)</span></div>`;
      } else {
        parentStatusBadge = `<div class="mt-1"><span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-semibold bg-sky-100 text-sky-800 border border-sky-300" title="Dự án đang làm: ${mainProgress.completedCount}/${mainProgress.totalCount} việc hoàn thành"><i class="fa-solid fa-spinner fa-spin-pulse text-sky-600"></i>Dự án: ${mainProgress.completedCount}/${mainProgress.totalCount} việc</span></div>`;
      }
    }

    // Hiển thị ngày cập nhật cuối (lastStatusUpdate)
    const hasStatusUpdate = !!(task.lastStatusUpdate && task.lastStatusUpdate.trim());
    const lastUpdateDisplay = hasStatusUpdate ? formatVnDate(task.lastStatusUpdate) : 'Chưa cập nhật';
    const lastUpdateInfo = (!isCompleted && !isPaused) ? `
      <div class="mt-1 flex items-center gap-1" title="${hasStatusUpdate ? `Lần cập nhật gần nhất: ${lastUpdateDisplay}` : 'Chưa từng ghi nhận cập nhật tiến độ'}">
        <i class="fa-regular fa-clock text-slate-400 text-[8px]"></i>
        <span class="text-[9px] ${(!hasStatusUpdate || isOverdueUpdate) ? 'text-rose-600 font-semibold' : 'text-slate-400'}">
          CN cuối: ${lastUpdateDisplay}
        </span>
      </div>
    ` : '';

    // Cảnh báo quá 3 ngày chưa cập nhật hoặc quá hạn kế hoạch
    const overdueWarning = isOverdueUpdate ? `
      <div class="mt-1">
        <span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-bold bg-rose-100 text-rose-700 border border-rose-300 animate-pulse" title="${overdueReason || `Quá ${daysSinceUpdate} ngày chưa cập nhật tình trạng! Cần click 'Cập nhật tình trạng' để ghi nhận.`}">
          <i class="fa-solid fa-triangle-exclamation"></i> Cần Cập Nhật (${daysSinceUpdate > 0 ? `${daysSinceUpdate} ngày` : 'Quá hạn'})
        </span>
      </div>
    ` : '';

    // DÒNG 1: THÔNG TIN GỘP + KẾ HOẠCH
    const tr1 = document.createElement('tr');
    tr1.className = `hover:bg-slate-50/80 transition group ${isOverdueUpdate ? 'row-overdue-update' : ''}`;

    const tdCB = `
      <td rowspan="2" class="p-2 border-r border-b border-slate-300 text-center bg-white sticky-col-left shadow-[1px_0_0_0_#cbd5e1]" style="left: 0;">
        <input type="checkbox" class="gantt-task-cb w-3.5 h-3.5 text-brand-600 rounded border-slate-300 cursor-pointer" data-id="${task.id}" onchange="_onGanttTaskCheckboxChange(this)">
      </td>
    `;
    const tdSTT = `<td rowspan="2" class="p-2 border-r border-b border-slate-300 text-center font-bold text-slate-500 bg-white sticky-col-left shadow-[1px_0_0_0_#cbd5e1]" style="left: 40px;">${idx + 1}</td>`;
    const tdTitle = `
      <td rowspan="2" class="p-2 border-r border-b border-slate-300 bg-white sticky-col-left shadow-[1px_0_0_0_#cbd5e1]" style="left: 80px;">
        <div class="font-bold text-slate-900 leading-snug">
          <button type="button" onclick="filterByMainTask('${task.mainTaskId || task.id}')" class="text-left font-bold text-slate-900 hover:text-sky-700 transition cursor-pointer" title="Nhấn để chỉ xem các việc của dự án này và tự động căn chỉnh biểu đồ">
            ${task.mainTaskTitle || task.title}
          </button>
        </div>
        <div class="text-[10px] text-slate-500 flex flex-wrap items-center gap-1 mt-0.5">
          ${mainBadge}
          <span>${task.id}</span>
          ${sourceBadge}
        </div>
        ${parentStatusBadge}
        ${lastUpdateInfo}
        ${overdueWarning}
        <div class="mt-1.5 flex flex-wrap items-center gap-1.5">
          ${!isCompleted ? `
            <button onclick="openStatusLogModal('${task.id}')" class="px-2 py-0.5 text-[10px] font-bold rounded bg-violet-100 text-violet-700 hover:bg-violet-200 border border-violet-300 transition flex items-center gap-1 shadow-sm" title="Ghi nhật ký / Cập nhật tình trạng công việc">
              <i class="fa-solid fa-clipboard-list"></i> Cập nhật tình trạng
            </button>
          ` : ''}
          ${isAdmin ? `
            <div class="flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition">
              <button onclick="toggleTaskPause('${task.id}')" class="text-amber-600 hover:text-amber-800 text-[10px] font-semibold" title="Tạm dừng hoặc tiếp tục công việc"><i class="fa-solid fa-circle-pause"></i> ${isPaused ? 'Tiếp tục' : 'Dừng'}</button>
              <button onclick="editTask('${task.id}')" class="text-blue-600 hover:text-blue-800 text-[10px]"><i class="fa-solid fa-pen"></i> Sửa</button>
              <button onclick="deleteTask('${task.id}')" class="text-rose-600 hover:text-rose-800 text-[10px]"><i class="fa-solid fa-trash"></i> Xóa</button>
            </div>
          ` : (isMyTask ? `
            <div class="flex items-center gap-1.5">
              <button onclick="toggleTaskPause('${task.id}')" class="text-amber-600 hover:text-amber-800 text-[10px] font-semibold"><i class="fa-solid fa-circle-pause"></i> ${isPaused ? 'Tiếp tục' : 'Dừng'}</button>
              <button onclick="openQuickUpdateModal('${task.id}')" class="text-emerald-600 hover:text-emerald-800 font-semibold text-[10px]"><i class="fa-solid fa-check-to-slot"></i> Cập nhật</button>
            </div>
          ` : '')}
        </div>
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
    const tdPlanDays = `<td rowspan="2" class="p-2 border-r border-b border-slate-300 text-center font-semibold text-slate-800">${formatPlanDuration(task)}</td>`;
    const tdActualDate = `<td rowspan="2" class="p-2 border-r border-b border-slate-300 text-center font-medium ${task.actualEndDate ? 'text-emerald-700 font-bold' : 'text-slate-400'}">${formatVnDate(task.actualEndDate) || (isPaused ? 'Tạm dừng' : 'Chưa hoàn thành')}</td>`;
    const tdStatus = `<td rowspan="2" class="p-2 border-r border-b border-slate-300 text-center">${statusBadge}</td>`;
    const tdNote = `<td rowspan="2" class="p-2 border-r border-b border-slate-300 text-slate-500 italic text-[11px]">${task.note || ''}</td>`;

    let linkHtml = '';
    if (task.link && task.link.trim()) {
      const safeLink = task.link.trim();
      const isWebUrl = /^https?:\/\//i.test(safeLink);
      const isFileUri = /^file:\/\//i.test(safeLink);
      const href = (isWebUrl || isFileUri) ? safeLink : (safeLink.includes(':') || safeLink.startsWith('\\\\') ? `file:///${safeLink.replace(/\\/g, '/')}` : safeLink);
      linkHtml = `
        <div class="flex items-center justify-center gap-1">
          <a href="${href}" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-sky-100 text-sky-800 hover:bg-sky-200 border border-sky-300 transition" title="Mở: ${safeLink.replace(/"/g, '&quot;')}">
            <i class="fa-solid fa-arrow-up-right-from-square text-[9px]"></i> Mở
          </a>
          <button type="button" onclick="openEditTaskLinkModal('${task.id}')" class="text-slate-400 hover:text-sky-600 p-0.5 text-[10px]" title="Chỉnh sửa link">
            <i class="fa-solid fa-pen"></i>
          </button>
        </div>
      `;
    } else {
      linkHtml = `
        <button type="button" onclick="openEditTaskLinkModal('${task.id}')" class="px-1.5 py-0.5 text-[10px] rounded text-slate-400 hover:text-sky-700 hover:bg-sky-50 border border-dashed border-slate-300 transition" title="Thêm liên kết tệp/thư mục">
          <i class="fa-solid fa-plus text-[8px]"></i> Link
        </button>
      `;
    }
    const tdLink = `<td rowspan="2" class="p-2 border-r border-b border-slate-300 text-center">${linkHtml}</td>`;
    const tdLabelPlan = `<td class="p-1.5 border-r border-b border-slate-300 text-center font-semibold text-slate-700 bg-sky-50/50 text-[10px]">Kế hoạch</td>`;

    tr1.innerHTML = tdCB + tdSTT + tdTitle + tdDetail + tdEmp + tdStart + tdPlanDays + tdActualDate + tdStatus + tdNote + tdLink + tdLabelPlan;

    const tStart = parseDate(task.startDate);
    const tPlanEnd = parseDate(task.planEndDate);

    // Vẽ thanh Kế hoạch theo các cột
    timelineCols.forEach(col => {
      const td = document.createElement('td');
      let cellBg = 'bg-slate-50/30';
      if (col.isHoliday) {
        cellBg = col.holidayType === 'NATIONAL' ? 'cell-national' : 'cell-special';
      } else if (col.isWeekend) {
        cellBg = 'cell-weekend';
      }
      td.className = `p-0 border-r border-b border-slate-200 text-center relative h-7 min-w-[54px] ${cellBg}`;

      const inRange = tStart && tPlanEnd && col.startDate <= tPlanEnd && col.endDate >= tStart;

      if (inRange) {
        const isStart = col.startDate <= tStart && col.endDate >= tStart;
        const isEnd = col.startDate <= tPlanEnd && col.endDate >= tPlanEnd;
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
    tr2.className = `hover:bg-slate-50/80 transition group border-b border-slate-300 ${isOverdueUpdate ? 'row-overdue-update' : ''}`;
    const tdLabelActual = `<td class="p-1.5 border-r border-b border-slate-300 text-center font-semibold text-emerald-800 bg-emerald-50/50 text-[10px]">Thực tích</td>`;
    tr2.innerHTML = tdLabelActual;

    let tActualEnd = parseDate(task.actualEndDate);
    if (!tActualEnd && isInProgress) {
      // Đang làm: biểu đồ kéo dài từ startDate đến hôm nay/ngày cập nhật mới nhất
      tActualEnd = taskEffectiveToday;
      if (tStart && tActualEnd < tStart) tActualEnd = tStart;
    } else if (!tActualEnd && isPaused) {
      tActualEnd = taskEffectiveToday;
      if (tStart && tActualEnd < tStart) tActualEnd = tStart;
    }

    timelineCols.forEach(col => {
      const td = document.createElement('td');
      let cellBg = 'bg-emerald-50/10';
      if (col.isHoliday) {
        cellBg = col.holidayType === 'NATIONAL' ? 'cell-national' : 'cell-special';
      } else if (col.isWeekend) {
        cellBg = 'cell-weekend';
      }
      td.className = `p-0 border-r border-b border-slate-300 text-center relative h-7 min-w-[54px] ${cellBg}`;

      const inRange = tStart && tActualEnd && col.startDate <= tActualEnd && col.endDate >= tStart;

      if (inRange) {
        const isStart = col.startDate <= tStart && col.endDate >= tStart;
        const isEnd = col.startDate <= tActualEnd && col.endDate >= tActualEnd;
        const isDelayed = !isPaused && tPlanEnd && col.startDate > tPlanEnd;

        let barClass = 'timeline-arrow-actual';
        let headClass = 'arrow-head-actual';
        let titleTip = `Thực tích: ${formatVnDate(task.startDate)} - ${formatVnDate(task.actualEndDate)}`;

        if (isPaused) {
          barClass = 'timeline-arrow-paused';
          headClass = 'arrow-head-paused';
          titleTip = `Tạm dừng: ${formatVnDate(task.startDate)} - hiện tại`;
        } else if (!task.actualEndDate && isInProgress) {
          // Biểu đồ thực tích khi Đang làm: dải màu cyan/blue kèm animation
          barClass = 'timeline-arrow-in-progress';
          headClass = 'arrow-head-in-progress';
          titleTip = `Đang làm (Tiến độ đến ${formatVnDate(formatDate(tActualEnd))}): ${formatVnDate(task.startDate)} → ${formatVnDate(formatDate(tActualEnd))}`;
        } else if (isDelayed) {
          barClass = 'timeline-arrow-late';
          headClass = 'arrow-head-late';
          titleTip = `Hoàn thành trễ: ${formatVnDate(task.startDate)} - ${formatVnDate(task.actualEndDate)}`;
        }

        const dateTag = (viewState.timeScale === 'MONTH' && isEnd) ? 
          `<span class="arrow-date-tag">${isPaused ? 'Dừng' : (!task.actualEndDate && isInProgress ? 'Đang làm' : formatVnDate(task.actualEndDate).slice(0, 5))}</span>` : '';

        // Tìm các lần cập nhật trong ngày/cột này
        const logMarkers = (task.statusLogs || []).filter(log => {
          const logDate = parseDate(log.date);
          return logDate && col.startDate <= logDate && col.endDate >= logDate;
        });

        // Biểu tượng ghi chú hiển thị TRỰC TIẾP TRÊN THÂN MŨI TÊN
        let noteIconHtml = '';
        if (logMarkers.length > 0) {
          const lastLog = logMarkers[logMarkers.length - 1];
          const progTxt = lastLog.progress !== undefined ? `${lastLog.progress}%` : '';
          const tooltipContent = logMarkers.map(l => {
            const p = l.progress !== undefined ? ` [${l.progress}%]` : '';
            return `📋 ${formatVnDate(l.date)}${p}: ${l.note || 'Ghi nhận tiến độ'} (${l.author || 'Người dùng'})`;
          }).join('\n');

          noteIconHtml = `
            <div onclick="openStatusLogModal('${task.id}')" 
                 class="absolute left-1/2 -translate-x-1/2 top-1/2 -translate-y-1/2 z-20 flex items-center justify-center cursor-pointer pointer-events-auto"
                 title="${tooltipContent.replace(/"/g, '&quot;')}">
              <span class="inline-flex items-center gap-0.5 px-1 py-0.5 rounded-full bg-amber-400 text-amber-950 text-[8px] font-black shadow border border-white hover:scale-110 hover:bg-amber-300 transition-transform">
                <i class="fa-solid fa-note-sticky text-[8px] text-amber-900"></i>
                ${progTxt ? `<span>${progTxt}</span>` : ''}
              </span>
            </div>
          `;
        }

        td.innerHTML = `
          <div class="h-4 my-1.5 ${barClass} relative flex items-center justify-end text-white text-[9px] font-bold ${isStart ? 'rounded-l-sm ml-1' : ''} ${isEnd ? 'mr-0' : ''}" title="${titleTip}">
            ${dateTag}
            ${noteIconHtml}
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
  if (typeof _updateGanttBulkDeleteUI === 'function') {
    _updateGanttBulkDeleteUI();
  }
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

// ================= QUẢN LÝ NHÂN SỰ & TỰ ĐỘNG SINH MÃ NV-XXXX =================
function generateNextEmpId() {
  let maxNum = 0;
  (appData.employees || []).forEach(emp => {
    if (!emp.id) return;
    const m = emp.id.match(/^NV[-_]?(\d+)$/i);
    if (m) {
      const num = parseInt(m[1], 10);
      if (num > maxNum) maxNum = num;
    }
  });
  return `NV-${String(maxNum + 1).padStart(4, '0')}`;
}

function openEmployeeModal() {
  document.getElementById('employeeModal').classList.remove('hidden');
  resetEmpForm();
  renderEmployeeTable();
}

function closeEmployeeModal() {
  document.getElementById('employeeModal').classList.add('hidden');
}

function renderEmployeeTable() {
  const tbody = document.getElementById('empTableBody');
  tbody.innerHTML = '';
  document.getElementById('empCountBadge').innerText = `Tổng số: ${appData.employees.length} nhân sự`;

  // Reset checkbox header
  const selectAllCb = document.getElementById('empSelectAll');
  if (selectAllCb) selectAllCb.checked = false;
  _updateEmpBulkDeleteBtn();

  appData.employees.forEach(emp => {
    const empTasks = appData.tasks.filter(t => t.empId === emp.id);
    const scores = calculateEmployeeMonthlyScores(emp.id, 2026);
    const currentMonthScore = scores[10] || 100;

    const tr = document.createElement('tr');
    tr.className = 'hover:bg-slate-50 transition';
    tr.innerHTML = `
      <td class="p-2 text-center">
        <input type="checkbox" class="emp-cb w-3.5 h-3.5 cursor-pointer accent-rose-500" data-id="${emp.id}" onchange="_onEmpCheckboxChange()">
      </td>
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
  let code = document.getElementById('empCode').value.trim().toUpperCase();
  const name = document.getElementById('empName').value.trim();
  const dept = document.getElementById('empDept').value.trim();

  if (!code) code = generateNextEmpId();
  if (!name) return;

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
      alert(`Mã nhân viên "${code}" đã tồn tại! Hệ thống sẽ tự động gán mã mới.`);
      code = generateNextEmpId();
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
  const codeInput = document.getElementById('empCode');
  codeInput.value = emp.id;
  codeInput.readOnly = false;
  document.getElementById('empName').value = emp.name;
  document.getElementById('empDept').value = emp.dept || '';

  document.getElementById('empFormTitle').innerText = 'Chỉnh Sửa Thông Tin Nhân Viên';
  document.getElementById('empBtnText').innerText = 'Cập Nhật';
  document.getElementById('empCancelEditBtn').classList.remove('hidden');
}

function resetEmpForm() {
  document.getElementById('empEditId').value = '';
  const codeInput = document.getElementById('empCode');
  codeInput.value = generateNextEmpId();
  codeInput.readOnly = true;
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

// ================= BỘ LỌC DỰ ÁN & CĂN CHỈNH BIỂU ĐỒ TỰ ĐỘNG =================
function renderFilterMainTasksSelect() {
  const select = document.getElementById('filterMainTask');
  if (!select) return;
  const curVal = viewState.filterMainTask || 'ALL';
  const mainTasks = getUniqueMainTasks();
  let html = '<option value="ALL">-- Tất cả dự án --</option>';
  mainTasks.forEach(mt => {
    const isSel = mt.id === curVal ? 'selected' : '';
    html += `<option value="${mt.id}" ${isSel}>[${mt.id}] ${mt.title} (${mt.subtasks.length} việc)</option>`;
  });
  select.innerHTML = html;
  select.value = curVal;
}

function handleMainTaskFilterChange() {
  const select = document.getElementById('filterMainTask');
  viewState.filterMainTask = select ? select.value : 'ALL';
  applyFilters();
  if (viewState.filterMainTask !== 'ALL') {
    fitTimelineToTaskDates();
  }
}

function filterByMainTask(mainTaskId) {
  if (!mainTaskId) return;
  if (viewState.filterMainTask === mainTaskId) {
    // Nhấn lại lần nữa -> Quay về xem tất cả
    viewState.filterMainTask = 'ALL';
  } else {
    viewState.filterMainTask = mainTaskId;
  }
  const select = document.getElementById('filterMainTask');
  if (select) select.value = viewState.filterMainTask;
  applyFilters();
  if (viewState.filterMainTask !== 'ALL') {
    fitTimelineToTaskDates();
  }
}

function clearProjectFilter() {
  viewState.filterMainTask = 'ALL';
  const select = document.getElementById('filterMainTask');
  if (select) select.value = 'ALL';
  applyFilters();
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
      const durationInput = document.getElementById('taskPlanDuration');
      const unitSelect = document.getElementById('taskPlanUnit');
      if (durationInput) durationInput.value = task.planDuration || task.planDays || 1;
      if (unitSelect) unitSelect.value = task.planUnit || 'ngày';
      document.getElementById('taskPlanDays').value = task.planDays || 1;
      document.getElementById('taskPlanEndDate').value = task.planEndDate || '';
      document.getElementById('taskActualEndDate').value = task.actualEndDate || '';
      document.getElementById('taskNote').value = task.note || '';
      const linkInput = document.getElementById('taskLink');
      if (linkInput) linkInput.value = task.link || '';
      const sourceSelect = document.getElementById('taskSource');
      if (sourceSelect) sourceSelect.value = task.taskSource || 'Cải thiện nội bộ';
    }
  } else {
    titleEl.innerText = 'Thêm Công Việc Mới';
    document.getElementById('taskId').value = '';
    document.getElementById('taskForm').reset();
    const linkInput = document.getElementById('taskLink');
    if (linkInput) linkInput.value = '';
    parentSelect.value = '__NEW__';
    const sourceSelect = document.getElementById('taskSource');
    if (sourceSelect) sourceSelect.value = 'Cải thiện nội bộ';
    // Sinh mã mainTaskCode tuần tự theo năm hiện tại (CV-YYYY-XXXX)
    const curYear = new Date().getFullYear();
    document.getElementById('taskMainCode').value = generateNextTaskId(curYear);
    document.getElementById('taskStartDate').value = '2026-10-01';
    const durationInput = document.getElementById('taskPlanDuration');
    const unitSelect = document.getElementById('taskPlanUnit');
    if (durationInput) durationInput.value = 1;
    if (unitSelect) unitSelect.value = 'ngày';
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
    if (!codeInput.value) {
      const curYear = new Date().getFullYear();
      codeInput.value = generateNextTaskId(curYear);
    }
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
  const durationInput = document.getElementById('taskPlanDuration');
  const unitSelect = document.getElementById('taskPlanUnit');
  const val = durationInput ? (parseFloat(durationInput.value) || 1) : (parseInt(document.getElementById('taskPlanDays').value) || 1);
  const unit = unitSelect ? unitSelect.value : 'ngày';

  if (startStr && val > 0) {
    const d = parseDate(startStr);
    if (d) {
      let end = d;
      let daysEquivalent = Math.ceil(val);
      if (unit === 'giờ') {
        end = d; // Cùng ngày
        daysEquivalent = 1;
      } else if (unit === 'ngày') {
        end = addDays(d, Math.ceil(val) - 1);
        daysEquivalent = Math.ceil(val);
      } else if (unit === 'tuần') {
        end = addDays(d, Math.ceil(val * 7) - 1);
        daysEquivalent = Math.ceil(val * 7);
      } else if (unit === 'tháng') {
        end = addDays(d, Math.ceil(val * 30) - 1);
        daysEquivalent = Math.ceil(val * 30);
      }
      document.getElementById('taskPlanEndDate').value = formatDate(end);
      const hiddenDays = document.getElementById('taskPlanDays');
      if (hiddenDays) hiddenDays.value = daysEquivalent;
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
  const durationInput = document.getElementById('taskPlanDuration');
  const unitSelect = document.getElementById('taskPlanUnit');
  const planDuration = durationInput ? (parseFloat(durationInput.value) || 1) : 1;
  const planUnit = unitSelect ? unitSelect.value : 'ngày';
  const planDays = parseInt(document.getElementById('taskPlanDays').value) || 1;
  const planEndDate = document.getElementById('taskPlanEndDate').value;
  const actualEndDate = document.getElementById('taskActualEndDate').value;
  const note = document.getElementById('taskNote').value.trim();
  const linkInput = document.getElementById('taskLink');
  const link = linkInput ? linkInput.value.trim() : '';
  const sourceSelect = document.getElementById('taskSource');
  const taskSource = sourceSelect ? sourceSelect.value : 'Cải thiện nội bộ';

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
      task.planDuration = planDuration;
      task.planUnit = planUnit;
      task.planDays = planDays;
      task.planEndDate = planEndDate;
      task.actualEndDate = actualEndDate;
      task.note = note;
      task.link = link;
      task.taskSource = taskSource;
    }
  } else {
    // Sinh mã CV chi tiết theo chuẩn CV-YYYY-XXXX (tự tăng theo năm bắt đầu)
    const taskYear = startDate ? parseInt(startDate.slice(0, 4)) : new Date().getFullYear();
    const newId = generateNextTaskId(taskYear);
    appData.tasks.push({
      id: newId,
      mainTaskId,
      mainTaskTitle,
      title: mainTaskTitle,
      detail,
      empId,
      empName,
      startDate,
      planDuration,
      planUnit,
      planDays,
      planEndDate,
      actualEndDate,
      status,
      link,
      note,
      taskSource,
      lastStatusUpdate: startDate
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
  const priEl = document.getElementById('filterPriority');
  if (priEl) viewState.filterPriority = priEl.value;
  const sortEl = document.getElementById('filterSortBy');
  if (sortEl) viewState.filterSortBy = sortEl.value;
  const mainEl = document.getElementById('filterMainTask');
  if (mainEl) viewState.filterMainTask = mainEl.value;

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

// ================= MODAL CẤU HÌNH XUẤT BÁO CÁO EXCEL (CONFIG TITLE & PERSISTENCE) =================
const EXPORT_CONFIG_STORAGE_KEY = 'MBC_EXCEL_EXPORT_CONFIG';

function generateSmartExportTitle() {
  let title = 'BÁO CÁO KẾ HOẠCH & THỰC TÍCH CÔNG VIỆC NHÓM';
  if (viewState.filterMainTask && viewState.filterMainTask !== 'ALL') {
    const mTasks = getUniqueMainTasks();
    const foundM = mTasks.find(m => m.id === viewState.filterMainTask);
    const mName = foundM ? foundM.title : viewState.filterMainTask;
    title += ` - DỰ ÁN: ${mName.toUpperCase()}`;
  } else if (viewState.filterEmp !== 'ALL') {
    const emp = appData.employees.find(e => e.id === viewState.filterEmp);
    if (emp) title += ` - NHÂN SỰ: ${emp.name.toUpperCase()} (${emp.dept})`;
  }
  if (viewState.filterMonth) {
    title += ` - THÁNG ${viewState.filterMonth.split('-')[1]}/${viewState.filterMonth.split('-')[0]}`;
  } else {
    title += ' - NĂM 2026';
  }
  return title;
}

function openExportConfigModal() {
  const modal = document.getElementById('exportConfigModal');
  const titleInput = document.getElementById('exportReportTitle');
  const unitInput = document.getElementById('exportUnitName');
  const scaleSelect = document.getElementById('exportScaleSelect');
  const chk = document.getElementById('saveExportConfigCheckbox');

  // Đọc cấu hình đã lưu trong LocalStorage (nếu có)
  try {
    const raw = localStorage.getItem(EXPORT_CONFIG_STORAGE_KEY);
    if (raw) {
      const saved = JSON.parse(raw);
      if (saved) {
        if (saved.customUnit && unitInput) unitInput.value = saved.customUnit;
        if (saved.exportScale && scaleSelect) scaleSelect.value = saved.exportScale;
        if (saved.customTitle && saved.isCustomTitle && titleInput) {
          titleInput.value = saved.customTitle;
        } else if (titleInput) {
          titleInput.value = generateSmartExportTitle();
        }
        if (chk) chk.checked = true;
        modal.classList.remove('hidden');
        return;
      }
    }
  } catch(e) {}

  if (titleInput) titleInput.value = generateSmartExportTitle();
  if (chk) chk.checked = true;
  modal.classList.remove('hidden');
}

function closeExportConfigModal() {
  document.getElementById('exportConfigModal').classList.add('hidden');
}

function saveExportConfigManual() {
  const titleInput = document.getElementById('exportReportTitle');
  const unitInput = document.getElementById('exportUnitName');
  const scaleSelect = document.getElementById('exportScaleSelect');
  const chk = document.getElementById('saveExportConfigCheckbox');

  const customTitle = titleInput ? titleInput.value.trim() : '';
  const customUnit = unitInput ? unitInput.value.trim() : '';
  const exportScale = scaleSelect ? scaleSelect.value : 'CURRENT';
  const isRemember = chk ? chk.checked : true;

  if (isRemember) {
    const config = { customTitle, customUnit, exportScale, isCustomTitle: true };
    localStorage.setItem(EXPORT_CONFIG_STORAGE_KEY, JSON.stringify(config));
    alert('Đã lưu cấu hình xuất báo cáo Excel thành công!');
  } else {
    localStorage.removeItem(EXPORT_CONFIG_STORAGE_KEY);
    alert('Đã bỏ ghi nhớ cấu hình xuất Excel.');
  }
}

function resetExportConfigToDefault() {
  localStorage.removeItem(EXPORT_CONFIG_STORAGE_KEY);
  const unitInput = document.getElementById('exportUnitName');
  const scaleSelect = document.getElementById('exportScaleSelect');
  const titleInput = document.getElementById('exportReportTitle');
  const chk = document.getElementById('saveExportConfigCheckbox');

  if (unitInput) unitInput.value = 'MBC Group - Phân xưởng sản xuất';
  if (scaleSelect) scaleSelect.value = 'CURRENT';
  if (chk) chk.checked = true;
  if (titleInput) titleInput.value = generateSmartExportTitle();
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
    const exportScale = document.getElementById('exportScaleSelect').value;

    // Ghi nhớ cấu hình nếu checkbox được chọn
    const chk = document.getElementById('saveExportConfigCheckbox');
    if (chk && chk.checked) {
      const config = { customTitle, customUnit, exportScale, isCustomTitle: true };
      localStorage.setItem(EXPORT_CONFIG_STORAGE_KEY, JSON.stringify(config));
    }

    // ── Bước 1: Lọc & gom nhóm task trước khi xây dựng timeline (fix hoisting bug) ──
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

    // ── Bước 2: Xây dựng cột timeline sau khi đã có tasksToExport ──
    let timelineCols = getTimelineColumns();
    if (exportScale === 'FIT_TASKS') {
      let minStart = null, maxEnd = null;
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
            type: 'DAY', date: d,
            label: `${String(d.getDate()).padStart(2,'0')}/${String(d.getMonth()+1).padStart(2,'0')}`,
            subLabel: dayNames[d.getDay()], yearLabel: d.getFullYear(),
            isWeekend: d.getDay() === 0 || d.getDay() === 6,
            startDate: d, endDate: d
          });
        }
      }
    } else if (exportScale && exportScale !== 'CURRENT') {
      const origScale = viewState.timeScale;
      viewState.timeScale = exportScale;
      timelineCols = getTimelineColumns();
      viewState.timeScale = origScale;
    }

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
            <td colspan="${12 + timelineCols.length}" class="title-row">${customTitle}</td>
          </tr>
          <tr>
            <td colspan="${12 + timelineCols.length}" class="sub-title">Đơn vị: <b>${customUnit}</b> | Thời gian xuất: <b>${new Date().toLocaleString('vi-VN')}</b> | Tổng số việc: <b>${totalExp}</b></td>
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
            <td colspan="${timelineCols.length + 1}" style="background-color: #f1f5f9; font-size: 10px; color: #334155;">
              <b>CHÚ THÍCH:</b> 
              <span style="color: #1e40af; font-weight: bold;">■ Kế hoạch (►)</span> | 
              <span style="color: #0284c7; font-weight: bold;">■ Đang làm (►)</span> | 
              <span style="color: #15803d; font-weight: bold;">■ Đúng hạn (✔)</span> | 
              <span style="color: #64748b; font-weight: bold;">■ Tạm dừng (⏸)</span> | 
              <span style="color: #d97706; font-weight: bold;">■ Trễ hạn (⚠)</span> | 
              <span style="color: #b45309; font-weight: bold;">📝 Có ghi chú tiến độ</span>
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
            <th style="width: 120px;">Link / Tệp</th>
            <th style="width: 65px;">Loại</th>
            ${timelineCols.map(col => `<th style="min-width: 48px;">${col.label}<br><span style="font-size: 9px; font-weight: normal; opacity: 0.8;">${col.subLabel || ''}</span></th>`).join('')}
          </tr>
    `;

    tasksToExport.forEach((task, idx) => {
      const rawStatus = (task.status || '').trim();
      const isPaused = rawStatus === 'Tạm dừng' || rawStatus === 'Tam dung' || rawStatus === 'Dừng dự án' || rawStatus === 'Dung du an';
      const isCompleted = rawStatus === 'Hoàn thành' || rawStatus === 'Hoan thanh' || rawStatus === 'Hoàn thành trễ' || rawStatus === 'Hoan thanh tre' || !!task.actualEndDate;
      const isInProgress = !isCompleted && !isPaused;

      const tStart = parseDate(task.startDate);
      const tPlanEnd = parseDate(task.planEndDate);
      let taskEffectiveToday = (new Date().getFullYear() === 2026) ? new Date() : new Date(2026, 9, 8);
      if (task.lastStatusUpdate) {
        const lastUp = parseDate(task.lastStatusUpdate);
        if (lastUp && lastUp > taskEffectiveToday) taskEffectiveToday = lastUp;
      }
      let tActualEnd = parseDate(task.actualEndDate);
      if (!tActualEnd && (isInProgress || isPaused)) {
        tActualEnd = taskEffectiveToday;
        if (tStart && tActualEnd < tStart) tActualEnd = tStart;
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
          <td rowspan="2" style="text-align: center; font-weight: bold;" class="info-cell">${formatPlanDuration(task)}</td>
          <td rowspan="2" style="text-align: center;" class="info-cell">${formatVnDate(task.actualEndDate) || (isPaused ? 'Tạm dừng' : 'Chưa xong')}</td>
          <td rowspan="2" style="text-align: center; font-weight: bold;" class="info-cell">${task.status}</td>
          <td rowspan="2" style="text-align: center; font-weight: bold; color: ${mainProgress && mainProgress.isAllCompleted ? '#15803d' : '#0369a1'};" class="info-cell">${mainStatusText}</td>
          <td rowspan="2" style="text-align: center; font-size: 10px;" class="info-cell">${task.link ? `<a href="${task.link}">Mở Link</a>` : ''}</td>
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

          // Kiểm tra xem cột này có ghi nhận cập nhật không
          const logForCol = (task.statusLogs || []).filter(l => {
            const ld = parseDate(l.date);
            return ld && col.startDate <= ld && col.endDate >= ld;
          });

          let barColor = '#16a34a';
          let borderColor = '#14532d';
          let symbol = isLast ? '✔' : '—';

          if (isPaused) {
            barColor = '#64748b';
            borderColor = '#334155';
            symbol = isLast ? '⏸' : '—';
          } else if (!task.actualEndDate && isInProgress) {
            barColor = '#0284c7'; // Xanh cyan/blue cho đang làm
            borderColor = '#0369a1';
            symbol = isLast ? '►' : '—';
          } else if (isDelayed) {
            barColor = '#d97706';
            borderColor = '#9a3412';
            symbol = isLast ? '⚠' : '—';
          }

          let noteText = '';
          if (logForCol.length > 0) {
            const lastLog = logForCol[logForCol.length - 1];
            const p = lastLog.progress !== undefined ? `${lastLog.progress}%` : '';
            symbol = p ? `📝${p}` : '📝';
            noteText = logForCol.map(l => `${l.date}${l.progress !== undefined ? ' ('+l.progress+'%)' : ''}: ${l.note || ''}`).join(' | ');
          }

          const borderStyle = `border-top: 2px solid ${borderColor}; border-bottom: 2px solid ${borderColor}; ${isFirst ? `border-left: 2px solid ${borderColor};` : 'border-left: none;'} ${isLast ? `border-right: 2px solid ${borderColor};` : 'border-right: none;'}`;
          row2 += `<td style="background-color: ${barColor}; ${borderStyle} text-align: center; color: #ffffff; font-weight: bold; font-size: 10px;" title="${noteText.replace(/"/g, '&quot;')}">${symbol}</td>`;
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
  const empBox = document.getElementById('empExportBox');
  const taskBox = document.getElementById('taskExportBox');
  const titleTxt = document.getElementById('templateTitleText');
  const subTxt = document.getElementById('templateSubText');

  if (target === 'TASK') {
    if (tabTask) tabTask.className = 'flex-1 py-1.5 rounded-lg bg-white text-emerald-700 shadow-sm transition flex items-center justify-center gap-1.5';
    if (tabEmp) tabEmp.className = 'flex-1 py-1.5 rounded-lg text-slate-600 hover:text-slate-900 transition flex items-center justify-center gap-1.5';
    if (modalTitle) modalTitle.innerText = 'Nhập Công Việc Vào Hệ Thống (Chỉ Chèn Việc Chưa Có)';
    if (modalIcon) modalIcon.className = 'fa-solid fa-list-check text-lg text-emerald-300';
    if (ruleDesc) ruleDesc.innerHTML = 'Hệ thống sẽ đối soát ID và nội dung: <b>Chỉ chèn các công việc chưa có</b>. Toàn bộ công việc đã có sẽ được giữ nguyên 100%, không bị trùng lặp!';
    if (empBox) empBox.classList.add('hidden');
    if (taskBox) taskBox.classList.remove('hidden');
    if (titleTxt) titleTxt.innerText = 'Tải file mẫu Excel Công Việc:';
    if (subTxt) subTxt.innerText = 'Mẫu có sẵn định dạng cột chuẩn xác để thêm công việc mới';
  } else {
    if (tabEmp) tabEmp.className = 'flex-1 py-1.5 rounded-lg bg-white text-indigo-700 shadow-sm transition flex items-center justify-center gap-1.5';
    if (tabTask) tabTask.className = 'flex-1 py-1.5 rounded-lg text-slate-600 hover:text-slate-900 transition flex items-center justify-center gap-1.5';
    if (modalTitle) modalTitle.innerText = 'Nhập Nhân Sự Vào Hệ Thống (Chỉ Chèn Nhân Sự Mới)';
    if (modalIcon) modalIcon.className = 'fa-solid fa-users text-lg text-indigo-300';
    if (ruleDesc) ruleDesc.innerHTML = 'Hệ thống sẽ đối soát Mã nhân viên và Họ tên: <b>Chỉ thêm nhân sự mới</b>. Nhân sự đã có sẽ được giữ nguyên!';
    if (empBox) empBox.classList.remove('hidden');
    if (taskBox) taskBox.classList.add('hidden');
    if (titleTxt) titleTxt.innerText = 'Tải file mẫu Excel Nhân Sự:';
    if (subTxt) subTxt.innerText = 'Mẫu có sẵn định dạng cột chuẩn xác để thêm nhân sự mới';
  }
}

function downloadSmartImportTemplate() {
  if (currentImportTarget === 'TASK') {
    downloadExcelTemplate();
  } else {
    downloadEmployeeTemplate();
  }
}

function downloadEmployeeTemplate() {
  const templateData = [
    ['Mã Nhân Viên', 'Họ Và Tên', 'Phòng Ban / Bộ Phận', 'Email', 'Điện Thoại'],
    ['NV06', 'Vũ Đình Trọng', 'Kỹ thuật - Bảo trì', 'trong.vd@mbc.vn', '0901234567'],
    ['NV07', 'Ngô Thu Trang', 'Kiểm tra chất lượng (QC)', 'trang.nt@mbc.vn', '0912345678'],
    ['NV08', 'Đỗ Mạnh Hùng', 'Kế hoạch sản xuất', 'hung.dm@mbc.vn', '0923456789']
  ];
  const ws = XLSX.utils.aoa_to_sheet(templateData);
  ws['!cols'] = [{ wch: 16 }, { wch: 25 }, { wch: 28 }, { wch: 28 }, { wch: 16 }];
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, 'MauImportNhanSu');
  XLSX.writeFile(wb, 'MBC_Mau_Import_NhanSu.xlsx');
}

function exportCurrentEmployeesToExcel() {
  if (!appData.employees || appData.employees.length === 0) {
    showToast('⚠️ Chưa có nhân sự nào trong hệ thống!', 'warning');
    return;
  }
  const header = ['Mã Nhân Viên', 'Họ Và Tên', 'Phòng Ban / Bộ Phận', 'Email', 'Điện Thoại'];
  const rows = appData.employees.map(emp => [
    emp.id || '',
    emp.name || '',
    emp.dept || emp.position || '',
    emp.email || '',
    emp.phone || ''
  ]);
  const ws = XLSX.utils.aoa_to_sheet([header, ...rows]);
  ws['!cols'] = [{ wch: 16 }, { wch: 28 }, { wch: 28 }, { wch: 30 }, { wch: 16 }];
  // Highlight header row
  const range = XLSX.utils.decode_range(ws['!ref']);
  for (let C = range.s.c; C <= range.e.c; C++) {
    const cellAddr = XLSX.utils.encode_cell({ r: 0, c: C });
    if (!ws[cellAddr]) continue;
    ws[cellAddr].s = { fill: { fgColor: { rgb: '0C4A6E' } }, font: { color: { rgb: 'FFFFFF' }, bold: true } };
  }
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, 'DanhSachNhanSu');
  const today = new Date();
  const fname = `MBC_DanhSach_NhanSu_${today.getFullYear()}${String(today.getMonth()+1).padStart(2,'0')}${String(today.getDate()).padStart(2,'0')}.xlsx`;
  XLSX.writeFile(wb, fname);
  showToast(`✅ Đã xuất ${rows.length} nhân sự ra ${fname}!`, 'success');
}

function exportCurrentTasksToExcel() {
  if (!appData.tasks || appData.tasks.length === 0) {
    showToast('⚠️ Chưa có công việc nào trong hệ thống!', 'warning');
    return;
  }
  const header = [
    'Mã CV',
    'Mã CV Chính',
    'Công việc chính',
    'Nội dung chi tiết',
    'Người thực hiện',
    'Mã NV',
    'Ngày bắt đầu (YYYY-MM-DD)',
    'Thời gian dự kiến (ngày)',
    'Thời gian hoàn thành (YYYY-MM-DD)',
    'Tình trạng',
    'Link / Tệp',
    'Ghi chú'
  ];
  const rows = appData.tasks.map(t => [
    t.id || '',
    t.mainTaskId || '',
    t.mainTaskTitle || t.title || '',
    t.detail || '',
    t.empName || '',
    t.empId || '',
    t.startDate || '',
    t.planDuration || t.planDays || 1,
    t.actualEndDate || '',
    t.status || 'Đang làm',
    t.link || '',
    t.note || ''
  ]);
  const ws = XLSX.utils.aoa_to_sheet([header, ...rows]);
  ws['!cols'] = [
    { wch: 16 },
    { wch: 16 },
    { wch: 28 },
    { wch: 32 },
    { wch: 22 },
    { wch: 12 },
    { wch: 26 },
    { wch: 24 },
    { wch: 28 },
    { wch: 18 },
    { wch: 32 },
    { wch: 25 }
  ];
  const range = XLSX.utils.decode_range(ws['!ref']);
  for (let C = range.s.c; C <= range.e.c; C++) {
    const cellAddr = XLSX.utils.encode_cell({ r: 0, c: C });
    if (!ws[cellAddr]) continue;
    ws[cellAddr].s = { fill: { fgColor: { rgb: '047857' } }, font: { color: { rgb: 'FFFFFF' }, bold: true } };
  }
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, 'DanhSachCongViec');
  const today = new Date();
  const fname = `MBC_DanhSach_CongViec_${today.getFullYear()}${String(today.getMonth()+1).padStart(2,'0')}${String(today.getDate()).padStart(2,'0')}.xlsx`;
  XLSX.writeFile(wb, fname);
  showToast(`✅ Đã xuất ${rows.length} công việc ra ${fname}!`, 'success');
}

function downloadExcelTemplate() {
  const templateData = [
    ['Mã CV Chính', 'Công việc chính', 'Nội dung chi tiết', 'Người thực hiện', 'Mã NV', 'Ngày bắt đầu (YYYY-MM-DD)', 'Thời gian dự kiến (ngày)', 'Thời gian hoàn thành (YYYY-MM-DD)', 'Tình trạng', 'Link / Tệp', 'Ghi chú'],
    ['CV-TUM', 'Sửa chữa máy TUM', 'Xác nhận tình trạng linh kiện', 'Nguyễn Quang Thảo', 'NV01', '2026-10-01', 1, '2026-10-01', 'Hoàn thành', 'https://drive.google.com/mbc', 'Nghiệm thu tốt'],
    ['CV-MAY-EP', 'Bảo dưỡng định kỳ máy ép', 'Kiểm tra đường ống dầu thủy lực', 'Trần Văn Bình', 'NV02', '2026-10-03', 3, '2026-10-05', 'Hoàn thành', 'C:\\MBC\\BaoDuongMayEp', 'Đúng hạn'],
    ['CV-KIEM-DINH', 'Kiểm định thiết bị đo', 'Hiệu chuẩn thước kẹp điện tử', 'Lê Thị Thu', 'NV03', '2026-10-05', 2, '', 'Đang làm', '', 'Đang thực hiện']
  ];

  const ws = XLSX.utils.aoa_to_sheet(templateData);
  ws['!cols'] = [{ wch: 14 }, { wch: 25 }, { wch: 30 }, { wch: 20 }, { wch: 10 }, { wch: 25 }, { wch: 22 }, { wch: 28 }, { wch: 16 }, { wch: 28 }, { wch: 25 }];
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
      const colTaskId = header.findIndex(h => h === 'mã cv' || h === 'ma cv' || h.includes('mã công việc'));
      const colMainId = header.findIndex(h => h.includes('mã cv chính') || h.includes('ma cv chinh') || (h.includes('mã cv') && h !== 'mã cv' && h !== 'ma cv'));
      const colMainTitle = header.findIndex(h => h.includes('công việc chính') || h.includes('cong viec chinh') || h.includes('công việc'));
      const colDetail = header.findIndex(h => h.includes('chi tiết') || h.includes('nội dung'));
      const colEmp = header.findIndex(h => h.includes('người') || h.includes('thực hiện'));
      const colEmpId = header.findIndex(h => h.includes('mã nv'));
      const colStart = header.findIndex(h => h.includes('bắt đầu'));
      const colDays = header.findIndex(h => (h.includes('dự kiến') && h.includes('thời gian')) || h.includes('ngày'));
      const colActual = header.findIndex(h => h.includes('hoàn thành'));
      const colStatus = header.findIndex(h => h.includes('tình trạng'));
      const colLink = header.findIndex(h => h.includes('link') || h.includes('tệp') || h.includes('tài liệu'));
      const colNote = header.findIndex(h => h.includes('ghi chú'));

      rows.forEach((row, rIdx) => {
        if (!row || row.length === 0) return;
        const title = colMainTitle >= 0 ? String(row[colMainTitle] || '').trim() : '';
        if (!title) return;
        const taskId = (colTaskId >= 0 && row[colTaskId]) ? String(row[colTaskId]).trim() : `TASK-IMP-${Date.now().toString().slice(-4)}${rIdx + 1}`;
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
        const link = colLink >= 0 ? String(row[colLink] || '').trim() : '';
        const note = colNote >= 0 ? String(row[colNote] || '').trim() : '';

        rawTasks.push({
          id: taskId,
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
          link,
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

// ================= XUẤT DỮ LIỆU RA EXCEL (BẢNG PHẲNG) =================
/**
 * Xuất toàn bộ danh sách công việc ra file Excel bảng phẳng (không Gantt).
 * Bao gồm đầy đủ các trường thông tin để thuận tiện phân tích / lưu trữ.
 */
function exportTasksDataToExcel() {
  const today = new Date();
  const todayStr = `${today.getDate().toString().padStart(2,'0')}/${(today.getMonth()+1).toString().padStart(2,'0')}/${today.getFullYear()}`;

  // Header
  const headers = [
    'STT', 'Mã CV', 'Mã Dự Án', 'Tên Công Việc', 'Nội Dung Chi Tiết',
    'Nhân Viên', 'Mã NV', 'Nguồn Yêu Cầu',
    'Ngày Bắt Đầu', 'Dự Kiến', 'Ngày HT Kế Hoạch',
    'Ngày HT Thực Tế', 'Trạng Thái', 'Điểm KPI',
    'Cập Nhật Cuối', 'Lịch Sử Cập Nhật & Tiến Độ', 'Link / Tài Liệu', 'Ghi Chú'
  ];

  const statusMap = { 'Hoàn thành': '✔ Hoàn thành', 'Hoàn thành trễ': '⚠ Hoàn thành trễ', 'Đang làm': '▶ Đang làm', 'Tạm dừng': '⏸ Tạm dừng', 'Dừng dự án': '⏹ Dừng dự án' };

  const rows = appData.tasks.map((t, i) => [
    i + 1,
    t.id || '',
    t.mainTaskId || '',
    t.mainTaskTitle || t.title || '',
    t.detail || t.title || '',
    t.empName || '',
    t.empId || '',
    t.taskSource || '',
    formatVnDate(t.startDate) || '',
    formatPlanDuration(t) || '',
    formatVnDate(t.planEndDate) || '',
    formatVnDate(t.actualEndDate) || '',
    statusMap[t.status] || t.status || '',
    t.kpiPoints !== undefined ? t.kpiPoints : '',
    formatVnDate(t.lastStatusUpdate || t.startDate) || '',
    (t.statusLogs || []).map(l => `[${formatVnDate(l.date)}${l.progress !== undefined ? ' - ' + l.progress + '%' : ''}]: ${l.note || ''}`).join(' ; ') || '',
    t.link || '',
    t.note || ''
  ]);

  // Xây dựng HTML table để xuất
  const title = `DANH SÁCH CÔNG VIỆC - MBC GROUP (Xuất: ${todayStr})`;
  let html = `<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">`;
  html += `<head><meta charset="UTF-8"><style>`;
  html += `body{font-family:Arial,sans-serif;font-size:10pt;}`;
  html += `table{border-collapse:collapse;width:100%;}`;
  html += `td,th{border:1px solid #94a3b8;padding:4px 6px;vertical-align:middle;}`;
  html += `.title-row td{background:#1e3a5f;color:white;font-weight:bold;font-size:13pt;text-align:center;border:none;padding:10px;}`;
  html += `.date-row td{background:#f1f5f9;color:#475569;font-size:9pt;text-align:right;border:none;padding:3px 6px;}`;
  html += `.header-row th{background:#334155;color:white;font-weight:bold;text-align:center;font-size:9pt;}`;
  html += `.data-row td{font-size:9pt;}`;
  html += `.data-row:nth-child(even) td{background:#f8fafc;}`;
  html += `.status-done{color:#16a34a;font-weight:bold;}`;
  html += `.status-late{color:#d97706;font-weight:bold;}`;
  html += `.status-overdue{color:#dc2626;font-weight:bold;}`;
  html += `.status-paused{color:#78716c;}`;
  html += `</style></head><body>`;
  html += `<table>`;
  html += `<tr class="title-row"><td colspan="${headers.length}">${title}</td></tr>`;
  html += `<tr class="date-row"><td colspan="${headers.length}">Tổng số: ${rows.length} công việc &nbsp;|&nbsp; Xuất lúc: ${todayStr}</td></tr>`;
  html += `<tr class="header-row">${headers.map(h => `<th>${h}</th>`).join('')}</tr>`;
  rows.forEach(r => {
    const statusVal = String(r[12] || '');
    let statusClass = '';
    if (statusVal.includes('Hoàn thành trễ')) statusClass = 'status-late';
    else if (statusVal.includes('Hoàn thành')) statusClass = 'status-done';
    else if (statusVal.includes('Tạm dừng') || statusVal.includes('Dừng')) statusClass = 'status-paused';
    html += `<tr class="data-row">${r.map((cell, ci) => `<td${ci === 12 && statusClass ? ` class="${statusClass}"` : ''}>${String(cell).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}</td>`).join('')}</tr>`;
  });
  html += `</table></body></html>`;

  const blob = new Blob([html], { type: 'application/vnd.ms-excel;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `DanhSach_CongViec_MBC_${today.getFullYear()}${String(today.getMonth()+1).padStart(2,'0')}${String(today.getDate()).padStart(2,'0')}.xls`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  showToast('✅ Đã xuất danh sách công việc ra Excel thành công!', 'success');
}

/**
 * Xuất toàn bộ danh sách nhân sự ra file Excel bảng phẳng.
 */
function exportEmployeesDataToExcel() {
  const today = new Date();
  const todayStr = `${today.getDate().toString().padStart(2,'0')}/${(today.getMonth()+1).toString().padStart(2,'0')}/${today.getFullYear()}`;

  const headers = [
    'STT', 'Mã NV', 'Họ & Tên', 'Phòng Ban / Vị Trí', 'Email',
    'Điện Thoại', 'Tổng Công Việc', 'Đã Hoàn Thành', 'Đang Làm', 'Tỷ Lệ HT (%)', 'Tổng Điểm KPI'
  ];

  const rows = appData.employees.map((emp, i) => {
    const empTasks = appData.tasks.filter(t => t.empId === emp.id);
    const doneCount = empTasks.filter(t => t.status && t.status.includes('Hoàn thành')).length;
    const doingCount = empTasks.filter(t => t.status && !t.status.includes('Hoàn thành') && t.status !== 'Tạm dừng' && t.status !== 'Dừng dự án').length;
    const total = empTasks.length;
    const rate = total > 0 ? Math.round(doneCount / total * 100) : 0;
    const kpiTotal = empTasks.reduce((sum, t) => sum + (t.kpiPoints || 0), 0);
    return [
      i + 1,
      emp.id || '',
      emp.name || '',
      emp.dept || emp.position || '',
      emp.email || '',
      emp.phone || '',
      total,
      doneCount,
      doingCount,
      rate,
      kpiTotal
    ];
  });

  const title = `DANH SÁCH NHÂN SỰ - MBC GROUP (Xuất: ${todayStr})`;
  let html = `<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">`;
  html += `<head><meta charset="UTF-8"><style>`;
  html += `body{font-family:Arial,sans-serif;font-size:10pt;}`;
  html += `table{border-collapse:collapse;width:100%;}`;
  html += `td,th{border:1px solid #94a3b8;padding:4px 6px;vertical-align:middle;}`;
  html += `.title-row td{background:#164e63;color:white;font-weight:bold;font-size:13pt;text-align:center;border:none;padding:10px;}`;
  html += `.date-row td{background:#f0f9ff;color:#0369a1;font-size:9pt;text-align:right;border:none;padding:3px 6px;}`;
  html += `.header-row th{background:#0c4a6e;color:white;font-weight:bold;text-align:center;font-size:9pt;}`;
  html += `.data-row td{font-size:9pt;}`;
  html += `.data-row:nth-child(even) td{background:#f0f9ff;}`;
  html += `.num{text-align:center;}`;
  html += `.rate-good{color:#16a34a;font-weight:bold;text-align:center;}`;
  html += `.rate-mid{color:#d97706;font-weight:bold;text-align:center;}`;
  html += `.rate-low{color:#dc2626;font-weight:bold;text-align:center;}`;
  html += `</style></head><body>`;
  html += `<table>`;
  html += `<tr class="title-row"><td colspan="${headers.length}">${title}</td></tr>`;
  html += `<tr class="date-row"><td colspan="${headers.length}">Tổng nhân sự: ${rows.length} &nbsp;|&nbsp; Xuất lúc: ${todayStr}</td></tr>`;
  html += `<tr class="header-row">${headers.map(h => `<th>${h}</th>`).join('')}</tr>`;
  rows.forEach(r => {
    const rate = r[9];
    const rateClass = rate >= 80 ? 'rate-good' : rate >= 50 ? 'rate-mid' : 'rate-low';
    html += `<tr class="data-row">${r.map((cell, ci) => {
      let cls = '';
      if (ci >= 6 && ci <= 8) cls = 'num';
      if (ci === 9) cls = rateClass;
      if (ci === 10) cls = 'num';
      return `<td${cls ? ` class="${cls}"` : ''}>${String(cell).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}</td>`;
    }).join('')}</tr>`;
  });
  html += `</table></body></html>`;

  const blob = new Blob([html], { type: 'application/vnd.ms-excel;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `DanhSach_NhanSu_MBC_${today.getFullYear()}${String(today.getMonth()+1).padStart(2,'0')}${String(today.getDate()).padStart(2,'0')}.xls`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  showToast('✅ Đã xuất danh sách nhân sự ra Excel thành công!', 'success');
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

// ================= NHẬT KÝ CẬP NHẬT TÌNH TRẠNG (STATUS LOG MODAL) =================
function openStatusLogModal(taskId) {
  const task = appData.tasks.find(t => t.id === taskId);
  if (!task) return;
  document.getElementById('statusLogTaskId').value = task.id;
  document.getElementById('statusLogTaskName').innerText = `[${task.id}] ${task.mainTaskTitle || task.title} - ${task.empName}`;
  document.getElementById('statusLogStatus').value = task.status || 'Đang làm';
  document.getElementById('statusLogContent').value = '';
  document.getElementById('statusLogProgress').value = '';

  const now = new Date();
  const todayStr = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')}`;
  const dateInputEl = document.getElementById('statusLogDate');
  if (dateInputEl) dateInputEl.value = todayStr;

  const historyEl = document.getElementById('statusLogHistory');
  const logs = task.statusLogs || [];

  // Vẽ mini SVG progress chart nếu có dữ liệu
  const miniChartEl = document.getElementById('statusLogMiniChart');
  if (miniChartEl) {
    const logsWithProg = logs.filter(l => l.progress !== undefined && l.progress !== '');
    if (logsWithProg.length >= 2) {
      const W = 320, H = 80, PAD = 20;
      const maxX = logsWithProg.length - 1;
      const pts = logsWithProg.map((l, i) => {
        const x = PAD + (i / maxX) * (W - PAD * 2);
        const y = H - PAD - ((l.progress || 0) / 100) * (H - PAD * 2);
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      }).join(' ');
      const circles = logsWithProg.map((l, i) => {
        const x = PAD + (i / maxX) * (W - PAD * 2);
        const y = H - PAD - ((l.progress || 0) / 100) * (H - PAD * 2);
        return `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="3" fill="#7c3aed" title="${formatVnDate(l.date)}: ${l.progress}%"/>`;
      }).join('');
      const labels = logsWithProg.map((l, i) => {
        const x = PAD + (i / maxX) * (W - PAD * 2);
        const y = H - PAD - ((l.progress || 0) / 100) * (H - PAD * 2);
        return `<text x="${x.toFixed(1)}" y="${(y - 5).toFixed(1)}" text-anchor="middle" font-size="8" fill="#6d28d9">${l.progress}%</text>`;
      }).join('');
      miniChartEl.innerHTML = `
        <div class="text-[10px] font-semibold text-violet-700 mb-1"><i class="fa-solid fa-chart-line mr-1"></i>Biểu đồ tiến độ theo các lần cập nhật:</div>
        <svg width="${W}" height="${H}" class="w-full" viewBox="0 0 ${W} ${H}" style="background:#f5f3ff;border-radius:8px;">
          <line x1="${PAD}" y1="${H-PAD}" x2="${W-PAD}" y2="${H-PAD}" stroke="#ddd6fe" stroke-width="1"/>
          <line x1="${PAD}" y1="${PAD}" x2="${PAD}" y2="${H-PAD}" stroke="#ddd6fe" stroke-width="1"/>
          <text x="${PAD-2}" y="${PAD+3}" text-anchor="end" font-size="7" fill="#9ca3af">100%</text>
          <text x="${PAD-2}" y="${H-PAD+3}" text-anchor="end" font-size="7" fill="#9ca3af">0%</text>
          <polyline points="${pts}" fill="none" stroke="#7c3aed" stroke-width="1.5" stroke-linejoin="round"/>
          ${circles}${labels}
        </svg>
      `;
      miniChartEl.classList.remove('hidden');
    } else {
      miniChartEl.innerHTML = '';
      miniChartEl.classList.add('hidden');
    }
  }

  if (logs.length === 0) {
    historyEl.innerHTML = '<div class="text-slate-400 text-center py-3 text-xs">Chưa có lịch sử cập nhật nào</div>';
  } else {
    historyEl.innerHTML = '';
    logs.slice().reverse().forEach(log => {
      const div = document.createElement('div');
      div.className = 'p-2 rounded-lg bg-white border border-slate-200 text-xs space-y-0.5 shadow-xs';
      const progressBadge = (log.progress !== undefined && log.progress !== '') ? `<span class="ml-1 px-1.5 py-0.5 rounded text-[9px] font-bold bg-amber-50 text-amber-700 border border-amber-200">${log.progress}%</span>` : '';
      div.innerHTML = `
        <div class="flex items-center justify-between font-bold text-slate-700">
          <span class="text-violet-700"><i class="fa-regular fa-clock mr-1"></i>${formatVnDate(log.date) || log.date} ${progressBadge}</span>
          <span class="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-violet-50 text-violet-700 border border-violet-200">${log.status || ''}</span>
        </div>
        <div class="text-slate-600 text-[11px]">${log.note ? log.note : '<em class="text-slate-400">Không ghi chú nội dung</em>'}</div>
        <div class="text-[9px] text-slate-400 text-right">Người cập nhật: ${log.author || 'Thành viên'}</div>
      `;
      historyEl.appendChild(div);
    });
  }

  document.getElementById('statusLogModal').classList.remove('hidden');
}

function closeStatusLogModal() {
  document.getElementById('statusLogModal').classList.add('hidden');
}

function saveStatusLog() {
  const taskId = document.getElementById('statusLogTaskId').value;
  const task = appData.tasks.find(t => t.id === taskId);
  if (!task) return;

  const note = document.getElementById('statusLogContent').value.trim();
  const status = document.getElementById('statusLogStatus').value;
  const progressRaw = document.getElementById('statusLogProgress') ? document.getElementById('statusLogProgress').value.trim() : '';
  const progress = progressRaw !== '' ? Math.min(100, Math.max(0, parseInt(progressRaw) || 0)) : undefined;

  // Dùng ngày người dùng chọn hoặc mặc định ngày thực tế hệ thống
  const now = new Date();
  const todayDefault = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')}`;
  const dateInputEl = document.getElementById('statusLogDate');
  const chosenDate = (dateInputEl && dateInputEl.value) ? dateInputEl.value : todayDefault;

  if (!task.statusLogs) task.statusLogs = [];
  const logEntry = {
    date: chosenDate,
    note: note,
    status: status,
    author: (appData.currentUser && appData.currentUser.name) ? appData.currentUser.name : 'Người dùng'
  };
  if (progress !== undefined) logEntry.progress = progress;
  task.statusLogs.push(logEntry);

  task.status = status;
  task.lastStatusUpdate = chosenDate;
  if (status.includes('Hoàn thành') && !task.actualEndDate) {
    task.actualEndDate = chosenDate;
  } else if (!status.includes('Hoàn thành') && task.actualEndDate) {
    task.actualEndDate = '';
  }

  saveDataToStorage();
  closeStatusLogModal();
  applyFilters();
  showToast('✅ Đã ghi nhận cập nhật tình trạng!', 'success');
}

// ================= MODAL GẮN LINK / TỆP CHO CÔNG VIỆC =================
function openEditTaskLinkModal(taskId) {
  const task = appData.tasks.find(t => t.id === taskId);
  if (!task) return;
  document.getElementById('taskLinkModalTaskId').value = task.id;
  const subTitle = document.getElementById('taskLinkModalSubTitle');
  if (subTitle) subTitle.innerText = `[${task.id}] ${task.mainTaskTitle || task.title} - ${task.empName}`;
  const input = document.getElementById('taskLinkModalInput');
  if (input) {
    input.value = task.link || '';
    setTimeout(() => input.focus(), 100);
  }
  document.getElementById('taskLinkModal').classList.remove('hidden');
}

function closeTaskLinkModal() {
  document.getElementById('taskLinkModal').classList.add('hidden');
}

function saveTaskLinkFromModal() {
  const taskId = document.getElementById('taskLinkModalTaskId').value;
  const task = appData.tasks.find(t => t.id === taskId);
  if (!task) return;
  const linkVal = document.getElementById('taskLinkModalInput').value.trim();
  task.link = linkVal;
  saveDataToStorage();
  closeTaskLinkModal();
  applyFilters();
  showToast(linkVal ? '✅ Đã cập nhật đường dẫn liên kết cho công việc!' : 'ℹ️ Đã xóa liên kết công việc!', 'success');
}

// ================= LỊCH NGHỈ ĐẶC BIỆT & NGÀY LỄ (HOLIDAY MODAL) =================
function openHolidayModal() {
  renderHolidayList();
  document.getElementById('holidayModal').classList.remove('hidden');
}

function closeHolidayModal() {
  document.getElementById('holidayModal').classList.add('hidden');
  applyFilters();
}

function renderHolidayList() {
  const listEl = document.getElementById('holidayList');
  const countBadge = document.getElementById('holidayCountBadge');
  const holidays = appData.holidays || [];
  if (countBadge) countBadge.innerText = `(${holidays.length} ngày)`;

  if (holidays.length === 0) {
    listEl.innerHTML = '<div class="text-xs text-slate-400 text-center py-4">Chưa có ngày nghỉ nào được cài đặt</div>';
    return;
  }

  holidays.sort((a, b) => (a.date || '').localeCompare(b.date || ''));

  listEl.innerHTML = '';
  holidays.forEach(h => {
    const isNational = h.type === 'NATIONAL';
    const div = document.createElement('div');
    div.className = `flex items-center justify-between p-2.5 rounded-xl border text-xs ${isNational ? 'bg-red-50/70 border-red-200' : 'bg-purple-50/70 border-purple-200'} shadow-xs`;
    div.innerHTML = `
      <div class="flex items-center gap-2">
        <span class="w-3 h-3 rounded-full ${isNational ? 'bg-red-500' : 'bg-purple-500'} shrink-0"></span>
        <div>
          <span class="font-bold text-slate-800">${formatVnDate(h.date)}</span>
          <span class="text-slate-600 ml-2 font-medium">${h.name}</span>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <span class="text-[10px] font-semibold px-2 py-0.5 rounded ${isNational ? 'bg-red-100 text-red-800 border border-red-300' : 'bg-purple-100 text-purple-800 border border-purple-300'}">
          ${isNational ? 'Lễ quốc gia' : 'Nghỉ đặc biệt'}
        </span>
        <button onclick="deleteHoliday('${h.date}')" class="text-slate-400 hover:text-rose-600 px-1 py-0.5 transition" title="Xóa ngày nghỉ">
          <i class="fa-solid fa-trash-can text-[11px]"></i>
        </button>
      </div>
    `;
    listEl.appendChild(div);
  });
}

function addHoliday() {
  const date = document.getElementById('holidayDate').value;
  const type = document.getElementById('holidayType').value;
  const name = document.getElementById('holidayName').value.trim();

  if (!date) {
    alert('Vui lòng chọn ngày nghỉ!');
    return;
  }
  if (!name) {
    alert('Vui lòng nhập tên / lý do ngày nghỉ!');
    return;
  }

  if (!appData.holidays) appData.holidays = [];
  const existing = appData.holidays.find(h => h.date === date);
  if (existing) {
    existing.name = name;
    existing.type = type;
  } else {
    appData.holidays.push({ date, name, type });
  }

  saveDataToStorage();
  document.getElementById('holidayName').value = '';
  document.getElementById('holidayDate').value = '';
  renderHolidayList();
}

function deleteHoliday(date) {
  if (!confirm(`Bạn có chắc muốn xóa ngày nghỉ ${formatVnDate(date)}?`)) return;
  appData.holidays = (appData.holidays || []).filter(h => h.date !== date);
  saveDataToStorage();
  renderHolidayList();
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
  renderFilterMainTasksSelect();
  applyFilters();

  document.addEventListener('click', (e) => {
    const userDropdown = document.getElementById('userDropdown');
    if (userDropdown && !userDropdown.contains(e.target) && !e.target.closest('button[onclick="toggleUserDropdown()"]')) {
      userDropdown.classList.add('hidden');
    }
  });
});

// ================= QUICK LINKS (LIÊN KẾT NHANH) =================
const QUICK_LINKS_KEY = 'MBC_QUICK_LINKS';

function loadQuickLinks() {
  try {
    const raw = localStorage.getItem(QUICK_LINKS_KEY);
    return raw ? JSON.parse(raw) : [
      { id: 'ql1', name: '📁 Thư mục dự án', url: 'file:///C:/Users/12953 Bao/Desktop/desktop/work/Project/Python/BasicLearnPython/W3schools/Python Tutorial/GravityCode/MBC/QuanLyCongViecNhom/', desc: 'Thư mục chứa ứng dụng' },
      { id: 'ql2', name: '📋 Hướng dẫn sử dụng', url: 'HuongDanSuDung.md', desc: 'File hướng dẫn' }
    ];
  } catch { return []; }
}

function saveQuickLinks(links) {
  localStorage.setItem(QUICK_LINKS_KEY, JSON.stringify(links));
}

function openQuickLinksModal() {
  renderQuickLinksModal();
  document.getElementById('quickLinksModal').classList.remove('hidden');
}

function closeQuickLinksModal() {
  document.getElementById('quickLinksModal').classList.add('hidden');
}

function renderQuickLinksModal() {
  const links = loadQuickLinks();
  const listEl = document.getElementById('quickLinksList');
  if (!listEl) return;

  if (links.length === 0) {
    listEl.innerHTML = '<div class="text-slate-400 text-center py-4 text-xs">Chưa có liên kết nào. Thêm bên dưới!</div>';
    return;
  }

  listEl.innerHTML = '';
  links.forEach(link => {
    const div = document.createElement('div');
    div.className = 'flex items-center gap-2 p-2.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 group transition';
    div.innerHTML = `
      <button onclick="openQuickLink('${encodeURIComponent(link.url)}')" class="flex-1 text-left min-w-0" title="${link.url}">
        <div class="font-semibold text-sm text-sky-700 truncate">${link.name}</div>
        <div class="text-[10px] text-slate-400 truncate">${link.url}</div>
        ${link.desc ? `<div class="text-[10px] text-slate-500 italic">${link.desc}</div>` : ''}
      </button>
      <button onclick="openQuickLink('${encodeURIComponent(link.url)}')" class="px-2.5 py-1.5 text-xs font-semibold rounded-lg bg-sky-100 text-sky-700 hover:bg-sky-200 transition flex items-center gap-1 shrink-0">
        <i class="fa-solid fa-external-link-alt text-[10px]"></i> Mở
      </button>
      <button onclick="deleteQuickLink('${link.id}')" class="opacity-0 group-hover:opacity-100 transition text-rose-400 hover:text-rose-600 text-xs px-1.5" title="Xóa liên kết này">
        <i class="fa-solid fa-trash"></i>
      </button>
    `;
    listEl.appendChild(div);
  });
}

function openQuickLink(encodedUrl) {
  const url = decodeURIComponent(encodedUrl).trim();
  if (!url) return;
  // Xử lý đường dẫn file:/// và UNC (\\server\share)
  let finalUrl = url;
  if (url.startsWith('\\\\') || (url.length > 2 && url[1] === ':' && (url[2] === '\\' || url[2] === '/'))) {
    // Windows absolute path → convert to file:///
    finalUrl = 'file:///' + url.replace(/\\/g, '/');
  }
  window.open(finalUrl, '_blank');
}

function addQuickLink() {
  const nameEl = document.getElementById('qlNewName');
  const urlEl = document.getElementById('qlNewUrl');
  const descEl = document.getElementById('qlNewDesc');
  const name = nameEl ? nameEl.value.trim() : '';
  const url = urlEl ? urlEl.value.trim() : '';
  const desc = descEl ? descEl.value.trim() : '';

  if (!name) { showToast('⚠️ Vui lòng nhập tên liên kết!', 'warning'); return; }
  if (!url)  { showToast('⚠️ Vui lòng nhập đường dẫn!', 'warning'); return; }

  const links = loadQuickLinks();
  links.push({ id: 'ql' + Date.now(), name, url, desc });
  saveQuickLinks(links);
  if (nameEl) nameEl.value = '';
  if (urlEl) urlEl.value = '';
  if (descEl) descEl.value = '';
  renderQuickLinksModal();
  showToast('✅ Đã thêm liên kết: ' + name, 'success');
}

function deleteQuickLink(id) {
  const links = loadQuickLinks().filter(l => l.id !== id);
  saveQuickLinks(links);
  renderQuickLinksModal();
  showToast('🗑️ Đã xóa liên kết', 'success');
}

// ================= XÓA NHANH NHÂN VIÊN (BULK DELETE EMPLOYEE) =================
function _onEmpCheckboxChange() {
  _updateEmpBulkDeleteBtn();
  // Cập nhật trạng thái checkbox "Chọn tất cả"
  const all = Array.from(document.querySelectorAll('.emp-cb'));
  const checked = all.filter(cb => cb.checked);
  const selectAllCb = document.getElementById('empSelectAll');
  if (selectAllCb) {
    selectAllCb.checked = all.length > 0 && checked.length === all.length;
    selectAllCb.indeterminate = checked.length > 0 && checked.length < all.length;
  }
}

function _updateEmpBulkDeleteBtn() {
  const checked = Array.from(document.querySelectorAll('.emp-cb:checked'));
  const btn = document.getElementById('btnBulkDeleteEmp');
  const countEl = document.getElementById('empSelectedCount');
  if (btn) {
    if (checked.length > 0) {
      btn.classList.remove('hidden');
    } else {
      btn.classList.add('hidden');
    }
  }
  if (countEl) countEl.innerText = checked.length;
}

function toggleSelectAllEmployees(checked) {
  document.querySelectorAll('.emp-cb').forEach(cb => { cb.checked = checked; });
  _updateEmpBulkDeleteBtn();
}

function bulkDeleteEmployees() {
  const checked = Array.from(document.querySelectorAll('.emp-cb:checked'));
  if (checked.length === 0) return;
  const ids = checked.map(cb => cb.dataset.id);
  const names = ids.map(id => {
    const emp = appData.employees.find(e => e.id === id);
    return emp ? `${emp.name} (${id})` : id;
  });
  if (!confirm(`Bạn có chắc muốn xóa ${ids.length} nhân viên sau đây?\n\n${names.join('\n')}\n\n⚠️ Lưu ý: Các công việc của nhân viên này sẽ KHÔNG bị xóa theo.`)) return;
  appData.employees = appData.employees.filter(e => !ids.includes(e.id));
  saveDataToStorage();
  renderEmployeeTable();
  renderUserDropdown();
  applyFilters();
  showToast(`🗑️ Đã xóa ${ids.length} nhân viên`, 'success');
}

// ================= XÓA NHANH CÔNG VIỆC (BULK DELETE TASK) =================
let _bulkTaskList = []; // Cache danh sách task đang hiện trong modal

function openBulkDeleteTaskModal() {
  document.getElementById('bulkDeleteTaskModal').classList.remove('hidden');
  document.getElementById('bulkTaskSearchInput').value = '';
  document.getElementById('bulkTaskSelectAll').checked = false;
  _bulkTaskList = [...appData.tasks]; // Lấy toàn bộ task
  renderBulkTaskTable(_bulkTaskList);
  updateBulkTaskSelectionUI();
}

function closeBulkDeleteTaskModal() {
  document.getElementById('bulkDeleteTaskModal').classList.add('hidden');
  _bulkTaskList = [];
}

function renderBulkTaskTable(taskList) {
  const tbody = document.getElementById('bulkTaskTableBody');
  const totalEl = document.getElementById('bulkTaskTotalCount');
  if (!tbody) return;
  tbody.innerHTML = '';
  if (totalEl) totalEl.innerText = taskList.length;

  const statusColorMap = {
    'Hoàn thành': 'text-emerald-700 bg-emerald-50',
    'Đang thực hiện': 'text-sky-700 bg-sky-50',
    'Chờ xử lý': 'text-amber-700 bg-amber-50',
    'Tạm dừng': 'text-slate-600 bg-slate-100',
    'Quá hạn': 'text-rose-700 bg-rose-50',
  };

  taskList.forEach(task => {
    const statusClass = statusColorMap[task.status] || 'text-slate-600 bg-slate-50';
    const tr = document.createElement('tr');
    tr.className = 'hover:bg-rose-50/30 transition';
    tr.dataset.taskId = task.id;
    tr.innerHTML = `
      <td class="p-2 text-center">
        <input type="checkbox" class="bulk-task-cb w-3.5 h-3.5 cursor-pointer accent-rose-500" data-id="${task.id}" onchange="updateBulkTaskSelectionUI()">
      </td>
      <td class="p-2 font-semibold text-slate-800 max-w-[220px] truncate" title="${task.name}">${task.name || '(Chưa đặt tên)'}</td>
      <td class="p-2 text-slate-600">${task.empName || task.empId || '-'}</td>
      <td class="p-2 text-center text-slate-500">${task.startDate || '-'}</td>
      <td class="p-2 text-center text-slate-500">${task.planEndDate || '-'}</td>
      <td class="p-2 text-center font-bold text-indigo-600">${task.progress != null ? task.progress + '%' : '-'}</td>
      <td class="p-2 text-center"><span class="px-1.5 py-0.5 rounded text-[10px] font-semibold ${statusClass}">${task.status || '-'}</span></td>
    `;
    tbody.appendChild(tr);
  });

  updateBulkTaskSelectionUI();
}

function filterBulkTaskList() {
  const keyword = (document.getElementById('bulkTaskSearchInput').value || '').toLowerCase().trim();
  if (!keyword) {
    renderBulkTaskTable(appData.tasks);
    _bulkTaskList = [...appData.tasks];
    return;
  }
  const filtered = appData.tasks.filter(t =>
    (t.name || '').toLowerCase().includes(keyword) ||
    (t.empName || '').toLowerCase().includes(keyword) ||
    (t.empId || '').toLowerCase().includes(keyword) ||
    (t.status || '').toLowerCase().includes(keyword)
  );
  _bulkTaskList = filtered;
  renderBulkTaskTable(filtered);
}

function toggleSelectAllBulkTasks(checked) {
  document.querySelectorAll('.bulk-task-cb').forEach(cb => { cb.checked = checked; });
  updateBulkTaskSelectionUI();
}

function updateBulkTaskSelectionUI() {
  const all = Array.from(document.querySelectorAll('.bulk-task-cb'));
  const checked = all.filter(cb => cb.checked);

  const badge = document.getElementById('bulkTaskSelectedBadge');
  const deleteCount = document.getElementById('bulkTaskDeleteCount');
  const selectAllCb = document.getElementById('bulkTaskSelectAll');

  if (badge) badge.innerText = `Đã chọn: ${checked.length}`;
  if (deleteCount) deleteCount.innerText = checked.length;

  if (selectAllCb) {
    selectAllCb.checked = all.length > 0 && checked.length === all.length;
    selectAllCb.indeterminate = checked.length > 0 && checked.length < all.length;
  }
}

function executeBulkDeleteTasks() {
  const checked = Array.from(document.querySelectorAll('.bulk-task-cb:checked'));
  if (checked.length === 0) {
    showToast('⚠️ Chưa chọn công việc nào để xóa!', 'warning');
    return;
  }
  const ids = checked.map(cb => cb.dataset.id);
  if (!confirm(`Bạn có chắc muốn xóa ${ids.length} công việc đã chọn?\n\n⚠️ Hành động này không thể hoàn tác!`)) return;
  appData.tasks = appData.tasks.filter(t => !ids.includes(t.id));
  saveDataToStorage();
  closeBulkDeleteTaskModal();
  applyFilters();
  showToast(`🗑️ Đã xóa ${ids.length} công việc`, 'success');
}

// ================= XÓA NHANH CÔNG VIỆC TRÊN BẢNG GANTT CHÍNH =================
function _onGanttTaskCheckboxChange(input) {
  _updateGanttBulkDeleteUI();
}

function toggleSelectAllGanttTasks(checked) {
  const cbs = document.querySelectorAll('.gantt-task-cb');
  cbs.forEach(cb => { cb.checked = checked; });
  _updateGanttBulkDeleteUI();
}

function _updateGanttBulkDeleteUI() {
  const all = Array.from(document.querySelectorAll('.gantt-task-cb'));
  const checked = all.filter(cb => cb.checked);
  const btn = document.getElementById('ganttBulkDeleteBtn');
  const countEl = document.getElementById('ganttSelectedCount');
  const selectAllCb = document.getElementById('selectAllGanttTasks');

  if (countEl) countEl.innerText = checked.length;
  if (btn) {
    if (checked.length > 0) {
      btn.classList.remove('hidden');
    } else {
      btn.classList.add('hidden');
    }
  }
  if (selectAllCb) {
    selectAllCb.checked = all.length > 0 && checked.length === all.length;
    selectAllCb.indeterminate = checked.length > 0 && checked.length < all.length;
  }
}

function bulkDeleteGanttSelectedTasks() {
  const checked = Array.from(document.querySelectorAll('.gantt-task-cb:checked'));
  if (checked.length === 0) {
    showToast('⚠️ Vui lòng chọn ít nhất 1 công việc để xóa!', 'warning');
    return;
  }
  const ids = checked.map(cb => cb.dataset.id).filter(Boolean);
  const tasksToDelete = appData.tasks.filter(t => ids.includes(t.id));
  const previewNames = tasksToDelete.slice(0, 5).map(t => `• [${t.id}] ${t.title || t.mainTaskTitle || 'Công việc'}`).join('\n');
  const moreText = tasksToDelete.length > 5 ? `\n... và ${tasksToDelete.length - 5} công việc khác` : '';

  if (!confirm(`Bạn có chắc muốn xóa ${ids.length} công việc đã chọn trên bảng Gantt?\n\n${previewNames}${moreText}\n\n⚠️ Hành động này không thể hoàn tác!`)) {
    return;
  }

  appData.tasks = appData.tasks.filter(t => !ids.includes(t.id));
  saveDataToStorage();
  applyFilters();
  _updateGanttBulkDeleteUI();
  showToast(`🗑️ Đã xóa thành công ${ids.length} công việc!`, 'success');
}
