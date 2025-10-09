# MonS Dashboard - Bảng Điều Khiển Đa Chức Năng

MonS là một ứng dụng web được xây dựng bằng Python (Flask) và Bootstrap 5, cung cấp một bộ công cụ tiện ích bao gồm:
- 📝 Ghi chú
- 🔐 MXH ( Quản lý Mật khẩu & Tài khoản Mạng Xã Hội)
- 🤖 Telegram ( Quản lý tác vụ Telegram)
- 🖼️ Chỉnh sửa hình ảnh cơ bản
- ... và nhiều tính năng khác trong tương lai.

## ✨ Tính Năng Nổi Bật
- **Giao diện Web:** Dễ dàng truy cập và sử dụng trên trình duyệt.
- **Tái cấu trúc:** Code được tổ chức gọn gàng theo module, dễ dàng bảo trì và mở rộng.
- **Hiện đại:** Sử dụng Flask cho backend và Bootstrap 5 cho frontend.

## 📁 Cấu Trúc Thư Mục
Dự án được cấu trúc theo mô hình package của Flask để đảm bảo tính tổ chức:
```
/Mon
|
|-- app/
|   |-- static/
|   |   |-- css/
|   |   |   `-- style.css       # Nơi chứa các tùy chỉnh CSS của bạn
|   |   |-- js/
|   |   |   `-- script.js       # Nơi chứa các mã JavaScript
|   |   `-- img/
|   |       `-- icontray.png    # Icon của ứng dụng
|   |
|   |-- templates/
|   |   |-- layouts/
|   |   |   `-- base.html       # Template layout chính
|   |   |-- partials/
|   |   |   `-- navbar.html     # Thanh điều hướng (sidebar ngang)
|   |   |-- home.html           # Nội dung trang chủ
|   |   |-- password.html       # Nội dung trang quản lý mật khẩu
|   |   `-- telegram.html       # Nội dung trang quản lý Telegram
|   |
|   |-- __init__.py             # Khởi tạo ứng dụng Flask
|   `-- routes.py               # Nơi định nghĩa các đường dẫn (URL)
|
|-- run.py                      # File để chạy toàn bộ ứng dụng
|-- requirements.txt            # Các thư viện Python cần thiết
`-- README.md                   # File hướng dẫn mới
```
## 🚀 Hướng Dẫn Cài Đặt và Chạy
### 1. Yêu Cầu
- Python 3.8 trở lên
- `pip` (trình quản lý gói của Python)
### 2. Cài Đặt Các Thư Viện
Mở terminal (hoặc Command Prompt) trong thư mục gốc `stool_project` và chạy lệnh sau:
```bash
pip install -r requirements.txt
```
### 3. Chạy Ứng Dụng
Sau khi cài đặt thành công, chạy lệnh:
```bash
python run.py
```
### 4. Truy Cập Ứng Dụng
Mở trình duyệt web và truy cập vào địa chỉ:
[http://127.0.0.1:5001](http://127.0.0.1:5001)
---
Chúc bạn phát triển dự án thành công!

# Mục Tiêu Phát Triển App:
Đa chức năng bao gồm: Telegram Bot, Ghi chú , Quản Lý Tài Khoản MXH , Chỉnh Sửa Hình Ảnh......

Cấu trúc thư mục:
