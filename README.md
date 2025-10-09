# 🧩 STool_v2 – Refactor & Modularization
## 📖 Overview
This project is a **refactored version** of the original STool dashboard.  
The goal is to separate monolithic files into smaller, maintainable, and reusable components — both in **Python logic** and **HTML interface**.
All original templates (`template_main.pyw`, `template_index.html`) remain as **reference blueprints** for layout and logic integrity.
---
## 🧱 Folder Structure
Mon/
├── data/ # Ignored local storage (not pushed to Git)
├── static/ # Static assets (CSS, JS, images)
│
├── template_main.pyw # Original main logic (Python template)
├── template_index.html # Original UI layout (HTML template)
├── template_main copy.pyw # Working copy for experimentation
├── template_index copy.html # Working copy for experimentation
│
├── requirements.txt # Python dependencies
├── .gitignore
├── .gitattributes
└── README.md # Project documentation

---

## 🚧 Refactor Plan
Each feature (e.g., Telegram, MXH, Notes, Health, Settings...) will be modularized as **individual files**:

| Feature | Logic File (.py) | UI File (.html) | Description |
|----------|------------------|------------------|--------------|
| Telegram | `telegram.py` | `telegram.html` | Messaging automation interface |
| MXH | `mxh.py` | `mxh.html` | Social media account manager |
| Notes | `notes.py` | `notes.html` | Personal notes and reminders |
| Health | `health.py` | `health.html` | Weight tracking and analytics |
| Settings | `settings.py` | `settings.html` | App configurations and preferences |

---

## 🧠 Development Notes
- **Python version:** 3.11+
- **Framework:** Flask / PyWebView / PyQt (depending on environment)
- **UI Engine:** HTML + CSS + JS (loaded from `/static`)
- **Templates:** Keep `template_*` files untouched as system references.

---

## 🧰 Commands
```bash
# Install dependencies
pip install -r requirements.txt
# Run template version (for layout reference)
python template_main.pyw
# Run refactored module version
python New\ code/main_refactor.pyw
Versioning & Credits
Refactor start: 2025-10-10
Author: Sếp Mon
Repository: STool_v2
Status: Phase 1 – Telegram & Notes modularization in progress
