window.MBC_DEFAULT_DATABASE = {
  "version": "3.7",
  "currentUser": {
    "id": "admin",
    "name": "Quản trị viên (Admin)",
    "role": "admin",
    "dept": "Ban Quản Trị"
  },
  "holidays": [
    { "date": "2026-01-01", "name": "Tết Dương Lịch 2026", "type": "NATIONAL" },
    { "date": "2026-02-16", "name": "Tết Nguyên Đán (29 Tết)", "type": "NATIONAL" },
    { "date": "2026-02-17", "name": "Tết Nguyên Đán (Mùng 1)", "type": "NATIONAL" },
    { "date": "2026-02-18", "name": "Tết Nguyên Đán (Mùng 2)", "type": "NATIONAL" },
    { "date": "2026-02-19", "name": "Tết Nguyên Đán (Mùng 3)", "type": "NATIONAL" },
    { "date": "2026-02-20", "name": "Tết Nguyên Đán (Mùng 4)", "type": "NATIONAL" },
    { "date": "2026-04-26", "name": "Giỗ Tổ Hùng Vương", "type": "NATIONAL" },
    { "date": "2026-04-30", "name": "Ngày Giải Phóng Miền Nam", "type": "NATIONAL" },
    { "date": "2026-05-01", "name": "Quốc Tế Lao Động", "type": "NATIONAL" },
    { "date": "2026-09-02", "name": "Quốc Khánh 2/9", "type": "NATIONAL" },
    { "date": "2026-09-03", "name": "Nghỉ Quốc Khánh", "type": "NATIONAL" }
  ],
  "employees": [
    { "id": "NV01", "name": "Nguyễn Quang Thảo",  "dept": "Kỹ thuật - Bảo trì" },
    { "id": "NV02", "name": "Trần Văn Bình",       "dept": "Vận hành - Cơ khí" },
    { "id": "NV03", "name": "Lê Thị Thu",           "dept": "Quản lý chất lượng (QC)" },
    { "id": "NV04", "name": "Phạm Đức Minh",        "dept": "Kỹ thuật điện - Tự động hóa" },
    { "id": "NV05", "name": "Hoàng Hải Yến",        "dept": "Kế hoạch sản xuất" }
  ],
  "tasks": [

    // ═══════════════════════════════════════════════════════════════
    // NHÓM 1: Bảo dưỡng đầu năm hệ thống điện (T1/2026) ─ HOÀN THÀNH
    // ═══════════════════════════════════════════════════════════════
    {
      "id": "CV-2026-0001",
      "mainTaskId": "CV-DIEN-2026",
      "mainTaskTitle": "Bảo dưỡng đầu năm hệ thống điện",
      "title": "Bảo dưỡng đầu năm hệ thống điện",
      "detail": "GĐ 1: Kiểm tra trạm biến áp 560 kVA và đo điện trở tiếp địa",
      "empId": "NV04",
      "empName": "Phạm Đức Minh",
      "startDate": "2026-01-05",
      "planDays": 5,
      "planEndDate": "2026-01-09",
      "actualEndDate": "2026-01-09",
      "status": "Hoàn thành",
      "link": "file:///C:/MBC/HoSoBaoTri/TramBienAp/",
      "note": "Điện trở tiếp địa đạt chuẩn < 4 Ω"
    },
    {
      "id": "CV-2026-0002",
      "mainTaskId": "CV-DIEN-2026",
      "mainTaskTitle": "Bảo dưỡng đầu năm hệ thống điện",
      "title": "Bảo dưỡng đầu năm hệ thống điện",
      "detail": "GĐ 2: Thay thế CB tổng tủ MSB và hiệu chỉnh rơ-le bảo vệ",
      "empId": "NV04",
      "empName": "Phạm Đức Minh",
      "startDate": "2026-01-10",
      "planDays": 4,
      "planEndDate": "2026-01-13",
      "actualEndDate": "2026-01-14",
      "status": "Hoàn thành trễ",
      "note": "Chậm 1 ngày do CB nhập khẩu giao muộn"
    },
    {
      "id": "CV-2026-0003",
      "mainTaskId": "CV-DIEN-2026",
      "mainTaskTitle": "Bảo dưỡng đầu năm hệ thống điện",
      "title": "Bảo dưỡng đầu năm hệ thống điện",
      "detail": "GĐ 3: Nghiệm thu cấp điện toàn phân xưởng và bàn giao",
      "empId": "NV04",
      "empName": "Phạm Đức Minh",
      "startDate": "2026-01-15",
      "planDays": 2,
      "planEndDate": "2026-01-16",
      "actualEndDate": "2026-01-16",
      "status": "Hoàn thành",
      "note": "Hệ thống điện ổn định, không sự cố"
    },

    // ═══════════════════════════════════════════════════════════════
    // NHÓM 2: Đại tu máy tiện CNC-01 (T2-T3/2026) ─ HOÀN THÀNH
    // ═══════════════════════════════════════════════════════════════
    {
      "id": "CV-2026-0004",
      "mainTaskId": "CV-CNC-2026",
      "mainTaskTitle": "Đại tu máy tiện CNC-01",
      "title": "Đại tu máy tiện CNC-01",
      "detail": "GĐ 1: Tháo máy, vệ sinh toàn bộ bộ truyền động trục chính",
      "empId": "NV01",
      "empName": "Nguyễn Quang Thảo",
      "startDate": "2026-02-20",
      "planDays": 7,
      "planEndDate": "2026-02-26",
      "actualEndDate": "2026-02-26",
      "status": "Hoàn thành",
      "note": "Phát hiện vòng bi trục Z mòn nặng, đặt mua thêm"
    },
    {
      "id": "CV-2026-0005",
      "mainTaskId": "CV-CNC-2026",
      "mainTaskTitle": "Đại tu máy tiện CNC-01",
      "title": "Đại tu máy tiện CNC-01",
      "detail": "GĐ 2: Thay vòng bi trục chính + căn chỉnh độ đảo trục Z",
      "empId": "NV01",
      "empName": "Nguyễn Quang Thảo",
      "startDate": "2026-03-02",
      "planDays": 5,
      "planEndDate": "2026-03-06",
      "actualEndDate": "2026-03-08",
      "status": "Hoàn thành trễ",
      "note": "Chậm 2 ngày chờ nhập vòng bi SKF đúng chủng loại"
    },
    {
      "id": "CV-2026-0006",
      "mainTaskId": "CV-CNC-2026",
      "mainTaskTitle": "Đại tu máy tiện CNC-01",
      "title": "Đại tu máy tiện CNC-01",
      "detail": "GĐ 3: Chạy thử gia công mẫu, kiểm tra dung sai và nghiệm thu",
      "empId": "NV01",
      "empName": "Nguyễn Quang Thảo",
      "startDate": "2026-03-09",
      "planDays": 3,
      "planEndDate": "2026-03-11",
      "actualEndDate": "2026-03-11",
      "status": "Hoàn thành",
      "note": "Độ chính xác đạt dung sai ±0.005 mm — đạt yêu cầu"
    },

    // ═══════════════════════════════════════════════════════════════
    // NHÓM 3: Cải tiến hệ thống làm mát PX2 (T4-T5/2026) ─ HT + HT TRỄHOÀN THÀNH
    // ═══════════════════════════════════════════════════════════════
    {
      "id": "CV-2026-0007",
      "mainTaskId": "CV-COOL-2026",
      "mainTaskTitle": "Cải tiến hệ thống làm mát phân xưởng 2",
      "title": "Cải tiến hệ thống làm mát phân xưởng 2",
      "detail": "GĐ 1: Khảo sát và thiết kế đường ống cấp nước giải nhiệt Chiller",
      "empId": "NV02",
      "empName": "Trần Văn Bình",
      "startDate": "2026-04-10",
      "planDays": 5,
      "planEndDate": "2026-04-14",
      "actualEndDate": "2026-04-14",
      "status": "Hoàn thành",
      "note": "Bản vẽ thiết kế được phê duyệt ngày 14/4"
    },
    {
      "id": "CV-2026-0008",
      "mainTaskId": "CV-COOL-2026",
      "mainTaskTitle": "Cải tiến hệ thống làm mát phân xưởng 2",
      "title": "Cải tiến hệ thống làm mát phân xưởng 2",
      "detail": "GĐ 2: Lắp đặt đường ống và đấu nối máy bơm tuần hoàn",
      "empId": "NV02",
      "empName": "Trần Văn Bình",
      "startDate": "2026-05-05",
      "planDays": 7,
      "planEndDate": "2026-05-11",
      "actualEndDate": "2026-05-14",
      "status": "Hoàn thành trễ",
      "note": "Chậm 3 ngày do mưa lớn ngập mương cáp điện"
    },
    {
      "id": "CV-2026-0009",
      "mainTaskId": "CV-COOL-2026",
      "mainTaskTitle": "Cải tiến hệ thống làm mát phân xưởng 2",
      "title": "Cải tiến hệ thống làm mát phân xưởng 2",
      "detail": "GĐ 3: Hiệu chỉnh lưu lượng + cân bằng nhiệt độ và nghiệm thu",
      "empId": "NV02",
      "empName": "Trần Văn Bình",
      "startDate": "2026-05-15",
      "planDays": 3,
      "planEndDate": "2026-05-17",
      "actualEndDate": "2026-05-17",
      "status": "Hoàn thành",
      "note": "Nhiệt độ PX2 giảm từ 38°C xuống 29°C — đạt mục tiêu"
    },

    // ═══════════════════════════════════════════════════════════════
    // NHÓM 4: Kiểm toán ISO 9001 (T6-T7/2026) ─ HOÀN THÀNH
    // ═══════════════════════════════════════════════════════════════
    {
      "id": "CV-2026-0010",
      "mainTaskId": "CV-ISO-2026",
      "mainTaskTitle": "Kiểm toán chất lượng nội bộ ISO 9001",
      "title": "Kiểm toán chất lượng nội bộ ISO 9001",
      "detail": "GĐ 1: Lập kế hoạch kiểm toán và chuẩn bị tài liệu quy trình",
      "empId": "NV03",
      "empName": "Lê Thị Thu",
      "startDate": "2026-06-20",
      "planDays": 5,
      "planEndDate": "2026-06-24",
      "actualEndDate": "2026-06-24",
      "status": "Hoàn thành",
      "note": "Danh mục 38 điểm kiểm tra đã được phê duyệt"
    },
    {
      "id": "CV-2026-0011",
      "mainTaskId": "CV-ISO-2026",
      "mainTaskTitle": "Kiểm toán chất lượng nội bộ ISO 9001",
      "title": "Kiểm toán chất lượng nội bộ ISO 9001",
      "detail": "GĐ 2: Đánh giá quy trình kiểm soát sai hỏng chuyền dập",
      "empId": "NV03",
      "empName": "Lê Thị Thu",
      "startDate": "2026-07-10",
      "planDays": 4,
      "planEndDate": "2026-07-13",
      "actualEndDate": "2026-07-13",
      "status": "Hoàn thành",
      "note": "Không phát hiện lỗi không phù hợp nặng (Major NC: 0)"
    },
    {
      "id": "CV-2026-0012",
      "mainTaskId": "CV-ISO-2026",
      "mainTaskTitle": "Kiểm toán chất lượng nội bộ ISO 9001",
      "title": "Kiểm toán chất lượng nội bộ ISO 9001",
      "detail": "GĐ 3: Lập báo cáo kiểm toán và theo dõi hành động khắc phục",
      "empId": "NV03",
      "empName": "Lê Thị Thu",
      "startDate": "2026-07-14",
      "planDays": 5,
      "planEndDate": "2026-07-18",
      "actualEndDate": "2026-07-20",
      "status": "Hoàn thành trễ",
      "note": "Chậm 2 ngày chờ phòng sản xuất phản hồi biên bản"
    },

    // ═══════════════════════════════════════════════════════════════
    // NHÓM 5: Bảo dưỡng trung tu máy ép 200T (T8/2026) ─ HOÀN THÀNH
    // ═══════════════════════════════════════════════════════════════
    {
      "id": "CV-2026-0013",
      "mainTaskId": "CV-EP200-2026",
      "mainTaskTitle": "Bảo dưỡng trung tu máy ép 200T",
      "title": "Bảo dưỡng trung tu máy ép 200T",
      "detail": "GĐ 1: Vệ sinh van servo và đường ống dầu thủy lực",
      "empId": "NV02",
      "empName": "Trần Văn Bình",
      "startDate": "2026-08-15",
      "planDays": 4,
      "planEndDate": "2026-08-18",
      "actualEndDate": "2026-08-18",
      "status": "Hoàn thành",
      "note": "Độ nhớt dầu thủy lực đạt ISO VG 46"
    },
    {
      "id": "CV-2026-0014",
      "mainTaskId": "CV-EP200-2026",
      "mainTaskTitle": "Bảo dưỡng trung tu máy ép 200T",
      "title": "Bảo dưỡng trung tu máy ép 200T",
      "detail": "GĐ 2: Thay dầu tuần hoàn và thử tải áp suất 210 bar",
      "empId": "NV02",
      "empName": "Trần Văn Bình",
      "startDate": "2026-08-19",
      "planDays": 4,
      "planEndDate": "2026-08-22",
      "actualEndDate": "2026-08-22",
      "status": "Hoàn thành",
      "note": "Lực ép chuẩn 200T, không rò rỉ"
    },

    // ═══════════════════════════════════════════════════════════════
    // NHÓM 6: Sửa chữa máy TUM (T9-T10/2026) ─ HỖN HỢP
    // ═══════════════════════════════════════════════════════════════
    {
      "id": "CV-2026-0015",
      "mainTaskId": "CV-TUM-2026",
      "mainTaskTitle": "Sửa chữa máy TUM",
      "title": "Sửa chữa máy TUM",
      "detail": "GĐ 1: Xác nhận tình trạng linh kiện và hệ thống bôi trơn",
      "empId": "NV01",
      "empName": "Nguyễn Quang Thảo",
      "startDate": "2026-10-01",
      "planDays": 2,
      "planDuration": 2,
      "planUnit": "ngày",
      "planEndDate": "2026-10-02",
      "actualEndDate": "2026-10-02",
      "status": "Hoàn thành",
      "taskSource": "Cải tiến",
      "link": "https://drive.google.com/drive/folders/mbc-tum-2026",
      "note": "Đã kiểm tra và thay thế 3 linh kiện đạt chuẩn"
    },
    {
      "id": "CV-2026-0016",
      "mainTaskId": "CV-TUM-2026",
      "mainTaskTitle": "Sửa chữa máy TUM",
      "title": "Sửa chữa máy TUM",
      "detail": "GĐ 2: Thay van áp suất và cảm biến nhiệt độ",
      "empId": "NV01",
      "empName": "Nguyễn Quang Thảo",
      "startDate": "2026-10-03",
      "planDays": 2,
      "planDuration": 2,
      "planUnit": "ngày",
      "planEndDate": "2026-10-04",
      "actualEndDate": "2026-10-05",
      "status": "Hoàn thành trễ",
      "taskSource": "Đối ứng",
      "note": "Phụ tùng giao muộn 1 ngày"
    },
    {
      "id": "CV-2026-0017",
      "mainTaskId": "CV-TUM-2026",
      "mainTaskTitle": "Sửa chữa máy TUM",
      "title": "Sửa chữa máy TUM",
      "detail": "GĐ 3: Chạy rà tải và bàn giao vận hành",
      "empId": "NV01",
      "empName": "Nguyễn Quang Thảo",
      "startDate": "2026-10-06",
      "planDays": 3,
      "planDuration": 3,
      "planUnit": "ngày",
      "planEndDate": "2026-10-08",
      "actualEndDate": "",
      "status": "Đang làm",
      "taskSource": "Trưởng phòng",
      "note": "Đang chạy rà đồ gá, kiểm tra rung",
      "lastStatusUpdate": "2026-10-08",
      "statusLogs": [
        {
          "date": "2026-10-08",
          "note": "Đang chạy rà đồ gá, kiểm tra rung và cân bằng động",
          "status": "Đang làm",
          "progress": 70,
          "author": "Nguyễn Quang Thảo"
        }
      ]
    },

    // ═══════════════════════════════════════════════════════════════
    // NHÓM 7: Sửa máy INEX (T10/2026) ─ TẠM DỪNG
    // ═══════════════════════════════════════════════════════════════
    {
      "id": "CV-2026-0019",
      "mainTaskId": "CV-INEX-2026",
      "mainTaskTitle": "Sửa máy INEX — Lỗi board điều khiển",
      "title": "Sửa máy INEX — Lỗi board điều khiển",
      "detail": "GĐ 1: Chẩn đoán lỗi mạch cảm biến encoder trục Y",
      "empId": "NV02",
      "empName": "Trần Văn Bình",
      "startDate": "2026-10-01",
      "planDays": 2,
      "planEndDate": "2026-10-02",
      "actualEndDate": "",
      "status": "Tạm dừng",
      "note": "Tạm dừng chờ linh kiện board nhập khẩu từ Nhật"
    },
    {
      "id": "CV-2026-0020",
      "mainTaskId": "CV-INEX-2026",
      "mainTaskTitle": "Sửa máy INEX — Lỗi board điều khiển",
      "title": "Sửa máy INEX — Lỗi board điều khiển",
      "detail": "GĐ 2: Thay board điều khiển và lập trình lại thông số PLC",
      "empId": "NV02",
      "empName": "Trần Văn Bình",
      "startDate": "2026-10-15",
      "planDays": 3,
      "planEndDate": "2026-10-17",
      "actualEndDate": "",
      "status": "Tạm dừng",
      "note": "Đang chờ board về kho — dự kiến 20/10"
    },

    // ═══════════════════════════════════════════════════════════════
    // NHÓM 8: Lắp biến tần Motor 3 (T10/2026) ─ ĐANG LÀM + QUÁ HẠN
    // ═══════════════════════════════════════════════════════════════
    {
      "id": "CV-2026-0021",
      "mainTaskId": "CV-BIEN-TAN-2026",
      "mainTaskTitle": "Lắp đặt tủ biến tần Motor 3",
      "title": "Lắp đặt tủ biến tần Motor 3",
      "detail": "GĐ 1: Lắp đặt tủ điện và đi cáp nguồn 3 pha",
      "empId": "NV04",
      "empName": "Phạm Đức Minh",
      "startDate": "2026-09-25",
      "planDays": 5,
      "planEndDate": "2026-09-29",
      "actualEndDate": "",
      "status": "Đang làm",
      "note": "Quá hạn — cáp 3 pha 70 mm² chưa về kho"
    },
    {
      "id": "CV-2026-0022",
      "mainTaskId": "CV-BIEN-TAN-2026",
      "mainTaskTitle": "Lắp đặt tủ biến tần Motor 3",
      "title": "Lắp đặt tủ biến tần Motor 3",
      "detail": "GĐ 2: Đấu nối tín hiệu PLC và kiểm tra tiếp địa an toàn",
      "empId": "NV04",
      "empName": "Phạm Đức Minh",
      "startDate": "2026-10-06",
      "planDays": 3,
      "planEndDate": "2026-10-08",
      "actualEndDate": "",
      "status": "Đang làm",
      "note": "Chờ cắt nguồn chính mới đấu nối được"
    },
    {
      "id": "CV-2026-0023",
      "mainTaskId": "CV-BIEN-TAN-2026",
      "mainTaskTitle": "Lắp đặt tủ biến tần Motor 3",
      "title": "Lắp đặt tủ biến tần Motor 3",
      "detail": "GĐ 3: Test vận hành, đặt thông số tần số và nghiệm thu",
      "empId": "NV04",
      "empName": "Phạm Đức Minh",
      "startDate": "2026-10-09",
      "planDays": 2,
      "planEndDate": "2026-10-10",
      "actualEndDate": "",
      "status": "Đang làm",
      "note": "Chờ GĐ 2 hoàn thành"
    },

    // ═══════════════════════════════════════════════════════════════
    // NHÓM 9: Nâng cấp SCADA (T11/2026) ─ ĐANG LÀM
    // ═══════════════════════════════════════════════════════════════
    {
      "id": "CV-2026-0024",
      "mainTaskId": "CV-SCADA-2026",
      "mainTaskTitle": "Nâng cấp phần mềm giám sát SCADA",
      "title": "Nâng cấp phần mềm giám sát SCADA",
      "detail": "GĐ 1: Cài đặt máy chủ SCADA mới và migrate dữ liệu tag cũ",
      "empId": "NV04",
      "empName": "Phạm Đức Minh",
      "startDate": "2026-11-03",
      "planDays": 7,
      "planEndDate": "2026-11-09",
      "actualEndDate": "",
      "status": "Đang làm",
      "note": "Đang cấu hình OPC DA → OPC UA bridge"
    },
    {
      "id": "CV-2026-0025",
      "mainTaskId": "CV-SCADA-2026",
      "mainTaskTitle": "Nâng cấp phần mềm giám sát SCADA",
      "title": "Nâng cấp phần mềm giám sát SCADA",
      "detail": "GĐ 2: Tích hợp dashboard OEE và cảnh báo theo ngưỡng thiết bị",
      "empId": "NV04",
      "empName": "Phạm Đức Minh",
      "startDate": "2026-11-10",
      "planDays": 14,
      "planEndDate": "2026-11-23",
      "actualEndDate": "",
      "status": "Đang làm",
      "note": "Đang lập trình giao diện HMI màn hình 27\""
    },

    // ═══════════════════════════════════════════════════════════════
    // NHÓM 10: Kiểm kê vật tư cuối năm (T12/2026) ─ ĐANG LÀM
    // ═══════════════════════════════════════════════════════════════
    {
      "id": "CV-2026-0026",
      "mainTaskId": "CV-KIEMKE-2026",
      "mainTaskTitle": "Kiểm kê vật tư & phụ tùng cuối năm 2026",
      "title": "Kiểm kê vật tư & phụ tùng cuối năm 2026",
      "detail": "GĐ 1: Kiểm kê vật tư tiêu hao và phụ tùng cơ khí tồn kho",
      "empId": "NV05",
      "empName": "Hoàng Hải Yến",
      "startDate": "2026-12-10",
      "planDays": 5,
      "planEndDate": "2026-12-14",
      "actualEndDate": "",
      "status": "Đang làm",
      "note": "Đang nhập phiếu xuất kho từ hệ thống ERP"
    },
    {
      "id": "CV-2026-0027",
      "mainTaskId": "CV-KIEMKE-2026",
      "mainTaskTitle": "Kiểm kê vật tư & phụ tùng cuối năm 2026",
      "title": "Kiểm kê vật tư & phụ tùng cuối năm 2026",
      "detail": "GĐ 2: Đối soát số liệu tồn kho và dự trù ngân sách mua sắm 2027",
      "empId": "NV05",
      "empName": "Hoàng Hải Yến",
      "startDate": "2026-12-15",
      "planDays": 10,
      "planEndDate": "2026-12-24",
      "actualEndDate": "",
      "status": "Đang làm",
      "note": "Chuẩn bị chốt sổ cuối năm"
    },

    // ═══════════════════════════════════════════════════════════════
    // NHÓM 11: Kiểm định thiết bị đo lường (T10/2026) ─ QUÁ HẠN
    // ═══════════════════════════════════════════════════════════════
    {
      "id": "CV-2026-0028",
      "mainTaskId": "CV-KIEM-DINH-2026",
      "mainTaskTitle": "Kiểm định & hiệu chuẩn thiết bị đo lường",
      "title": "Kiểm định & hiệu chuẩn thiết bị đo lường",
      "detail": "GĐ 1: Gửi mẫu thước kẹp điện tử và đồng hồ so ra phòng kiểm định",
      "empId": "NV03",
      "empName": "Lê Thị Thu",
      "startDate": "2026-09-20",
      "planDays": 7,
      "planEndDate": "2026-09-26",
      "actualEndDate": "",
      "status": "Đang làm",
      "note": "Phòng kiểm định bận — dời lịch sang tuần sau"
    },
    {
      "id": "CV-2026-0029",
      "mainTaskId": "CV-KIEM-DINH-2026",
      "mainTaskTitle": "Kiểm định & hiệu chuẩn thiết bị đo lường",
      "title": "Kiểm định & hiệu chuẩn thiết bị đo lường",
      "detail": "GĐ 2: Nhận kết quả, cập nhật tem hiệu chuẩn và lưu hồ sơ",
      "empId": "NV03",
      "empName": "Lê Thị Thu",
      "startDate": "2026-10-04",
      "planDays": 4,
      "planEndDate": "2026-10-07",
      "actualEndDate": "",
      "status": "Đang làm",
      "note": "Đang gửi mẫu đợt 2 — quá hạn 2 ngày"
    },

    // ═══════════════════════════════════════════════════════════════
    // NHÓM 12: Lắp dây chuyền dập tự động 2027 ─ DỪNG DỰ ÁN + ĐANG LÀM
    // ═══════════════════════════════════════════════════════════════
    {
      "id": "CV-2027-0001",
      "mainTaskId": "CV-LINE-2027",
      "mainTaskTitle": "Lắp đặt dây chuyền dập tự động 2027",
      "title": "Lắp đặt dây chuyền dập tự động 2027",
      "detail": "GĐ 1: Khảo sát móng máy và thiết kế layout dây chuyền",
      "empId": "NV01",
      "empName": "Nguyễn Quang Thảo",
      "startDate": "2027-01-05",
      "planDays": 10,
      "planEndDate": "2027-01-14",
      "actualEndDate": "",
      "status": "Dừng dự án",
      "note": "Dừng do ngân sách chưa phê duyệt Q1/2027 — dời sang Q2"
    },
    {
      "id": "CV-2027-0002",
      "mainTaskId": "CV-LINE-2027",
      "mainTaskTitle": "Lắp đặt dây chuyền dập tự động 2027",
      "title": "Lắp đặt dây chuyền dập tự động 2027",
      "detail": "GĐ 2: Lắp đặt cánh tay robot gắp phôi và băng tải thu hồi sản phẩm",
      "empId": "NV01",
      "empName": "Nguyễn Quang Thảo",
      "startDate": "2027-04-01",
      "planDays": 20,
      "planEndDate": "2027-04-20",
      "actualEndDate": "",
      "status": "Đang làm",
      "note": "Dự án tái khởi động Q2/2027 — đang nhận máy từ nhà cung cấp"
    },
    {
      "id": "CV-2027-0003",
      "mainTaskId": "CV-LINE-2027",
      "mainTaskTitle": "Lắp đặt dây chuyền dập tự động 2027",
      "title": "Lắp đặt dây chuyền dập tự động 2027",
      "detail": "GĐ 3: Lập trình PLC dây chuyền và tích hợp SCADA nhà máy",
      "empId": "NV04",
      "empName": "Phạm Đức Minh",
      "startDate": "2027-04-21",
      "planDays": 30,
      "planEndDate": "2027-05-20",
      "actualEndDate": "",
      "status": "Đang làm",
      "note": "Đang lập trình logic điều khiển robot Fanuc"
    },
    {
      "id": "CV-2027-0004",
      "mainTaskId": "CV-LINE-2027",
      "mainTaskTitle": "Lắp đặt dây chuyền dập tự động 2027",
      "title": "Lắp đặt dây chuyền dập tự động 2027",
      "detail": "GĐ 4: Chạy thử, đào tạo vận hành và nghiệm thu bàn giao",
      "empId": "NV05",
      "empName": "Hoàng Hải Yến",
      "startDate": "2027-05-21",
      "planDays": 14,
      "planEndDate": "2027-06-03",
      "actualEndDate": "",
      "status": "Đang làm",
      "note": "Kế hoạch nghiệm thu trước 5/6/2027"
    }
  ]
};
