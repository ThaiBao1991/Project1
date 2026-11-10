---
name: ldplayer_game_pipeline
description: >
  Quy trinh toan dien ve trich xuat APK, assets, data game Android tu gia lap LDPlayer 9 qua ADB.
  Bao gom: tu dong tim dia chi port ADB, nhan dien package, pull base/split APKs, phan tich Engine (Unity Mono / IL2CPP, Cocos, Unreal),
  va trich xuat du lieu cho bot automation hoac reverse engineering.
---

# Skill: LDPlayer Game Extraction & Reverse Pipeline

## 1. Mục Đích & Bối Cảnh
Khi làm việc với các game hoặc ứng dụng Android đã cài sẵn trong giả lập LDPlayer 9 (đường dẫn mặc định `D:\LDPlayer\LDPlayer9` hoặc `C:\LDPlayer\LDPlayer9`):
- Trích xuất nhanh chóng file APK gốc (bao gồm split APKs).
- Không làm gián đoạn hay hỏng dữ liệu trong máy ảo (`data.vmdk`).
- Phân tích kiến trúc Game Engine để chọn đúng phương pháp can thiệp (IL2CPP Dumper, AssetStudio, Frida, hoặc ADB Automation).

---

## 2. Đường Dẫn & Môi Trường Chuẩn của LDPlayer 9
- **Thư mục chạy**: `D:\LDPlayer\LDPlayer9\`
- **ADB Binary**: `D:\LDPlayer\LDPlayer9\adb.exe`
- **Quản lý CLI**: `D:\LDPlayer\LDPlayer9\ldconsole.exe`
- **Cổng kết nối ADB**: Instance 0 thường lắng nghe tại `127.0.0.1:5555` hoặc hiển thị là `emulator-5554`.
- **Lưu ý Admin UAC**: `dnplayer.exe` có cờ `requireAdministrator` trong manifest, nên việc kích hoạt từ background console yêu cầu người dùng mở trực tiếp từ Desktop hoặc chạy qua process có quyền tương đương.

---

## 3. Quy Trình Trích Xuất & Phân Tích (ADB Pipeline)

### Bước 1: Kết nối ADB
```bash
& "D:\LDPlayer\LDPlayer9\adb.exe" connect 127.0.0.1:5555
& "D:\LDPlayer\LDPlayer9\adb.exe" devices
```

### Bước 2: Tìm đường dẫn APK của Package
```bash
adb shell pm path <package_name>
# Ví dụ: com.herocraft.game.mafioso.gangster.paradise.pvp
# Output có thể gồm:
# package:/data/app/.../base.apk
# package:/data/app/.../split_config.arm64_v8a.apk
```

### Bước 3: Pull APK về máy
```bash
adb pull /data/app/.../base.apk ./apk/base.apk
```

### Bước 4: Nhận diện Game Engine qua cấu trúc file
Sau khi unzip `base.apk`:
- **Unity IL2CPP**: Có `lib/arm64-v8a/libil2cpp.so` + `assets/bin/Data/Managed/Metadata/global-metadata.dat`.
  - *Công cụ giải mã*: `Il2CppDumper` để khôi phục dummy DLLs và header C#.
- **Unity Mono**: Có `libunity.so` + `assets/bin/Data/Managed/Assembly-CSharp.dll`.
  - *Công cụ giải mã*: `dnSpy` hoặc `ILSpy` đọc trực tiếp C# code.
- **Cocos2d-x**: Có `libcocos2djs.so` hoặc `libcocos2dlua.so`.
- **Unreal Engine**: Có `libUE4.so`.

