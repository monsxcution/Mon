# 🧩 STool_v2 Code Refactor (New Structure)

## 📂 Project Overview
This folder (`New code/`) is a complete refactor of the original project.
The goal is to separate each logic and UI module into independent, maintainable files, replacing the previous single-file architecture (`Main.pyw` + `index.html`).

---

## 🧱 Folder Structure
Mon/
├── data/ # Ignored (local data, not pushed)
├── static/ # Static assets (CSS, JS, images)
├── New code/ # Refactored project
│ ├── telegram.py # Logic for Telegram tab
│ ├── telegram.html # UI layout for Telegram tab
│ ├── mxh.py # Social Media manager logic
│ ├── mxh.html # UI layout for MXH
│ ├── notes.py # Notes/Ghi chú logic
│ ├── notes.html # Notes UI layout
│ ├── ...
│ ├── main_refactor.pyw # Entry point for new modular version
│ ├── template_main.pyw # Reference template (original logic)
│ ├── template_index.html # Reference UI template (original layout)
│ └── README.md # This file
├── requirements.txt
└── .gitignore

---

## 🚀 Refactor Rules
1. No logic duplication: Each module must handle one feature (Telegram, Notes, MXH...).
2. Shared assets only in `/static/`.
3. Keep layout identical to `template_index.html`.
4. Do not modify template files directly.
5. Test each module independently before merging.

---

## 🧠 Development Notes
- Base environment: Python 3.11+
- Framework: Flask (or compatible if GUI embedded)
- Each `.py` file imports core functions from the main entry (`main_refactor.pyw`).
- Communication between Python and HTML uses `render_template()` or direct UI loader in PyWebView/PyQt (depending on runtime).

---

## 🧰 Commands
```powershell
# Run new modular version
python ".\New code\main_refactor.pyw"

# Run original template (for reference)
python ".\template_main.pyw"
```

---

## Versioning
- Refactor start: 2025-10-10
- Author: Sếp Mon
- Status: Phase 1 – Separate Telegram + Notes modules

---
