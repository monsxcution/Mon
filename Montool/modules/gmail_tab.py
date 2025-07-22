import os
import json
import sqlite3
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QListWidget, QTextBrowser, QLabel, QComboBox, QMessageBox, QListWidgetItem, QApplication)
from PyQt6.QtCore import QUrl, Qt, QObject, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QDesktopServices
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import base64
from bs4 import BeautifulSoup

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/userinfo.email', 'openid']

# --- START: UPDATED FILE PATHS ---
basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Go up one level to project root
CREDENTIALS_PATH = os.path.join(basedir, 'data', 'credentials.json')
TOKEN_PICKLE_PATH = os.path.join(basedir, 'data', 'gmail_tokens.pkl')
DATABASE_PATH = os.path.join(basedir, 'data', 'main_database.db') # Use SQLite database
# --- END: UPDATED FILE PATHS ---

class AccountSwitcher(QObject):
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import base64
from bs4 import BeautifulSoup

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/userinfo.email', 'openid']

# --- START: UPDATED FILE PATHS ---
basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Go up one level to project root
CREDENTIALS_PATH = os.path.join(basedir, 'data', 'credentials.json')
TOKEN_PICKLE_PATH = os.path.join(basedir, 'data', 'gmail_tokens.pkl')
DATABASE_PATH = os.path.join(basedir, 'data', 'main_database.db') # Use SQLite database
# --- END: UPDATED FILE PATHS ---

class AccountSwitcher(QObject):
    """Worker class for switching Gmail accounts without blocking UI"""
    finished = pyqtSignal(dict)

    def __init__(self, accounts, email):
        super().__init__()
        self.accounts = accounts
        self.email = email

    def run(self):
        try:
            creds = self.accounts[self.email]
            if creds and hasattr(creds, 'expired') and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            
            service = build('gmail', 'v1', credentials=creds)
            self.finished.emit({'success': True, 'service': service, 'email': self.email})
        except Exception as e:
            self.finished.emit({'success': False, 'error': str(e), 'email': self.email})
    """
    A worker that fetches the full content of an email in a separate thread.
    """
    finished = pyqtSignal(dict)

    def __init__(self, service, message_id):
        super().__init__()
        self.service = service
        self.message_id = message_id

    def run(self):
        """Executes the long-running task."""
        try:
            print(f"Fetching email: {self.message_id}")  # Debug log
            msg = self.service.users().messages().get(userId='me', id=self.message_id, format='full').execute()
            print(f"Email fetched successfully: {self.message_id}")  # Debug log
            self.finished.emit({'success': True, 'data': msg, 'id': self.message_id})
        except Exception as e:
            print(f"Error fetching email {self.message_id}: {e}")  # Debug log
            self.finished.emit({'success': False, 'error': str(e), 'id': self.message_id})

class GmailTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("gmailTab")
        self.service = None
        self.accounts = {}
        self.current_account = None
        self.active_workers = {} # Use a dictionary to track workers by message_id

        # --- UI Setup ---
        layout = QVBoxLayout(self)
        
        top_bar_layout = QHBoxLayout()
        self.account_switcher = QComboBox()
        self.account_switcher.setPlaceholderText("Chọn tài khoản...")
        self.account_switcher.currentIndexChanged.connect(self.switch_account)
        self.add_account_btn = QPushButton("➕ Thêm tài khoản")
        self.add_account_btn.clicked.connect(self.add_account)
        self.refresh_btn = QPushButton("🔄 Tải lại")
        self.refresh_btn.clicked.connect(self.force_refresh)
        
        top_bar_layout.addWidget(QLabel("Tài khoản:"))
        top_bar_layout.addWidget(self.account_switcher, 1)
        top_bar_layout.addWidget(self.add_account_btn)
        top_bar_layout.addWidget(self.refresh_btn)
        
        content_layout = QHBoxLayout()
        self.email_list_widget = QListWidget()
        self.email_list_widget.itemClicked.connect(self.on_email_selected)
        self.email_content_browser = QTextBrowser()
        
        # Add status messages
        welcome_item = QListWidgetItem("📭 Chọn tài khoản để xem email")
        welcome_item.setFlags(Qt.ItemFlag.NoItemFlags)
        self.email_list_widget.addItem(welcome_item)
        self.email_content_browser.setHtml("<h3>🚀 Chào mừng đến với Gmail Manager</h3><p>Vui lòng chọn tài khoản để bắt đầu.</p>")
        
        content_layout.addWidget(self.email_list_widget, 1)
        content_layout.addWidget(self.email_content_browser, 2)
        
        layout.addLayout(top_bar_layout)
        layout.addLayout(content_layout)

        self.load_saved_accounts()
        self.init_gmail_cache()

    def init_gmail_cache(self):
        """Initialize Gmail cache table in SQLite database"""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            # Drop and recreate the table to ensure correct schema
            cursor.execute('DROP TABLE IF EXISTS gmail_cache')
            cursor.execute('''
                CREATE TABLE gmail_cache (
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
        except sqlite3.Error as e:
            print(f"Database error initializing Gmail cache: {e}")

    def load_email_from_cache(self, message_id):
        """Load email content from SQLite cache"""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute('SELECT content FROM gmail_cache WHERE message_id = ?', (message_id,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else None
        except sqlite3.Error as e:
            print(f"Database error loading from cache: {e}")
            return None

    def save_email_to_cache(self, message_id, account_email, subject, sender, content):
        """Save email content to SQLite cache"""
        try:
            from datetime import datetime
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # Convert content dict to HTML string for storage
            if isinstance(content, dict):
                content_html = f"""
                <p><b>Ngày:</b> {content['date']}</p>
                <p><b>Từ:</b> {content['sender']}</p>
                <p><b>Chủ đề:</b> {content['subject']}</p>
                <hr>
                <div>{content['body']}</div>
                """
            else:
                content_html = str(content)
            
            cursor.execute('''
                INSERT OR REPLACE INTO gmail_cache 
                (message_id, account_email, subject, sender, content, cached_at) 
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (message_id, account_email, subject, sender, content_html, datetime.now().isoformat()))
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"Database error saving to cache: {e}")
        except Exception as e:
            print(f"Lỗi khi lưu cache email: {e}")

    def add_account(self):
        """Add a new Gmail account with better user experience"""
        if not os.path.exists(CREDENTIALS_PATH):
            QMessageBox.critical(self, "Lỗi", f"Không tìm thấy file credentials tại:\n{CREDENTIALS_PATH}")
            return
            
        # Show loading message
        self.account_switcher.setEnabled(False)
        self.add_account_btn.setText("🔄 Đang xác thực...")
        self.add_account_btn.setEnabled(False)
        
        try:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
            service = build('oauth2', 'v2', credentials=creds)
            user_info = service.userinfo().get().execute()
            email = user_info.get('email')
            
            if email:
                self.accounts[email] = creds
                self.save_accounts()
                self.update_account_switcher()
                self.account_switcher.setCurrentText(email)
                QMessageBox.information(self, "Thành công", f"Đã thêm tài khoản {email}!")
            else:
                QMessageBox.warning(self, "Lỗi", "Không thể lấy thông tin tài khoản.")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi xác thực", f"Lỗi khi thêm tài khoản:\n{str(e)}")
        finally:
            # Restore UI
            self.account_switcher.setEnabled(True)
            self.add_account_btn.setText("➕ Thêm tài khoản")
            self.add_account_btn.setEnabled(True)

    def switch_account(self, index):
        email = self.account_switcher.itemText(index)
        if email and email in self.accounts:
            self.current_account = email
            self.email_list_widget.clear()
            self.email_content_browser.setText("<h3>⏳ Đang chuyển tài khoản...</h3>")
            
            # Disable UI to prevent multiple requests
            self.account_switcher.setEnabled(False)
            self.add_account_btn.setEnabled(False)
            self.refresh_btn.setEnabled(False)
            
            # Create thread for account switching
            thread = QThread()
            worker = AccountSwitcher(self.accounts, email)
            worker.moveToThread(thread)
            
            # Connect signals
            thread.started.connect(worker.run)
            worker.finished.connect(self.on_account_switch_finished)
            
            # Cleanup
            worker.finished.connect(thread.quit)
            worker.finished.connect(worker.deleteLater)
            thread.finished.connect(thread.deleteLater)
            
            # Start thread
            thread.start()
        else:
            self.service = None
            self.email_list_widget.clear()
            self.email_content_browser.clear()

    def on_account_switch_finished(self, result):
        """Handle account switch completion"""
        # Re-enable UI
        self.account_switcher.setEnabled(True)
        self.add_account_btn.setEnabled(True) 
        self.refresh_btn.setEnabled(True)
        
        if result.get('success'):
            self.service = result.get('service')
            self.current_account = result.get('email')
            self.load_emails()
            self.email_content_browser.clear()
        else:
            error_msg = f"<h3>❌ Lỗi chuyển tài khoản</h3><p>{result.get('error')}</p>"
            self.email_content_browser.setHtml(error_msg)

    def force_refresh(self):
        """Refreshes the email list or the currently selected email."""
        current_item = self.email_list_widget.currentItem()
        if self.email_content_browser.toPlainText() and current_item:
            # If viewing an email, refresh its content
            self.display_email(current_item.data(Qt.ItemDataRole.UserRole), force_network=True)
        else:
            # Otherwise, refresh the email list
            self.load_emails()

    def load_emails(self):
        if not self.service:
            self.email_list_widget.clear()
            return
            
        # Show loading message
        self.email_list_widget.clear()
        loading_item = QListWidgetItem("📧 Đang tải email...")
        loading_item.setFlags(Qt.ItemFlag.NoItemFlags)  # Make it unclickable
        self.email_list_widget.addItem(loading_item)
        
        # Process events to show loading message immediately
        QApplication.processEvents()
        
        # Load emails directly
        self._load_emails_async()
        
    def _load_emails_async(self):
        """Load emails asynchronously to prevent UI blocking"""
        try:
            results = self.service.users().messages().list(userId='me', labelIds=['INBOX'], maxResults=20).execute()
            messages = results.get('messages', [])
            self.email_list_widget.clear()
            
            if not messages:
                no_mail_item = QListWidgetItem("📭 Không có thư nào.")
                no_mail_item.setFlags(Qt.ItemFlag.NoItemFlags)
                self.email_list_widget.addItem(no_mail_item)
            else:
                # Load emails in smaller batches to prevent UI blocking
                for i, message in enumerate(messages[:15]):  # Limit to 15 emails initially
                    try:
                        msg = self.service.users().messages().get(userId='me', id=message['id'], format='metadata', metadataHeaders=['Subject', 'From']).execute()
                        headers = msg['payload']['headers']
                        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(Không có chủ đề)')
                        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Không rõ người gửi').split('<')[0].strip().replace('"', '')
                        
                        # Truncate long subjects/senders
                        if len(subject) > 50:
                            subject = subject[:47] + "..."
                        if len(sender) > 30:
                            sender = sender[:27] + "..."
                            
                        list_item = QListWidgetItem(f"Từ: {sender}\nChủ đề: {subject}")
                        list_item.setData(Qt.ItemDataRole.UserRole, message['id'])
                        self.email_list_widget.addItem(list_item)
                        
                        # Process events every few items to keep UI responsive
                        if i % 5 == 0:
                            QApplication.processEvents()
                    except Exception as e:
                        print(f"Error loading email {message['id']}: {e}")
                        continue
        except Exception as e:
            self.email_list_widget.clear()
            error_item = QListWidgetItem(f"❌ Lỗi tải email: {str(e)}")
            error_item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.email_list_widget.addItem(error_item)

    def on_email_selected(self, item):
        message_id = item.data(Qt.ItemDataRole.UserRole)
        if message_id:
            self.display_email(message_id)

    def display_email(self, message_id, force_network=False):
        if not self.current_account: 
            return

        # Check SQLite cache first, unless forced to refresh
        if not force_network:
            cached_content = self.load_email_from_cache(message_id)
            if cached_content:
                self.render_email_content(cached_content)
                return

        # If already fetching this email, don't start another worker
        if message_id in self.active_workers:
            return

        self.email_content_browser.setText("<h3>Đang tải nội dung email...</h3>")
        
        try:
            # Create thread and worker
            thread = QThread()
            worker = EmailFetcher(self.service, message_id)
            worker.moveToThread(thread)  # Move worker to thread
            
            # Store the thread reference
            self.active_workers[message_id] = thread
            
            # Connect signals properly
            thread.started.connect(worker.run)
            worker.finished.connect(self.on_fetch_finished)
            
            # Cleanup connections
            worker.finished.connect(thread.quit)
            worker.finished.connect(worker.deleteLater)
            thread.finished.connect(thread.deleteLater)
            thread.finished.connect(lambda: self.active_workers.pop(message_id, None))
            
            # Start the thread
            thread.start()
            
            # Fallback: If thread doesn't start within 5 seconds, try direct loading
            QTimer.singleShot(5000, lambda: self._fallback_email_load(message_id) if message_id in self.active_workers else None)
            
        except Exception as e:
            print(f"Error creating email thread: {e}")
            self._fallback_email_load(message_id)

    def _fallback_email_load(self, message_id):
        """Fallback method to load email directly if threading fails"""
        try:
            print(f"Using fallback loading for email: {message_id}")
            msg = self.service.users().messages().get(userId='me', id=message_id, format='full').execute()
            processed_content = self.process_email_payload(msg)
            self.render_email_content(processed_content)
            
            # Save to cache
            headers = msg.get('payload', {}).get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(Không có chủ đề)')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            self.save_email_to_cache(message_id, self.current_account, subject, sender, processed_content)
        except Exception as e:
            self.email_content_browser.setHtml(f"<h3>❌ Lỗi tải email</h3><p>{str(e)}</p>")

    def on_fetch_finished(self, result):
        print(f"Fetch finished: {result}")  # Debug log
        
        if not result.get('success'):
            error_msg = f"<h3>❌ Lỗi tải email</h3><p>{result.get('error')}</p>"
            self.email_content_browser.setHtml(error_msg)
            return

        msg = result.get('data', {})
        message_id = result.get('id')
        
        try:
            # Process and render the email
            processed_content = self.process_email_payload(msg)
            self.render_email_content(processed_content)

            # Save to SQLite cache in background to avoid blocking UI
            headers = msg.get('payload', {}).get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(Không có chủ đề)')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            
            # Use processEvents to defer cache saving and avoid UI blocking
            QApplication.processEvents()
            self.save_email_to_cache(message_id, self.current_account, subject, sender, processed_content)
        except Exception as e:
            print(f"Error processing email: {e}")  # Debug log
            self.email_content_browser.setHtml(f"<h3>❌ Lỗi xử lý email</h3><p>{str(e)}</p>")

    def process_email_payload(self, msg):
        payload = msg.get('payload', {})
        headers = payload.get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(Không có chủ đề)')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Không rõ người gửi')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Không rõ ngày')

        body = ""
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/html':
                    if 'data' in part['body']:
                        data = part['body']['data']
                        body = base64.urlsafe_b64decode(data.encode('ASCII')).decode('utf-8', 'ignore')
                        break
        if not body and 'body' in payload and 'data' in payload['body']:
            data = payload['body']['data']
            body = base64.urlsafe_b64decode(data.encode('ASCII')).decode('utf-8', 'ignore')
        
        # Clean HTML and apply white color
        soup = BeautifulSoup(body, 'html.parser')
        for tag in soup.find_all(True, {'style': True}):
            del tag['style']
        for tag in soup.find_all('font'):
            tag.unwrap()
        
        # Add white color to all text elements
        for tag in soup.find_all(['p', 'div', 'span', 'td', 'th', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            tag['style'] = 'color: white !important;'
        
        cleaned_body = str(soup)

        return {
            'date': date, 
            'sender': sender, 
            'subject': subject, 
            'body': cleaned_body
        }

    def render_email_content(self, content):
        # Handle both dict and string content formats
        if isinstance(content, dict):
            display_html = f"""
            <html>
                <head>
                    <style>
                        body {{ font-family: sans-serif; font-size: 14px; color: white !important; background-color: #1a1d21; }}
                        p, div, span, td, th, li, h1, h2, h3, h4, h5, h6, a {{ color: white !important; }}
                        hr {{ border-color: #444; }}
                        b, strong {{ color: #00e0ff !important; }}
                    </style>
                </head>
                <body>
                    <p><b>Ngày:</b> {content['date']}</p>
                    <p><b>Từ:</b> {content['sender']}</p>
                    <p><b>Chủ đề:</b> {content['subject']}</p>
                    <hr>
                    <div style="color: white !important;">{content['body']}</div>
                </body>
            </html>
            """
        else:
            # Handle string content (cached content)
            display_html = f"""
            <html>
                <head>
                    <style>
                        body {{ font-family: sans-serif; font-size: 14px; color: white !important; background-color: #1a1d21; }}
                        p, div, span, td, th, li, h1, h2, h3, h4, h5, h6, a {{ color: white !important; }}
                    </style>
                </head>
                <body>
                    <div style="color: white !important;">{content}</div>
                </body>
            </html>
            """
        
        self.email_content_browser.setHtml(display_html)

    def save_accounts(self):
        with open(TOKEN_PICKLE_PATH, 'wb') as token_file:
            pickle.dump(self.accounts, token_file)

    def load_saved_accounts(self):
        if os.path.exists(TOKEN_PICKLE_PATH):
            with open(TOKEN_PICKLE_PATH, 'rb') as token_file:
                self.accounts = pickle.load(token_file)
            self.update_account_switcher()
            if self.accounts:
                self.account_switcher.setCurrentIndex(0)

    def update_account_switcher(self):
        self.account_switcher.blockSignals(True)
        self.account_switcher.clear()
        if self.accounts:
            self.account_switcher.addItems(self.accounts.keys())
        self.account_switcher.blockSignals(False)
 