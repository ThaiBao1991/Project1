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
        ]
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
        ]
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
    if any(k in val for k in ("excel", "ms excel", "ms_excel", "bảng tính")):
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

Yêu cầu phân tích sâu sắc và thực tế:
1. Xác định bản chất lĩnh vực (CSDL, Bảng tính, Ngôn ngữ lập trình, Kỹ thuật cơ khí, Nghệ thuật, Khoa học...).
2. 'recommended_days': Số ngày học thực tế để từ con số 0 trở thành CHUYÊN GIA BẬC CAO CẤP RẤT SÂU (từ 30 đến 3000 ngày). TUYỆT ĐỐI KHÔNG cào bằng 365 hay 600 ngày nếu lĩnh vực đó lớn hơn hoặc nhỏ hơn.
3. 'persona': Định danh người học khi thành tài (ví dụ: 'Kỹ sư CSDL Access', 'Kỹ sư Tính toán Ma trận Excel', 'Kỹ sư Lập trình C++', ...).
4. 'mandatory_milestones': Mảng gồm 8-15 từ khóa tiếng Anh/Việt snake_case biểu thị các cột mốc bắt buộc không được bỏ sót.
5. 'instruction': Đoạn hướng dẫn định hình giáo trình (tối đa 250 từ) nêu rõ các mảng kiến thức từ cơ bản đến đỉnh cao.

Trả về JSON DUY NHẤT dạng:
{{
  "title": "{domain_clean}",
  "recommended_days": 600,
  "persona": "...",
  "category": "...",
  "instruction": "PROFILE {domain_clean.upper()}: ...",
  "mandatory_milestones": ["...", "..."]
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
                    log_fn(f"[✅ AI DOMAIN PROFILER] Khảo sát thành công: {profile_data.get('title')} -> Khuyến nghị: {profile_data.get('recommended_days')} Ngày.")
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
