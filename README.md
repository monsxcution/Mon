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
Tóm tắt file mẫu temp_index.html

# Tóm tắt code cho Ghi chú dựa vào file temp_index.html
 CSS Styles (Các dòng 591 - 1007)
Toàn bộ phần CSS tùy chỉnh cho giao diện của Ghi chú, bao gồm:
Dòng 591 - 661: Định dạng layout chính (.notes-layout-container), hiệu ứng co dãn của danh sách và khung chi tiết.
Dòng 663 - 738: Định dạng cho các card ghi chú (#notes-container .card) ở cả chế độ xem lưới và xem danh sách.
Dòng 740 - 781: Tùy chỉnh thanh tìm kiếm (#notes-search-input).
Dòng 783 - 881: Định dạng cho khung hiển thị chi tiết ghi chú (#notes-detail-panel) và trình soạn thảo nội dung (#detail-editable-full).
Dòng 883 - 974: Các hiệu ứng animation khi tạo mới, hover và "ghim" card ghi chú.
HTML Structure (Các dòng 1221 - 1391 & 1863 - 2068)
Phần HTML được chia thành các khu vực chính:
Dòng 1221 - 1248: Các div dùng để hiển thị Context Menu (menu chuột phải) cho:
Toàn bộ tab Ghi chú (#notes-tab-context-menu).
Từng card ghi chú (#note-card-context-menu).
Vùng văn bản được bôi đen (#profile-span-context-menu).
Dòng 1391 - 1417: Cấu trúc layout chính cho tab Ghi chú, bao gồm:
#notes-tool-pane: Thẻ div chính chứa toàn bộ chức năng.
#notes-list-wrapper: Khu vực chứa thanh tìm kiếm và danh sách các card ghi chú.
#notes-detail-wrapper: Khu vực để hiển thị nội dung chi tiết của một ghi chú được chọn.
Dòng 1863 - 2068: Các Modals (cửa sổ pop-up) được sử dụng bởi chức năng Ghi chú:
Dòng 1863 - 1948: Modal để Thêm/Sửa ghi chú và đặt báo thức (#notes-addEditModal).
Dòng 1950 - 1965: Modal hiển thị thông báo khi đến giờ hẹn (#notes-notificationModal).
Dòng 1967 - 1989: Context menu cho trình soạn thảo văn bản (#notes-context-menu).
Dòng 2026 - 2068: Các modal phụ trợ để Gán Link (#notes-addLinkModal) và Gán Profile (#notes-addProfileModal).
⚙️ JavaScript Logic (Các dòng 2769 - 3474)
Đây là phần quan trọng nhất, chứa toàn bộ "não bộ" của chức năng Ghi chú.
Bắt đầu từ dòng 2769: Toàn bộ script được bọc trong một khối (() => { ... })(); bắt đầu bằng comment // --- NOTES MANAGER SCRIPT ---.
Logic chính bao gồm:
DOM Selectors: Khai báo các biến để tương tác với HTML.
State Management: Quản lý trạng thái của ứng dụng (danh sách ghi chú, ghi chú đang được chọn).
Core Functions: Các hàm chính như fetchAndRenderNotes(), renderNotes(), createNoteCard(), showNoteDetail(), saveNoteChanges().
Event Handlers: Xử lý các sự kiện của người dùng như click, nhập liệu vào thanh tìm kiếm, submit form, và đặc biệt là sự kiện contextmenu (chuột phải) để hiển thị các menu tương ứng.
Initialization: Logic khởi tạo initializeNotesView() để tải dữ liệu và tự động chọn ghi chú đầu tiên khi mở tab.
Kết thúc ở dòng 3474: Ngay trước comment // --- End of Notes Manager ---.

# Tổng hợp các dòng code cho chức năng MXH
File tham chiếu: temp_index.html
🎨 CSS Styles (Các dòng 1118 - 1219)
Phần này chứa các định dạng cho giao diện của tab Mạng Xã Hội.
Dòng 1118 - 1147: Định dạng cho các card tài khoản (.mxh-card), icon (.mxh-card-icon), và hiệu ứng lật thẻ (.mxh-card-container).
Dòng 1149 - 1162: Hiệu ứng nhấp nháy (@keyframes blink) cho các card có ngày kỷ niệm.
Dòng 1164 - 1219: Tùy chỉnh cho các context menu (#wechat-context-menu, #generic-context-menu) và các modal liên quan.
📄 HTML Structure (Các dòng 1419 - 1436 & 2070 - 2320)
Cấu trúc HTML cho tab MXH và các cửa sổ chức năng.
Dòng 1419 - 1436: Thẻ div chính cho tab Mạng Xã Hội (#mxh-tool-pane), chứa tiêu đề, các nút chức năng và khu vực hiển thị các card tài khoản (#mxh-accounts-container).
Dòng 2070 - 2320: Toàn bộ các Modals (cửa sổ pop-up) và Context Menus (menu chuột phải) dành riêng cho MXH:
Dòng 2070 - 2119: Modal Thêm Tài Khoản MXH (#mxh-addAccountModal).
Dòng 2122 - 2154: Context Menu dành riêng cho tài khoản WeChat (#wechat-context-menu), bao gồm các chức năng như "Đã Quét", "Câm", "Cứu tài khoản"...
Dòng 2157 - 2165: Context Menu chung cho các loại tài khoản khác (#generic-context-menu).
Dòng 2168 - 2320: Các modal để Chỉnh sửa tài khoản (#generic-account-modal, #wechat-account-modal), Đổi số hiệu card (#change-card-number-modal), và Xác nhận xóa (#delete-card-modal).
⚙️ JavaScript Logic (Các dòng 3477 - 4038)
Đây là toàn bộ phần logic xử lý cho chức năng Mạng Xã Hội.
Bắt đầu từ dòng 3477: Toàn bộ script được bắt đầu bằng comment // MXH Functionality.
Logic chính bao gồm:
State Management: Khai báo các biến mxhGroups, mxhAccounts để lưu trữ dữ liệu.
Core Functions: Các hàm chính như initMXH(), loadMXHData(), và quan trọng nhất là renderMXHAccounts() (chịu trách nhiệm vẽ toàn bộ card ra giao diện).
Card Flipping: Hàm flipCard() để xử lý hiệu ứng lật thẻ 2 mặt.
Event Handlers: Xử lý các sự kiện click, chuột phải (contextmenu) để hiển thị menu, lưu dữ liệu từ modal.
API Interaction: Các hàm async để gọi API (fetch) lấy và cập nhật dữ liệu tài khoản, nhóm.
Kết thúc ở dòng 4038: Ngay trước khi kết thúc thẻ <script> chính.

# 🤖 Tổng hợp các dòng code cho chức năng Telegram
File tham chiếu: temp_index.html
🎨 CSS Styles (Các dòng 269 - 302 & 470 - 544)
Các định dạng CSS cho giao diện của tab Telegram.
Dòng 269 - 282: Tùy chỉnh cho thanh công cụ phía trên (.sticky-top) trong tab Telegram.
Dòng 284 - 302: Định dạng chung cho các tab con và panel bên trong Telegram và Image Editor.
Dòng 470 - 544: Định dạng cho layout 2 cột (sidebar và nội dung chính), bao gồm cả các card chức năng (.stat-card) và hiệu ứng hover/select cho các card tác vụ (#tg-group-task-cards).
📄 HTML Structure (Các dòng 1019 - 1023 & 1572 - 1861)
Cấu trúc HTML cho tab Telegram và các cửa sổ chức năng của nó.
Dòng 1019 - 1023: Context menu (menu chuột phải) dành riêng cho tab Telegram (#telegram-context-menu).
Dòng 1572 - 1699: Giao diện chính của tab Telegram (#telegram-tool-pane), bao gồm:
Thanh công cụ trên cùng chứa các nút điều khiển, input cấu hình (Core, Delay), và dropdown chọn nhóm session.
Layout 2 cột với sidebar (#tg-v-pills-tab) và khu vực nội dung chính (#tg-v-pills-tabContent).
Bảng hiển thị danh sách session (#tg-session-tables-container).
Các card để chọn tác vụ như "Join Group", "Seeding Group".
Giao diện cho chức năng "Auto Seeding".
Dòng 1801 - 1861: Các Modals (cửa sổ pop-up) được sử dụng bởi chức năng Telegram:
Dòng 1801 - 1820: Modal để Thêm/Quản lý nhóm Session (#tg-addSessionModal).
Dòng 1822 - 1861: Các modal cấu hình cho từng tác vụ như Join Group (#tg-joinGroupModal), Seeding (#tg-seedingGroupModal), và Xóa Session (#tg-deleteDeadSessionsModal).
⚙️ JavaScript Logic (Các dòng 2322 - 2767)
Toàn bộ logic vận hành chức năng Telegram.
Bắt đầu từ dòng 2322: Toàn bộ script được bọc trong một khối (async () => { ... })(); và bắt đầu bằng comment // --- TELEGRAM MANAGER SCRIPT ---.
Logic chính bao gồm:
State Management: Quản lý trạng thái các tác vụ, cấu hình, danh sách session.
API Interaction: Các hàm async để gọi API (fetch) để tải nhóm, tải session, lưu cấu hình, bắt đầu/dừng tác vụ.
Task Execution: Các hàm tg_handleRunStopClick, tg_pollTaskStatus để quản lý luồng chạy của tác vụ.
UI Updates: Các hàm tg_renderSessions, tg_updateUiWithTaskProgress để cập nhật giao diện dựa trên dữ liệu từ server.
Event Handlers: Xử lý các sự kiện click nút, thay đổi lựa chọn trong dropdown, và các tương tác trong modal.
Auto-Seeding Logic: Phần script quản lý chức năng hẹn giờ seeding tự động.
Kết thúc ở dòng 2767: Ngay trước comment // --- IMAGE EDITOR SCRIPT ---.




# 🐍 Tổng hợp các dòng code trong temp_Main.pyw
File tham chiếu: temp_Main.pyw
🔐 Quản lý Mật khẩu (Password Manager)
Dòng 207 - 235: Các hàm load_password_accounts, save_password_accounts, load_password_types, save_password_types để đọc/ghi dữ liệu từ file JSON (phiên bản cũ, giờ đã chuyển sang SQLite).
Dòng 417 - 522: Toàn bộ Blueprint (password_bp) cho chức năng mật khẩu.
Dòng 420 - 431: Route /add để xử lý việc thêm tài khoản mới.
Dòng 434 - 446: Route /update/<id> để cập nhật thông tin tài khoản.
Dòng 449 - 457: Route /delete/<id> để xóa tài khoản.
Dòng 460 - 496: Các route để thêm, xóa và cập nhật màu sắc cho "Loại" tài khoản (/types/...).
🤖 Quản lý Telegram (Telegram Manager)
Dòng 74 - 79: Khai báo các biến toàn cục cho Telegram (TASKS, API_ID, API_HASH).
Dòng 618 - 845: Chứa các hàm worker chính, là logic lõi để tương tác với API Telegram.
join_group_worker: Logic để tham gia nhóm.
seeding_group_worker: Logic để gửi tin nhắn seeding.
run_admin_task: Logic riêng cho session admin.
check_single_session_worker: Logic để kiểm tra session có còn hoạt động hay không.
Dòng 847 - 1018: Hàm run_task_in_thread, đây là "bộ điều khiển" chính, chịu trách nhiệm quản lý việc chạy các tác vụ (chia batches, xử lý delay, gọi worker, quản lý proxy...).
Dòng 525 - 616 & 1022 - 1177: Toàn bộ Blueprint (telegram_bp) và các API endpoint (/api/...) để frontend có thể:
Quản lý group session (thêm, xóa, lấy danh sách).
Lưu/tải cấu hình tác vụ (/api/config/...).
Thực thi, dừng và kiểm tra trạng thái tác vụ (/api/run-task, /api/stop-task, /api/task-status).
Quản lý proxy.
📝 Ghi chú & Nhắc việc (Notes/Reminders)
Dòng 1457 - 1507: Hàm check_and_queue_reminders(). Đây là hàm cực kỳ quan trọng, chạy định kỳ để kiểm tra các ghi chú đã đến hạn và đưa chúng vào hàng đợi thông báo.
Dòng 1509 - 1625: Toàn bộ Blueprint (notes_bp) và các API endpoint cho Ghi chú.
/api/get: Lấy danh sách tất cả ghi chú.
/api/add: Thêm ghi chú mới.
/api/update/<id>: Cập nhật nội dung.
/api/delete/<id>: Xóa ghi chú.
/api/mark/<id>: Đánh dấu/bỏ đánh dấu ghi chú.
/api/check-notifications: API để frontend gọi liên tục, kiểm tra xem có thông báo mới nào trong hàng đợi không.
🖼️ Chỉnh sửa ảnh (Image Editor)
Dòng 1228 - 1344: Logic xử lý hình ảnh.
resize_crop_image: Hàm tiện ích để cắt và thay đổi kích thước ảnh cho vừa với layout.
Dòng 1347 - 1455: Blueprint (image_editor_bp) và các API endpoint.
/upload: Xử lý việc tải ảnh từ máy người dùng lên server.
/create-collage: Nhận thông tin về layout, danh sách ảnh, và các tùy chọn khác để tạo ra ảnh ghép.
/files/...: Route để phục vụ (hiển thị) các file ảnh đã được xử lý cho trình duyệt.
🍔 Healthy / Kcal Calculator
Dòng 1914 - 2000: Blueprint (kcal_bp) và các API endpoint.
/api/settings: Lấy và lưu các thông số cơ thể của người dùng (chiều cao, cân nặng, tuổi...).
/api/foods: Lấy danh sách, thêm, và xóa các loại thực phẩm trong cơ sở dữ liệu.
🚀 Cài đặt chung & Khởi chạy
Dòng 20 - 72: Cấu hình ban đầu cho Flask, định nghĩa các đường dẫn file và thư mục.
Dòng 81 - 415: Hàm init_database() và các hàm di chuyển dữ liệu (migrate_...), chịu trách nhiệm tạo và cập nhật cấu trúc cơ sở dữ liệu.
Dòng 2202 - 2373: Các hàm liên quan đến việc quản lý ứng dụng, mở trình duyệt, và tạo icon trên khay hệ thống (system tray).
Dòng 2376 - 2381: if __name__ == "__main__": - Điểm khởi đầu của toàn bộ chương trình.