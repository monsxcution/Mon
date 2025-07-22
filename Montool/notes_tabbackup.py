import sys
import os
import json
import uuid
from datetime import datetime, timezone
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget,
    QListWidget, QListWidgetItem, QFrame, QLabel, QDialog, QTextEdit,
    QMenu, QLineEdit, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QGridLayout, QWidgetAction
)
from PyQt6.QtGui import QAction, QColor, QTextCursor, QDesktopServices
from PyQt6.QtCore import Qt, QTimer, QSize, pyqtSignal, QUrl

# =============================================================================
# Helper Function for Relative Time
# =============================================================================
def format_relative_time(iso_timestamp_str):
    if not iso_timestamp_str: return ""
    note_time = datetime.fromisoformat(iso_timestamp_str.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    delta = now - note_time
    if delta.total_seconds() < 60: return "Vừa xong"
    elif delta.total_seconds() < 3600: return f"{int(delta.total_seconds() / 60)} phút trước"
    elif delta.total_seconds() < 86400: return f"{int(delta.total_seconds() / 3600)} giờ trước"
    elif delta.days == 1 or (delta.total_seconds() < 172800 and now.day != note_time.day): return "Hôm qua"
    elif delta.days < 30: return f"{delta.days} ngày trước"
    else: return note_time.strftime("%d/%m/%Y")

# =============================================================================
# Color Palette Widget for Context Menu
# =============================================================================
class ColorPaletteWidget(QWidget):
    color_selected = pyqtSignal(QColor)
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QGridLayout(self); layout.setSpacing(4); layout.setContentsMargins(4, 4, 4, 4)
        colors = ["#FFFFFF", "#EF5350", "#EC407A", "#AB47BC", "#7E57C2", "#5C6BC0", "#42A5F5", "#26C6DA", "#26A69A", "#66BB6A", "#FFCA28", "#FF7043"]
        positions = [(i, j) for i in range(3) for j in range(4)]
        for pos, color_hex in zip(positions, colors):
            btn = QPushButton(); btn.setFixedSize(24, 24); btn.setStyleSheet(f"background-color: {color_hex}; border-radius: 12px;")
            btn.clicked.connect(lambda ch, c=color_hex: self.on_color_click(c)); layout.addWidget(btn, pos[0], pos[1])
    def on_color_click(self, color_hex):
        self.color_selected.emit(QColor(color_hex))
        parent_menu = self;
        while parent_menu is not None and not isinstance(parent_menu, QMenu): parent_menu = parent_menu.parent()
        if parent_menu: parent_menu.close()

# =============================================================================
# Custom Rich Text Editor with Context Menu
# =============================================================================
class RichTextEditor(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("noteEditor")
        self.setAutoFormatting(QTextEdit.AutoFormattingFlag.AutoAll)
        self.setMouseTracking(True)
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            anchor = self.anchorAt(event.pos())
            if anchor:
                QDesktopServices.openUrl(QUrl(anchor)); return
        super().mousePressEvent(event)
    def mouseMoveEvent(self, event):
        self.viewport().setCursor(Qt.CursorShape.PointingHandCursor if self.anchorAt(event.pos()) else Qt.CursorShape.IBeamCursor)
        super().mouseMoveEvent(event)
    def contextMenuEvent(self, event):
        menu = QMenu(self); cursor = self.textCursor()
        copy_action = menu.addAction("Sao chép"); copy_action.setEnabled(cursor.hasSelection())
        copy_action.triggered.connect(self.copy)
        color_action_menu = QMenu("Chọn màu chữ", self)
        color_palette = ColorPaletteWidget(self)
        color_palette.color_selected.connect(self.setTextColor)
        custom_action = QWidgetAction(self); custom_action.setDefaultWidget(color_palette)
        color_action_menu.addAction(custom_action)
        menu.addMenu(color_action_menu); menu.exec(event.globalPos())

# =============================================================================
# Note List Item Widget
# =============================================================================
class NoteListItem(QWidget):
    def __init__(self, note_id, title, preview, modified_at):
        super().__init__(); self.note_id = note_id; self.setObjectName("noteListItem")
        main_layout = QVBoxLayout(self); main_layout.setContentsMargins(10, 8, 10, 8); main_layout.setSpacing(2)
        top_layout = QHBoxLayout()
        self.title_label = QLabel(title, objectName="noteTitle")
        self.timestamp_label = QLabel(format_relative_time(modified_at), objectName="noteTimestamp")
        top_layout.addWidget(self.title_label); top_layout.addStretch(); top_layout.addWidget(self.timestamp_label)
        self.preview_label = QLabel(preview, objectName="notePreview")
        main_layout.addLayout(top_layout); main_layout.addWidget(self.preview_label)
        self.setMaximumHeight(80)
    def update_content(self, title, preview, modified_at):
        self.title_label.setText(title); self.preview_label.setText(preview)
        self.timestamp_label.setText(format_relative_time(modified_at))
        
# =============================================================================
# Main Notes Tab Widget (with Search Logic)
# =============================================================================
class NotesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.notes_data = []; self.current_note_id = None
        self.data_file_path = "pyqt_dashboard/notes_data.json"

        # --- Debounce Timer for Saving ---
        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.setInterval(500) # Wait 500ms after last keystroke to save
        self.save_timer.timeout.connect(self._perform_save_and_resort)

        # --- Main Two-Pane Layout ---
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 10, 20, 20); main_layout.setSpacing(15)

        # --- Left Pane ---
        left_pane = QWidget(objectName="notesLeftPane"); left_pane.setFixedWidth(300)
        left_layout = QVBoxLayout(left_pane); left_layout.setContentsMargins(8, 8, 8, 8); left_layout.setSpacing(8)
        header_widget = QWidget(objectName="notesListHeader")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0); header_layout.setSpacing(5)
        self.search_bar = QLineEdit(placeholderText="🔍 Tìm kiếm..."); self.search_bar.setObjectName("notesSearchBar")
        self.switch_view_button = QPushButton("🔄"); self.switch_view_button.setToolTip("Chuyển đổi Ghi chú / MXH")
        self.switch_view_button.setObjectName("switchViewButton")
        self.add_new_button = QPushButton("➕"); self.add_new_button.setObjectName("addNewButton")
        header_layout.addWidget(self.search_bar, 1); header_layout.addWidget(self.switch_view_button); header_layout.addWidget(self.add_new_button)
        
        self.content_stack_left = QStackedWidget()
        self.note_list_widget = QListWidget(objectName="notesList")
        self.mxh_table_widget = QTableWidget(objectName="mxhList")
        self.content_stack_left.addWidget(self.note_list_widget); self.content_stack_left.addWidget(self.mxh_table_widget)
        left_layout.addWidget(header_widget); left_layout.addWidget(self.content_stack_left)
        
        # --- Right Pane ---
        right_pane = QWidget()
        right_layout = QVBoxLayout(right_pane); right_layout.setContentsMargins(0,0,0,0)
        self.editor_stack = QStackedWidget()
        self.placeholder_label = QLabel("Chọn một ghi chú để xem hoặc tạo ghi chú mới.", objectName="editorPlaceholder")
        self.placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.editor = RichTextEditor()
        self.editor_stack.addWidget(self.placeholder_label); self.editor_stack.addWidget(self.editor)
        right_layout.addWidget(self.editor_stack)

        main_layout.addWidget(left_pane); main_layout.addWidget(right_pane, 1)

        # --- Load Data and Connections ---
        self.load_notes_from_file()
        self.add_new_button.clicked.connect(self.handle_add_new)
        self.switch_view_button.clicked.connect(self.toggle_view)
        self.note_list_widget.currentItemChanged.connect(self.display_note_content)
        self.editor.textChanged.connect(self.request_save_on_edit) # Connect to the timer trigger
        self.note_list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.note_list_widget.customContextMenuRequested.connect(self.show_list_context_menu)
        self.search_bar.textChanged.connect(self._filter_note_list)
        self.populate_note_list()
        self.populate_mxh_table()

    def _filter_note_list(self, search_text):
        search_text_lower = search_text.lower().strip()
        for i in range(self.note_list_widget.count()):
            item = self.note_list_widget.item(i)
            note_id = item.data(Qt.ItemDataRole.UserRole)
            note_data = self.get_note_by_id(note_id)
            if note_data:
                temp_doc = QTextEdit(); temp_doc.setHtml(note_data.get('content_html', ''))
                note_content_plain = temp_doc.toPlainText()
                if search_text_lower in note_content_plain.lower():
                    item.setHidden(False)
                else:
                    item.setHidden(True)

    def toggle_view(self):
        next_index = 1 - self.content_stack_left.currentIndex()
        self.content_stack_left.setCurrentIndex(next_index)
        self.add_new_button.setToolTip("Thêm tài khoản MXH" if next_index == 1 else "Thêm ghi chú mới")

    def handle_add_new(self):
        if self.content_stack_left.currentIndex() == 0: self.add_new_note()
        else: print("Logic to add new social media account")
            
    def get_note_by_id(self, note_id):
        return next((note for note in self.notes_data if note.get('id') == note_id), None)

    def load_notes_from_file(self):
        if os.path.exists(self.data_file_path):
            try:
                with open(self.data_file_path, 'r', encoding='utf-8') as f: self.notes_data = json.load(f)
            except: self.notes_data = []
        else: self.notes_data = []

    def save_notes_to_file(self):
        with open(self.data_file_path, 'w', encoding='utf-8') as f:
            json.dump(self.notes_data, f, indent=4, ensure_ascii=False)

    def populate_note_list(self):
        self.note_list_widget.currentItemChanged.disconnect(self.display_note_content)
        self.note_list_widget.clear()
        sorted_notes = sorted(self.notes_data, key=lambda x: x.get('modified_at', ''), reverse=True)
        for note in sorted_notes:
            self._add_item_to_list_widget(note)
        self.note_list_widget.currentItemChanged.connect(self.display_note_content)
            
    def _add_item_to_list_widget(self, note, position=None):
        plain_content = QTextEdit(); plain_content.setHtml(note.get('content_html', ''))
        lines = plain_content.toPlainText().split('\n')
        title = lines[0] if lines and lines[0].strip() else "Ghi chú mới"
        body_lines = lines[1:]
        preview = "\n".join(body_lines[:2])
        list_item_widget = NoteListItem(note['id'], title, preview, note.get('modified_at'))
        list_widget_item = QListWidgetItem()
        list_widget_item.setSizeHint(list_item_widget.sizeHint())
        list_widget_item.setData(Qt.ItemDataRole.UserRole, note['id'])
        if position is not None: self.note_list_widget.insertItem(position, list_widget_item)
        else: self.note_list_widget.addItem(list_widget_item)
        self.note_list_widget.setItemWidget(list_widget_item, list_item_widget)
        return list_widget_item

    def populate_mxh_table(self):
        self.mxh_table_widget.setColumnCount(3)
        self.mxh_table_widget.setHorizontalHeaderLabels(["Nickname", "URL", "Ghi Chú"])
        self.mxh_table_widget.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        mxh_data = [{"nick": "Nick Chính", "url": "https://facebook.com/user1", "notes": "TK seeding"}]
        self.mxh_table_widget.setRowCount(len(mxh_data))
        for row, item in enumerate(mxh_data):
            self.mxh_table_widget.setItem(row, 0, QTableWidgetItem(item["nick"]))
            self.mxh_table_widget.setItem(row, 1, QTableWidgetItem(item["url"]))
            self.mxh_table_widget.setItem(row, 2, QTableWidgetItem(item["notes"]))

    def add_new_note(self):
        new_note = { "id": str(uuid.uuid4()), "content_html": "Ghi chú mới\n", "modified_at": datetime.now(timezone.utc).isoformat() }
        self.notes_data.append(new_note)
        self.resort_and_refresh_list()
        for i in range(self.note_list_widget.count()):
            item = self.note_list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == new_note['id']:
                self.note_list_widget.setCurrentItem(item); break
        self.editor.setFocus()

    def display_note_content(self, current_item, previous_item):
        if not current_item:
            self.current_note_id = None; self.editor_stack.setCurrentWidget(self.placeholder_label)
            return
        self.current_note_id = current_item.data(Qt.ItemDataRole.UserRole)
        note = self.get_note_by_id(self.current_note_id)
        if note:
            self.editor.textChanged.disconnect(self.request_save_on_edit)
            self.editor.setHtml(note.get('content_html', ''))
            self.editor.textChanged.connect(self.request_save_on_edit)
            self.editor_stack.setCurrentWidget(self.editor)

    def request_save_on_edit(self):
        """Called on every keystroke to start or restart the debounce timer."""
        self.save_timer.start()

    def _perform_save_and_resort(self):
        """This is the actual save method, called by the timer when the user stops typing."""
        if not self.current_note_id: return
        note = self.get_note_by_id(self.current_note_id)
        
        if note and note['content_html'] != self.editor.toHtml():
            note['content_html'] = self.editor.toHtml()
            note['modified_at'] = datetime.now(timezone.utc).isoformat()
            
            # Now, re-sort the data and rebuild the visual list
            self.resort_and_refresh_list()

    def resort_and_refresh_list(self):
        self.notes_data.sort(key=lambda x: x.get('modified_at', ''), reverse=True)
        self.save_notes_to_file()
        current_id_before_refresh = self.current_note_id
        self.populate_note_list()
        # Restore selection after refresh
        if current_id_before_refresh:
             for i in range(self.note_list_widget.count()):
                item = self.note_list_widget.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == current_id_before_refresh:
                    # Setting current row without emitting signal to avoid recursion
                    self.note_list_widget.setCurrentRow(i)
                    break

    def show_list_context_menu(self, pos):
        item = self.note_list_widget.itemAt(pos)
        if not item: return
        note_id = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self); delete_action = menu.addAction("🗑️ Xóa Ghi Chú")
        action = menu.exec(self.note_list_widget.mapToGlobal(pos))
        if action == delete_action: self.delete_note(note_id)

    def delete_note(self, note_id):
        reply = QMessageBox.question(self, "Xác nhận xóa", "Bạn có chắc muốn xóa ghi chú này?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.notes_data = [note for note in self.notes_data if note.get('id') != note_id]
            was_current_note = self.current_note_id == note_id
            self.resort_and_refresh_list()
            if was_current_note:
                self.current_note_id = None; self.editor_stack.setCurrentWidget(self.placeholder_label) 