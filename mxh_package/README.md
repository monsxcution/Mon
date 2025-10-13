# MXH Package - WeChat Account Management System

## Tổng quan
Package này chứa toàn bộ code và data liên quan đến tab MXH (WeChat Account Management) trong hệ thống quản lý tài khoản.

## Files trong package:

### 1. Frontend Files
- **mxh.html** - Template chính chứa toàn bộ HTML, CSS và JavaScript cho tab MXH
- **mxh_style.css** - File CSS riêng cho MXH (extracted từ style.css chính)

### 2. Backend Files  
- **mxh_routes.py** - File routes chính chứa tất cả API endpoints cho MXH

### 3. Database Files
- **mxh_accounts_schema.sql** - Schema của bảng mxh_accounts
- **mxh_accounts_dump.sql** - Full dump của bảng mxh_accounts (có thể dùng để restore)
- **mxh_accounts_data.csv** - Data dạng CSV để dễ đọc và import

## Tính năng chính:
1. **Quản lý tài khoản WeChat** - Thêm, sửa, xóa tài khoản
2. **Card 3D flip** - Hiển thị tài khoản chính và phụ trên card có thể lật
3. **Context menu** - Menu chuột phải với các tùy chọn nhanh
4. **Inline editing** - Chỉnh sửa trực tiếp trên card
5. **Auto-refresh** - Tự động cập nhật dữ liệu
6. **Status management** - Quản lý trạng thái tài khoản (active, disabled, die)
7. **Secondary accounts** - Hỗ trợ tài khoản phụ cho mỗi card chính

## Cấu trúc database:
Bảng `mxh_accounts` chứa:
- Thông tin cơ bản: card_name, username, phone
- Ngày tạo: wechat_created_day/month/year  
- Trạng thái: status, wechat_status
- Tài khoản phụ: secondary_* fields
- Metadata: platform, group_id, timestamps

## Debug features:
- Console logging cho tất cả actions
- Debug mode cho card chính/phụ
- Debug cho modal mở/đóng

## Recent fixes:
- Sửa lỗi syntax JavaScript
- Thêm CSS pointer-events để chặn click vào mặt ẩn
- Debounce cho modal mở
- Cứng hóa stopPropagation
- Chuẩn hóa status mapping (available → active)
