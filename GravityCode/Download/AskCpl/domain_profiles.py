"""Small domain-specific guardrails layered on the common learning engine."""

from __future__ import annotations


def instruction_for(domain: str) -> str:
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

