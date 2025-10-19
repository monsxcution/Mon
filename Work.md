# 🎯 **MỤC TIÊU: Tái cấu trúc (refactor) module MXH một cách tuần tự theo từng tính năng**

## 📁 **THƯ MỤC MXH_Old - CODE MẪU**

**LƯU Ý QUAN TRỌNG:** Thư mục `MXH_Old/` chứa code dự án cũ, chỉ làm **MẪU THAM KHẢO**. 
- ✅ **Có sẵn giao diện** hoàn chỉnh trong `MXH_Old/mxh.html`
- ✅ **Có sẵn logic** JavaScript trong `MXH_Old/mxh_routes.py` 
- ✅ **Có sẵn CSS** styling trong `MXH_Old/style.css`
- 🎯 **Mục đích:** Dựa vào đó để làm cho nhanh

---

Mỗi giai đoạn là một đơn vị công việc hoàn chỉnh và có thể kiểm thử được. Chúng ta sẽ xây dựng từ đầu, bắt đầu bằng việc sửa lỗi backend, sau đó triển khai từng tính năng một ở phía frontend.

---

## 🔧 **GIAI ĐOẠN 1: NỀN TẢNG - SỬA LỖI BACKEND (BẮT BUỘC)**

**MÔ TẢ:** Trước khi viết bất kỳ tính năng mới nào, chúng ta phải sửa các điểm không nhất quán giữa kế hoạch và code backend hiện tại. Đây là điều kiện tiên quyết cho tất cả các bước tiếp theo.

### **1.1. Sửa Tên Bảng trong app/database.py**

**HÀNH ĐỘNG:** Trong file `app/database.py`, tìm câu lệnh `CREATE TABLE` cho `mxh_card`.

**THAY ĐỔI:** 
- Đổi tên bảng từ `mxh_card` thành `mxh_cards`
- Cập nhật `FOREIGN KEY` trong bảng `mxh_accounts` để tham chiếu đến `mxh_cards(id)`
- Cập nhật tên các chỉ mục (index) thành:
  - `idx_accounts_card_id`
  - `idx_cards_group_id` 
  - `idx_cards_platform`
  - `idx_accounts_status`

### **1.2. Cập nhật Tất cả Truy vấn API trong app/mxh_api.py**

**HÀNH ĐỘNG:** Trong file `app/mxh_api.py`, xem lại mọi hàm (`create_card`, `get_cards`, `create_account`).

**THAY ĐỔI:** Thay thế tất cả các tham chiếu SQL từ bảng `mxh_card` thành `mxh_cards`.

### **1.3. Triển khai Lồng ghép Dữ liệu Chính xác trong GET /mxh/api/cards**

**HÀNH ĐỘNG:** Trong file `app/mxh_api.py`, sửa đổi hàm `get_cards()`.

**TRẠNG THÁI HIỆN TẠI:** Hàm này trả về một `accounts_summary` tĩnh và không chính xác.

**THAY ĐỔI YÊU CẦU:**
1. Lấy tất cả các card từ `mxh_cards`
2. Lấy **TẤT CẢ** các tài khoản từ `mxh_accounts`
3. Với mỗi card, tạo một khóa (key) mới là `accounts` có giá trị là một mảng (array)
4. Đưa các đối tượng tài khoản thuộc về card đó vào mảng `accounts` tương ứng
5. Phản hồi JSON cuối cùng phải là một mảng các đối tượng card, mỗi đối tượng chứa danh sách `accounts` của nó

**TÀI LIỆU THAM KHẢO:** Sử dụng logic từ file cũ `MXH_Old/mxh_routes.py.txt` (hàm `mxh_cards_and_sub_accounts`).

---

## 🎨 **GIAI ĐOẠN 2: FRONTEND - HIỂN THỊ CARD (CHỈ ĐỌC)**

**MÔ TẢ:** Mục tiêu là hiển thị dữ liệu hiện có lên màn hình, dựa trên API đã được sửa lỗi.

### **2.1. Tái tạo Toàn bộ Cấu trúc HTML**

**HÀNH ĐỘNG:** Thay thế toàn bộ nội dung của `app/templates/mxh.html` bằng nội dung từ `MXH_Old/mxh.html`.

**LÝ DO:** Việc này sẽ mang vào tất cả các yếu tố giao diện người dùng (UI) cần thiết như modal và menu ngữ cảnh cho các giai đoạn sau.

### **2.2. Triển khai JavaScript ban đầu trong app/static/js/mxh.js**

**HÀNH ĐỘNG:** Ghi đè lên nội dung hiện có của `app/static/js/mxh.js`.

**NHIỆM VỤ:** Viết đoạn script ban đầu có chức năng:

1. **Khi sự kiện `DOMContentLoaded` được kích hoạt**, gọi một hàm chính như `initializeMXH()`
2. **Hàm `initializeMXH()`** sẽ gọi `loadMXHData()`
3. **Hàm `loadMXHData()`** thực hiện:
   - Fetch dữ liệu từ `GET /mxh/api/groups` và `GET /mxh/api/cards`
   - Lưu trữ kết quả vào các mảng toàn cục (`mxhGroups`, `mxhCards`)
   - Sau khi fetch xong, gọi `renderMXHAccounts()`
4. **Hàm `renderMXHAccounts()`**:
   - Lặp qua `mxhCards`
   - Với mỗi card, tìm tài khoản chính (`is_primary: 1`) trong mảng `accounts`
   - Sử dụng dữ liệu của tài khoản đó để xây dựng HTML cho card
   - Chèn HTML cuối cùng vào phần tử có id là `#mxh-accounts-container`

---

## ➕ **GIAI ĐOẠN 3: CHỨC NĂNG TẠO MỚI - THÊM CARD MỚI**

**MÔ TẢ:** Triển khai quy trình thêm một card mới cùng với tài khoản chính của nó.

### **3.1. Kết nối Sự kiện cho Modal "Thêm Tài Khoản"**

**HÀNH ĐỘNG:** Trong `app/static/js/mxh.js`, thêm một trình lắng nghe sự kiện (event listener) cho nút "Thêm Tài Khoản" (nút kích hoạt `#mxh-addAccountModal`).

**NHIỆM VỤ:** Triển khai logic cho nút lưu (save) bên trong modal `#mxh-addAccountModal`.

### **3.2. Triển khai Lệnh gọi API**

**HÀNH ĐỘNG:** Khi nút lưu được nhấp, thu thập tất cả dữ liệu từ form.

**NHIỆM VỤ:** 
- Thực hiện một yêu cầu `POST` đến `/mxh/api/cards`
- Phần thân (body) của yêu cầu phải là một đối tượng JSON chứa tất cả các trường cần thiết (`card_name`, `group_id`, `platform`, `username`, `phone`, v.v.) để tạo cả card và tài khoản chính ban đầu của nó

**LƯU Ý:** Backend cần được điều chỉnh để xử lý việc tạo tài khoản chính ngay trong endpoint `POST /mxh/api/cards`, tương tự như logic cũ của `alias_create_card_from_accounts`.

### **3.3. Cập nhật Giao diện người dùng (UI)**

Khi nhận được phản hồi thành công từ API:
- Đóng modal
- Gọi lại hàm `loadMXHData()` để làm mới giao diện và hiển thị card mới

---

## 🖱️ **GIAI ĐOẠN 4: TƯƠNG TÁC - MENU NGỮ CẢNH & XÓA**

**MÔ TẢ:** Thêm menu ngữ cảnh khi nhấp chuột phải và triển khai hành động đầu tiên, đơn giản nhất: Xóa.

### **4.1. Triển khai Hiển thị Menu Ngữ cảnh**

**HÀNH ĐỘNG:** Trong `mxh.js`, tạo một hàm `handleCardContextMenu(event, cardId)`.

**NHIỆM VỤ:** 
- Trong bước `renderMXHAccounts`, thêm thuộc tính `oncontextmenu` vào div chính của mỗi card để gọi hàm này
- Hàm này nên:
  - Ngăn chặn menu mặc định
  - Lấy `cardId`
  - Lưu nó vào một biến toàn cục (ví dụ: `currentContextCardId`)
  - Hiển thị menu `#unified-context-menu` tại vị trí con trỏ chuột

### **4.2. Triển khai Hành động "Xóa Card"**

**HÀNH ĐỘNG:** Thêm một trình lắng nghe sự kiện nhấp chuột cho mục "Xóa Card" trong menu ngữ cảnh.

**NHIỆM VỤ:** 
- Khi được nhấp, nó sẽ mở modal xác nhận (`#delete-card-modal`)
- **GỌI API:** Nút xác nhận (`#confirm-delete-btn`) sẽ kích hoạt một yêu cầu `DELETE` đến `/mxh/api/cards/<card_id>`, sử dụng `currentContextCardId` đã lưu
- **CẬP NHẬT UI:** Khi thành công, xóa card khỏi giao diện ngay lập tức (để có phản hồi tức thì) và sau đó có thể tùy chọn gọi `loadMXHData()` để đồng bộ lại dữ liệu

---

## ✏️ **GIAI ĐOẠN 5: TƯƠNG TÁC - SỬA CARD/TÀI KHOẢN**

**MÔ TẢ:** Triển khai khả năng chỉnh sửa thông tin của một tài khoản.

### **5.1. Kết nối Sự kiện cho mục Menu "Thông tin" (Sửa)**

**HÀNH ĐỘNG:** Trong `mxh.js`, thêm một trình lắng nghe sự kiện nhấp chuột cho mục menu "Thông tin".

**NHIỆM VỤ:** 
- Khi được nhấp, nó sẽ mở modal tương ứng (ví dụ: `#wechat-account-modal`)
- **NẠP DỮ LIỆU:** Tìm card và tài khoản chính chính xác từ trạng thái toàn cục bằng cách sử dụng `currentContextCardId`. Điền dữ liệu này vào các trường trong form của modal

### **5.2. Triển khai Logic Lưu**

**HÀNH ĐỘNG:** Nút "Apply" trong modal sẽ kích hoạt logic lưu.

**GỌI API:** Nó sẽ thực hiện một yêu cầu `PUT` đến `/mxh/api/accounts/<account_id>` với dữ liệu đã được cập nhật. 

**LƯU Ý:** Chúng ta đang cập nhật **TÀI KHOẢN**, không phải card.

**CẬP NHẬT UI:** Khi thành công, đóng modal và làm mới dữ liệu.

---

## 🚀 **CÁC GIAI ĐOẠN TIẾP THEO: MỖI LẦN MỘT TÍNH NĂNG**

**MÔ TẢ:** Triển khai các tính năng còn lại của menu ngữ cảnh một cách riêng lẻ. Đối với mỗi tính năng, hãy tuân theo mẫu sau:

1. **Thêm trình lắng nghe sự kiện** cho mục menu
2. **Kích hoạt lệnh gọi API** tương ứng (ví dụ: `POST /mxh/api/accounts/<id>/scan`)
3. **Cập nhật giao diện người dùng** khi thành công

### **📋 CÁC TÍNH NĂNG TIẾP THEO CẦN TRIỂN KHAI THEO THỨ TỰ:**

- **Tính năng:** Submenu "Tài khoản" (liệt kê tất cả accounts)
- **Tính năng:** Submenu "Trạng Thái" (Available, Die, Disabled)  
- **Tính năng:** Submenu "Quét" (Đánh dấu Đã Quét, Đặt lại Quét)
- **Tính năng:** "Thông báo" (Đặt/Xóa thông báo)
- **... và cứ thế tiếp tục**

---

**[KẾT THÚC KHỐI LỆNH CHO AI]**