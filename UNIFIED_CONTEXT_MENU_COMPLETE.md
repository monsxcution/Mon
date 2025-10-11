# ✅ UNIFIED CONTEXT MENU - COMPLETE

## 🎯 Cải tiến Context Menu mới

### **Unified Context Menu** cho tất cả platforms

#### Thứ tự menu items:
1. ⚙️ **Thông tin** (đổi tên từ "Chỉnh sửa thông tin")
2. 🎭 **Trạng Thái** (submenu với 3 options)
   - ✅ Available (trắng)
   - ❌ Die (đỏ + icon X)
   - ⛔ Vô hiệu hóa (cam + icon slash-circle)
3. ✅ **Đã Quét** (WeChat only)
4. 🔔 **Thông báo**
5. 📞 **Copy SĐT** (nếu có phone)
6. 📧 **Copy Email** (nếu có email)
7. 🔄 **Reset lượt quét** (WeChat only)
8. 🔢 **Đổi Số Hiệu**
9. 🗑️ **Xóa Card**

---

## 🎨 Status Styling

### **1. Available (Active)**
```css
.account-status-available {
    color: #fff !important;  /* Trắng */
}
```
- **Icon**: Không có
- **Màu tên**: Trắng
- **Backend value**: `status = 'active'`

### **2. Die**
```css
.account-status-die {
    color: #dc3545 !important;  /* Đỏ */
}
```
- **Icon**: `<i class="bi bi-x-circle-fill" style="color: #dc3545;"></i>`
- **Màu tên**: Đỏ
- **Backend value**: `status = 'die'`

### **3. Vô Hiệu Hóa (Disabled)**
```css
.account-status-disabled {
    color: #ff8c00 !important;  /* Cam */
}
```
- **Icon**: `<i class="bi bi-slash-circle" style="color: #ff8c00;"></i>`
- **Màu tên**: Cam
- **Backend value**: `status = 'disabled'`

---

## 📋 Implementation Details

### **HTML Structure** (`app/templates/mxh.html`)

```html
<!-- Unified Context Menu -->
<div id="unified-context-menu" class="custom-context-menu">
    <!-- Thông tin -->
    <div class="menu-item" data-action="edit">
        <i class="bi bi-pencil-square me-2"></i> Thông tin
    </div>
    
    <!-- Trạng Thái (submenu) -->
    <div class="menu-item has-submenu">
        <i class="bi bi-circle-fill me-2"></i> Trạng Thái
        <i class="bi bi-chevron-right ms-auto"></i>
        <div class="submenu">
            <div class="menu-item" data-action="status-available">
                <i class="bi bi-check-circle-fill me-2 text-success"></i> Available
            </div>
            <div class="menu-item" data-action="status-die">
                <i class="bi bi-x-circle-fill me-2 text-danger"></i> Die
            </div>
            <div class="menu-item" data-action="status-disabled">
                <i class="bi bi-slash-circle me-2 text-warning"></i> Vô hiệu hóa
            </div>
        </div>
    </div>
    
    <!-- WeChat specific items with .wechat-only class -->
    <!-- Other items... -->
</div>
```

### **JavaScript Functions**

#### 1. Show Unified Menu
```javascript
function showUnifiedContextMenu(event, accountId, platform, isSecondary = false) {
    // Show/hide platform-specific items
    const wechatOnlyItems = contextMenu.querySelectorAll('.wechat-only');
    wechatOnlyItems.forEach(item => {
        item.style.display = platform === 'wechat' ? 'block' : 'none';
    });
    
    // Position and display menu
    contextMenu.style.display = 'block';
    contextMenu.style.left = event.pageX + 'px';
    contextMenu.style.top = event.pageY + 'px';
}
```

#### 2. Update Status
```javascript
async function updateAccountStatus(newStatus) {
    // newStatus: 'active' | 'die' | 'disabled'
    
    // Local update for instant feedback
    mxhAccounts[accountIndex][statusKey] = newStatus;
    renderMXHAccounts();
    
    // API call to persist
    await fetch(`/mxh/api/accounts/${accountId}`, {
        method: 'PUT',
        body: JSON.stringify({ status: newStatus })
    });
}
```

#### 3. Render with Status
```javascript
// Determine status class and icon
let statusClass = 'account-status-available';
let statusIcon = '';

if (accountStatus === 'die') {
    statusClass = 'account-status-die';
    statusIcon = '<i class="bi bi-x-circle-fill status-icon" style="color: #dc3545;"></i>';
} else if (accountStatus === 'disabled') {
    statusClass = 'account-status-disabled';
    statusIcon = '<i class="bi bi-slash-circle status-icon" style="color: #ff8c00;"></i>';
}

// Render username with status
<small class="${statusClass}">
    ${account.username}${statusIcon}
</small>
```

---

## 📁 Files Modified

### 1. **app/templates/mxh.html**
- **Line ~115**: Added `unified-context-menu` HTML
- **Line ~870**: Added status logic (statusClass, statusIcon)
- **Line ~966**: Updated username rendering with status
- **Line ~1245**: Added `showUnifiedContextMenu()` function
- **Line ~1307**: Updated `handleCardContextMenu()` to use unified menu
- **Line ~1670**: Added `updateAccountStatus()` function
- **Line ~1563**: Added `copyEmail()` function
- **Line ~2187**: Added unified menu event listener

### 2. **app/static/css/style.css**
- **Line ~965**: Added status styling classes
  - `.account-status-available`
  - `.account-status-die`
  - `.account-status-disabled`
  - `.status-icon`

---

## 🧪 Test Scenarios

### Test 1: Context Menu Display
1. Right-click vào bất kỳ card nào
2. **Expected**: Unified menu hiện với đúng thứ tự
3. **WeChat**: Có "Đã Quét" và "Reset lượt quét"
4. **Other platforms**: Không có 2 items trên

### Test 2: Trạng Thái Submenu
1. Right-click card → Hover "Trạng Thái"
2. **Expected**: Submenu hiện với 3 options:
   - ✅ Available (green check icon)
   - ❌ Die (red X icon)
   - ⛔ Vô hiệu hóa (orange slash icon)

### Test 3: Status Available
1. Click "Available" trong submenu
2. **Expected**:
   - Tên người dùng → **Màu trắng**
   - Không có icon
   - Toast: "✅ Đã đổi sang Available!"

### Test 4: Status Die
1. Click "Die" trong submenu
2. **Expected**:
   - Tên người dùng → **Màu đỏ**
   - Icon X đỏ sau tên
   - Toast: "✅ Đã đổi sang Die!"

### Test 5: Status Vô hiệu hóa
1. Click "Vô hiệu hóa" trong submenu
2. **Expected**:
   - Tên người dùng → **Màu cam**
   - Icon slash-circle cam sau tên
   - Toast: "✅ Đã đổi sang Vô hiệu hóa!"

### Test 6: Platform-Specific Items
**WeChat card**:
- ✅ Có "Đã Quét"
- ✅ Có "Reset lượt quét"

**Telegram/Other cards**:
- ❌ Không có "Đã Quét"
- ❌ Không có "Reset lượt quét"

### Test 7: Copy Actions
1. **Copy SĐT**: Chỉ hiện nếu card có phone
2. **Copy Email**: Chỉ hiện nếu card có email
3. Click → Clipboard có data → Toast success

---

## 🎨 Visual Examples

### Status Display:

```
┌──────────────────┐
│ Card 1           │
│ John Doe         │  ← Available (Trắng)
│ 📞 +123456       │
└──────────────────┘

┌──────────────────┐
│ Card 2           │
│ Jane Doe ❌      │  ← Die (Đỏ + icon X)
│ 📞 +789012       │
└──────────────────┘

┌──────────────────┐
│ Card 3           │
│ Bob Smith ⛔     │  ← Disabled (Cam + icon slash)
│ 📞 +345678       │
└──────────────────┘
```

### Context Menu:

```
┌─────────────────────────┐
│ ⚙️ Thông tin            │
│ 🎭 Trạng Thái         ▶ │ → ┌──────────────────┐
│ ✅ Đã Quét (WeChat)     │   │ ✅ Available     │
│ 🔔 Thông báo            │   │ ❌ Die           │
│ 📞 Copy SĐT             │   │ ⛔ Vô hiệu hóa  │
│ 📧 Copy Email           │   └──────────────────┘
│ 🔄 Reset (WeChat)       │
│ 🔢 Đổi Số Hiệu          │
│ 🗑️ Xóa Card            │
└─────────────────────────┘
```

---

## ✅ Benefits

### 1. **Consistency**
- ✅ Tất cả platforms dùng chung 1 menu
- ✅ Không còn duplicate code
- ✅ Dễ maintain

### 2. **Clear Status**
- ✅ 3 trạng thái rõ ràng với màu sắc
- ✅ Icon trực quan dễ nhận biết
- ✅ Không còn toggle (chọn trực tiếp)

### 3. **Better UX**
- ✅ Menu có thứ tự logic
- ✅ Submenu cho related items
- ✅ Platform-specific items tự động ẩn/hiện

### 4. **Easy Extension**
- ✅ Dễ thêm platform mới
- ✅ Dễ thêm action mới
- ✅ Code clean và organized

---

## 🚀 Migration Notes

### Legacy Menus (Kept for compatibility):
- `wechat-context-menu` - Still works
- `telegram-context-menu` - Still works
- `generic-context-menu` - Still works

### New Unified Menu:
- `unified-context-menu` - Recommended for all new code
- `handleCardContextMenu()` - Now uses unified menu by default

**Recommendation**: Gradually migrate all to unified menu, then remove legacy menus.

---

**Hoàn tất! Context menu bây giờ unified, clean và powerful hơn!** 🎉
