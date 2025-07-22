import sys
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser, QTextEdit, QPushButton, QLabel
from PyQt6.QtCore import Qt, QThread, QObject, pyqtSignal
from PyQt6.QtGui import QKeyEvent, QTextCursor

# Import the new Gemini client from services
from services.ai_services.gemini_client import get_gemini_response
from services.ai_services.ai_controller import process_ai_command
from services import memory_manager

# --- Worker for Threaded API Calls ---
class GeminiWorker(QObject):
    """
    A worker object that runs in a separate thread to make non-blocking API calls.
    """
    response_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, prompt, memories):
        super().__init__()
        self.prompt = prompt
        self.memories = memories

    def run(self):
        """Execute the API call with memories and emit the result."""
        try:
            response = get_gemini_response(self.prompt, self.memories)
            self.response_ready.emit(response)
        except Exception as e:
            self.error_occurred.emit(str(e))


class HomeTab(QWidget):
    # Remove the old card clicked signals
    # notes_card_clicked = pyqtSignal()
    # password_card_clicked = pyqtSignal()
    # telegram_card_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("homeTab")
        self.thread = None
        self.worker = None

        # --- Main Layout ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # --- Chat History Display ---
        self.chat_display = QTextBrowser(self)
        self.chat_display.setOpenExternalLinks(True) # Allow opening links
        self.chat_display.setStyleSheet("border: none; font-size: 15px; background-color: #1E1F22; border-radius: 8px; padding: 10px;")
        self.chat_display.setHtml('<p style="color: #999;">Chào sếp, sếp cần gì?</p>')

        # --- Input Area Layout ---
        input_layout = QHBoxLayout()
        self.input_field = QTextEdit(self)
        self.input_field.setPlaceholderText("Nhập câu hỏi của bạn ở đây...")
        self.input_field.setObjectName("chatInputField")
        self.input_field.setFixedHeight(50) # Start with a reasonable height
        self.input_field.installEventFilter(self) # To catch Enter key press

        self.send_button = QPushButton("Gửi")
        self.send_button.setObjectName("sendButton")
        self.send_button.setFixedSize(80, 50)

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)

        main_layout.addWidget(self.chat_display)
        main_layout.addLayout(input_layout)

        # --- Connect Signals ---
        self.send_button.clicked.connect(self.send_message)

    def eventFilter(self, obj, event):
        """Filters events on the input field to handle Enter/Shift+Enter."""
        if obj is self.input_field and event.type() == QKeyEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                if not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                    # Enter pressed without Shift: send message
                    self.send_message()
                    return True # Event handled
                # else: Shift+Enter will be handled as a normal newline by QTextEdit
        return super().eventFilter(obj, event)

    def send_message(self):
        """
        Handles sending messages, checking for commands, and interacting with the AI.
        """
        user_text = self.input_field.toPlainText().strip()
        if not user_text:
            return

        self.add_message_to_display(user_text, is_user=True)
        self.input_field.clear()

        # --- NEW: Command Processing Logic ---
        command = process_ai_command(user_text)
        if command:
            tool_name = command.get("tool_name")
            if tool_name == "add_memory":
                text_to_remember = command["parameters"]["text"]
                if memory_manager.add_memory(text_to_remember):
                    self.add_message_to_display("Đã ghi nhớ!", is_user=False, is_system=True)
                else:
                    self.add_message_to_display("Lỗi: Không thể ghi nhớ.", is_user=False, is_error=True)
            elif tool_name == "clear_memory":
                if memory_manager.clear_all_memories():
                    self.add_message_to_display("Đã xóa toàn bộ bộ nhớ!", is_user=False, is_system=True)
                else:
                    self.add_message_to_display("Lỗi: Không thể xóa bộ nhớ.", is_user=False, is_error=True)
            return # Stop here, don't send to AI

        # --- If not a command, proceed with normal chat ---
        # self.chat_display.append("<p><i>AI đang nghĩ...</i></p>")  # Removed as requested

        # Fetch memories to provide context
        memories = memory_manager.get_all_memories()

        self.thread = QThread()
        # Pass memories to the worker
        self.worker = GeminiWorker(user_text, memories)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.response_ready.connect(self.handle_ai_response)
        self.worker.error_occurred.connect(self.handle_ai_error)
        
        self.worker.response_ready.connect(self.thread.quit)
        self.worker.response_ready.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        
        self.thread.start()

    def handle_ai_response(self, response_text):
        """Slot to handle the successful response from the AI worker."""
        # This is the corrected and more robust way to remove the "thinking..." message.
        # It avoids the selection method that was causing the crash.
        current_html = self.chat_display.toHtml()
        thinking_message = "<p><i>AI đang nghĩ...</i></p>"
        
        # Find the last occurrence of the thinking message and remove it
        last_occurrence_index = current_html.rfind(thinking_message)
        if last_occurrence_index != -1:
            new_html = current_html[:last_occurrence_index]
            self.chat_display.setHtml(new_html)
            
            # Move the cursor to the end after updating the content
            cursor = self.chat_display.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.chat_display.setTextCursor(cursor)

        # Add the AI's actual response
        self.add_message_to_display(response_text, is_user=False)
        
    def handle_ai_error(self, error_message):
        """Slot to handle errors from the AI worker."""
        # You can format the error message here
        self.add_message_to_display(f"Lỗi: {error_message}", is_user=False, is_error=True)

    def add_message_to_display(self, text: str, is_user: bool, is_error: bool = False, is_system: bool = False):
        """Appends a formatted message to the chat display with no background bubbles and consistent text color."""
        # Sanitize and format text for HTML
        text = text.replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')
        
        if is_user:
            # User messages on the RIGHT, plain text, no background
            formatted_text = f'''
        <table width="100%">
            <tr>
                <td align="right">
                    <p style="color: #E6E6E6;">
                        {text}
                    </p>
                </td>
            </tr>
        </table>
        '''
        elif is_error:
            formatted_text = f'<p style="color: #F3726A;">Lỗi hệ thống:<br>{text}</p>'
        elif is_system:
            formatted_text = f'<p style="text-align: center; color: #888;"><i>{text}</i></p>'
        else: # AI response
            # AI messages on the LEFT, plain text, no background
            formatted_text = f'''
        <table width="100%">
            <tr>
                <td align="left">
                    <p style="color: #E6E6E6;">
                        AI:<br>{text}
                    </p>
                </td>
            </tr>
        </table>
        '''
        self.chat_display.append(formatted_text) 