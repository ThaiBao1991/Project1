---
name: web_gantt_excel_exporter
description: Zero-dependency client-side Excel (.xls / .xlsx XML SpreadsheetML) export with advanced formatting (cell background colors, borders, custom number/date formats, merged cells) and Gantt task timeline projection in pure JavaScript. Use when generating complex corporate Excel reports, P.KT directive forms, or Gantt chart spreadsheets without third-party npm packages (like SheetJS/xlsx).
---

# Zero-Dependency Web Gantt & Corporate Excel Exporter

Giải pháp tạo và tải file Excel chuẩn doanh nghiệp (SpreadsheetML XML 2003 / Excel XML) hoàn toàn bằng JavaScript thuần chạy trực tiếp trên trình duyệt, không cần bất kỳ thư viện ngoài nào (như `xlsx`, `exceljs`, `xlsx-populate`).

---

## 1. Tại Sao Dùng Excel XML (SpreadsheetML)?

- **0 KB Phụ Thuộc**: Không cần `npm install` hay nhúng file CDN nặng nề (SheetJS thường >1MB).
- **Hỗ trợ Style Màu Sắc 100%**: Excel XML cho phép định nghĩa màu nền header (ví dụ: `#E6B8B7` pastel), viền ô kẻ nét đứt/liền, font chữ in đậm, canh giữa/trái, format ngày tháng `dd/mm/yyyy` trực tiếp trong mã XML.
- **Tương Thích Mọi Phiên Bản Excel**: Mở mượt mà trên Microsoft Excel (2007 đến 2026, Office 365), WPS Office, LibreOffice Calc.
- **An Toàn Tuyệt Đối**: Không bị giới hạn CSP trình duyệt vì chỉ tạo `Blob` từ chuỗi string XML nội bộ.

---

## 2. Cấu Trúc Khung Mẫu XML SpreadsheetML Chuẩn

```javascript
function generateSpreadsheetML(sheetName, stylesXml, rowsXml) {
  return `<?xml version="1.0" encoding="UTF-8"?>
<?mso-application progid="Excel.Sheet"?>
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"
 xmlns:o="urn:schemas-microsoft-com:office:office"
 xmlns:x="urn:schemas-microsoft-com:office:excel"
 xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"
 xmlns:html="http://www.w3.org/TR/REC-html40">
 <Styles>
  <Style ss:ID="Default" ss:Name="Normal">
   <Alignment ss:Vertical="Center"/>
   <Borders/>
   <Font ss:FontName="Calibri" ss:Size="11" ss:Color="#000000"/>
   <Interior/>
   <NumberFormat/>
   <Protection/>
  </Style>
  <!-- Header style: Nền màu pastel #E6B8B7, chữ đậm, viền mỏng -->
  <Style ss:ID="sHeader">
   <Alignment ss:Horizontal="Center" ss:Vertical="Center" ss:WrapText="1"/>
   <Borders>
    <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#A6A6A6"/>
    <Border ss:Position="Left" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#A6A6A6"/>
    <Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#A6A6A6"/>
    <Border ss:Position="Top" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#A6A6A6"/>
   </Borders>
   <Font ss:FontName="Calibri" ss:Size="11" ss:Bold="1" ss:Color="#000000"/>
   <Interior ss:Color="#E6B8B7" ss:Pattern="Solid"/>
  </Style>
  <!-- Data cell border style -->
  <Style ss:ID="sData">
   <Alignment ss:Vertical="Center"/>
   <Borders>
    <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#D9D9D9"/>
    <Border ss:Position="Left" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#D9D9D9"/>
    <Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#D9D9D9"/>
    <Border ss:Position="Top" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#D9D9D9"/>
   </Borders>
   <Font ss:FontName="Calibri" ss:Size="10" ss:Color="#000000"/>
  </Style>
  ${stylesXml}
 </Styles>
 <Worksheet ss:Name="${escapeXml(sheetName)}">
  <Table>
   ${rowsXml}
  </Table>
 </Worksheet>
</Workbook>`;
}
```

---

## 3. Escape Ký Tự Đặc Biệt XML & Tiếng Việt

Bắt buộc escape các ký tự đặc biệt trong XML để file không bị lỗi "XML Corrupted" khi mở trong Excel:

```javascript
function escapeXml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

function makeCell(val, styleId = "sData", type = "String") {
  if (val === null || val === undefined || val === '') {
    return `<Cell ss:StyleID="${styleId}"><Data ss:Type="String"></Data></Cell>`;
  }
  return `<Cell ss:StyleID="${styleId}"><Data ss:Type="${type}">${escapeXml(val)}</Data></Cell>`;
}
```

---

## 4. Cơ Chế Download 1-Chạm Trên Trình Duyệt

```javascript
function downloadExcelFile(xmlContent, fileName) {
  const blob = new Blob([xmlContent], { type: 'application/vnd.ms-excel;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = fileName.endsWith('.xls') ? fileName : `${fileName}.xls`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
```

---

## 5. Quy Tắc Biểu Mẫu Doanh Nghiệp (P.KT 12 Cột Mẫu)

Khi xuất danh sách công việc theo chuẩn báo cáo chỉ thị nội bộ:
1. **Đối tượng**: Nguồn việc (Giám đốc, Trưởng phòng, Mục tiêu năm...).
2. **Đảm trách**: Chuẩn hóa `Mã NV + Tên` (ví dụ: `12333 Sỹ`).
3. **Chịu trách nhiệm**: Mặc định người phụ trách chính.
4. **Nội dung**: Kết hợp Tên việc + Chi tiết (`task.title: task.detail`).
5. **Ngày chỉ thị / Kỳ hạn**: Định dạng chuẩn `dd/mm/yyyy`.
6. **Ngày hoàn tất**: Nếu chưa hoàn thành $\rightarrow$ để trống `""` (không điền text rác).
7. **Tình trạng**: Đang làm, Hoàn thành, Tạm dừng, Trễ hạn.

