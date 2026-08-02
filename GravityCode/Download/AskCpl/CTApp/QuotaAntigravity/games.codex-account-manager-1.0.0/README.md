# Codex Account Manager

Local VS Code/Antigravity extension for adding multiple Codex accounts with the official `codex login --device-auth` browser flow and displaying each account's current quota and reset time.

It keeps each login in a separate local Codex profile and writes only quota snapshots to `~/.quota-tracker/codex_quota_data.dat`, which the Python QuotaApp can read offline. Credentials are never copied into that snapshot.

Install by copying this folder to the IDE extensions directory, then reload the IDE and run **Codex Account Manager: Open**.
