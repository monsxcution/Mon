# STool Dashboard - Project README

## 1. Project Goal

The main goal of this project is to develop a multi-functional desktop dashboard application using Python and PyQt6. The application, named "STool Dashboard", aims to integrate various tools into a single, convenient tab-based interface.

Current and planned modules include:
- **Home:** A central dashboard or welcome screen.
- **Notes:** A feature-rich note-taking module with reminders and notifications.
- **Passwords:** A secure module for managing passwords.
- **Telegram:** A module for interacting with the Telegram API, likely for managing sessions or automation.
- **Gmail:** A multi-account Gmail client for reading emails directly within the application.

## 2. Project Structure

To ensure the project is scalable and easy to maintain, we have adopted the following directory structure:

```
Montool/
├── main.py             # Main application entry point
├── styles.qss          # Global stylesheet for the application
├── README.md           # This file
|
├── data/               # Contains all user data and credentials
│   ├── main_database.db  # Central SQLite database for all modules
│   ├── credentials.json  # Google API credentials
│   └── gmail_tokens.pkl  # Google API authentication tokens
|
├── modules/            # Contains the UI and front-end logic for each tab
│   ├── home_tab.py
│   ├── notes_tab.py
│   ├── password_tab.py
│   ├── telegram_tab.py
│   └── gmail_tab.py
|
├── services/           # Contains background logic, API interactions, and business logic
│   ├── memory_manager.py
│   └── ai_services/
│       ├── ai_controller.py
│       └── gemini_client.py
|
└── assets/             # Contains all static resources
    ├── icons/
    │   └── icon.png      # Application tray icon
    └── sounds/
        └── ... (notification sounds)
```

## 3. Development Progress & Context

### Key Technologies
- **Language:** Python 3
- **Framework:** PyQt6
- **Database:** SQLite
- **APIs:** Google Gmail API

### Completed Milestones
1.  **Application Skeleton:** A tab-based main window has been set up.
2.  **Notes Module:**
    - Fully functional note-taking with a rich text editor.
    - Data is stored in an SQLite database (`notes.db`, now being merged into `main_database.db`).
    - Features include creating, editing, deleting, and searching notes.
    - Implemented a notification system for notes with due times.
3.  **Gmail Module:**
    - **Multi-Account Authentication:** Users can add multiple Gmail accounts via Google's OAuth2 flow. Authentication tokens are securely stored.
    - **Email Listing:** Fetches and displays a list of emails from the inbox.
    - **Email Viewing:** Displays the content of a selected email.
    - **Performance Optimization:**
        - **UI Freezing Fixed:** Implemented `QThread` to move network requests (fetching email content) to a background thread, preventing the UI from becoming unresponsive.
        - **HTML Sanitization:** Using `BeautifulSoup4` to clean email HTML, fixing rendering errors (`QFont::setPixelSize`).
        - **Crashing Fixed:** Refactored thread management to prevent `RuntimeError` when switching between emails quickly.
4.  **Project Refactoring:**
    - Re-organized the entire project into the logical structure detailed above.

### Current Task
- **Finalizing the Refactoring:**
    - **Update all file imports** across the project to match the new structure.
    - **Merge `notes.db` and `memory.db`** into a single `data/main_database.db`.
    - **Convert the Gmail cache system** from using a JSON file to using the central SQLite database (`main_database.db`) for consistency and better performance.
    - **Update all hardcoded file paths** (e.g., for icons, sounds, database files) to correctly point to their new locations in the `data/` and `assets/` directories.
