"""Domain-specific knowledge blueprints and dynamic AI-powered domain profiling."""

from __future__ import annotations
import os
import json
import re

CACHE_FILE = os.path.join(os.path.dirname(__file__), "domain_profiles_cache.json")

PREDEFINED_PROFILES = {
    "access": {
        "title": "Microsoft Access VBA & Database Architecture",
        "recommended_days": 600,
        "persona": "Kiến trúc sư Cơ sở Dữ liệu & Ứng dụng Doanh nghiệp Access VBA",
        "category": "RDBMS & Enterprise Desktop Application",
        "instruction": (
            "PROFILE ACCESS VBA (Khối lượng chuẩn 600 Ngày): Bắt buộc đạt cấp độ Enterprise Database Architect: "
            "(1) Chuẩn hóa CSDL quan hệ 1NF-3NF, Khóa chính/ngoại, Indexes & Relationships -> "
            "(2) SQL Jet/ACE nâng cao (DDL, DML, Subquery, Union, Crosstab) -> "
            "(3) DAO & ADODB Recordsets, QueryDefs, Transactions (BeginTrans/Commit/Rollback) -> "
            "(4) Form/Subform lifecycle, Continuous Forms, Custom Reports, Validation & Error Trapping -> "
            "(5) Tối ưu hóa truy vấn, Split Database (Frontend/Backend) -> "
            "(6) Multi-user Concurrency & Kỹ thuật khóa Record (Optimistic/Pessimistic Locking) -> "
            "(7) Giao tiếp Thiết bị phần cứng qua Cổng COM RS232 (Máy quét mã vạch, Cân điện tử, Đầu đọc thẻ RFID, Máy in nhiệt) -> "
            "(8) Windows API sâu (kernel32, user32, Registry, GDI, Shell) -> "
            "(9) Tùy biến Ribbon XML, Custom Menu, Đóng gói ACCDE & Bảo mật -> "
            "(10) Client/Server với SQL Server/Azure SQL qua ODBC Linked Tables, REST API Client (WinHttp), Microsoft Graph API & Hybrid Cloud ERP/CRM."
        ),
        "mandatory_milestones": [
            "vba_foundation_forms", "rdbms_normalization_sql", "dao_adodb_recordset",
            "querydef_transactions", "multi_user_locking_concurrency", "split_db_backend_maintenance",
            "com_port_hardware_devices", "winapi_deep_integration", "ribbon_xml_security",
            "sql_server_azure_odbc", "rest_api_graph_cloud", "enterprise_erp_capstone"
        ],
        "milestone_descriptions": {
            "vba_foundation_forms": "Nền tảng Form & Subform lifecycle: Continuous Forms, Validation dữ liệu, Error Trapping tập trung và điều hướng giao diện nghiệp vụ",
            "rdbms_normalization_sql": "Cơ sở dữ liệu quan hệ & SQL Jet/ACE: Chuẩn hóa 1NF-3NF, Khóa chính/ngoại, Indexes, DDL, DML, Subqueries, Union, Crosstab Queries",
            "dao_adodb_recordset": "Lập trình dữ liệu chuyên sâu: DAO & ADODB Recordsets, Seek, Find, Filter, Batch Update, QueryDefs và tối ưu hóa con trỏ Cursor",
            "querydef_transactions": "Giao dịch an toàn & Toàn vẹn dữ liệu: Transactions (BeginTrans/Commit/Rollback), Parameterized QueryDefs chống SQL Injection",
            "multi_user_locking_concurrency": "Đa người dùng & Đồng thời: Khóa bản ghi Optimistic vs Pessimistic Locking, xử lý xung đột ghi đè dữ liệu (Write Conflict)",
            "split_db_backend_maintenance": "Kiến trúc Split Database: Phân tách Frontend/Backend, tự động Relink bảng động (TableDefs), Compact & Repair qua code",
            "com_port_hardware_devices": "Giao tiếp phần cứng qua Cổng COM (RS232/USB): Đọc máy quét mã vạch, cân điện tử, máy in hóa đơn, đầu đọc thẻ RFID",
            "winapi_deep_integration": "Can thiệp sâu Windows API: kernel32, user32, GDI, đọc ghi Registry hệ thống, lấy thông tin phần cứng và máy in",
            "ribbon_xml_security": "Tùy biến Ribbon XML & Đóng gói thương mại: Custom Tab/Menu, Custom Task Pane, bảo mật MDE/ACCDE chống dịch ngược",
            "sql_server_azure_odbc": "Mô hình Client/Server: Kết nối SQL Server & Azure SQL qua ODBC Linked Tables, Pass-Through Queries tối ưu tốc độ",
            "rest_api_graph_cloud": "Điện toán đám mây & REST API: Tích hợp WinHttp REST Client, Microsoft Graph API gửi mail, đọc dữ liệu SharePoint/Office 365",
            "enterprise_erp_capstone": "Đồ án Tổng lực Doanh nghiệp: Hệ thống ERP/CRM quản lý sản xuất, bán hàng, kho đa kho, phân quyền ma trận phân cấp"
        }
    },
    "excel": {
        "title": "Microsoft Excel VBA, High-Performance Computing & AI Add-in Master",
        "recommended_days": 1000,
        "persona": "Kỹ sư Tính toán Ma trận, Phân tích Dữ liệu Lớn & Phát triển Add-in Excel Master",
        "category": "Spreadsheet Matrix Computing, High-Performance Analytics & Automation",
        "instruction": (
            "PROFILE EXCEL VBA (Khối lượng chuẩn 1.000 Ngày): Bắt buộc đạt cấp độ Master Spreadsheet Developer & AI System Integrator: "
            "(1) Range/Sheet/Workbook Object Model, SpecialCells, Names, Lambda & Dynamic Ranges -> "
            "(2) Thuật toán Tốc độ cao & Xử lý Mảng 2D (Variant Arrays), SafeArray, con trỏ bộ nhớ WinAPI CopyMemory -> "
            "(3) Cấu trúc dữ liệu Scripting.Dictionary, Collection, Thuật toán QuickSort/MergeSort/BinarySearch tự viết trong VBA -> "
            "(4) UserForm Chuyên nghiệp, Modern Flat Dark/Light UI, Custom Controls, Kiến trúc bắt sự kiện toàn cục với Class Module (WithEvents) -> "
            "(5) Báo cáo Nâng cao, PivotTable, PivotChart, Slicers, Timelines, Data Model & Power Pivot (DAX & VBA) -> "
            "(6) Tự động hóa Power Query (M Code) & Dynamic Formula Injection -> "
            "(7) Trực quan hóa Dữ liệu Động, Interactive Real-time Dashboards, Canvas & Shape Engine -> "
            "(8) Mô hình hóa Tài chính (Financial Modeling: DCF, NPV/IRR, Amortization, Monte Carlo Simulation, Tự động hóa Solver & What-If Analysis) -> "
            "(9) Giao tiếp Thiết bị phần cứng qua Cổng COM RS232 (Cảm biến, PLC, Thiết bị đo lường, Máy in mã vạch) -> "
            "(10) Windows API sâu (GDI, Subclassing, Registry, Process Memory, Multithreading qua PowerShell/DLL) -> "
            "(11) Web Scraping (Selenium, Chrome DevTools Protocol CDP), REST API, OAuth2, Webhooks, Tự động hóa liên ứng dụng (Word, PPT, Outlook, Access, PDF, CAD) -> "
            "(12) Đóng gói Add-in Thương mại (.xlam), Ribbon XML Customization, Custom Task Pane, Cấp License bản quyền & Nhúng Generative AI (OpenAI/Gemini/DeepSeek) vào công thức Excel (Async UDFs) & Capstone Enterprise System."
        ),
        "mandatory_milestones": [
            "excel_object_model_mastery", "high_speed_2d_arrays_copymemory", "dictionary_sorting_algorithms",
            "modern_userforms_withevents", "pivot_power_pivot_dax", "power_query_m_automation",
            "interactive_dynamic_dashboards", "financial_modeling_solver_montecarlo", "com_port_hardware_interfacing",
            "winapi_subclassing_multithreading", "web_scraping_rest_api_office_sync", "commercial_addin_ribbon_xml_licensing",
            "generative_ai_async_udfs_capstone"
        ],
        "milestone_descriptions": {
            "excel_object_model_mastery": "Làm chủ mô hình đối tượng Excel: Range, Cells, Offset/Resize, SpecialCells, UsedRange, Dynamic Array Formulas và Names",
            "high_speed_2d_arrays_copymemory": "Thuật toán xử lý mảng 2D (Variant Arrays) tốc độ cao trong RAM, SafeArray, con trỏ bộ nhớ WinAPI CopyMemory đạt chuẩn 60fps",
            "dictionary_sorting_algorithms": "Cấu trúc dữ liệu & Thuật toán: Scripting.Dictionary, Collection, ArrayList, QuickSort 2D, MergeSort, BinarySearch tự viết trong VBA",
            "modern_userforms_withevents": "Thiết kế UserForm hiện đại: Modern Flat Dark/Light UI, Custom Controls, bắt sự kiện động tập trung qua Class Module WithEvents",
            "pivot_power_pivot_dax": "Báo cáo phân tích nâng cao: PivotTable, PivotChart, Slicers, Data Model & Power Pivot tích hợp công thức DAX tự động hóa",
            "power_query_m_automation": "Tự động hóa ETL với Power Query (mã M-Code) và Dynamic Formula Injection từ VBA nạp dữ liệu đa nguồn",
            "interactive_dynamic_dashboards": "Trực quan hóa dữ liệu thời gian thực: Real-time Dashboards, Canvas Shapes Engine, KPI Cards và Chart Events",
            "financial_modeling_solver_montecarlo": "Mô hình tài chính doanh nghiệp: DCF, NPV, IRR, Amortization, mô phỏng Monte Carlo rủi ro danh mục và tự động hóa Solver",
            "com_port_hardware_interfacing": "Giao tiếp phần cứng qua Cổng COM RS232/Virtual USB: PLC Modbus RTU, cảm biến đo lường, cân điện tử, máy in mã vạch",
            "winapi_subclassing_multithreading": "Can thiệp sâu Windows API: GDI vẽ UI, Subclassing bắt thông điệp cửa sổ, Registry, giả lập đa luồng Multi-threading",
            "web_scraping_rest_api_office_sync": "Cào dữ liệu & Tích hợp liên ứng dụng: Selenium, Chrome DevTools Protocol (CDP), REST API/OAuth2, đồng bộ Office Word/PPT/Outlook",
            "commercial_addin_ribbon_xml_licensing": "Thương mại hóa giải pháp: Đóng gói Add-in .xlam, lập trình giao diện Ribbon XML, Custom Task Pane và khóa License theo phần cứng",
            "generative_ai_async_udfs_capstone": "Tích hợp Generative AI: Nhúng AI (OpenAI/Gemini/DeepSeek) vào công thức Excel (Async UDFs) và Đồ án Master Doanh nghiệp"
        }
    }
}


def load_cached_profiles() -> dict:
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8", errors="replace") as f:
                return json.loads(f.read())
        except Exception:
            return {}
    return {}


def save_cached_profiles(profiles: dict):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(profiles, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _match_static_profile(domain: str) -> dict | None:
    val = (domain or "").casefold()
    if any(k in val for k in ("access", "ms access", "ms_access")):
        return PREDEFINED_PROFILES["access"]
    if any(k in val for k in ("excel", "excell", "ms excel", "ms_excel", "bảng tính")):
        return PREDEFINED_PROFILES["excel"]
    return None


def get_or_create_domain_profile(domain: str, llm_callable=None, log_fn=None) -> dict:
    """Get domain knowledge profile from static dict, cache or dynamically analyze via AI."""
    domain_clean = (domain or "").strip()
    domain_key = domain_clean.casefold()

    # 1. Static match
    static_prof = _match_static_profile(domain_key)
    if static_prof:
        return static_prof

    # 2. Cache match
    cache = load_cached_profiles()
    if domain_key in cache:
        if log_fn:
            log_fn(f"[🧠 DOMAIN PROFILE] Nạp từ Cache: '{cache[domain_key].get('title')}' ({cache[domain_key].get('recommended_days', 'N/A')} Ngày)")
        return cache[domain_key]

    for k, v in cache.items():
        if k in domain_key or domain_key in k:
            if log_fn:
                log_fn(f"[🧠 DOMAIN PROFILE] Nạp từ Cache khớp gần đúng '{k}': {v.get('recommended_days')} Ngày")
            return v

    # 3. Dynamic Discovery via AI if llm_callable provided
    if llm_callable:
        if log_fn:
            log_fn(f"[🔍 AI DOMAIN PROFILER] Chưa có hồ sơ cho '{domain_clean}'. Đang dùng AI phân tích độ sâu tri thức thực tế...")
        prompt = f"""Bạn là Kiến trúc sư Trưởng Khảo sát & Hoạch định Tri thức Quốc tế.
Hãy phân tích lĩnh vực: '{domain_clean}' để thiết lập Hồ Sơ Định Danh Tri Thức (Domain Knowledge Blueprint).

Yêu cầu phân tích sâu sắc và định lượng quy mô thực tế:
1. Xác định bản chất lĩnh vực (Ngành kỹ sư đa ngành, Kế toán - Kiểm toán, Y khoa, CSDL, Bảng tính, Ngôn ngữ lập trình, Kỹ thuật cơ khí, Điện tử...).
2. 'recommended_days': Số ngày học thực tế (mỗi ngày 1-2 tiếng) để từ con số 0 trở thành CHUYÊN GIA BẬC CAO CẤP RẤT SÂU (từ 30 đến 3000 ngày).
   - QUY CHUẨN ĐỊNH LƯỢNG QUY MÔ BẮT BUỘC:
     * Cả một ngành kỹ sư/chuyên môn hoàn chỉnh (Kỹ sư điện, Kỹ sư cơ khí, Kế toán trưởng & Kiểm toán viên, Bác sĩ...): 1500 đến 2500 ngày (tương đương 4-5 năm đại học chuyên sâu).
     * Một hệ sinh thái công nghệ / ngôn ngữ đồ sộ (Python Full-stack & AI, C++ Systems, Excel VBA Master): 800 đến 1200 ngày.
     * Một công cụ, cơ sở dữ liệu chuyên biệt (Access VBA, Docker & DevOps căn bản, SQL Jet): 300 đến 600 ngày.
     * Một kỹ năng, chủ đề hẹp: 30 đến 180 ngày.
   TUYỆT ĐỐI KHÔNG cào bằng 365 hay 600 ngày nếu lĩnh vực đó lớn hơn hoặc nhỏ hơn. Hãy đánh giá trung thực theo đúng khối lượng kiến thức của ngành!
3. 'persona': Định danh người học khi thành tài (ví dụ: 'Kỹ sư Điện Công nghiệp & Tự động hóa PLC', 'Kế toán trưởng & Chuyên gia Phân tích Tài chính', ...).
4. 'mandatory_milestones': Mảng gồm 12-20 mã phân môn ngắn gọn (snake_case) đại diện cho các trụ cột cốt lõi không được bỏ sót.
5. 'milestone_descriptions': Object ánh xạ từng mã trong 'mandatory_milestones' sang một câu diễn giải tiếng Việt RẤT CHI TIẾT (chứa từ khóa kỹ thuật chuyên sâu, công nghệ, tiêu chuẩn, nghiệp vụ thực chiến).
6. 'instruction': Đoạn hướng dẫn định hình giáo trình (tối đa 250 từ) nêu rõ các mảng kiến thức từ cơ bản đến đỉnh cao.

Trả về JSON DUY NHẤT dạng:
{{
  "title": "{domain_clean}",
  "recommended_days": 1800,
  "persona": "...",
  "category": "...",
  "instruction": "PROFILE {domain_clean.upper()}: ...",
  "mandatory_milestones": ["phan_mon_1", "phan_mon_2"],
  "milestone_descriptions": {{
    "phan_mon_1": "Mô tả chi tiết phân môn 1 bằng tiếng Việt kèm các công cụ, tiêu chuẩn và kỹ năng bắt buộc...",
    "phan_mon_2": "Mô tả chi tiết phân môn 2 bằng tiếng Việt..."
  }}
}}
LUÔN dùng tiếng Việt."""
        try:
            res_text = llm_callable(prompt, "AI Domain Profiler", json_mode=True)
            from roadmap_pipeline import load_json_response
            profile_data = load_json_response(res_text)
            if isinstance(profile_data, dict) and profile_data.get("recommended_days"):
                cache[domain_key] = profile_data
                save_cached_profiles(cache)
                if log_fn:
                    log_fn(f"[✅ AI DOMAIN PROFILER] Khảo sát thành công: {profile_data.get('title')} -> Khuyến nghị: {profile_data.get('recommended_days')} Ngày ({len(profile_data.get('mandatory_milestones', []))} cột mốc chuẩn).")
                return profile_data
        except Exception as e:
            if log_fn:
                log_fn(f"[⚠️ AI DOMAIN PROFILER] Lỗi khảo sát: {e}. Dùng profile fallback.")

    # 4. Fallback default
    fallback = {
        "title": domain_clean,
        "recommended_days": 365,
        "persona": f"Chuyên gia {domain_clean}",
        "category": "General",
        "instruction": f"PROFILE {domain_clean.upper()}: Biến mọi kiến thức thành một sản phẩm/kỹ năng kiểm chứng được trong thời lượng cam kết.",
        "mandatory_milestones": []
    }
    return fallback


def instruction_for(domain: str) -> str:
    prof = _match_static_profile(domain)
    if prof:
        return prof["instruction"]
    value = (domain or "").casefold()
    if any(word in value for word in ("thiên công", "khai vật", "văn minh", "tái thiết", "tiến hóa", "con số 0", "máy tính từ số 0", "đồ đá", "tech tree", "reboot civilization", "sinh tồn sau tận thế", "chế tạo từ đầu")):
        return (
            "PROFILE TECH TREE / TÁI THIẾT VĂN MINH: Bắt buộc tuân thủ cây công nghệ tiến hóa tuần tự không nhảy cóc: "
            "(1) Sinh tồn thảm họa/chiến tranh & bảo tồn tri thức -> (2) Đồ đá & tạo lửa ma sát -> (3) Đồ gốm nung & nông nghiệp -> "
            "(4) Luyện kim đồng/sắt bloomery -> (5) Hóa chất cơ bản (axit sulfuric, xút, xà phòng, cồn) & Giấy/In ấn -> "
            "(6) Chuẩn đo lường (3-plate method) & Cơ khí chính xác/ren ốc/động cơ hơi nước -> (7) Điện từ học (pin Volta, máy phát Dynamo, động cơ điện) -> "
            "(8) Đèn chân không & Cổng logic rời -> (9) Tinh chế Silic 9N, kéo đơn tinh thể & Quang khắc bán dẫn -> "
            "(10) Ghép ALU, Clock, RAM, CPU 8-bit, Bootloader/Assembly từ số 0. Mỗi bước phải chứng minh đã đủ vật liệu và công cụ của bước trước đó."
        )
    if any(word in value for word in ("python", "lập trình", "programming", "code")):
        return (
            "PROFILE PYTHON: nêu phiên bản/câu lệnh chạy khi liên quan; mỗi Day phải có "
            "artifact hoặc test case cụ thể. Không khẳng định code chạy nếu chưa có output thực tế."
        )
    if any(word in value for word in ("đồ chơi", "diy", "thủ công", "craft")):
        return (
            "PROFILE DIY/TRẺ EM: tách rõ người làm và người chơi; luôn nêu độ tuổi, giám sát, "
            "rủi ro chi tiết nhỏ/cạnh sắc/nhiệt/điện/keo. Không nói sản phẩm đạt EN71/ASTM hay "
            "an toàn tuyệt đối nếu không có kiểm định độc lập."
        )
    if any(word in value for word in ("ngoại ngữ", "tiếng anh", "tiếng nhật", "tiếng trung", "tiếng hàn")):
        return "PROFILE NGOẠI NGỮ: nối từ vựng mới với nội dung gần đây; yêu cầu một đầu ra nói/viết có thể tự đối chiếu."
    return "PROFILE CHUNG: biến kiến thức thành một đầu ra kiểm chứng được trong thời lượng đã cam kết."


CIVILIZATION_TECH_TREE_MILESTONES = [
    "sinh_ton_chien_tranh",
    "do_da_tao_lua",
    "gom_su_nong_nghiep",
    "luyen_kim_dong_sat",
    "hoa_chat_co_ban_giay",
    "do_luong_co_khi_chinh_xac",
    "dien_tu_hoc_nang_luong",
    "den_chan_khong_logic",
    "ban_dan_tinh_che_silic",
    "che_tao_cpu_may_tinh",
]


def is_tech_tree_domain(domain: str) -> bool:
    value = (domain or "").casefold()
    return any(word in value for word in ("thiên công", "khai vật", "văn minh", "tái thiết", "tiến hóa", "con số 0", "máy tính từ số 0", "đồ đá", "tech tree", "reboot civilization", "sinh tồn sau tận thế", "chế tạo từ đầu"))
