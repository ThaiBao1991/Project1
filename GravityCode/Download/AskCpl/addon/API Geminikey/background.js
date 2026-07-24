chrome.runtime.onInstalled.addListener(() => {
    chrome.storage.local.set({ auto_create_running: false, key_count: 0, last_log: "" });
});
