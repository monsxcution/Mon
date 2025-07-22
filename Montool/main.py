import sys
import os
import json
import sqlite3
from datetime import datetime, timezone
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget,
    QLabel, QPushButton, QSystemTrayIcon, QMenu, QDialog,
    QVBoxLayout, QTextBrowser, QDialogButtonBox, QTextEdit
)
from PyQt6.QtGui import QAction, QIcon, QCloseEvent
from PyQt6.QtCore import Qt, QTimer, QUrl, QDateTime, QFile, QTextStream
from PyQt6.QtMultimedia import QSoundEffect
import re

# Import your tab files
from modules.home_tab import HomeTab
from modules.notes_tab import NotesTab
from modules.password_tab import PasswordTab
from modules.telegram_tab import TelegramTab
from modules.gmail_tab import GmailTab
from services.memory_manager import initialize_memory


def init_database():
    """Initialize the main database with all required tables"""
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    db_path = os.path.join(data_dir, 'main_database.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create notes table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id TEXT PRIMARY KEY,
            title TEXT,
            content TEXT,
            created_at TEXT,
            updated_at TEXT,
            tags TEXT
        )
    ''')
    
    # Create memory table if it doesn't exist  
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT,
            timestamp TEXT,
            context TEXT
        )
    ''')
    
    # Create Gmail cache table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gmail_cache (
            message_id TEXT PRIMARY KEY,
            account_email TEXT,
            subject TEXT,
            sender TEXT,
            content TEXT,
            timestamp TEXT,
            cached_at TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    
    print(f"Database initialized at '{db_path}'")


class NotificationAlertDialog(QDialog):
    def __init__(self, note, parent=None):
        super().__init__(parent)
        self.note = note
        self.re_notify_timer = QTimer(self)
        self.auto_close_timer = QTimer(self)
        self.sound_effect = QSoundEffect(self)
        self.setWindowTitle("🔔 BÁO THỨC!")
        self.setModal(True)
        layout = QVBoxLayout(self)
        self.browser = QTextBrowser()
        temp_doc = QTextEdit()
        temp_doc.setHtml(note.get('content_html', ''))
        title_text = temp_doc.toPlainText().split('\n', 1)[0]
        title_html = f"<h1>{title_text or 'Không có tiêu đề'}</h1>"
        self.browser.setHtml(title_html + note.get('content_html', ''))
        layout.addWidget(self.browser)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.accept_and_stop)
        layout.addWidget(button_box)
        self.auto_close_timer.setSingleShot(True)
        self.auto_close_timer.timeout.connect(self.timeout_close)
        self.re_notify_timer.setSingleShot(True)
        self.re_notify_timer.timeout.connect(self.re_notify)
    def show_alert(self):
        self.play_sound()
        self.auto_close_timer.start(300000)
        self.show()
    def play_sound(self):
        sound_path = self.note.get("sound_file", "default")
        basedir = os.path.dirname(os.path.abspath(__file__))
        if sound_path == "default" or not os.path.exists(sound_path):
            sound_path = os.path.join(basedir, "assets", "sounds", "notification.wav")
        if os.path.exists(sound_path):
            self.sound_effect.setSource(QUrl.fromLocalFile(sound_path))
            self.sound_effect.setLoopCount(3)
            self.sound_effect.play()
    def accept_and_stop(self):
        self.cleanup()
        self.accept()
    def timeout_close(self):
        self.cleanup()
        self.re_notify_timer.start(60000)
        self.close()
    def re_notify(self):
        self.show_alert()
    def cleanup(self):
        self.sound_effect.stop()
        self.auto_close_timer.stop()
        self.re_notify_timer.stop()
    def closeEvent(self, event):
        self.cleanup()
        super().closeEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("STool Dashboard - PyQt6 Version")
        self.setGeometry(100, 100, 1400, 800)
        self.setObjectName("main_window")
        self.active_notification_alert = None
        self.basedir = os.path.dirname(os.path.abspath(__file__))
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)
        self.home_tab = HomeTab()
        self.notes_tab = NotesTab()
        self.password_tab = PasswordTab()
        self.telegram_tab = TelegramTab()
        self.gmail_tab = GmailTab()
        self.tab_widget.addTab(self.home_tab, "🏠 Trang Chủ")
        self.tab_widget.addTab(self.notes_tab, "📝 Ghi Chú")
        self.tab_widget.addTab(self.password_tab, "🛡️ Mật Khẩu")
        self.tab_widget.addTab(self.telegram_tab, "✈️ Telegram")
        self.tab_widget.addTab(self.gmail_tab, "📧 Gmail")
        self.customize_tab_widget()
        self.setup_tray_icon()
        self.setup_notification_checker()
    def customize_tab_widget(self):
        tab_bar = self.tab_widget.tabBar()
        settings_button = QPushButton("⚙️")
        settings_button.setObjectName("settingsButton")
        self.tab_widget.setCornerWidget(settings_button, Qt.Corner.TopRightCorner)
        tab_bar.setExpanding(False)
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { border-top: 2px solid #0d6efd; background-color: #1a1d21; }
            QTabBar { min-height: 50px; }
            QTabBar::tab { width: 160px; height: 38px; margin-top: 6px; margin-left: 4px; background-color: #2c303a; border: 1px solid #444a59; border-bottom: none; border-top-left-radius: 10px; border-top-right-radius: 10px; font-weight: bold; font-size: 15px; }
            QTabBar::tab:hover:!selected { margin-top: 2px; background-color: #3d4453; }
            QTabBar::tab:selected { background-color: #0d6efd; color: white; border: 2px solid #00e0ff; border-bottom: none; margin-top: 2px; }
            QPushButton#settingsButton { width: 50px; height: 38px; margin-top: 6px; margin-right: 4px; background-color: #2c303a; border: 1px solid #444a59; border-bottom: none; border-top-left-radius: 10px; border-top-right-radius: 10px; font-size: 18px; }
            QPushButton#settingsButton:hover { margin-top: 2px; background-color: #3d4453; color: #00e0ff; }
            QWidget#notesHeader { background-color: transparent; }
            QWidget#notesHeader QPushButton { background-color: #2c303a; border: 1px solid #444a59; border-radius: 8px; padding: 8px 15px; }
            QWidget#notesHeader QPushButton:checked { background-color: #0d6efd; border-color: #0d6efd; }
            QLineEdit#notesSearchBar { padding: 8px; font-size: 14px; border-radius: 8px; }
            QPushButton#switchViewButton, QPushButton#addNewButton { font-weight: bold; background-color: #374151; border: none; border-radius: 8px; min-width: 40px; max-width: 40px; min-height: 35px; max-height: 35px; }
            QPushButton#switchViewButton:pressed, QPushButton#addNewButton:pressed { background-color: #1a1d21; padding-top: 2px; }
            QPushButton#addNewButton { font-size: 18px; }
            QWidget#notesLeftPane { background-color: #2c303a; border-radius: 8px; }
            QListWidget#notesList { border: none; background-color: transparent; }
            QListWidget::item { border-bottom: 1px solid #444a59; padding: 0; }
            QListWidget::item:selected { background-color: #0d6efd; }
            QFrame#noteListItem { background-color: transparent; }
            QListWidget::item:selected QFrame#noteListItem, QListWidget::item:selected QLabel { color: white; }
            QLabel#noteTitle { font-size: 15px; font-weight: bold; }
            QLabel#noteTimestamp { font-size: 13px; font-weight: bold; color: #888; }
            QListWidget::item:selected QLabel#noteTimestamp { color: #ccc; }
            QLabel#notePreview { color: #9ca3af; }
            QTextEdit#noteEditor { background-color: #1a1d21; border: none; font-size: 15px; padding: 10px; }
            QLabel#editorPlaceholder { color: #888; font-size: 16px; }
            QTableWidget#mxhList { border: none; background-color: transparent; }
        """)
    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        icon_path = os.path.join(self.basedir, "assets", "icons", "icon.png")
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            print(f"Warning: Tray icon not found at '{icon_path}'. Please create the file.")
        self.tray_icon.setToolTip("STool Dashboard")
        tray_menu = QMenu()
        show_action = QAction("Mở Dashboard", self)
        show_action.triggered.connect(self.show_window)
        quit_action = QAction("Thoát", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.handle_tray_activation)
    def show_window(self):
        self.show()
        self.activateWindow()
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
    def handle_tray_activation(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_window()
    def setup_notification_checker(self):
        self.notification_timer = QTimer(self)
        self.notification_timer.timeout.connect(self.check_for_notifications)
        self.notification_timer.start(10000)
    def check_for_notifications(self):
        notes_data = self.notes_tab.notes_data
        now_utc = datetime.now(timezone.utc)
        for note in notes_data:
            due_time_str = note.get("due_time")
            if due_time_str and note.get("notified") == 0:
                due_time = datetime.fromisoformat(due_time_str.replace("Z", "+00:00"))
                if now_utc >= due_time:
                    self.trigger_notification(note)
                    self.notes_tab.mark_note_as_notified(note['id'])
                    break
    def trigger_notification(self, note):
        if self.active_notification_alert and self.active_notification_alert.isVisible():
            self.active_notification_alert.close()
        self.active_notification_alert = NotificationAlertDialog(note, self)
        self.active_notification_alert.show_alert()
    def closeEvent(self, event: QCloseEvent):
        event.ignore()
        self.hide()
        self.tray_icon.show()
        self.tray_icon.showMessage(
            "STool Dashboard",
            "Ứng dụng đang chạy trong khay hệ thống.",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )

if __name__ == "__main__":
    init_database()
    initialize_memory()
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    basedir = os.path.dirname(os.path.abspath(__file__))
    style_file = QFile(os.path.join(basedir, "styles.qss"))
    if style_file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
        stream = QTextStream(style_file)
        app.setStyleSheet(stream.readAll())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())