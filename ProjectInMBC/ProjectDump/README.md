# 🚀 ProjectDump

**ProjectDump** is a Python CLI tool that detects a project's technologies, filters out non-essential files, and compiles the source code and directory structure into a single readable file.

---

## 📦 Features

- 🔍 Auto-detects technologies (Python, JavaScript, Java, etc.)
- 🧹 Skips dependencies, binaries, media, and config clutter
- 🌲 Generates a clean directory tree
- 📄 Dumps readable source code with syntax highlighting
- ⚡ Handles large projects and ignores huge files (>100MB)

---

## 🧑‍💻 Supported Technologies (Partial List)

- **Languages**: Python, JS/TS, Java, Kotlin, PHP, Ruby, Go, Rust, C#, Dart, R, Scala, Elixir
- **Frameworks**: React, Vue, Svelte, Angular, Next.js, Nuxt, Flutter, Android, iOS
- **Infra**: Docker, Kubernetes, Terraform, Ansible
- **CI/CD**: GitHub Actions, GitLab CI, CircleCI

---

## 📂 Output Example
```
🚀 PROJECTDUMP
========================================
🌐 Select language (en/vi): en
📂 Enter the project folder path: /path/to/your/project
🔍 Analyzing project at: /path/to/your/project
🔍 Scanning directories...
🛠️  Detected technologies: python
📁 Extensions included: .py, .pyi, .pyx
📁 Generating directory tree...
📄 Processing files...
  📝 Processing: aggregator.py
  📝 Processing: constants.py
  📝 Processing: detector.py
  📝 Processing: filters.py
  📝 Processing: one_file_version.py
  📝 Processing: tree_generator.py
  📝 Processing: __main__.py

✅ Success! File created: /path/to/your/project/source_dump.txt

📊 Summary:
   - Files processed: 7
   - Output size: 30275 characters (~28 KB)
   - Total lines: 870

🎉 Done! The source_dump.txt file is ready.
```

Inside `source_dump.txt`demo:
```text
# ==================================================
# Path: /path/to/your/project
# Detected tech: python
# ==================================================

## DIRECTORY STRUCTURE

New folder/
├── __pycache__/
├── __main__.py
├── aggregator.py
├── constants.py
├── detector.py
├── filters.py
├── one_file_version.py
├── source_dump.txt
└── tree_generator.py

## FILE CONTENTS

### __main__.py

import os
...
```

## 🚀 Usage
Run from the command line:
```bash
  python main.py /path/to/your/project
```

## 📁 What It Ignores
- **Dependency folders**: node_modules, venv, etc.

- **Media & binaries**: .jpg, .exe, .log, etc.

- **Config/IDE**: .git, .vscode, .github, etc.

- **Large files over 100MB**

## ✅ Requirements
Python 3.x

## 🤝 Contributing
Feel free to fork and contribute to enhance tech detection, support new stacks, or improve output formatting!

