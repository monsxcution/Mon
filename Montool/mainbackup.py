import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget,
    QLabel, QPushButton
)
from PyQt6.QtCore import Qt, QFile, QTextStream

# Import các tab giao diện đã tạo
from home_tab import HomeTab
from notes_tab import NotesTab
from password_tab import PasswordTab
from telegram_tab import TelegramTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("STool Dashboard - PyQt6 Version")
        self.setGeometry(100, 100, 1400, 800)
        self.setObjectName("main_window")

        # --- 1. Tạo QTabWidget làm trung tâm ---
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        # --- 2. Tạo và thêm các tab con ---
        self.home_tab = HomeTab()
        self.notes_tab = NotesTab()
        self.password_tab = PasswordTab()
        self.telegram_tab = TelegramTab()

        self.tab_widget.addTab(self.home_tab, "🏠 Trang Chủ")
        self.tab_widget.addTab(self.notes_tab, "📝 Ghi Chú")
        self.tab_widget.addTab(self.password_tab, "🛡️ Mật Khẩu")
        self.tab_widget.addTab(self.telegram_tab, "✈️ Telegram")

        # --- 3. Tùy chỉnh QTabWidget theo yêu cầu ---
        self.customize_tab_widget()

        # --- 4. Kết nối tín hiệu từ card ở Trang Chủ để chuyển tab ---
        self.home_tab.notes_card_clicked.connect(lambda: self.tab_widget.setCurrentWidget(self.notes_tab))
        self.home_tab.password_card_clicked.connect(lambda: self.tab_widget.setCurrentWidget(self.password_tab))
        self.home_tab.telegram_card_clicked.connect(lambda: self.tab_widget.setCurrentWidget(self.telegram_tab))


    def customize_tab_widget(self):
        # Lấy đối tượng thanh tab (QTabBar)
        tab_bar = self.tab_widget.tabBar()

        # Thêm nút cài đặt vào góc phải
        settings_button = QPushButton("⚙️")
        settings_button.setObjectName("settingsButton")
        settings_button.setToolTip("Cài đặt")
        self.tab_widget.setCornerWidget(settings_button, Qt.Corner.TopRightCorner)
        settings_button.clicked.connect(lambda: print("Nút Cài đặt đã được nhấn!"))

        # Tắt chế độ co giãn
        tab_bar.setExpanding(False)

        # Tùy chỉnh giao diện bằng QSS
        style_sheet = """
            QTabWidget::pane {
                border-top: 2px solid #0d6efd;
                background-color: #1a1d21;
            }
            QTabBar {
                min-height: 50px;
            }
            QTabBar::tab {
                width: 160px;
                height: 38px;
                margin-top: 6px;
                margin-left: 4px;
                background-color: #2c303a;
                border: 1px solid #444a59;
                border-bottom: none;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                font-weight: bold;
                font-size: 15px;
            }
            QTabBar::tab:hover:!selected {
                margin-top: 2px;
                background-color: #3d4453;
            }
            QTabBar::tab:selected {
                background-color: #0d6efd;
                color: white;
                border: 2px solid #00e0ff;
                border-bottom: none;
                margin-top: 2px;
            }
            
            /* --- START: SỬA LỖI Ở ĐÂY --- */
            QPushButton#settingsButton {
                /* 1. Giảm chiều rộng nút cài đặt */
                width: 50px;
                height: 38px;
                margin-top: 6px;
                margin-right: 4px;
                background-color: #2c303a;
                border: 1px solid #444a59;
                border-bottom: none;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                font-size: 18px;
            }
            QPushButton#settingsButton:hover {
                margin-top: 2px;
                background-color: #3d4453;
                color: #00e0ff;
            }

            /* 2. Style cho header của tab Ghi Chú để các nút tách rời */
            QWidget#notesHeader {
                background-color: transparent; /* Nền trong suốt */
            }
            QWidget#notesHeader QPushButton {
                background-color: #2c303a;
                border: 1px solid #444a59;
                border-radius: 8px;
                padding: 8px 15px;
            }
            QWidget#notesHeader QPushButton:checked {
                background-color: #0d6efd;
                border-color: #0d6efd;
            }
            /* --- Style for Redesigned Notes Tab --- */
            QLineEdit#notesSearchBar {
                padding: 8px;
                font-size: 14px;
                border-radius: 8px;
            }
            QPushButton#switchViewButton, QPushButton#addNewButton {
                font-weight: bold;
                background-color: #374151;
                border: none;
                border-radius: 8px;
                min-width: 40px;
                max-width: 40px;
                min-height: 35px;
                max-height: 35px;
            }
            QPushButton#switchViewButton:pressed, QPushButton#addNewButton:pressed {
                background-color: #1a1d21; /* Darker background on press */
                padding-top: 2px; /* Simple "push down" effect */
            }
            QPushButton#addNewButton {
                font-size: 18px;
            }
            QWidget#notesLeftPane {
                background-color: #2c303a;
                border-radius: 8px;
            }
            QListWidget#notesList {
                border: none;
                background-color: transparent;
            }
            QListWidget::item {
                border-bottom: 1px solid #444a59;
                padding: 0;
            }
            QListWidget::item:selected {
                background-color: #0d6efd;
            }
            QFrame#noteListItem {
                background-color: transparent;
            }
            QListWidget::item:selected QFrame#noteListItem, 
            QListWidget::item:selected QLabel {
                color: white;
            }
            QLabel#noteTitle {
                font-size: 15px;
                font-weight: bold;
            }
            QLabel#noteTimestamp {
                font-size: 13px;
                font-weight: bold;
                color: #888;
            }
            QListWidget::item:selected QLabel#noteTimestamp {
                color: #ccc;
            }
            QLabel#notePreview {
                color: #9ca3af;
            }
            QTextEdit#noteEditor {
                background-color: #1a1d21;
                border: none;
                font-size: 15px;
                padding: 10px;
            }
            QLabel#editorPlaceholder {
                color: #888;
                font-size: 16px;
            }
            QTableWidget#mxhList {
                border: none;
                background-color: transparent;
            }
        """
        self.tab_widget.setStyleSheet(style_sheet)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Tải file style chung (nếu muốn, các style riêng đã có trong hàm trên)
    style_file = QFile("pyqt_dashboard/styles.qss")
    if style_file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
        stream = QTextStream(style_file)
        # Nối style chung và style của tab widget
        # app.setStyleSheet(stream.readAll() + ...) # Có thể nối sau nếu cần
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 