# 📱 Telegram Dashboard v2.2.0

Một dashboard toàn diện để quản lý mật khẩu, ghi chú, nhắc nhở, tài khoản Facebook và proxy với xác thực bảo mật cho Telegram automation.

## 🏗️ Cấu Trúc Thư Mục

```
📁 Main/                                    # Thư mục gốc của dự án
├── 📄 Main.py                             # ⭐ File chính Flask app với tất cả routes và logic
├── 📄 index.html                          # 🌐 Giao diện chính của web dashboard
├── 📄 indexbackup.html                    # 💾 Backup của giao diện chính
├── 📄 requirements.txt                    # 📋 Danh sách dependencies Python
├── 📄 package.json                        # 📦 Cấu hình Node.js và metadata dự án
├── 📄 package-lock.json                   # 🔒 Lock file cho Node.js dependencies
├── 📄 .gitignore                          # 🚫 File cấu hình Git ignore
├── 📄 README.md                           # 📖 Documentation dự án (file này)
│
├── 📁 __pycache__/                        # 🐍 Cache files của Python
│   └── 📄 Main.cpython-313.pyc           # Compiled Python bytecode
│
├── 📁 .vscode/                            # ⚙️ Cấu hình VS Code workspace
│   └── (settings, launch configs, etc.)
│
├── 📁 node_modules/                       # 📦 Node.js dependencies (tự động tạo)
│   └── (các package Node.js)
│
├── 📁 data/                               # 💾 THỨC MỤC DỮ LIỆU CHÍNH
│   ├── 📄 accounts.json                   # 👥 Danh sách tài khoản Telegram
│   ├── 📄 facebook_accounts.json          # 📘 Danh sách tài khoản Facebook
│   ├── 📄 password_types.json             # 🔐 Các loại mật khẩu được định nghĩa
│   ├── 📄 auth.db                         # 🛡️ Database SQLite cho xác thực
│   ├── 📄 Data.db                         # 🗃️ Database chính SQLite
│   ├── 📄 migration_done.flag             # ✅ Flag đánh dấu migration hoàn thành
│   │
│   ├── 📁 uploaded_sessions/              # 📱 Telegram session files
│   │   ├── 📁 Adminsession/               # 👨‍💼 Session admin
│   │   │   └── 📄 84928551330.session     # Session file cụ thể
│   │   ├── 📁 M1_Session/                 # 🎯 Nhóm session M1
│   │   │   ├── 📄 84_567573036.session    # Session files số điện thoại
│   │   │   ├── 📄 84_567575726.session
│   │   │   ├── 📄 84_567582586.session
│   │   │   └── ... (nhiều session files khác)
│   │   ├── 📁 M2_Session/                 # 🎯 Nhóm session M2
│   │   └── 📁 Main_session/               # 🎯 Nhóm session chính
│   │
│   ├── 📁 sounds/                         # 🔊 File âm thanh thông báo
│   │   ├── 📄 Tantan.wav                  # 💕 Âm thanh Tantan
│   │   ├── 📄 Túy Âm.mp3                 # 🎵 Âm thanh Túy Âm
│   │   ├── 📄 Wechat.wav                  # 💬 Âm thanh WeChat
│   │   ├── 📄 whatapp.wav                 # 📞 Âm thanh WhatsApp
│   │   └── 📄 Zalo.wav                    # 💬 Âm thanh Zalo
│   │
│   └── 📁 image_editor_files/             # 🖼️ Files cho chức năng chỉnh sửa ảnh
│       └── (cached/processed images)
│
├── 📁 src/                                # 💻 MÃ NGUỒN CHÍNH
│   ├── 📁 auth/                           # 🔐 Module xác thực
│   │   └── 📄 auth.py                     # Logic xác thực và authorization
│   │
│   └── 📁 database/                       # 🗄️ Module database
│       └── 📄 sqlite_data_handler.py      # Handler cho SQLite operations
│
├── 📁 static/                             # 🌐 STATIC WEB ASSETS
│   ├── 📄 style.css                       # 🎨 CSS styling chính
│   ├── 📄 favicon.png                     # 🔖 Icon website
│   ├── 📄 icontray.png                    # 🖼️ Icon cho system tray
│   │
│   └── 📁 js/                             # 📜 JavaScript files
│       ├── 📄 app.js                      # ⚙️ Logic JavaScript chính
│       ├── 📄 stagewise-init.js           # 🚀 Initialization scripts
│       └── 📄 stagewise-toolbar.js        # 🔧 Toolbar functionality
│
└── 📁 fonts/                              # 🔤 FONT FILES
    ├── 📄 Roboto-Bold.ttf                 # 🔤 Font Roboto đậm
    └── 📄 Roboto-Regular.ttf               # 🔤 Font Roboto thường
```

## 📋 Chi Tiết Chức Năng Từng Thư Mục

### 🏠 **Root Directory**
- **Main.py**: File chính chứa Flask application với tất cả routes, API endpoints, và business logic
- **index.html**: Giao diện web chính với Bootstrap UI cho dashboard
- **requirements.txt**: Dependencies Python cần thiết (Flask, SQLite3, etc.)
- **package.json**: Metadata dự án và scripts NPM

### 💾 **data/ - Thư Mục Dữ Liệu**
Chứa tất cả dữ liệu người dùng và cấu hình:
- **Database Files**: `auth.db`, `Data.db` cho lưu trữ SQLite
- **Account Management**: JSON files cho tài khoản Telegram và Facebook
- **Session Management**: Telegram session files được phân nhóm theo folders
- **Media Assets**: Âm thanh thông báo và ảnh chỉnh sửa
- **Configuration**: Password types và migration flags

### 💻 **src/ - Source Code**
Module hóa code theo chức năng:
- **auth/**: Xử lý xác thực, đăng nhập, authorization
- **database/**: SQLite data handlers và database operations

### 🌐 **static/ - Web Assets**
Frontend resources:
- **CSS**: Styling cho UI/UX
- **JavaScript**: Client-side logic và interactive features
- **Images**: Icons và graphics cho web interface

### 🔤 **fonts/ - Typography**
Font files cho UI consistency:
- Roboto family fonts cho clean, modern appearance

## 🚀 Các Tính Năng Chính

### 🔐 **Quản Lý Xác Thực**
- Đăng nhập bảo mật với SQLite database
- Session management cho multiple users
- Authorization controls

### 📱 **Telegram Automation**
- Quản lý multiple Telegram accounts
- Auto-seeding với time windows
- Session file management theo nhóm
- Proxy support và connection handling

### 📘 **Facebook Integration**
- Quản lý tài khoản Facebook
- Account automation features
- Data synchronization

### 🔑 **Password Management**
- Categorized password storage
- Secure encryption và hashing
- Password types definition

### 🎵 **Notification System**
- Multi-platform sound notifications
- Customizable alert tones
- Real-time feedback

### 🖼️ **Image Processing**
- Built-in image editor
- File caching và optimization
- Media management tools

## 🛠️ Tech Stack

### Backend
- **Flask 3.0.0**: Web framework
- **SQLite3**: Database
- **Telethon**: Telegram API client
- **PIL/Pillow**: Image processing

### Frontend
- **Bootstrap 5.3.3**: UI framework
- **Vanilla JavaScript**: Client-side logic
- **Custom CSS**: Styling và theming

### Development Tools
- **pytest**: Testing framework
- **VS Code**: IDE configuration
- **Node.js**: Package management

## 📊 Database Schema

### 🗃️ **Data.db Tables**
- `auto_seeding_settings`: Auto-seeding configuration
- `passwords`: Encrypted password storage
- `notes`: User notes và reminders
- `facebook_accounts`: Facebook account data

### 🛡️ **auth.db Tables**
- `users`: User authentication data
- `sessions`: Login session tracking
- `permissions`: Access control

## 🚦 Cách Chạy Dự Án

### 📋 Prerequisites
```bash
Python 3.11+
pip install -r requirements.txt
```

### 🏃‍♂️ Running
```bash
# Development mode
python Main.py

# Or using NPM scripts
npm start
npm run dev
```

### 🌐 Access
- Web Interface: `http://localhost:5000`
- Admin Panel: Dashboard có built-in authentication

## 🔧 Configuration

### 🗃️ Database Setup
- SQLite databases tự động tạo khi chạy lần đầu
- Migration scripts handle schema updates
- Backup functionality available

### 📱 Telegram Setup
- Upload session files vào `data/uploaded_sessions/`
- Configure API credentials trong settings
- Set up proxy nếu cần thiết

### 🔐 Security
- Change `app.secret_key` trong Main.py
- Configure authentication trong auth.db
- Set up proper file permissions

## 📈 Version History

- **v2.3.0**: Auto-start refactoring với winshell library - reliable Windows startup shortcut management, cleaner code architecture
- **v2.2.0**: Auto-seeding UI reset fix và data consistency  
- **v2.1.0**: Comprehensive database schema verification
- **v2.0.0**: Auto-seeding time windows implementation
- **v1.9**: Browser password save prevention với autocomplete attributes cho sensitive inputs
- **v1.8**: Fully functional Windows auto-start với startup shortcut creation/deletion
- **v1.7**: UI refinements cho settings modal và context menu với hidden input spinners
- **v1.6**: Simplified shutdown timer inputs với integrated placeholders, removed external labels
- **v1.5**: Precision alignment fix cho shutdown timer inputs using baseline alignment
- **v1.4**: Settings modal layout alignment fixes và stateful shutdown timer với live countdown
- **v1.3**: SQL typo fixes và enhanced error handling
- **v1.2**: Frontend NaN validation
- **v1.1**: UI improvements và daily toggle relocation
- **v1.0**: Initial auto-seeding implementation

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📞 Support

For issues and questions:
- Check logs trong terminal output
- Review database connections
- Verify session file integrity
- Check proxy configuration

---

*Generated on August 3, 2025 - Telegram Dashboard v2.2.0*
