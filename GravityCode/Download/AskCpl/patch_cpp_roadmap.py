# -*- coding: utf-8 -*-
"""
patch_cpp_roadmap.py
====================
Bổ sung 2 thứ vào file 'roadmap_cpp test.md':
1. Non-Interactive warning cho các Phan cuối chu kỳ (15-cycle: 13-15, 25-cycle: 13-25)
2. Thêm 18 topic mới (270 Day) từ Day 3081 → 3350 vào cuối file
"""

import re
import os

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
INPUT_FILE  = r"c:\Users\games\Desktop\Project\Python\Python MyWork\Project1\GravityCode\Download\AskCpl\roadmap_cpp test.md"
OUTPUT_FILE = INPUT_FILE  # Ghi đè trực tiếp

WARNING_LINE = "(⚠️ QUAN TRỌNG: TUYỆT ĐỐI KHÔNG tạo bài test/quiz tương tác chờ tôi trả lời. HÃY IN RA TOÀN BỘ câu hỏi VÀ ĐÁP ÁN CHI TIẾT CÙNG LÚC để tôi tự đọc và đối chiếu)"

GIAOTRINHLINE = "Hãy viết giáo trình, code mẫu và giải thích ĐÚNG trọng tâm vào khía cạnh này."

# ─────────────────────────────────────────────
# PART 1: Non-Interactive Warning
# ─────────────────────────────────────────────

def should_add_warning(phan_num: int, total: int) -> bool:
    """Kiểm tra xem Phan X/Y có cần Non-Interactive warning không."""
    if total == 15 and phan_num >= 13:
        return True
    if total == 25 and phan_num >= 13:
        return True
    return False


def insert_non_interactive(content: str) -> tuple[str, int]:
    """Chèn Non-Interactive warning vào đúng vị trí."""
    # Split thành các block theo ## Day
    # Dùng lookahead để giữ nguyên dấu ## Day
    day_blocks = re.split(r'(?=## Day \d+)', content)

    result_blocks = []
    insert_count = 0

    for block in day_blocks:
        # Tìm Phan X/Y trong block này
        phan_match = re.search(r'\(Phan (\d+)/(\d+)\):', block)
        if phan_match:
            phan_num = int(phan_match.group(1))
            total    = int(phan_match.group(2))

            if should_add_warning(phan_num, total) and WARNING_LINE not in block:
                # Chèn warning sau "Hãy viết giáo trình..." + dòng trống
                # Pattern: "...khía cạnh này.\n\nYeu cau day hoc"
                # Sau khi chèn: "...khía cạnh này.\n\n(⚠️...)\n\nYeu cau day hoc"
                new_block, n = re.subn(
                    re.escape(GIAOTRINHLINE) + r'\n\n',
                    GIAOTRINHLINE + '\n\n' + WARNING_LINE + '\n\n',
                    block,
                    count=1
                )
                if n > 0:
                    block = new_block
                    insert_count += 1

        result_blocks.append(block)

    return ''.join(result_blocks), insert_count


# ─────────────────────────────────────────────
# PART 2: Định nghĩa 18 topics mới
# ─────────────────────────────────────────────

# 25 khía cạnh cho chu kỳ 25 ngày
ASPECTS_25 = [
    ("Core Concept",             "Bản chất cốt lõi, tại sao công nghệ này tồn tại, và ví dụ 'Hello World' cơ bản nhất."),
    ("Basic Syntax & Usage",     "Cú pháp nền tảng phổ biến nhất và cách dùng thông thường."),
    ("Advanced Syntax & Tricks", "Tham số ẩn, cú pháp rút gọn (syntax sugar) và các thủ thuật nâng cao."),
    ("Under the hood",           "Kiến trúc tầng thấp (Memory, Compiler, cách máy tính hiểu code này)."),
    ("Basic Error Handling",     "Bắt lỗi thông thường, exception, và các mã lỗi thường gặp."),
    ("Gotchas & Edge Cases",     "Các trường hợp dị biệt, góc khuất dễ gây bug nghiêm trọng khó tìm."),
    ("Hidden Gems",              "Các kỹ thuật/tính năng cực kỳ hữu ích nhưng ít tài liệu nhắc tới."),
    ("Anti-patterns",            "Những cách viết TỒI TỆ NHẤT, những 'red flags' tuyệt đối phải tránh khi dùng công nghệ này."),
    ("Memory Optimization",      "Quản lý bộ nhớ, ngăn chặn Memory Leak, và công cụ phân tích bộ nhớ."),
    ("Speed Performance",        "Tối ưu CPU, giảm thiểu chi phí thừa, cách viết code chạy nhanh nhất."),
    ("Scalability",              "Cấu trúc code thế nào để dễ dàng mở rộng khi dự án phình to hàng triệu dòng code."),
    ("Security",                 "Các lỗ hổng bảo mật tiềm ẩn (buffer overflow, UB khai thác được...) và cách phòng chống."),
    ("Ecosystem Integration",    "Best practices khi kết hợp với thư viện/framework/công cụ thứ 3."),          # +Warning
    ("Deep Debugging",           "Kỹ thuật gỡ lỗi chuyên sâu dùng debugger, breakpoints, và Profiler."),       # +Warning
    ("Execution Lifecycle",      "Thứ tự chạy, vòng đời đối tượng, và luồng thực thi thực tế."),              # +Warning
    ("Creational Design Patterns",  "Áp dụng các Design Pattern khởi tạo cho chủ đề này."),                    # +Warning
    ("Structural Design Patterns",  "Áp dụng các Design Pattern cấu trúc cho chủ đề này."),                    # +Warning
    ("Behavioral Design Patterns",  "Áp dụng các Design Pattern hành vi để quản lý luồng."),                   # +Warning
    ("Unit Testing",             "Cách mock/stub và viết bài test cục bộ cho tính năng này."),                 # +Warning
    ("Integration Testing",      "Viết test tích hợp luồng dữ liệu hoặc test end-to-end."),                   # +Warning
    ("CI/CD Automation",         "Cách tự động hóa kiểm tra tính năng này trên pipeline."),                    # +Warning
    ("Cross-platform Compatibility","Xử lý tương thích đa nền tảng (Windows/Linux/macOS/embedded)."),          # +Warning
    ("Open Source Analysis",     "Mổ xẻ đọc code thực tế của dự án lớn xem họ triển khai chủ đề này ra sao."), # +Warning
    ("Interview Prep (Junior/Mid)","Trả lời lý thuyết cốt lõi và giải quyết bài tập nhỏ thường gặp khi phỏng vấn."), # +Warning
    ("Interview Prep (Senior)",  "System Design, trade-offs, và trả lời các câu hỏi kiến trúc hóc búa."),      # +Warning
]

# 15 khía cạnh cho chu kỳ 15 ngày
ASPECTS_15 = ASPECTS_25[:12] + ASPECTS_25[12:15]  # Phan 1-12 giống, 13-15 là Ecosystem/Debug/Lifecycle

NEW_TOPICS = [
    # (phase_name, topic_title_ascii, topic_title_vi, cycle_days, tags_extra)
    # Advanced Core & STL — 2 topics
    (
        "Advanced Core & STL",
        "std::format va text formatting C++20/23: std::format, std::vformat, std::print",
        "std::format va text formatting C++20/23: std::format, std::vformat, std::print",
        15, "advanced_core stl formatting"
    ),
    (
        "Advanced Core & STL",
        "std::jthread va Cooperative Cancellation: stop_token, std::generator (C++23 coroutine)",
        "std::jthread va Cooperative Cancellation: stop_token, std::generator (C++23 coroutine)",
        15, "advanced_core stl jthread coroutine"
    ),
    # Systems & Performance — 2 topics
    (
        "Systems & Performance",
        "Memory-mapped files: mmap (Linux) va MapViewOfFile (Windows) cho hieu nang cao",
        "Memory-mapped files: mmap (Linux) va MapViewOfFile (Windows) cho hieu nang cao",
        15, "systems performance mmap"
    ),
    (
        "Systems & Performance",
        "Coroutine internals chuyên sâu: viet awaitable, promise type, coroutine_handle tu tay",
        "Coroutine internals chuyen sau: viet awaitable, promise type, coroutine_handle tu tay",
        15, "systems performance coroutine"
    ),
    # Embedded & Firmware — 2 topics
    (
        "Embedded & Firmware",
        "DMA va USB protocol stack tren MCU: DMA transfer, USB HID/CDC voi STM32 USB library",
        "DMA va USB protocol stack tren MCU: DMA transfer, USB HID/CDC voi STM32 USB library",
        15, "embedded firmware dma usb"
    ),
    (
        "Embedded & Firmware",
        "Ethernet va lwIP TCP/IP stack cho embedded: eth driver, DHCP, HTTP server tren MCU",
        "Ethernet va lwIP TCP/IP stack cho embedded: eth driver, DHCP, HTTP server tren MCU",
        15, "embedded firmware ethernet lwip"
    ),
    # Graphics & Game Dev — 3 topics
    (
        "Graphics & Game Dev",
        "Animation systems: skeletal animation, blend trees, Inverse Kinematics trong C++",
        "Animation systems: skeletal animation, blend trees, Inverse Kinematics trong C++",
        15, "graphics game animation ik"
    ),
    (
        "Graphics & Game Dev",
        "Game networking: lag compensation, rollback netcode, deterministic lockstep trong C++",
        "Game networking: lag compensation, rollback netcode, deterministic lockstep trong C++",
        15, "graphics game networking rollback"
    ),
    (
        "Graphics & Game Dev",
        "Metal API (Apple): command buffer, pipeline state, render pass cho iOS/macOS game/app",
        "Metal API (Apple): command buffer, pipeline state, render pass cho iOS/macOS game/app",
        15, "graphics game metal apple"
    ),
    # Networking & Distributed — 2 topics
    (
        "Networking & Distributed",
        "HTTP/2 va HTTP/3 (QUIC) trong C++: nghttp2, libcurl nang cao, multiplexing",
        "HTTP/2 va HTTP/3 (QUIC) trong C++: nghttp2, libcurl nang cao, multiplexing",
        15, "networking http2 http3 quic"
    ),
    (
        "Networking & Distributed",
        "io_uring (Linux): modern async I/O API thay the epoll, zero-copy, high-throughput server",
        "io_uring (Linux): modern async I/O API thay the epoll, zero-copy, high-throughput server",
        15, "networking iouring async"
    ),
    # Specialized (gồm cả AI/LLM, Database) — 6 topics
    (
        "Specialized",
        "Machine Learning inference trong C++: ONNX Runtime, TensorFlow Lite C++ API, OpenVINO",
        "Machine Learning inference trong C++: ONNX Runtime, TensorFlow Lite C++ API, OpenVINO",
        15, "specialized ml inference onnx"
    ),
    (
        "Specialized",
        "Computer Vision voi OpenCV C++: image processing, feature detection, camera calibration",
        "Computer Vision voi OpenCV C++: image processing, feature detection, camera calibration",
        15, "specialized cv opencv"
    ),
    (
        "Specialized",
        "Signal Processing (DSP) trong C++: FFT, FIR/IIR filters, KISSFFT, vung dung audio/RF",
        "Signal Processing (DSP) trong C++: FFT, FIR/IIR filters, KISSFFT, vung dung audio/RF",
        15, "specialized dsp fft"
    ),
    (
        "Specialized",
        "Database tu C++: SQLite C++ API (SQLiteCpp), libpqxx (PostgreSQL), connection pooling",
        "Database tu C++: SQLite C++ API (SQLiteCpp), libpqxx (PostgreSQL), connection pooling",
        15, "specialized database sqlite postgresql"
    ),
    (
        "Specialized",
        "LLM Inference trong C++: llama.cpp internals, GGUF format, KV-cache, quantization",
        "LLM Inference trong C++: llama.cpp internals, GGUF format, KV-cache, quantization",
        15, "specialized llm llamacpp inference"
    ),
    (
        "Specialized",
        "GPU Computing tu C++: CUDA kernels, memory model, ROCm (AMD), thrust library",
        "GPU Computing tu C++: CUDA kernels, memory model, ROCm (AMD), thrust library",
        15, "specialized cuda rocm gpu"
    ),
    # Documentation & Tooling — 1 topic
    (
        "Documentation & Tooling",
        "Google Benchmark va Valgrind deep dive: micro-benchmark, Callgrind, Cachegrind profiling",
        "Google Benchmark va Valgrind deep dive: micro-benchmark, Callgrind, Cachegrind profiling",
        15, "tooling benchmark valgrind"
    ),
]


def make_day_block(day_num: int, phase: str, topic: str, phan: int, total: int,
                   aspect_name: str, aspect_desc: str,
                   phase_short: str, tags_extra: str) -> str:
    """Tạo nội dung 1 Day theo đúng format chuẩn."""

    # Xác định có cần Non-Interactive không
    add_warning = should_add_warning(phan, total)
    warning_block = (
        "\n" + WARNING_LINE + "\n"
    ) if add_warning else ""

    # Xây dựng bài tập section
    baitap_short = aspect_name
    baitap_detail = f"{aspect_name}: {aspect_desc}"

    return f"""## Day {day_num} — [{phase}] {topic} (Phan {phan}/{total})
**Prompt:**
Day {day_num} trong lo trinh C++ 3350 ngay.
Chuyen de: [Phase - {phase}] — {topic} (Phan {phan}/{total}).
Trinh do hien tai: Xem cac ngay truoc de biet nguoi hoc dang o dau trong lo trinh.

**Yêu cầu ĐẶC BIỆT cho (Phan {phan}/{total}):**
Hôm nay, BẮT BUỘC bỏ qua các phần lý thuyết chung chung đã học. Hãy tập trung 100% vào khía cạnh sau: **[{aspect_name}: {aspect_desc}]**
Hãy viết giáo trình, code mẫu và giải thích ĐÚNG trọng tâm vào khía cạnh này.
{warning_block}
Yeu cau day hoc (30-60 phut):
1. GIAI THICH TRỌNG TÂM: Giải thích ngắn gọn nhưng ĐÚNG vào khía cạnh được yêu cầu.
2. CODE MẪU CHUYÊN SÂU: Đoạn code C++ ví dụ tập trung trực tiếp vào khía cạnh hôm nay, comment từng dòng.
3. ÁP DỤNG THỰC TẾ: Khía cạnh này được sử dụng thế nào trong dự án production (bao gồm embedded/firmware nếu liên quan)?

Bai tap (3 cap do, tu lam truoc khi xem dap an):
- Bai 1 (Co ban): Hieu va go lai vi du co ban theo huong tiep can hom nay.
- Bai 2 (Trung cap): Mo rong tinh nang hoac toi uu code.
- Bai 3 (Nang cao): Ap dung vao 1 mini-project/module thu nghiem (bien dich thu tren compiler that).

**Bài tập:**
- Bài 1 (Cơ bản): Hoàn thành ví dụ cơ bản về [{baitap_detail}].
- Bài 2 (Trung cấp): Mở rộng code và xử lý edge cases cho [{baitap_detail}].
- Bài 3 (Nâng cao): Áp dụng [{baitap_detail}] vào mini-project/module thực tế.

**Tags:** #cpp #day{day_num} #{phase_short} #{tags_extra.split()[0] if tags_extra else phase_short}

---

"""


def generate_new_days(start_day: int) -> str:
    """Sinh nội dung cho 18 topics mới (270 Day)."""
    output = ""
    current_day = start_day

    for (phase, topic_ascii, topic_vi, cycle_days, tags_extra) in NEW_TOPICS:
        # phase_short dùng cho tags
        phase_short = phase.lower().replace(" ", "_").replace("&", "").replace(",", "").replace("__", "_")

        # Chọn aspect list phù hợp
        if cycle_days == 15:
            aspects = ASPECTS_15
        elif cycle_days == 25:
            aspects = ASPECTS_25
        else:
            aspects = ASPECTS_15

        for phan_idx in range(cycle_days):
            phan     = phan_idx + 1
            asp_name, asp_desc = aspects[phan_idx]
            block = make_day_block(
                day_num     = current_day,
                phase       = phase,
                topic       = topic_ascii,
                phan        = phan,
                total       = cycle_days,
                aspect_name = asp_name,
                aspect_desc = asp_desc,
                phase_short = phase_short,
                tags_extra  = tags_extra,
            )
            output += block
            current_day += 1

    return output, current_day - 1  # trả về last day number


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    print(f"Đọc file: {INPUT_FILE}")
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    original_day_count = len(re.findall(r'^## Day \d+', content, re.MULTILINE))
    print(f"Số Day hiện tại: {original_day_count}")

    # ── Bước 1: Cập nhật header 3080 → 3350 ──
    print("Bước 1: Cập nhật header file...")
    content = content.replace("3080 Ngay", "3350 Ngay", 1)
    content = content.replace("3080 ngay", "3350 ngay")
    content = content.replace("C++ 3080 ngay", "C++ 3350 ngay")
    # Cập nhật trong mỗi prompt
    content = content.replace(
        "lo trinh C++ 3080 ngay.",
        "lo trinh C++ 3350 ngay."
    )

    # ── Bước 2: Chèn Non-Interactive warning ──
    print("Bước 2: Chèn Non-Interactive warning...")
    content, insert_count = insert_non_interactive(content)
    print(f"  → Đã chèn warning vào {insert_count} Day")

    # ── Bước 3: Append 18 topics mới ──
    print("Bước 3: Sinh và append 18 topics mới...")
    new_days_content, last_day = generate_new_days(start_day=3081)
    days_added = last_day - 3080
    content = content.rstrip() + "\n\n" + new_days_content
    print(f"  → Đã thêm {days_added} Day mới (Day 3081 → {last_day})")

    # ── Bước 4: Ghi file ──
    print(f"Bước 4: Ghi file ra {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(content)

    # ── Bước 5: Verify ──
    print("\n=== VERIFY ===")
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        verify_content = f.read()

    total_days    = len(re.findall(r'^## Day \d+', verify_content, re.MULTILINE))
    total_warning = len(re.findall(re.escape(WARNING_LINE), verify_content))
    total_prompt  = len(re.findall(r'^\*\*Prompt:\*\*', verify_content, re.MULTILINE))
    total_tags    = len(re.findall(r'^\*\*Tags:\*\*', verify_content, re.MULTILINE))
    total_baitap  = len(re.findall(r'^\*\*Bài tập:\*\*', verify_content, re.MULTILINE))

    print(f"  Tổng Day:            {total_days}")
    print(f"  **Prompt:**          {total_prompt}")
    print(f"  **Bài tập:**         {total_baitap}")
    print(f"  **Tags:**            {total_tags}")
    print(f"  Non-Interactive:     {total_warning}")
    print(f"  File size:           {os.path.getsize(OUTPUT_FILE)/1024/1024:.2f} MB")

    # Check missing days
    day_nums = sorted([int(m) for m in re.findall(r'^## Day (\d+)', verify_content, re.MULTILINE)])
    missing  = [i for i in range(1, total_days + 1) if i not in day_nums]
    if missing:
        print(f"\n  ⚠️  THIẾU {len(missing)} Day: {missing[:10]}...")
    else:
        print(f"\n  ✅ Không thiếu Day nào!")

    print("\nHoàn thành!")


if __name__ == "__main__":
    main()
