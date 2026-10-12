/* ─────────────────────────────────────────────────────────
   app.js  –  myfaveTT Archive PWA  (optimized: lazy render)
   ─────────────────────────────────────────────────────────
   Giải pháp tốc độ:
   • Chỉ render 40 card đầu (header only, không có video HTML)
   • Video list được tạo on-demand khi bấm mở card
   • Infinite scroll: tải thêm khi cuộn đến cuối
   • Search debounce 150ms
   ───────────────────────────────────────────────────────── */

const PAGE_SIZE = 40;

let allAuthors    = [];   // raw data
let currentTab    = 'fav';
let searchQuery   = '';
let filtered      = [];   // sau khi filter
let renderedCount = 0;    // số card đã render
let searchTimer   = null;
let scrollObserver = null;

// DOM refs
const $loading    = document.getElementById('loading');
const $empty      = document.getElementById('empty');
const $list       = document.getElementById('author-list');
const $sentinel   = document.getElementById('scroll-sentinel'); // OUTSIDE $list
const $search     = document.getElementById('search');
const $resultBar  = document.getElementById('result-bar');
const $statsLine  = document.getElementById('stats-line');
const $footer     = document.getElementById('footer');
const $tabs       = document.querySelectorAll('.tab-btn');

// ── Load data ─────────────────────────────────────────────
async function loadData() {
  try {
    const resp = await fetch('./data.json');
    if (!resp.ok) throw new Error('HTTP ' + resp.status);
    const data = await resp.json();

    allAuthors = data.authors || [];

    const s = data.stats || {};
    $statsLine.textContent = `❤️ ${fmtN(s.fav || 0)}  👍 ${fmtN(s.likes || 0)}`;
    $footer.textContent    = `myfaveTT Archive · Cập nhật ${fmtDate(data.updated)}`;

    $loading.style.display = 'none';
    applyFilter();
  } catch (e) {
    $loading.innerHTML = `
      <div style="color:#fe2c55;text-align:center;padding:32px 24px">
        ⚠️ Không tải được dữ liệu.<br>
        <small style="color:#8a8a8a;margin-top:8px;display:block">
          Chạy sync.py rồi thử lại.<br><code>${e.message}</code>
        </small>
      </div>`;
  }
}

// ── Filter ────────────────────────────────────────────────
function applyFilter() {
  const q = searchQuery.toLowerCase().trim();
  const isFav = currentTab === 'fav';

  filtered = allAuthors.filter(a => {
    const hasVideos = isFav ? a.b.length > 0 : a.l.length > 0;
    if (!hasVideos) return false;
    if (!q) return true;
    return (a.u || '').toLowerCase().includes(q) ||
           (a.n || '').toLowerCase().includes(q);
  });

  $resultBar.textContent = searchQuery
    ? `${fmtN(filtered.length)} kết quả cho "${searchQuery}"`
    : `${fmtN(filtered.length)} tác giả`;

  // Reset list: remove all .author-card children (sentinel is outside)
  $list.innerHTML = '';
  renderedCount = 0;

  if (filtered.length === 0) {
    $empty.style.display = 'block';
    return;
  }
  $empty.style.display = 'none';

  renderNextPage();
  setupScrollObserver();
}

// ── Render one page (PAGE_SIZE cards) ────────────────────
function renderNextPage() {
  if (renderedCount >= filtered.length) return;

  const isFav = currentTab === 'fav';
  const q     = searchQuery.toLowerCase().trim();
  const slice = filtered.slice(renderedCount, renderedCount + PAGE_SIZE);
  const frag  = document.createDocumentFragment();

  slice.forEach(a => {
    frag.appendChild(buildCard(a, isFav, q));
  });

  $list.appendChild(frag);  // sentinel is outside $list now
  renderedCount += slice.length;
}

// ── Build one author card (header only, no video HTML) ────
function buildCard(a, isFav, q) {
  const display  = a.n || a.u || '(unknown)';
  const username = a.u ? '@' + a.u : '';
  const initial  = (display[0] || '?').toUpperCase();
  const videos   = isFav ? a.b : a.l;
  const count    = videos.length;

  const card = document.createElement('div');
  card.className = 'author-card';

  // Header
  const header = document.createElement('div');
  header.className = 'author-header';
  header.innerHTML = `
    <div class="author-avatar">${esc(initial)}</div>
    <div class="author-info">
      <div class="author-name">${highlight(esc(display), q)}</div>
      <div class="author-username">${highlight(esc(username), q)}</div>
    </div>
    <div class="author-count">
      <span class="count-badge ${isFav ? '' : 'likes-badge'}">${fmtN(count)} ${isFav ? 'FAV' : 'LIKE'}</span>
    </div>
    <span class="chevron">▾</span>`;

  // Empty video container (lazy filled on open)
  const videoList = document.createElement('div');
  videoList.className = 'video-list';

  header.addEventListener('click', () => {
    const isOpen = card.classList.toggle('open');
    if (isOpen && !videoList.dataset.loaded) {
      videoList.innerHTML = buildVideoHTML(videos, isFav);
      videoList.dataset.loaded = '1';
    }
  });

  card.appendChild(header);
  card.appendChild(videoList);
  return card;
}

// ── Build video list HTML (on demand) ────────────────────
function buildVideoHTML(videos, isFav) {
  if (!videos.length) return '<div class="video-item" style="color:#555">Trống</div>';
  const typeClass = isFav ? 'fav' : 'like';
  const typeLabel = isFav ? 'FAV' : 'LIKE';
  return videos.map(([vid, ts]) =>
    `<div class="video-item">
      <span class="video-type ${typeClass}">${typeLabel}</span>
      <span class="video-id">${vid}</span>
      <span class="video-date">${fmtDate(ts)}</span>
    </div>`
  ).join('');
}

// ── Infinite scroll (IntersectionObserver) ────────────────
function setupScrollObserver() {
  if (scrollObserver) scrollObserver.disconnect();
  if (!$sentinel) return;
  scrollObserver = new IntersectionObserver(entries => {
    if (entries[0].isIntersecting && renderedCount < filtered.length) {
      renderNextPage();
    }
  }, { rootMargin: '300px' });
  scrollObserver.observe($sentinel);
}

// ── Tabs ──────────────────────────────────────────────────
$tabs.forEach(btn => {
  btn.addEventListener('click', () => {
    $tabs.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentTab = btn.dataset.tab;
    applyFilter();
  });
});

// ── Search ────────────────────────────────────────────────
$search.addEventListener('input', () => {
  searchQuery = $search.value;
  clearTimeout(searchTimer);
  searchTimer = setTimeout(applyFilter, 150);
});

// ── Helpers ───────────────────────────────────────────────
function esc(s) {
  return String(s ?? '')
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function highlight(safeHtml, q) {
  if (!q) return safeHtml;
  const idx = safeHtml.toLowerCase().indexOf(q);
  if (idx < 0) return safeHtml;
  return safeHtml.slice(0, idx) +
    '<mark>' + safeHtml.slice(idx, idx + q.length) + '</mark>' +
    safeHtml.slice(idx + q.length);
}

function fmtN(n) {
  if (n >= 1000) return (n / 1000).toFixed(1).replace(/\.0$/,'') + 'k';
  return String(n);
}

function fmtDate(val) {
  if (!val) return '';
  const ms = typeof val === 'number' ? val * 1000 : NaN;
  if (!ms || isNaN(ms)) return '';
  const d = new Date(ms);
  return d.toLocaleDateString('vi-VN', { day:'2-digit', month:'2-digit', year:'numeric' });
}

// ── Start ─────────────────────────────────────────────────
loadData();
