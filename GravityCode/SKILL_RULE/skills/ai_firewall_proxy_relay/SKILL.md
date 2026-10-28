---
name: ai_firewall_proxy_relay
description: Giải pháp vượt tường lửa doanh nghiệp / DPI chặn các dịch vụ AI (OpenAI, Anthropic, Gemini, Claude) thông qua Cloudflare Worker Reverse Proxy, local HTTP CONNECT Proxy và kỹ thuật phân mảnh SNI.
---

# Vượt Tường Lửa Doanh Nghiệp & DPI Chặn AI API (AlowGPT Strategy)

Kỹ năng thiết lập cổng trung gian (Relay Gateway) để các công cụ lập trình (OpenCode, VSCode, Cline, Antigravity) kết nối được tới các API AI khi bị tường lửa (Trend Micro, Fortinet, Cisco) chặn.

## 1. Giải Pháp 1: Cloudflare Worker Reverse Proxy
Triển khai một Worker miễn phí làm trung gian chuyển tiếp yêu cầu:
```javascript
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    // Chuyển tiếp tới domain đích (ví dụ OpenAI hoặc Anthropic)
    url.hostname = "api.openai.com";
    const newRequest = new Request(url, request);
    return fetch(newRequest);
  }
}
```
- Đặt `Base URL` trong công cụ AI thành: `https://ten-worker-cua-ban.workers.dev/v1`.
- Lưu lượng được mã hóa qua mạng của Cloudflare, vượt qua bộ lọc tên miền của tường lửa nội bộ.

## 2. Giải Pháp 2: Local HTTP CONNECT Proxy & Phân Mảnh SNI (SNI Fragmentation)
- Khởi chạy một proxy server nội bộ bằng Python trên máy (`127.0.0.1:8080`).
- Khi client bắt đầu bắt tay TLS (`Client Hello`), chia gói tin TCP mang Server Name Indication (SNI) thành nhiều mảnh nhỏ (ví dụ 2 phần).
- Tường lửa kiểm tra gói tin dạng DPI thông thường sẽ không đọc được đầy đủ tên miền bị chặn trong gói đầu tiên, do đó bỏ qua kết nối.

## 3. Tự Động Cấu Hình VSCode / IDE Proxy
- Cập nhật trong `settings.json` của VSCode/IDE:
```json
{
  "http.proxy": "http://127.0.0.1:8080",
  "http.proxyStrictSSL": false
}
```