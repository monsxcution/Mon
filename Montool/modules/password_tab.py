# pyqt_dashboard/password_tab.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QLineEdit, QPushButton, QHBoxLayout, QHeaderView
from PyQt6.QtCore import Qt

class PasswordCellWidget(QWidget):
    def __init__(self, password):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)
        self.password_edit = QLineEdit(password)
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setReadOnly(True)
        self.password_edit.setStyleSheet("border: none; background-color: transparent;")
        
        self.toggle_btn = QPushButton("👁️")
        self.toggle_btn.setFixedSize(30, 30)
        self.toggle_btn.setStyleSheet("background-color: #444; border-radius: 15px;")
        
        layout.addWidget(self.password_edit)
        layout.addWidget(self.toggle_btn)
        self.toggle_btn.clicked.connect(self.toggle_visibility)
        
    def toggle_visibility(self):
        mode = QLineEdit.EchoMode.Normal if self.password_edit.echoMode() == QLineEdit.EchoMode.Password else QLineEdit.EchoMode.Password
        self.password_edit.setEchoMode(mode)

class ActionsCellWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        edit_btn = QPushButton("Sửa")
        edit_btn.setObjectName("edit_button")
        delete_btn = QPushButton("Xóa")
        delete_btn.setObjectName("delete_button")
        layout.addWidget(edit_btn)
        layout.addWidget(delete_btn)

class PasswordTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        self.table = QTableWidget()
        layout.addWidget(self.table)
        self.setup_table()

    def setup_table(self):
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Loại", "Tên Đăng Nhập", "Mật Khẩu", "Ghi Chú", "Hành Động"])
        # Use the QHeaderView.ResizeMode enum instead of integers
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Mock data
        data = [
            {"type": "Gmail", "username": "user1@gmail.com", "password": "password123", "notes": ""},
            {"type": "Facebook", "username": "user2_fb", "password": "supersecret", "notes": "Tài khoản chính"},
        ]
        self.table.setRowCount(len(data))
        for row, item in enumerate(data):
            self.table.setItem(row, 0, QTableWidgetItem(item["type"]))
            self.table.setItem(row, 1, QTableWidgetItem(item["username"]))
            self.table.setCellWidget(row, 2, PasswordCellWidget(item["password"]))
            self.table.setItem(row, 3, QTableWidgetItem(item["notes"]))
            self.table.setCellWidget(row, 4, ActionsCellWidget()) 