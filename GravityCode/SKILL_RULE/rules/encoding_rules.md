# Encoding & Data Serialization Rules

## Text Encoding
- Always use UTF-8 encoding across all text files, tools, and streams.
- In Python: always specify `encoding="utf-8"` when reading/writing text files.
- In Windows console Python scripts: add `sys.stdout.reconfigure(encoding="utf-8")`.

## Base64 & Unicode Synchronization Rule
- When encoding JSON containing Vietnamese, CJK, or Markdown:
  - Save: `btoa(unescape(encodeURIComponent(JSON.stringify(obj))))`
  - Load: `JSON.parse(decodeURIComponent(escape(atob(str))))`
- Or use `TextEncoder` and `TextDecoder` with `Uint8Array`.
- NEVER decode with raw `atob()` without UTF-8 reinterpretation, as it causes exponential memory and payload explosion in save/load cycles.