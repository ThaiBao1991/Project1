# Codex Quota Tracker

Local VS Code extension that displays the active Codex quota snapshot and writes a portable, token-free `codex_quota_data.dat` file.

Use the **Codex Quota** Activity Bar view or run `Codex Quota Tracker: Refresh`. The extension reads only local Codex session rate-limit events; it does not read, export, or copy authentication files, API keys, or tokens.

Set `codexQuotaTracker.dataDirectory` to the folder shared with QuotaApp when you want the Python dashboard to show the same snapshot.
