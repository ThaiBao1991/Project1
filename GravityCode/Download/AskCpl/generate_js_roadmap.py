# Generate JS Roadmap - 15-Day Ultimate Mastery Cycle
filepath = r"c:\Users\games\Desktop\Project\Python\Python MyWork\Project1\GravityCode\Download\AskCpl\roadmap_javascript_7years.md"

def build_roadmap():
    roadmap = []
    day = 1

    def add_topic(section, topic, tags, days):
        nonlocal day
        for i in range(1, days + 1):
            roadmap.append((day, section, topic, tags, i, days))
            day += 1

    # -- Foundation
    add_topic("Phase - Foundation", "Biến & kiểu dữ liệu", "#foundation #js #dom", 15)
    add_topic("Phase - Foundation", "Hàm", "#foundation #js #dom", 15)
    add_topic("Phase - Foundation", "DOM", "#foundation #js #dom", 15)
    add_topic("Phase - Foundation", "Event", "#foundation #js #dom", 15)
    add_topic("Phase - Foundation", "Async/Await", "#foundation #js #dom", 15)
    add_topic("Phase - Foundation", "ES6+", "#foundation #js #dom", 15)
    add_topic("Phase - Foundation", "Fetch API", "#foundation #js #dom", 15)

    # -- Core JS nâng cao
    add_topic("Phase - Core JS nâng cao", "Closure", "#core #advanced", 30)
    add_topic("Phase - Core JS nâng cao", "Prototype", "#core #advanced", 30)
    add_topic("Phase - Core JS nâng cao", "Event loop", "#core #advanced", 30)
    add_topic("Phase - Core JS nâng cao", "V8 engine", "#core #advanced", 30)
    add_topic("Phase - Core JS nâng cao", "Memory", "#core #advanced", 30)
    add_topic("Phase - Core JS nâng cao", "Design Pattern", "#core #advanced", 30)
    add_topic("Phase - Core JS nâng cao", "Regex", "#core #advanced", 30)

    # -- Thuật toán & DSA
    add_topic("Phase - Thuật toán & DSA", "Big O", "#dsa #algorithm", 30)
    add_topic("Phase - Thuật toán & DSA", "Array/LinkedList", "#dsa #algorithm", 30)
    add_topic("Phase - Thuật toán & DSA", "Tree/Graph", "#dsa #algorithm", 30)
    add_topic("Phase - Thuật toán & DSA", "Sorting", "#dsa #algorithm", 30)
    add_topic("Phase - Thuật toán & DSA", "DP", "#dsa #algorithm", 30)
    add_topic("Phase - Thuật toán & DSA", "Recursion", "#dsa #algorithm", 30)

    # -- Ôn tập + Capstone 1
    add_topic("Phase - Ôn tập + Capstone 1", "Dự án tổng hợp: xây CLI tool thuật toán", "#capstone #project", 15)

    # -- TypeScript
    add_topic("Phase - TypeScript", "Types", "#typescript #types", 30)
    add_topic("Phase - TypeScript", "Interface", "#typescript #types", 30)
    add_topic("Phase - TypeScript", "Generic", "#typescript #types", 30)
    add_topic("Phase - TypeScript", "Decorator", "#typescript #types", 30)
    add_topic("Phase - TypeScript", "tsconfig", "#typescript #types", 30)
    add_topic("Phase - TypeScript", "ESLint", "#typescript #types", 30)

    # -- React + Next.js
    add_topic("Phase - React + Next.js", "React", "#react #nextjs", 30)
    add_topic("Phase - React + Next.js", "Hooks", "#react #nextjs", 30)
    add_topic("Phase - React + Next.js", "Context", "#react #nextjs", 30)
    add_topic("Phase - React + Next.js", "Redux", "#react #nextjs", 30)
    add_topic("Phase - React + Next.js", "Next.js", "#react #nextjs", 30)
    add_topic("Phase - React + Next.js", "SSR/SSG", "#react #nextjs", 30)
    add_topic("Phase - React + Next.js", "TanStack", "#react #nextjs", 30)

    # -- React Native
    add_topic("Phase - React Native", "RN components", "#reactnative #mobile", 30)
    add_topic("Phase - React Native", "Navigation", "#reactnative #mobile", 30)
    add_topic("Phase - React Native", "Expo", "#reactnative #mobile", 30)
    add_topic("Phase - React Native", "Native API", "#reactnative #mobile", 30)
    add_topic("Phase - React Native", "Build & Deploy", "#reactnative #mobile", 30)

    # -- Ôn tập + Capstone 2
    add_topic("Phase - Ôn tập + Capstone 2", "Dự án: app fullstack web + mobile cùng codebase", "#capstone #fullstack", 15)

    # -- Node.js Backend
    add_topic("Phase - Node.js Backend", "Express", "#nodejs #backend", 30)
    add_topic("Phase - Node.js Backend", "REST", "#nodejs #backend", 30)
    add_topic("Phase - Node.js Backend", "GraphQL", "#nodejs #backend", 30)
    add_topic("Phase - Node.js Backend", "Auth/JWT", "#nodejs #backend", 30)
    add_topic("Phase - Node.js Backend", "Database", "#nodejs #backend", 30)
    add_topic("Phase - Node.js Backend", "Prisma", "#nodejs #backend", 30)

    # -- Security
    add_topic("Phase - Security", "XSS/CSRF", "#security #web", 15)
    add_topic("Phase - Security", "OAuth", "#security #web", 15)
    add_topic("Phase - Security", "HTTPS", "#security #web", 15)
    add_topic("Phase - Security", "Rate limit", "#security #web", 15)
    add_topic("Phase - Security", "Pentest cơ bản", "#security #web", 15)

    # -- Testing / Jest
    add_topic("Phase - Testing / Jest", "Jest", "#testing #jest", 15)
    add_topic("Phase - Testing / Jest", "TDD", "#testing #jest", 15)
    add_topic("Phase - Testing / Jest", "Cypress", "#testing #jest", 15)
    add_topic("Phase - Testing / Jest", "E2E", "#testing #jest", 15)
    add_topic("Phase - Testing / Jest", "Mock/Stub", "#testing #jest", 15)
    add_topic("Phase - Testing / Jest", "Coverage", "#testing #jest", 15)

    # -- DevOps / CI-CD
    add_topic("Phase - DevOps / CI-CD", "Docker", "#devops #cicd", 30)
    add_topic("Phase - DevOps / CI-CD", "GitHub Actions", "#devops #cicd", 30)
    add_topic("Phase - DevOps / CI-CD", "AWS/GCP", "#devops #cicd", 30)
    add_topic("Phase - DevOps / CI-CD", "Nginx", "#devops #cicd", 30)
    add_topic("Phase - DevOps / CI-CD", "Monitoring", "#devops #cicd", 30)

    # -- Ôn tập + Capstone 3
    add_topic("Phase - Ôn tập + Capstone 3", "Dự án: backend production-ready với CI/CD hoàn chỉnh", "#capstone #devops", 15)

    # -- Three.js / WebGL
    add_topic("Phase - Three.js / WebGL", "Three.js", "#threejs #webgl #3d", 30)
    add_topic("Phase - Three.js / WebGL", "WebGL", "#threejs #webgl #3d", 30)
    add_topic("Phase - Three.js / WebGL", "Shader", "#threejs #webgl #3d", 30)
    add_topic("Phase - Three.js / WebGL", "Animation", "#threejs #webgl #3d", 30)
    add_topic("Phase - Three.js / WebGL", "3D model", "#threejs #webgl #3d", 30)

    # -- Electron + Extension
    add_topic("Phase - Electron + Extension", "Electron", "#electron #extension", 30)
    add_topic("Phase - Electron + Extension", "IPC", "#electron #extension", 30)
    add_topic("Phase - Electron + Extension", "Browser Extension", "#electron #extension", 30)
    add_topic("Phase - Electron + Extension", "Chrome API", "#electron #extension", 30)
    add_topic("Phase - Electron + Extension", "Packaging", "#electron #extension", 30)

    # -- Video / Audio
    add_topic("Phase - Video / Audio", "Web Audio API", "#media #video #audio", 15)
    add_topic("Phase - Video / Audio", "MediaStream", "#media #video #audio", 15)
    add_topic("Phase - Video / Audio", "Canvas video", "#media #video #audio", 15)
    add_topic("Phase - Video / Audio", "FFmpeg.wasm", "#media #video #audio", 15)

    # -- GIS & Bản đồ
    add_topic("Phase - GIS & Bản đồ", "Leaflet", "#gis #map", 15)
    add_topic("Phase - GIS & Bản đồ", "Mapbox", "#gis #map", 15)
    add_topic("Phase - GIS & Bản đồ", "GeoJSON", "#gis #map", 15)
    add_topic("Phase - GIS & Bản đồ", "Turf.js", "#gis #map", 15)
    add_topic("Phase - GIS & Bản đồ", "OpenLayers", "#gis #map", 15)

    # -- Ôn tập + Capstone 4
    add_topic("Phase - Ôn tập + Capstone 4", "Dự án: desktop app 3D + bản đồ tương tác", "#capstone #3d #map", 15)

    # -- TensorFlow.js / AI
    add_topic("Phase - TensorFlow.js / AI", "TensorFlow.js", "#ai #tensorflowjs", 30)
    add_topic("Phase - TensorFlow.js / AI", "OCR", "#ai #tensorflowjs", 30)
    add_topic("Phase - TensorFlow.js / AI", "NLP", "#ai #tensorflowjs", 30)
    add_topic("Phase - TensorFlow.js / AI", "Computer Vision", "#ai #tensorflowjs", 30)
    add_topic("Phase - TensorFlow.js / AI", "AI Agents", "#ai #tensorflowjs", 30)
    add_topic("Phase - TensorFlow.js / AI", "MCP tools", "#ai #tensorflowjs", 30)

    # -- Multi-agent / Search
    add_topic("Phase - Multi-agent / Search", "Agent chains", "#agent #search", 15)
    add_topic("Phase - Multi-agent / Search", "Lunr.js", "#agent #search", 15)
    add_topic("Phase - Multi-agent / Search", "Recommender", "#agent #search", 15)
    add_topic("Phase - Multi-agent / Search", "Vector DB", "#agent #search", 15)
    add_topic("Phase - Multi-agent / Search", "RAG", "#agent #search", 15)

    # -- WebAssembly
    add_topic("Phase - WebAssembly", "WASM", "#wasm #webassembly", 30)
    add_topic("Phase - WebAssembly", "Rust→WASM", "#wasm #webassembly", 30)
    add_topic("Phase - WebAssembly", "AssemblyScript", "#wasm #webassembly", 30)
    add_topic("Phase - WebAssembly", "Low-level JS", "#wasm #webassembly", 30)

    # -- Blockchain / Web3
    add_topic("Phase - Blockchain / Web3", "Solidity", "#web3 #blockchain", 30)
    add_topic("Phase - Blockchain / Web3", "Ethers.js", "#web3 #blockchain", 30)
    add_topic("Phase - Blockchain / Web3", "dApp", "#web3 #blockchain", 30)
    add_topic("Phase - Blockchain / Web3", "Smart contract", "#web3 #blockchain", 30)
    add_topic("Phase - Blockchain / Web3", "IPFS", "#web3 #blockchain", 30)

    # -- Ôn tập + Capstone 5
    add_topic("Phase - Ôn tập + Capstone 5", "Dự án: AI agent tích hợp Web3 + search", "#capstone #ai #web3", 15)

    # -- Distributed Systems
    add_topic("Phase - Distributed Systems", "Microservices", "#distributed #systems", 15)
    add_topic("Phase - Distributed Systems", "Kafka", "#distributed #systems", 15)
    add_topic("Phase - Distributed Systems", "Redis", "#distributed #systems", 15)
    add_topic("Phase - Distributed Systems", "gRPC", "#distributed #systems", 15)
    add_topic("Phase - Distributed Systems", "WebSocket nâng cao", "#distributed #systems", 15)
    add_topic("Phase - Distributed Systems", "Streaming", "#distributed #systems", 15)

    # -- Compiler / Interpreter
    add_topic("Phase - Compiler / Interpreter", "AST", "#compiler #ast", 15)
    add_topic("Phase - Compiler / Interpreter", "Lexer/Parser", "#compiler #ast", 15)
    add_topic("Phase - Compiler / Interpreter", "Bytecode", "#compiler #ast", 15)
    add_topic("Phase - Compiler / Interpreter", "Custom language", "#compiler #ast", 15)
    add_topic("Phase - Compiler / Interpreter", "Babel plugin", "#compiler #ast", 15)

    # -- Reverse Engineering
    add_topic("Phase - Reverse Engineering", "Deobfuscation", "#reverse #engineering", 15)
    add_topic("Phase - Reverse Engineering", "Source map", "#reverse #engineering", 15)
    add_topic("Phase - Reverse Engineering", "Chrome DevTools", "#reverse #engineering", 15)
    add_topic("Phase - Reverse Engineering", "Minifier", "#reverse #engineering", 15)

    # -- AR/VR + Robotics
    add_topic("Phase - AR/VR + Robotics", "WebXR", "#ar #vr #robotics", 15)
    add_topic("Phase - AR/VR + Robotics", "A-Frame", "#ar #vr #robotics", 15)
    add_topic("Phase - AR/VR + Robotics", "Johnny-Five", "#ar #vr #robotics", 15)
    add_topic("Phase - AR/VR + Robotics", "IoT/MQTT", "#ar #vr #robotics", 15)
    add_topic("Phase - AR/VR + Robotics", "Robotics.js", "#ar #vr #robotics", 15)

    # -- Capstone tổng hợp
    add_topic("Phase - Capstone tổng hợp", "Thesis project", "#thesis #portfolio", 15)
    add_topic("Phase - Capstone tổng hợp", "Portfolio", "#thesis #portfolio", 15)
    add_topic("Phase - Capstone tổng hợp", "Open source", "#thesis #portfolio", 15)
    add_topic("Phase - Capstone tổng hợp", "Tech blog", "#thesis #portfolio", 15)
    add_topic("Phase - Capstone tổng hợp", "System design", "#thesis #portfolio", 15)


    return roadmap

def generate_markdown(roadmap):
    total = len(roadmap)
    md_lines = [
        "# 🚀 JavaScript — Lộ trình Từ 0 → Master Đa Nền Tảng (15-Day Mastery Cycle)",
        "",
        "> **Mục tiêu**: Làm chủ JavaScript từ cơ bản đến chuyên gia đa nền tảng (Frontend, Backend, Đồ họa 3D, Mobile, AI, Web3, Distributed System).",
        "> **Cấu trúc hoàn hảo**: Mọi chủ đề đều được rèn luyện chính xác qua 15 góc nhìn kỹ sư (Từ vỡ lòng đến Open Source, Phỏng vấn, và Mini-project).",
        ""
    ]

    focus_areas = [
        "Core Concept: Bản chất cốt lõi, tại sao công nghệ này tồn tại, và ví dụ 'Hello World' cơ bản nhất.",
        "Basic Syntax & Usage: Cú pháp nền tảng phổ biến nhất và cách dùng thông thường.",
        "Advanced Syntax & Tricks: Tham số ẩn, cú pháp rút gọn (syntax sugar) và các thủ thuật nâng cao.",
        "Under the hood: Kiến trúc tầng thấp (Memory, Compiler/Interpreter, cách máy tính hiểu code này).",
        "Execution Lifecycle: Thứ tự chạy, Event Loop, Call Stack và luồng thực thi (execution flow) thực tế.",
        "Hidden Gems: Các phương thức/tính năng cực kỳ hữu ích nhưng ít tài liệu nhắc tới.",
        "Basic Error Handling: Bắt lỗi thông thường, try/catch, và các mã lỗi thường gặp.",
        "Gotchas & Edge Cases: Các trường hợp dị biệt, góc khuất dễ gây bug nghiêm trọng khó tìm.",
        "Speed Performance: Tối ưu CPU, giảm thiểu vòng lặp thừa, cách viết code chạy nhanh nhất.",
        "Memory Optimization: Quản lý bộ nhớ, ngăn chặn Memory Leak, và Garbage Collection profiling.",
        "Scalability: Cấu trúc code thế nào để dễ dàng mở rộng (scale) khi dự án phình to hàng triệu dòng code.",
        "Security: Các lỗ hổng bảo mật tiềm ẩn (XSS, Injection, Prototype Pollution...) và cách phòng chống.",
        "Structural Design Patterns: Áp dụng các Design Pattern về mặt cấu trúc (Structural) cho chủ đề này.",
        "Behavioral Design Patterns: Áp dụng các Design Pattern về mặt hành vi (Behavioral) để quản lý luồng.",
        "Anti-patterns: Những cách viết TỒI TỆ NHẤT, những 'red flags' tuyệt đối phải tránh khi dùng công nghệ này.",
        "Unit Testing: Cách mock/stub và viết bài test cục bộ (Unit Test) cho tính năng này.",
        "Integration Testing: Viết test tích hợp luồng dữ liệu hoặc E2E test.",
        "Deep Debugging: Kỹ thuật gỡ lỗi chuyên sâu dùng DevTools, breakpoints, và Profiler.",
        "Polyfill & Compatibility: Xử lý tương thích đa môi trường (Cross-browser, phiên bản cũ, fallback).",
        "Ecosystem Integration: Best practices khi kết hợp với thư viện/framework/công cụ thứ 3.",
        "Config & Bundling: Tương tác và cấu hình với các công cụ build (Webpack, Vite, Rollup...).",
        "CI/CD Automation: Cách tự động hóa kiểm tra tính năng này trên pipeline (GitHub Actions, Jenkins).",
        "Open Source Analysis: Mổ xẻ đọc code thực tế của dự án lớn xem họ triển khai chủ đề này ra sao.",
        "Interview Prep (Junior/Mid): Trả lời lý thuyết cốt lõi và giải quyết bài tập nhỏ thường gặp khi phỏng vấn.",
        "Interview Prep (Senior): System Design, trade-offs, và trả lời các câu hỏi kiến trúc hóc búa.",
        "Reinvent the wheel (Phase 1): Tự code lại công nghệ này từ con số 0 - Phân tích và Khởi tạo cấu trúc.",
        "Reinvent the wheel (Phase 2): Tự code lại - Triển khai Core Logic cốt lõi.",
        "Capstone Phase 1: Áp dụng vào Mini-Project thực tế - Lên ý tưởng & Thiết kế kiến trúc.",
        "Capstone Phase 2: Áp dụng vào Mini-Project - Code nghiệp vụ chính và luồng dữ liệu.",
        "Capstone Phase 3: Áp dụng vào Mini-Project - Hoàn thiện, Review, Refactor và Đóng gói."
    ]

    for (day, section, topic, tags, part, total_parts) in roadmap:
        progress = f"(Phần {part}/{total_parts})"
        short_section = section.split(" - ")[1] if " - " in section else section

        md_lines.append(f"## Day {day} — [{short_section}] {topic} {progress}")
        md_lines.append("**Prompt:**")
        
        focus = focus_areas[(part - 1) % len(focus_areas)]
        
        if "Capstone" in section or "Dự án" in topic:
            prompt = f"Dạy tôi thực hành Day {day} thuộc chuỗi {section}. Trọng tâm công việc hôm nay: {topic} {progress}. Hãy đóng vai trò là một Senior Mentor, hướng dẫn tôi từng bước thực hành xây dựng cấu trúc dự án và code tính năng này. Đưa ra code cụ thể, giải thích tại sao lại thiết kế kiến trúc như vậy và chỉ ra các best practices, patterns cần lưu ý. Khía cạnh hôm nay: **[{focus}]**. Kết thúc bằng checklist 3 đầu việc để tôi tự hoàn thiện."
            exercises = "- Hoàn thành phần thiết kế và setup cơ sở dữ liệu/cấu trúc.\n- Triển khai và test tính năng chính được đề cập hôm nay.\n- Refactor code, tách hàm/component hợp lý và viết comment."
        else:
            prompt = f"Dạy tôi JavaScript Day {day}. Phần: {section}. Chủ đề hôm nay: {topic} {progress}.\n\n**Yêu cầu ĐẶC BIỆT:** (⚠️ LỆNH TỐI THƯỢNG: BẮT BUỘC bỏ qua toàn bộ lý thuyết cơ bản. KHÔNG nhắc lại khái niệm chung chung). Hãy đào cực sâu và tập trung 100% vào khía cạnh duy nhất sau: **[{focus}]**.\n\nHãy giải thích ngắn gọn, kèm theo 2 ví dụ code thực tế xoáy sâu vào khía cạnh này (1 cơ bản, 1 nâng cao). Giải thích từng dòng code."
            exercises = f"- Bài 1 (Cơ bản): Gõ lại và chạy hiểu ví dụ cơ bản về [{focus}].\n- Bài 2 (Trung cấp): Thêm logic mở rộng, bắt lỗi cho đoạn code trên.\n- Bài 3 (Nâng cao): Áp dụng [{focus}] vào một use case thực tế trong ứng dụng lớn."
        
        md_lines.append(prompt)
        md_lines.append("")
        
        if part in [13, 14, 15]:
            md_lines.append("(⚠️ QUAN TRỌNG: TUYỆT ĐỐI KHÔNG tạo bài test/quiz tương tác chờ tôi trả lời. HÃY IN RA TOÀN BỘ câu hỏi VÀ ĐÁP ÁN CHI TIẾT CÙNG LÚC để tôi tự đọc và đối chiếu)")
            md_lines.append("")

        md_lines.append("**Bài tập:**")
        md_lines.append(exercises)
        md_lines.append("")
        md_lines.append(f"**Tags:** {tags} #js #day{day}")
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

if __name__ == "__main__":
    data = build_roadmap()
    generate_markdown(data)
    print("Done JS Roadmap! Total days:", len(data))
