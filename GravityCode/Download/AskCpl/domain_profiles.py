"""Small domain-specific guardrails layered on the common learning engine."""

from __future__ import annotations


def instruction_for(domain: str) -> str:
    value = (domain or "").casefold()
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
