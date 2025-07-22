import sys
import os
import json
import uuid
from datetime import datetime, timezone
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QStackedWidget,
    QListWidget,
    QListWidgetItem,
    QFrame,
    QLabel,
    QDialog,
    QTextEdit,
    QMenu,
    QLineEdit,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDateTimeEdit,
    QComboBox,
    QDialogButtonBox,
    QInputDialog,
    QSpinBox,
    QStyle,
)
from PyQt6.QtGui import (
    QAction,
    QColor,
    QTextCursor,
    QDesktopServices,
    QIcon,
    QTextCharFormat,
    QFont,
    QKeyEvent,
)
from PyQt6.QtCore import (
    Qt,
    QTimer,
    QSize,
    pyqtSignal,
    QUrl,
    QDateTime,
    QTime,
    QItemSelectionModel,
)
import sqlite3


# =============================================================================
# Helper Function for Relative Time
# =============================================================================
def format_relative_time(iso_timestamp_str):
    if not iso_timestamp_str:
        return ""
    note_time = datetime.fromisoformat(iso_timestamp_str.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    delta = now - note_time
    total_seconds = delta.total_seconds()

    if total_seconds < 60:
        return "Vừa xong"
    elif total_seconds < 3600:
        return f"{int(total_seconds / 60)} phút trước"
    elif total_seconds < 86400:
        return f"{int(total_seconds / 3600)} giờ trước"
    elif delta.days < 7:
        return f"{delta.days} ngày trước"
    else:
        return note_time.strftime("%d/%m/%Y")


# =============================================================================
# PlaceholderSpinBox and Notification Dialog
# =============================================================================
class PlaceholderSpinBox(QSpinBox):
    """A QSpinBox that shows placeholder text when its value is 0."""

    def __init__(self, parent=None):
        super().__init__(parent)
        # By default, when a user clears the text, the value reverts to the minimum.
        # This ensures the placeholder reappears if the user deletes their input.
        # [!MODIFIED!] Changed CorrectToMinimumValue to CorrectToPreviousValue as per the error log.
        self.setCorrectionMode(QSpinBox.CorrectionMode.CorrectToPreviousValue)

    def textFromValue(self, value: int) -> str:
        """
        Overrides the default behavior to return an empty string for the minimum value,
        which allows the placeholder text to be shown.
        """
        if value == self.minimum():
            return ""
        return super().textFromValue(value)

    def setPlaceholderText(self, text: str):
        """A convenience method to set the placeholder on the internal QLineEdit."""
        self.lineEdit().setPlaceholderText(text)


class SetNotificationDialog(QDialog):
    def __init__(self, note_title, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Đặt Thông Báo")
        self.setWindowIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation)
        )
        self.layout = QVBoxLayout(self)
        self.view_stack = QStackedWidget()
        self.layout.addWidget(self.view_stack)
        spinbox_view = QWidget()
        spinbox_layout = QHBoxLayout(spinbox_view)
        spinbox_layout.setContentsMargins(0, 0, 0, 0)
        # START: Replace with this block
        self.day_spin = PlaceholderSpinBox(self)
        self.day_spin.setMinimum(0)
        self.day_spin.setMaximum(365)  # Allow setting more than 1 month
        self.day_spin.setPlaceholderText("Ngày")
        self.day_spin.setToolTip("Số ngày trong tương lai")

        self.hour_spin = PlaceholderSpinBox(self)
        self.hour_spin.setMinimum(0)
        self.hour_spin.setMaximum(23)
        self.hour_spin.setPlaceholderText("Giờ")

        self.minute_spin = PlaceholderSpinBox(self)
        self.minute_spin.setMinimum(0)
        self.minute_spin.setMaximum(59)
        self.minute_spin.setPlaceholderText("Phút")
        # END: Replace with this block
        self.toggle_view_btn = QPushButton(
            icon=self.style().standardIcon(
                QStyle.StandardPixmap.SP_FileDialogDetailedView
            )
        )
        self.toggle_view_btn.setToolTip("Chuyển sang chế độ chọn lịch")
        self.toggle_view_btn.setFixedSize(32, 32)
        self.toggle_view_btn.clicked.connect(self.switch_to_calendar_view)
        spinbox_layout.addWidget(self.day_spin)
        spinbox_layout.addWidget(QLabel(":"))
        spinbox_layout.addWidget(self.hour_spin)
        spinbox_layout.addWidget(QLabel(":"))
        spinbox_layout.addWidget(self.minute_spin)
        spinbox_layout.addStretch()
        spinbox_layout.addWidget(self.toggle_view_btn)
        self.datetime_edit = QDateTimeEdit(self)
        self.datetime_edit.setCalendarPopup(True)
        self.datetime_edit.dateTimeChanged.connect(self.sync_spins_from_calendar)
        self.view_stack.addWidget(spinbox_view)
        self.view_stack.addWidget(self.datetime_edit)
        self.sound_combo = QComboBox(self)
        self.layout.addWidget(QLabel("Chọn âm thanh thông báo:"))
        self.layout.addWidget(self.sound_combo)
        self.populate_sounds(note_title)
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Reset
        )
        self.button_box.button(QDialogButtonBox.StandardButton.Reset).setText(
            "Xóa Báo Thức"
        )
        self.layout.addWidget(self.button_box)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.StandardButton.Reset).clicked.connect(
            self.reset_notification
        )
        self.reset = False

    # [!NEW!] Add this entire method.
    def set_from_due_time(self, due_time_iso_str: str):
        """Calculates the remaining time from now until the due time and populates the widgets."""
        if not due_time_iso_str:
            return

        due_dt = QDateTime.fromString(due_time_iso_str, Qt.DateFormat.ISODateWithMs)
        due_dt.setTimeSpec(Qt.TimeSpec.UTC) # Ensure it's interpreted as UTC
        due_dt_local = due_dt.toLocalTime() # Convert to local time for calculations with `now`

        now = QDateTime.currentDateTime()

        if now >= due_dt_local:
            # The alarm is in the past, do not pre-fill.
            return

        # Calculate the delta in seconds
        delta_seconds = now.secsTo(due_dt_local)

        # Convert seconds to days, hours, minutes
        days = delta_seconds // 86400
        remaining_seconds = delta_seconds % 86400
        hours = remaining_seconds // 3600
        minutes = (remaining_seconds % 3600) // 60
        
        # Block signals to prevent feedback loops while setting values
        self.day_spin.blockSignals(True)
        self.hour_spin.blockSignals(True)
        self.minute_spin.blockSignals(True)
        self.datetime_edit.blockSignals(True)

        self.day_spin.setValue(days)
        self.hour_spin.setValue(hours)
        self.minute_spin.setValue(minutes)
        self.datetime_edit.setDateTime(due_dt_local)

        # Unblock signals
        self.day_spin.blockSignals(False)
        self.hour_spin.blockSignals(False)
        self.minute_spin.blockSignals(False)
        self.datetime_edit.blockSignals(False)

    # START: Replace the entire method
    def sync_spins_from_calendar(self, dt: QDateTime):
        """Calculates the offset from now to the selected datetime and updates spins."""
        now = QDateTime.currentDateTime()

        # If the selected time is in the past, reset spins to 0
        if now >= dt:
            self.day_spin.setValue(0)
            self.hour_spin.setValue(0)
            self.minute_spin.setValue(0)
            return

        # [!MODIFIED!] Correctly calculate remaining duration instead of absolute time.
        delta_seconds = now.secsTo(dt)
        days = delta_seconds // 86400
        remaining_seconds = delta_seconds % 86400
        hours = remaining_seconds // 3600
        minutes = (remaining_seconds % 3600) // 60

        self.day_spin.setValue(days)
        self.hour_spin.setValue(hours)
        self.minute_spin.setValue(minutes)

    # START: Replace the entire method
    def switch_to_calendar_view(self):
        """Calculates the future datetime based on spinbox offsets and switches view."""
        now = QDateTime.currentDateTime()
        days = self.day_spin.value()
        hours = self.hour_spin.value()
        minutes = self.minute_spin.value()

        # [!MODIFIED!] Correctly calculate the future datetime by adding durations.
        future_datetime = now.addDays(days)
        future_datetime = future_datetime.addSecs(hours * 3600)
        future_datetime = future_datetime.addSecs(minutes * 60)

        # Set the QDateTimeEdit widget, blocking signals to prevent feedback loops
        self.datetime_edit.blockSignals(True)
        # Set a minimum datetime to now to prevent setting past dates
        self.datetime_edit.setMinimumDateTime(now)
        self.datetime_edit.setDateTime(future_datetime)
        self.datetime_edit.blockSignals(False)

        # Switch to the calendar view
        self.view_stack.setCurrentIndex(1)

    def get_data(self):
        """Calculates and returns the notification datetime and sound without UI side-effects."""
        if self.reset:
            return None, None

        final_dt = None
        sound = self.sound_combo.currentData()

        # If the user is on the spinbox view, calculate the datetime from it.
        if self.view_stack.currentIndex() == 0:
            days = self.day_spin.value()
            hours = self.hour_spin.value()
            minutes = self.minute_spin.value()

            # If all spinboxes are at their minimum (0), it means no time is set.
            is_time_set = days > 0 or hours > 0 or minutes > 0
            if not is_time_set:
                return None, None  # Return None for both if no time is set

            # [!MODIFIED!] Correctly add the duration instead of setting the time.
            now = QDateTime.currentDateTime()
            future_datetime = now.addDays(days)
            future_datetime = future_datetime.addSecs(hours * 3600)
            future_datetime = future_datetime.addSecs(minutes * 60)
            final_dt = future_datetime
        # If the user is on the calendar view, get the datetime from the widget.
        else:
            final_dt = self.datetime_edit.dateTime()

        # For both views, if the final selected time is in the past or now, it's invalid.
        if final_dt and final_dt <= QDateTime.currentDateTime():
            return None, None  # Invalid time

        return final_dt, sound

    def populate_sounds(self, note_title):
        self.sound_combo.addItem("Mặc định (notification.wav)", "default")
        sounds_dir = "pyqt_dashboard/sounds"
        if not os.path.exists(sounds_dir):
            os.makedirs(sounds_dir)
            return
        note_title_lower = note_title.lower()
        found_match = False
        for filename in sorted(os.listdir(sounds_dir)):
            if filename.endswith((".wav", ".mp3")):
                self.sound_combo.addItem(filename, os.path.join(sounds_dir, filename))
                if os.path.splitext(filename)[0].lower() in note_title_lower:
                    self.sound_combo.setCurrentText(filename)
                    found_match = True
        if not found_match:
            self.sound_combo.setCurrentIndex(0)

    def reset_notification(self):
        self.reset = True
        self.accept()


# =============================================================================
# MODIFIED: Rich Text Editor with Enhanced Context Menu
# =============================================================================
class RichTextEditor(QTextEdit):
    editorLostFocus = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("noteEditor")
        self.setMouseTracking(True)

    def focusOutEvent(self, event):
        self.editorLostFocus.emit()
        super().focusOutEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            anchor = self.anchorAt(event.pos())
            if anchor:
                QDesktopServices.openUrl(QUrl(anchor))
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        self.viewport().setCursor(
            Qt.CursorShape.PointingHandCursor
            if self.anchorAt(event.pos())
            else Qt.CursorShape.IBeamCursor
        )
        super().mouseMoveEvent(event)

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        menu.addSeparator()
        cursor = self.textCursor()
        copy_action = menu.addAction("Copy")
        copy_action.setEnabled(cursor.hasSelection())
        copy_action.triggered.connect(self.copy)
        bold_action = menu.addAction("In đậm")
        bold_action.setEnabled(cursor.hasSelection())
        bold_action.triggered.connect(self.toggle_bold_selection)
        link_action = menu.addAction("Tạo/Sửa Link")
        link_action.setEnabled(cursor.hasSelection())
        link_action.triggered.connect(self.create_link)
        menu.exec(event.globalPos())

    def toggle_bold_selection(self):
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return
        char_format = cursor.charFormat()
        is_bold = char_format.fontWeight() == QFont.Weight.Bold
        new_format = QTextCharFormat()
        new_format.setFontWeight(QFont.Weight.Normal if is_bold else QFont.Weight.Bold)
        cursor.mergeCharFormat(new_format)
        self.mergeCurrentCharFormat(new_format)

    def create_link(self):
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return
        current_format = cursor.charFormat()
        existing_url = current_format.anchorHref()
        url, ok = QInputDialog.getText(self, "Tạo Link", "Nhập URL:", text=existing_url)
        if ok:
            if url:
                link_format = QTextCharFormat()
                link_format.setAnchor(True)
                link_format.setAnchorHref(url)
                link_format.setForeground(QColor("#42A5F5"))
                link_format.setFontUnderline(True)
                cursor.mergeCharFormat(link_format)
            else:
                link_format = QTextCharFormat()
                link_format.setAnchor(False)
                cursor.mergeCharFormat(link_format)


# =============================================================================
# MODIFIED: Note List Item Widget with Status Label
# =============================================================================
class NoteListItem(QWidget):
    def __init__(self, note_id, title, preview, modified_at):
        super().__init__()
        self.note_id = note_id
        self.setObjectName("noteListItem")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 8, 10, 8)
        main_layout.setSpacing(2)
        top_layout = QHBoxLayout()
        self.title_label = QLabel(title, objectName="noteTitle")
        self.timestamp_label = QLabel(
            format_relative_time(modified_at), objectName="noteTimestamp"
        )
        top_layout.addWidget(self.title_label)
        top_layout.addStretch()
        top_layout.addWidget(self.timestamp_label)
        self.preview_label = QLabel(preview, objectName="notePreview")
        self.status_label = QLabel("", objectName="noteStatus")  # NEW status label
        self.status_label.hide()  # Initially hidden
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.preview_label)
        main_layout.addWidget(self.status_label)  # Add to layout
        self.setMaximumHeight(90)  # Increased height for status

    def update_content(self, title, preview, modified_at):
        self.title_label.setText(title)
        self.preview_label.setText(preview)
        self.timestamp_label.setText(format_relative_time(modified_at))

    def update_status(self, text, color):  # NEW method
        if text:
            self.status_label.setText(text)
            self.status_label.setStyleSheet(f"font-weight: bold; color: {color};")
            self.status_label.show()
        else:
            self.status_label.hide()


# =============================================================================
# MODIFIED: Main Notes Tab Widget
# =============================================================================
class NotesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.notes_data = []  # This will act as an in-memory cache
        self.current_note_id = None
        # 🔄 Point to the new database file
        basedir = os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)
        ))  # Go up one level from modules to project root
        self.db_path = os.path.join(
            basedir, "data", "main_database.db"
        )  # Creates the full, absolute path

        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.setInterval(500)
        self.save_timer.timeout.connect(
            self._update_note_content_in_db
        )  # Renamed for clarity

        self.ui_update_timer = QTimer(self)
        self.ui_update_timer.setInterval(1000)
        self.ui_update_timer.timeout.connect(self._update_visible_item_statuses)
        self.ui_update_timer.start()

        # --- UI Setup (This part is unchanged) ---
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 10, 20, 20)
        main_layout.setSpacing(15)
        left_pane = QWidget(objectName="notesLeftPane")
        left_pane.setFixedWidth(300)
        left_layout = QVBoxLayout(left_pane)
        left_layout.setContentsMargins(8, 8, 8, 8)
        left_layout.setSpacing(8)
        header_widget = QWidget(objectName="notesListHeader")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(5)
        self.search_bar = QLineEdit(placeholderText="🔍 Tìm kiếm...")
        self.search_bar.setObjectName("notesSearchBar")
        self.add_new_button = QPushButton("➕")
        self.add_new_button.setObjectName("addNewButton")
        self.add_new_button.setToolTip("Thêm ghi chú mới")
        header_layout.addWidget(self.search_bar, 1)
        header_layout.addWidget(self.add_new_button)
        self.note_list_widget = QListWidget(objectName="notesList")
        left_layout.addWidget(header_widget)
        left_layout.addWidget(self.note_list_widget)
        right_pane = QWidget()
        right_layout = QVBoxLayout(right_pane)
        right_layout.setContentsMargins(0, 0, 0, 0)
        self.editor_stack = QStackedWidget()
        self.placeholder_label = QLabel(
            "Chọn một ghi chú để xem hoặc tạo ghi chú mới.",
            objectName="editorPlaceholder",
        )
        self.placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.editor = RichTextEditor()
        self.editor.setPlaceholderText("Vui lòng nhập...")
        self.editor_stack.addWidget(self.placeholder_label)
        self.editor_stack.addWidget(self.editor)
        right_layout.addWidget(self.editor_stack)
        main_layout.addWidget(left_pane)
        main_layout.addWidget(right_pane, 1)
        # --- End of UI Setup ---

        # --- Load Data and Connections ---
        self.load_notes_from_db()  # 🔄 Load from DB
        self.add_new_button.clicked.connect(self.add_new_note)
        self.note_list_widget.currentItemChanged.connect(self.display_note_content)
        self.editor.textChanged.connect(self.request_save_on_edit)
        self.editor.textChanged.connect(self._format_first_line)
        self.editor.editorLostFocus.connect(self.force_save_on_focus_out)
        self.note_list_widget.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.note_list_widget.customContextMenuRequested.connect(
            self.show_list_context_menu
        )
        self.search_bar.textChanged.connect(self._filter_note_list)
        self.populate_note_list()

    def keyPressEvent(self, event: QKeyEvent):  # Handle Del key
        if self.note_list_widget.hasFocus() and event.key() == Qt.Key.Key_Delete:
            current_item = self.note_list_widget.currentItem()
            if current_item:
                note_id = current_item.data(Qt.ItemDataRole.UserRole)
                self.delete_note(note_id)
        else:
            super().keyPressEvent(event)

    # --- Database Methods ---
    def load_notes_from_db(self):
        """Loads all notes from the SQLite database into the in-memory list."""
        try:
            con = sqlite3.connect(self.db_path)
            con.row_factory = sqlite3.Row  # This allows accessing columns by name
            cur = con.cursor()
            cur.execute("SELECT * FROM notes ORDER BY modified_at DESC")
            rows = cur.fetchall()
            # Convert rows to a list of dictionaries, which the rest of the app expects
            self.notes_data = [dict(row) for row in rows]
            con.close()
        except Exception as e:
            print(f"Error loading notes from DB: {e}")
            self.notes_data = []
        # After loading, we always refresh the visual list
        self.populate_note_list()

    def add_new_note(self):
        """Inserts a new blank note into the database."""
        note_id = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            con = sqlite3.connect(self.db_path)
            cur = con.cursor()
            cur.execute(
                "INSERT INTO notes (id, content_html, modified_at) VALUES (?, ?, ?)",
                (note_id, "", now_iso),
            )
            con.commit()
            con.close()
            # Reload from DB to get the new note and refresh the list
            self.load_notes_from_db()
            # Find and select the newly created note
            for i in range(self.note_list_widget.count()):
                item = self.note_list_widget.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == note_id:
                    self.note_list_widget.setCurrentItem(item)
                    break
            self.editor.setFocus()
        except Exception as e:
            print(f"Error adding new note to DB: {e}")

    def delete_note(self, note_id):
        """Deletes a note from the database."""
        reply = QMessageBox.question(
            self,
            "Xác nhận xóa",
            "Bạn có chắc muốn xóa ghi chú này?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                con = sqlite3.connect(self.db_path)
                cur = con.cursor()
                cur.execute("DELETE FROM notes WHERE id = ?", (note_id,))
                con.commit()
                con.close()
                was_current = self.current_note_id == note_id
                self.load_notes_from_db()  # Reload and refresh
                if was_current:
                    self.current_note_id = None
                    self.editor_stack.setCurrentWidget(self.placeholder_label)
            except Exception as e:
                print(f"Error deleting note from DB: {e}")

    def request_save_on_edit(self):
        self.save_timer.start()

    def force_save_on_focus_out(self):
        """
        Stops the debounce timer and immediately triggers a save.
        This is called when the editor loses focus.
        """
        if self.save_timer.isActive():
            self.save_timer.stop()
            self._update_note_content_in_db()

    def _update_note_content_in_db(self):
        """
        MODIFIED: Updates the current note in the DB and UI without reloading the whole list.
        This prevents losing focus while typing.
        """
        if not self.current_note_id:
            return

        note_in_memory = self.get_note_by_id(self.current_note_id)
        if (
            not note_in_memory
            or note_in_memory.get("content_html", "") == self.editor.toHtml()
        ):
            return  # Không có thay đổi để lưu

        new_html = self.editor.toHtml()
        new_timestamp = datetime.now(timezone.utc).isoformat()

        # --- 1. Cập nhật vào cơ sở dữ liệu (Database) ---
        try:
            con = sqlite3.connect(self.db_path)
            cur = con.cursor()
            cur.execute(
                "UPDATE notes SET content_html = ?, modified_at = ? WHERE id = ?",
                (new_html, new_timestamp, self.current_note_id),
            )
            con.commit()
            con.close()
        except Exception as e:
            print(f"Error updating note content in DB: {e}")
            return  # Dừng lại nếu có lỗi DB

        # --- 2. Cập nhật vào bộ nhớ đệm (in-memory cache) và sắp xếp lại ---
        note_in_memory["content_html"] = new_html
        note_in_memory["modified_at"] = new_timestamp
        self.notes_data.sort(key=lambda x: x.get("modified_at", ""), reverse=True)

        # --- 3. Cập nhật giao diện một cách "thông minh" ---
        found_item = None
        current_index = -1
        # Tìm item tương ứng trong QListWidget
        for i in range(self.note_list_widget.count()):
            item = self.note_list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == self.current_note_id:
                found_item = item
                current_index = i
                break

        if found_item:
            # Lấy widget con để cập nhật nội dung
            widget = self.note_list_widget.itemWidget(found_item)
            if widget:
                # Trích xuất lại tiêu đề và xem trước từ nội dung mới
                temp_doc = QTextEdit()
                temp_doc.setHtml(new_html)
                lines = temp_doc.toPlainText().split("\n")
                title = lines[0] if lines and lines[0].strip() else "(Không có tiêu đề)"
                preview = "\n".join(lines[1:3])
                # Gọi hàm cập nhật của widget
                widget.update_content(title, preview, new_timestamp)

            # Nếu item không ở trên cùng, di chuyển nó lên đầu danh sách
            if current_index > 0:
                # Tạm thời ngắt tín hiệu để tránh kích hoạt sự kiện thay đổi không mong muốn
                self.note_list_widget.currentItemChanged.disconnect(
                    self.display_note_content
                )

                # Lấy item ra khỏi vị trí cũ và chèn vào đầu
                taken_item = self.note_list_widget.takeItem(current_index)
                self.note_list_widget.insertItem(0, taken_item)

                # Đặt lại item hiện tại là item vừa di chuyển để giữ focus
                self.note_list_widget.setCurrentItem(taken_item)

                # Kết nối lại tín hiệu
                self.note_list_widget.currentItemChanged.connect(
                    self.display_note_content
                )

    def open_notification_dialog(self, note_id):
        """Opens dialog to set notification and updates the database."""
        note = self.get_note_by_id(note_id)
        if not note:
            return

        temp_doc = QTextEdit()
        temp_doc.setHtml(note.get("content_html", ""))
        title = temp_doc.toPlainText().split("\n")[0]

        dialog = SetNotificationDialog(title, self)
        
        # [!MODIFIED!] Use the new method to correctly pre-fill the dialog.
        if note.get("due_time"):
            dialog.set_from_due_time(note["due_time"])

        if note.get("sound_file"):
            index = dialog.sound_combo.findData(note["sound_file"])
            if index != -1:
                dialog.sound_combo.setCurrentIndex(index)

        if dialog.exec():
            dt, sound = dialog.get_data()
            due_time_str = None
            sound_file_str = None
            notified_int = 0
            if dt is not None and sound is not None:  # Not reset
                due_time_str = dt.toUTC().toString(Qt.DateFormat.ISODateWithMs)
                sound_file_str = sound

            try:
                con = sqlite3.connect(self.db_path)
                cur = con.cursor()
                cur.execute(
                    "UPDATE notes SET due_time = ?, sound_file = ?, notified = ? WHERE id = ?",
                    (due_time_str, sound_file_str, notified_int, note_id),
                )
                con.commit()
                con.close()
                self.load_notes_from_db()  # Reload to reflect changes
            except Exception as e:
                print(f"Error updating notification in DB: {e}")

    # --- UI Update Methods (largely unchanged, but now rely on DB-loaded data) ---
    def populate_note_list(self):
        # Safely disconnect the signal to prevent errors on initial run
        try:
            self.note_list_widget.currentItemChanged.disconnect(
                self.display_note_content
            )
        except TypeError:
            pass  # Ignore the error if the signal was not connected

        self.note_list_widget.clear()

        current_id_to_restore = self.current_note_id

        for note in self.notes_data:
            self._add_item_to_list_widget(note)

        # Reconnect the signal after populating the list
        self.note_list_widget.currentItemChanged.connect(self.display_note_content)

        # Restore selection if a note was previously selected
        if current_id_to_restore:
            for i in range(self.note_list_widget.count()):
                item = self.note_list_widget.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == current_id_to_restore:
                    self.note_list_widget.setCurrentRow(
                        i, QItemSelectionModel.SelectionFlag.ClearAndSelect
                    )
                    break

    def _add_item_to_list_widget(self, note):
        plain_content = QTextEdit()
        plain_content.setHtml(note.get("content_html", ""))
        lines = plain_content.toPlainText().split("\n")
        title = lines[0] if lines and lines[0].strip() else "(Không có tiêu đề)"
        preview = "\n".join(lines[1:3])
        list_item_widget = NoteListItem(
            note["id"], title, preview, note.get("modified_at")
        )
        list_widget_item = QListWidgetItem()
        list_widget_item.setSizeHint(list_item_widget.sizeHint())
        list_widget_item.setData(Qt.ItemDataRole.UserRole, note["id"])
        self.note_list_widget.addItem(list_widget_item)
        self.note_list_widget.setItemWidget(list_widget_item, list_item_widget)
        return list_widget_item

    def display_note_content(self, current_item, previous_item):
        if not current_item:
            self.current_note_id = None
            self.editor.textChanged.disconnect(self.request_save_on_edit)
            self.editor.setHtml("")
            self.editor.textChanged.connect(self.request_save_on_edit)
            self.editor_stack.setCurrentWidget(self.placeholder_label)
            return

        self.current_note_id = current_item.data(Qt.ItemDataRole.UserRole)
        note = self.get_note_by_id(self.current_note_id)
        if note:
            self.editor.textChanged.disconnect(self.request_save_on_edit)
            self.editor.setHtml(note.get("content_html", ""))
            self.editor.textChanged.connect(self.request_save_on_edit)
            self.editor_stack.setCurrentWidget(self.editor)

    def get_note_by_id(self, note_id):
        return next(
            (note for note in self.notes_data if note.get("id") == note_id), None
        )

    def show_list_context_menu(self, pos):
        item = self.note_list_widget.itemAt(pos)
        if not item:
            return
        note_id = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        set_notification_action = menu.addAction("🔔 Đặt Thông báo...")
        delete_action = menu.addAction("🗑️ Xóa Ghi Chú")
        action = menu.exec(self.note_list_widget.mapToGlobal(pos))
        if action == delete_action:
            self.delete_note(note_id)
        elif action == set_notification_action:
            self.open_notification_dialog(note_id)

    def _update_visible_item_statuses(self):
        # This method's logic is correct and does not need to change
        now_utc = datetime.now(timezone.utc)
        for i in range(self.note_list_widget.count()):
            item = self.note_list_widget.item(i)
            if item.isHidden():
                continue
            widget = self.note_list_widget.itemWidget(item)
            note_id = item.data(Qt.ItemDataRole.UserRole)
            note = self.get_note_by_id(note_id)
            if note and widget:
                status_text, status_color = "", "gray"
                if note.get("due_time") and note.get("notified", 0) == 0:
                    due_time = datetime.fromisoformat(
                        note["due_time"].replace("Z", "+00:00")
                    )
                    delta = due_time - now_utc
                    if delta.total_seconds() > 0:
                        days, rem = divmod(delta.seconds, 86400)
                        days += delta.days
                        hours, rem = divmod(rem, 3600)
                        minutes, seconds = divmod(rem, 60)
                        if days > 0:
                            status_text = f"{days} ngày {hours} giờ nữa"
                        elif hours > 0:
                            status_text = f"{hours} giờ {minutes} phút nữa"
                        elif minutes > 0:
                            status_text = f"{minutes} phút {seconds} giây nữa"
                        else:
                            status_text = f"{seconds} giây nữa"
                        status_color = "#FFA500"
                widget.update_status(status_text, status_color)
                widget.timestamp_label.setText(
                    format_relative_time(note.get("modified_at"))
                )

    def _filter_note_list(self, search_text):
        # This method's logic is correct and does not need to change
        search_text_lower = search_text.lower().strip()
        for i in range(self.note_list_widget.count()):
            item = self.note_list_widget.item(i)
            note_id = item.data(Qt.ItemDataRole.UserRole)
            note_data = self.get_note_by_id(note_id)
            if note_data:
                temp_doc = QTextEdit()
                temp_doc.setHtml(note_data.get("content_html", ""))
                note_content_plain = temp_doc.toPlainText()
                if search_text_lower in note_content_plain.lower():
                    item.setHidden(False)
                else:
                    item.setHidden(True)

    def _format_first_line(self):
        """A slot to automatically format the first line of the editor to be bold."""
        # Block signals to prevent this function from being called recursively
        self.editor.blockSignals(True)

        # Save the current cursor position to restore it later
        original_cursor = self.editor.textCursor()

        # Create a new cursor to perform the formatting without moving the user's cursor
        format_cursor = self.editor.textCursor()
        format_cursor.movePosition(QTextCursor.MoveOperation.Start)
        format_cursor.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.MoveMode.KeepAnchor)

        # Create a format for bold text
        bold_format = QTextCharFormat()
        bold_format.setFontWeight(QFont.Weight.Bold)
        
        # Apply the bold format to the first line
        format_cursor.mergeCharFormat(bold_format)

        # Restore the original cursor position
        self.editor.setTextCursor(original_cursor)

        # Unblock signals to allow normal operation
        self.editor.blockSignals(False)
