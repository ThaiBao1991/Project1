"""
MISA Sales Voucher Database Builder
Dùng để lưu trữ và quản lý dữ liệu phiếu bán hàng từ MISA
"""
import sqlite3
import json
import os
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = os.path.join(os.path.dirname(__file__), 'misa_data.db')


def create_database():
    """Tạo cấu trúc database"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # ===== BẢNG KHÁCH HÀNG =====
    cur.execute('''
        CREATE TABLE IF NOT EXISTS khach_hang (
            ma_khach_hang   TEXT PRIMARY KEY,
            ten_khach_hang  TEXT,
            ma_so_thue      TEXT,
            dia_chi         TEXT,
            nguoi_lien_he   TEXT,
            dien_thoai      TEXT,
            email           TEXT,
            ghi_chu         TEXT,
            ngay_tao        TEXT DEFAULT (datetime('now','localtime'))
        )
    ''')

    # ===== BẢNG HÀNG HÓA =====
    cur.execute('''
        CREATE TABLE IF NOT EXISTS hang_hoa (
            ma_hang         TEXT PRIMARY KEY,
            ten_hang        TEXT,
            dvt             TEXT,
            don_gia_mac_dinh REAL DEFAULT 0,
            ma_nhom_hang    TEXT,
            ghi_chu         TEXT,
            ngay_tao        TEXT DEFAULT (datetime('now','localtime'))
        )
    ''')

    # ===== BẢNG PHIẾU BÁN HÀNG =====
    cur.execute('''
        CREATE TABLE IF NOT EXISTS phieu_ban_hang (
            so_chung_tu         TEXT PRIMARY KEY,
            ngay_chung_tu       TEXT,
            ngay_hach_toan      TEXT,
            ma_khach_hang       TEXT,
            ten_khach_hang      TEXT,
            dieu_khoan_tt       TEXT,
            so_ngay_no          INTEGER DEFAULT 0,
            han_thanh_toan      TEXT,
            nhan_vien_ban_hang  TEXT,
            dien_giai           TEXT,
            tong_tien_hang      REAL DEFAULT 0,
            tong_thue_gtgt      REAL DEFAULT 0,
            tong_tien_tt        REAL DEFAULT 0,
            loai_tien           TEXT DEFAULT 'VND',
            ty_gia              REAL DEFAULT 1,
            trang_thai          TEXT DEFAULT 'Chưa thu tiền',
            ngay_nhap           TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (ma_khach_hang) REFERENCES khach_hang(ma_khach_hang)
        )
    ''')

    # ===== BẢNG CHI TIẾT PHIẾU BÁN =====
    cur.execute('''
        CREATE TABLE IF NOT EXISTS chi_tiet_phieu_ban (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            so_chung_tu     TEXT,
            so_thu_tu       INTEGER,
            ma_hang         TEXT,
            ten_hang        TEXT,
            dvt             TEXT,
            kho             TEXT,
            so_luong        REAL DEFAULT 0,
            don_gia         REAL DEFAULT 0,
            thanh_tien      REAL DEFAULT 0,
            pct_thue_gtgt   REAL DEFAULT 0,
            tien_thue_gtgt  REAL DEFAULT 0,
            tk_cong_no      TEXT,
            tk_doanh_thu    TEXT,
            tk_thue_gtgt    TEXT,
            han_su_dung     TEXT,
            so_lo           TEXT,
            hang_khuyen_mai INTEGER DEFAULT 0,
            ghi_chu         TEXT,
            FOREIGN KEY (so_chung_tu) REFERENCES phieu_ban_hang(so_chung_tu),
            FOREIGN KEY (ma_hang) REFERENCES hang_hoa(ma_hang)
        )
    ''')

    # ===== INDEX để tìm kiếm nhanh =====
    cur.execute('CREATE INDEX IF NOT EXISTS idx_pbh_khach_hang ON phieu_ban_hang(ma_khach_hang)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_pbh_ngay ON phieu_ban_hang(ngay_chung_tu)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_ctpb_phieu ON chi_tiet_phieu_ban(so_chung_tu)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_ctpb_hang ON chi_tiet_phieu_ban(ma_hang)')

    conn.commit()
    print(f'✅ Database tạo thành công: {DB_PATH}')
    return conn


def insert_khach_hang(conn, data: dict):
    """Thêm hoặc cập nhật khách hàng"""
    cur = conn.cursor()
    cur.execute('''
        INSERT OR REPLACE INTO khach_hang
        (ma_khach_hang, ten_khach_hang, ma_so_thue, dia_chi, nguoi_lien_he, ghi_chu)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        data.get('ma_khach_hang', ''),
        data.get('ten_khach_hang', ''),
        data.get('ma_so_thue', ''),
        data.get('dia_chi', ''),
        data.get('nguoi_lien_he', ''),
        data.get('ghi_chu', ''),
    ))
    conn.commit()
    print(f'  → Khách hàng: {data.get("ma_khach_hang")} - {data.get("ten_khach_hang")}')


def insert_phieu_ban_hang(conn, header: dict, chi_tiet: list):
    """Thêm phiếu bán hàng + chi tiết"""
    cur = conn.cursor()

    # Tính tổng
    tong_tien_hang = sum(float(d.get('thanh_tien', 0) or 0) for d in chi_tiet)
    tong_thue = sum(float(d.get('tien_thue_gtgt', 0) or 0) for d in chi_tiet)

    cur.execute('''
        INSERT OR REPLACE INTO phieu_ban_hang
        (so_chung_tu, ngay_chung_tu, ngay_hach_toan, ma_khach_hang, ten_khach_hang,
         dieu_khoan_tt, so_ngay_no, han_thanh_toan, nhan_vien_ban_hang, dien_giai,
         tong_tien_hang, tong_thue_gtgt, tong_tien_tt, loai_tien, trang_thai)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        header.get('so_chung_tu'),
        header.get('ngay_chung_tu'),
        header.get('ngay_hach_toan'),
        header.get('ma_khach_hang'),
        header.get('ten_khach_hang'),
        header.get('dieu_khoan_tt'),
        int(header.get('so_ngay_no', 0) or 0),
        header.get('han_thanh_toan'),
        header.get('nhan_vien_ban_hang'),
        header.get('dien_giai'),
        tong_tien_hang,
        tong_thue,
        tong_tien_hang + tong_thue,
        header.get('loai_tien', 'VND'),
        header.get('trang_thai', 'Chưa thu tiền'),
    ))

    # Xóa chi tiết cũ và thêm lại
    cur.execute('DELETE FROM chi_tiet_phieu_ban WHERE so_chung_tu = ?', (header.get('so_chung_tu'),))

    for idx, row in enumerate(chi_tiet, 1):
        # Upsert hàng hóa nếu có
        if row.get('ma_hang'):
            cur.execute('''
                INSERT OR IGNORE INTO hang_hoa (ma_hang, ten_hang, dvt)
                VALUES (?, ?, ?)
            ''', (row.get('ma_hang'), row.get('ten_hang', ''), row.get('dvt', '')))

        cur.execute('''
            INSERT INTO chi_tiet_phieu_ban
            (so_chung_tu, so_thu_tu, ma_hang, ten_hang, dvt, kho,
             so_luong, don_gia, thanh_tien, pct_thue_gtgt, tien_thue_gtgt,
             tk_cong_no, tk_doanh_thu, tk_thue_gtgt, han_su_dung, so_lo, hang_khuyen_mai)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            header.get('so_chung_tu'),
            idx,
            row.get('ma_hang', ''),
            row.get('ten_hang', ''),
            row.get('dvt', ''),
            row.get('kho', ''),
            float(row.get('so_luong', 0) or 0),
            float(row.get('don_gia', 0) or 0),
            float(row.get('thanh_tien', 0) or 0),
            float(row.get('pct_thue_gtgt', 0) or 0),
            float(row.get('tien_thue_gtgt', 0) or 0),
            row.get('tk_cong_no', ''),
            row.get('tk_doanh_thu', ''),
            row.get('tk_thue_gtgt', ''),
            row.get('han_su_dung', ''),
            row.get('so_lo', ''),
            1 if row.get('hang_khuyen_mai') else 0,
        ))

    conn.commit()
    print(f'  → Phiếu: {header.get("so_chung_tu")} | KH: {header.get("ma_khach_hang")} | {len(chi_tiet)} dòng hàng')


def load_from_json(json_file: str, conn):
    """Nạp dữ liệu từ file JSON (kết quả extract_misa.js)"""
    with open(json_file, encoding='utf-8') as f:
        data = json.load(f)

    print(f'\n📂 Đang nạp dữ liệu từ: {json_file}')

    # Nếu là list các phiếu
    if isinstance(data, list):
        for item in data:
            _process_voucher(item, conn)
    elif isinstance(data, dict):
        _process_voucher(data, conn)


def _process_voucher(data: dict, conn):
    """Xử lý 1 phiếu bán hàng"""
    header = data.get('header', data)
    chi_tiet = data.get('chi_tiet', data.get('products', []))

    # Upsert khách hàng
    if header.get('ma_khach_hang'):
        insert_khach_hang(conn, {
            'ma_khach_hang': header.get('ma_khach_hang'),
            'ten_khach_hang': header.get('ten_khach_hang'),
            'ma_so_thue': header.get('ma_so_thue'),
            'dia_chi': header.get('dia_chi'),
            'nguoi_lien_he': header.get('nguoi_lien_he'),
        })

    # Insert phiếu + chi tiết
    if header.get('so_chung_tu'):
        insert_phieu_ban_hang(conn, header, chi_tiet)


def query_summary(conn):
    """Hiển thị tóm tắt dữ liệu trong DB"""
    cur = conn.cursor()
    print('\n' + '='*60)
    print('📊 DATABASE SUMMARY')
    print('='*60)

    cur.execute('SELECT COUNT(*) FROM khach_hang')
    print(f'Khách hàng:      {cur.fetchone()[0]:>6}')

    cur.execute('SELECT COUNT(*) FROM hang_hoa')
    print(f'Hàng hóa:        {cur.fetchone()[0]:>6}')

    cur.execute('SELECT COUNT(*) FROM phieu_ban_hang')
    print(f'Phiếu bán hàng:  {cur.fetchone()[0]:>6}')

    cur.execute('SELECT COUNT(*) FROM chi_tiet_phieu_ban')
    print(f'Dòng chi tiết:   {cur.fetchone()[0]:>6}')

    cur.execute('SELECT SUM(tong_tien_tt) FROM phieu_ban_hang')
    total = cur.fetchone()[0] or 0
    print(f'Tổng tiền TT:    {total:>12,.0f} VND')

    print('\n--- Top khách hàng ---')
    cur.execute('''
        SELECT kh.ma_khach_hang, kh.ten_khach_hang,
               COUNT(p.so_chung_tu) as so_phieu,
               SUM(p.tong_tien_tt) as tong_tt
        FROM khach_hang kh
        LEFT JOIN phieu_ban_hang p ON p.ma_khach_hang = kh.ma_khach_hang
        GROUP BY kh.ma_khach_hang
        ORDER BY tong_tt DESC
        LIMIT 10
    ''')
    for row in cur.fetchall():
        print(f'  {row[0]:15} | {row[1][:30]:30} | {row[2]} phiếu | {(row[3] or 0):>12,.0f} VND')


# ===== DỮ LIỆU MẪU từ screenshot =====
SAMPLE_DATA = {
    'header': {
        'so_chung_tu': 'BH150178I',
        'ngay_chung_tu': '05/10/2026',
        'ngay_hach_toan': '05/10/2026 21:49:37',
        'ma_khach_hang': 'CTYTH-E',
        'ten_khach_hang': 'CÔNG TY CP PHÒNG KHÁM ĐA KHOA TÂN THÀNH',
        'ma_so_thue': '3001748675',
        'dia_chi': 'Số nhà 17, đường Lê Hữu Trác, Tổ dân phố số 7, Xã Hương Khê, Tỉnh Hà Tĩnh, Việt Nam.',
        'nguoi_lien_he': '',
        'nhan_vien_ban_hang': '',
        'dieu_khoan_tt': 'TM/CK',
        'so_ngay_no': 30,
        'han_thanh_toan': '04/11/2026',
        'dien_giai': 'Bán hàng CÔNG TY CP PHÒNG KHÁM ĐA KHOA TÂN THÀNH',
        'loai_tien': 'VND',
        'trang_thai': 'Chưa thu tiền',
    },
    'chi_tiet': [
        {
            # Dòng 1 từ screenshot - Mã hàng và tên hàng cần bổ sung sau khi scroll
            'so_thu_tu': 1,
            'ma_hang': '',
            'ten_hang': '',
            'dvt': '131',
            'kho': '',
            'so_luong': 1.00,
            'don_gia': 0.0,
            'thanh_tien': 0,
            'pct_thue_gtgt': 0,
            'tien_thue_gtgt': 0,
            'tk_thue_gtgt': '33311',
        }
    ]
}


if __name__ == '__main__':
    print('🗄️  MISA Database Builder')
    print('='*60)

    conn = create_database()

    # Nạp dữ liệu mẫu từ screenshot
    print('\n📝 Nạp dữ liệu mẫu từ screenshot...')
    _process_voucher(SAMPLE_DATA, conn)

    # Nếu có file JSON từ extract_misa.js -> nạp thêm
    json_file = os.path.join(os.path.dirname(__file__), 'misa_extracted.json')
    if os.path.exists(json_file):
        load_from_json(json_file, conn)
    else:
        print(f'\n💡 TIP: Chạy extract_misa.js trong Console MISA, lưu kết quả vào:')
        print(f'   {json_file}')
        print('   Sau đó chạy lại script này để nạp dữ liệu đầy đủ.')

    query_summary(conn)
    conn.close()
    print(f'\n✅ Done! Database: {DB_PATH}')
