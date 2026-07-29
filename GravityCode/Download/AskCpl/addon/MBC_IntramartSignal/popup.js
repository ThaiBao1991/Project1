document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("btn-inspect").addEventListener("click", () => {
        // Gửi message tới content script để bật chế độ chọn element
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if(tabs[0]) {
                chrome.scripting.executeScript({
                    target: { tabId: tabs[0].id },
                    func: () => {
                        const btn = document.getElementById("mbc-btn-scale-pdf");
                        if (btn) {
                            btn.click();
                        } else {
                            alert("Không tìm thấy thanh công cụ. Vui lòng tải lại trang (F5)!");
                        }
                    }
                });
            }
        });
    });

    document.getElementById("btn-save-config").addEventListener("click", () => {
        alert("Chưa có cấu hình nào được tạo.");
    });
});
