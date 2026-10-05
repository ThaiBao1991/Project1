/**
 * MISA Network Interceptor - Lấy dữ liệu từ API response
 * CÁCH DÙNG:
 *   Bước 1: Paste TOÀN BỘ script này vào Console TRƯỚC KHI mở/reload phiếu
 *   Bước 2: Reload trang hoặc mở lại phiếu bán hàng
 *   Bước 3: Sau khi trang load xong, gọi: downloadCapture()
 *
 * HOẶC nếu trang đã mở sẵn:
 *   - Paste script -> Enter (cài interceptor)
 *   - Mở phiếu khác bất kỳ (hoặc F5 reload) -> data tự được bắt
 *   - Gọi downloadCapture() để tải JSON
 */

// ================================================================
// PHẦN 1: CÀI INTERCEPTOR (chạy ngay khi paste)
// ================================================================
window._misaCapture = {
  requests: [],
  responses: [],
  voucherData: null,
};

// --- Override fetch ---
const _origFetch = window.fetch;
window.fetch = async function(...args) {
  const url = typeof args[0] === 'string' ? args[0] : args[0]?.url || '';
  const res = await _origFetch.apply(this, args);
  
  // Clone để đọc body mà không consume stream
  const clone = res.clone();
  try {
    const text = await clone.text();
    let data;
    try { data = JSON.parse(text); } catch(e) { data = text.substring(0, 500); }
    
    // Chỉ lưu API calls quan trọng
    if (url.includes('/api/') || url.includes('actapp.misa')) {
      window._misaCapture.requests.push({ url, method: args[1]?.method || 'GET' });
      window._misaCapture.responses.push({ url, data });
      
      // Tìm API trả về data phiếu bán hàng
      if (typeof data === 'object' && data !== null) {
        const dataStr = JSON.stringify(data);
        if (dataStr.includes('voucher') || dataStr.includes('Voucher') ||
            dataStr.includes('customer') || dataStr.includes('khach') ||
            dataStr.includes('BH') || dataStr.includes('refNo') ||
            dataStr.includes('details') || dataStr.includes('items') ||
            dataStr.includes('totalAmount') || dataStr.includes('listDetail')) {
          window._misaCapture.voucherData = { url, data };
          console.log('%c📦 MISA API Response captured!', 'color:green;font-weight:bold', url);
          console.log('Keys:', Object.keys(data));
        }
      }
    }
  } catch(e) {}
  
  return res;
};

// --- Override XMLHttpRequest ---
const _origXHROpen = XMLHttpRequest.prototype.open;
const _origXHRSend = XMLHttpRequest.prototype.send;

XMLHttpRequest.prototype.open = function(method, url, ...rest) {
  this._captureUrl = url;
  this._captureMethod = method;
  return _origXHROpen.apply(this, [method, url, ...rest]);
};

XMLHttpRequest.prototype.send = function(body) {
  this.addEventListener('load', function() {
    const url = this._captureUrl || '';
    if (url.includes('/api/') || url.includes('actapp.misa')) {
      let data;
      try { data = JSON.parse(this.responseText); } catch(e) { data = this.responseText?.substring(0, 300); }
      window._misaCapture.requests.push({ url, method: this._captureMethod });
      window._misaCapture.responses.push({ url, data });
      
      if (typeof data === 'object' && data !== null) {
        const s = JSON.stringify(data);
        if (s.includes('voucher') || s.includes('Voucher') || s.includes('customer') ||
            s.includes('listDetail') || s.includes('totalAmount') || s.includes('refNo')) {
          window._misaCapture.voucherData = { url, data };
          console.log('%c📦 XHR MISA Response captured!', 'color:blue;font-weight:bold', url);
        }
      }
    }
  });
  return _origXHRSend.apply(this, arguments);
};

console.log('%c✅ MISA Interceptor đã cài!', 'color:green;font-size:14px;font-weight:bold');
console.log('Giờ hãy: F5 reload trang, hoặc mở 1 phiếu bán hàng bất kỳ');
console.log('Sau khi load xong → gọi: downloadCapture()');
console.log('Hoặc xem ngay: window._misaCapture');

// ================================================================
// PHẦN 2: HÀM TẢI KẾT QUẢ
// ================================================================
window.downloadCapture = function(filename) {
  const capture = window._misaCapture;
  
  // Nếu có voucherData thì ưu tiên extract chi tiết
  let structured = null;
  if (capture.voucherData) {
    const d = capture.voucherData.data;
    // Thử các cấu trúc MISA phổ biến
    const root = d.Data || d.data || d.Result || d.result || d;
    structured = {
      raw_api_url: capture.voucherData.url,
      raw_data: root,
    };
  }
  
  const output = {
    extracted_at: new Date().toLocaleString('vi-VN'),
    total_api_calls: capture.requests.length,
    api_urls: capture.requests.map(r => `${r.method} ${r.url}`),
    
    // Dữ liệu phiếu nếu bắt được
    voucher_structured: structured,
    
    // Tất cả responses quan trọng
    all_captured_responses: capture.responses.map(r => ({
      url: r.url.substring(0, 150),
      keys: typeof r.data === 'object' && r.data ? Object.keys(r.data) : typeof r.data,
      sample: JSON.stringify(r.data).substring(0, 300),
    })),
    
    // Full voucher response
    voucher_raw_full: capture.voucherData?.data || null,
  };
  
  const json = JSON.stringify(output, null, 2);
  const blob = new Blob([json], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = filename || 'misa_api_capture.json';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  
  console.log('%c📥 File tải xong!', 'color:green;font-size:14px;font-weight:bold');
  console.log('API calls bắt được:', capture.requests.length);
  console.log('Voucher data:', capture.voucherData ? 'CÓ ✅' : 'CHƯA ❌');
  console.log('API URLs:');
  capture.requests.forEach(r => console.log(' ', r.method, r.url));
  
  return output;
};

// ================================================================
// PHẦN 3: ĐỌC DOM TRỰC TIẾP (chạy ngay - không cần reload)
// ================================================================
window.readDomNow = function() {
  // Đọc TẤT CẢ span/div có text trong MISA form
  const result = {};
  
  // MISA combo value thường nằm trong: .ms-combo-txt, .mis-combo__input, span.txt
  const comboSelectors = [
    '.ms-combo-txt', '.mis-combo__input', '.combo-txt',
    '.ms-combo .txt', '[class*="combo"] span', '[class*="combo"] .txt',
    '.mis-select__selection span', '.ms-input-value',
    'span.ms-combo-text', '.ms-combobox-content span',
    // MISA form field value
    '.mis-form-item__content span', '.form-value',
    '.mis-select-dropdown__option--selected',
  ];
  
  comboSelectors.forEach(sel => {
    document.querySelectorAll(sel).forEach((el, i) => {
      const txt = (el.textContent || el.innerText || '').trim();
      if (txt && txt.length > 0 && txt.length < 300) {
        result[`${sel}[${i}]`] = txt;
      }
    });
  });
  
  // Đọc tất cả input kể cả readonly, disabled, hidden
  const inputs = {};
  document.querySelectorAll('input, textarea, select').forEach((el, i) => {
    const val = el.value || '';
    const attrs = {
      value: val,
      placeholder: el.placeholder || '',
      name: el.name || '',
      id: el.id || '',
      type: el.type || '',
      readonly: el.readOnly,
      disabled: el.disabled,
      class: el.className.substring(0, 50),
    };
    if (val || el.id || el.name) {
      inputs[`input_${i}_${el.id || el.name || el.placeholder || 'unknown'}`] = attrs;
    }
  });

  // Đặc biệt: đọc text của toàn bộ table cells
  const tableRows = [];
  document.querySelectorAll('table tr').forEach((tr, ri) => {
    const cells = [];
    tr.querySelectorAll('td, th').forEach(td => {
      const inp = td.querySelector('input, textarea');
      const val = inp ? inp.value : td.textContent.trim();
      cells.push(val.replace(/\s+/g, ' ').trim());
    });
    if (cells.some(c => c)) tableRows.push({ row: ri, cells });
  });

  const domResult = {
    combo_values: result,
    all_inputs: inputs,
    table_rows: tableRows,
    page_text: document.body.innerText.split('\n').map(l => l.trim()).filter(l => l),
  };
  
  const json = JSON.stringify(domResult, null, 2);
  const blob = new Blob([json], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'misa_dom_now.json';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  
  console.log('%c✅ DOM snapshot tải xong! (misa_dom_now.json)', 'color:green;font-weight:bold');
  console.log('Combo values:', Object.keys(result).length);
  console.log('Inputs:', Object.keys(inputs).length);
  console.log('Table rows:', tableRows.length);
  return domResult;
};

console.log('');
console.log('%c=== CÁC LỆNH CÓ THỂ DÙNG NGAY ===', 'color:blue;font-size:13px;font-weight:bold');
console.log('%c readDomNow()     ', 'background:green;color:white;padding:2px 4px', '→ Tải snapshot DOM hiện tại (không cần reload)');
console.log('%c downloadCapture() ', 'background:blue;color:white;padding:2px 4px', '→ Tải API responses đã bắt được');
console.log('%c _misaCapture      ', 'background:gray;color:white;padding:2px 4px', '→ Xem raw data trực tiếp');
