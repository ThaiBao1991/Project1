---
name: python_desktop_app_best_practices
description: Use this skill for building Python Desktop Apps (Tkinter, PyQt, etc.) to ensure best practices like auto-installing dependencies, responsive UI scaling, and fast data processing/encryption. Trigger on: creating a new desktop app, fixing UI freezing, handling missing dependencies, optimizing large file encryption, or making UI responsive.
---

# Python Desktop App Best Practices

When building or optimizing Python desktop applications, strictly follow these generalized best practices. They ensure your app is portable, scalable, and highly performant across different environments.

## 1. Auto-Installing Dependencies (Smart Bootstrapping)
Desktop applications often fail when shared because the target machine lacks required Python packages (e.g., `requests`, `cryptography`, `pywin32`).
**Rule:** Always include a dependency auto-installer at the very top of the main entry point (e.g., `main.py` or `App.py`), *before* any third-party imports.
- **Workflow:**
  1. Define a mapping of module names to their PyPI package names.
  2. Use a `try...except ImportError:` loop to detect missing modules.
  3. Attempt to automatically install them silently using `subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])`.
  4. **Fallback:** If auto-installation fails (due to permissions, proxy, etc.), immediately launch a minimal GUI window (e.g., using `tkinter.Tk()`) that displays the exact error and provides a **selectable, copyable textbox** with the exact CLI command (e.g., `pip install ...`) so the user can easily copy and run it themselves. Then exit.

## 2. Responsive UI & Dynamic Sizing (Never Hardcode Geometries)
Applications must adapt to different screen resolutions and window resizing. Hardcoding sizes (e.g., `width=800, height=600`) or relying on fixed grids will cause elements to collapse or stretch unnaturally.
**Rule:** Let the UI layout manager do the math.
- Use dynamic sizing weights (`weight=1`) in grid or `fill=both, expand=True` in pack.
- Set reasonable `minsize` for root windows and PanedWindows to prevent them from shrinking beyond usability.
- Use `wraplength` dynamically bound to frame width for long text labels instead of hardcoding `wraplength=200`.
- Do not assume a fixed screen resolution; use `winfo_screenwidth()` if you absolutely need to calculate proportions.

## 3. High-Performance Data Processing & Encryption
When handling large files, folders, or archives, reading the entire payload into RAM (e.g., `f.read()`) causes memory spikes, UI freezes, and slow execution.
**Rule:** Always use streaming and chunking for file operations.
- **Encryption:** Use streaming ciphers or block ciphers in counter mode (e.g., `AES-CTR` via `cryptography.hazmat`) instead of high-level wrappers like `Fernet` (which mandate loading the entire file into memory). Read in chunks (e.g., 64KB) and write the cipher stream continuously.
- **Compression/Archiving:** Use `shutil.make_archive` and `shutil.unpack_archive` for blazing-fast folder zipping/unzipping. They are highly optimized by the C standard library.
- **Background Threads:** Any IO-bound task (encryption, large file copies, network requests) must run in a `threading.Thread(target=..., daemon=True)` so the main UI loop is never blocked.

These rules apply universally to any desktop application codebase to maintain professional software standards.

## 4. Secure Credential & API Key Management
Desktop apps often need to interact with external APIs (like GitHub, AWS, or custom servers). Hardcoding tokens or saving them in plain text files (e.g., standard `.json` settings) is a major security vulnerability.
**Rule:** Always encrypt sensitive credentials at rest.
- **Local Storage:** Use the OS's native credential manager (e.g., `keyring` library in Python) or encrypt the API keys in your local config files using a robust algorithm (e.g., AES-GCM) tied to a machine-specific hardware ID or a user-provided master password.
- **Memory Protection:** Clear sensitive tokens from memory when no longer in active use, and avoid logging them to terminal outputs or debugging files.
- **GitHub Tokens/Private Keys:** If the app uses GitHub APIs for synchronization, never save the raw Personal Access Token (PAT). Mask it in the UI (using `show="*"` in password fields) and securely encrypt it before writing to `settings.json`.

## 5. Handling Massive Data & UI Rendering (Lazy Loading)
Desktop apps frequently display or export large amounts of data (e.g., thousands of HTML files, large logs, or complex UI components). Rendering everything at once will cause severe memory leaks and application crashes.
**Rule:** Always implement Lazy Loading or Virtualization.
- **UI Elements:** Use pagination for lists/tables, or dynamically render elements only when they scroll into the viewport (virtualized lists).
- **HTML/Webviews:** When generating massive HTML files or displaying them via a webview, do not concatenate and load the entire DOM string at once. Load the skeleton first, then fetch or render content in chunks as the user interacts.

## 6. Network & API Resilience (Chunking & Rate Limits)
Interacting with platforms like GitHub (e.g., uploading files via API) often hits hard limits (like file size caps or rate limits).
**Rule:** Never send huge payloads in a single request.
- **Payload Splitting:** Break down large files into smaller chunks (e.g., under 1MB per chunk) when pushing to APIs. If the API doesn't support chunked uploads, compress the data before sending or break the task into multiple discrete files.
- **Exponential Backoff:** Always wrap network calls in a retry block with exponential backoff (e.g., wait 2s, then 4s, then 8s) to gracefully handle 429 Too Many Requests or 503 errors.

## 7. State Persistence & Auto-Save (Crash Recovery)
Users hate losing progress or having to repeatedly configure the same settings (like selecting the same folder every time).
**Rule:** Always persist the application state.
- **Last Used State:** Save UI states (last selected directory, active filters, window size, checked options) to a local `settings.json`. When the app starts, restore these states so the user can continue exactly where they left off.
- **Auto-Save:** For long-running tasks or editors, implement an auto-save mechanism (e.g., saving to a temporary `.bak` file or internal SQLite db) to prevent data loss if the app crashes or is closed abruptly. 

## 8. UX, File Filters & Portable Configs
Desktop applications must feel native and foolproof.
**Rule:** Ensure strict file selection and portable architecture.
- **File Dialog Filters:** Whenever using `filedialog.askopenfilename` or `asksaveasfilename`, ALWAYS provide explicit `filetypes` (e.g., `[("JSON Files", "*.json"), ("AskCpl Files", "*.askcpl")]`). Never let the user blindly pick unsupported files which leads to crashes.
- **Portable Architecture:** Store configuration files (`settings.json`), databases, and temporary output folders alongside the main entry point (e.g., `os.path.dirname(__file__)`) or in a clearly defined user-local AppData directory. Do not scatter files randomly. This guarantees the app is completely portable and can be moved between computers without breaking paths.
