# pyqt_dashboard/telegram_tab.py
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QStackedWidget, 
                             QTableWidget, QTableWidgetItem, QPushButton, QComboBox, QCheckBox)
from PyQt6.QtCore import Qt

class TelegramTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Left Sidebar
        sidebar_widget = QWidget()
        sidebar_widget.setObjectName("telegram_sidebar")
        sidebar_widget.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(sidebar_widget)
        self.sidebar_list = QListWidget()
        self.sidebar_list.addItem("🤖 Session Manager")
        self.sidebar_list.addItem("👥 Group")
        self.sidebar_list.setCurrentRow(0)
        sidebar_layout.addWidget(self.sidebar_list)
        
        # Right Content Area
        self.content_stack = QStackedWidget()
        self.content_stack.addWidget(self.create_session_manager_page())
        
        main_layout.addWidget(sidebar_widget)
        main_layout.addWidget(self.content_stack)

    def create_session_manager_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        controls_layout = QHBoxLayout()
        check_live_btn = QPushButton("Check Live")
        group_combo = QComboBox()
        group_combo.addItems(["Nhóm A (150)", "Nhóm B (75)"])
        controls_layout.addStretch()
        controls_layout.addWidget(check_live_btn)
        controls_layout.addWidget(group_combo)
        
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels(["", "STT", "Phone", "Full Name", "Username", "Live", "Status"])
        table.setColumnWidth(0, 30)
        table.setColumnWidth(1, 40)
        table.horizontalHeader().setStretchLastSection(True)
        
        # Mock data
        session_data = [
            {"stt": 1, "phone": "567573036", "name": "Nguyễn Quang Vũ", "user": "nguyenvu05", "live": True, "status": "Live"},
            {"stt": 2, "phone": "567575726", "name": "Daniel Nguyễn", "user": "danielng", "live": False, "status": "Dead"},
            {"stt": 3, "phone": "583461002", "name": "Chưa kiểm tra", "user": "", "live": None, "status": "Sẵn sàng"},
        ]
        table.setRowCount(len(session_data))
        for row, item in enumerate(session_data):
            table.setCellWidget(row, 0, QCheckBox())
            table.setItem(row, 1, QTableWidgetItem(str(item["stt"])))
            table.setItem(row, 2, QTableWidgetItem(item["phone"]))
            table.setItem(row, 3, QTableWidgetItem(item["name"]))
            table.setItem(row, 4, QTableWidgetItem(item["user"]))
            live_status = "✔️" if item["live"] else ("❌" if item["live"] is not None else "❓")
            live_item = QTableWidgetItem(live_status)
            live_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 5, live_item)
            table.setItem(row, 6, QTableWidgetItem(item["status"]))

        layout.addLayout(controls_layout)
        layout.addWidget(table)
        return page 