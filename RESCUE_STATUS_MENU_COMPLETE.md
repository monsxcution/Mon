# ✅ RESCUE FUNCTION IN STATUS MENU - COMPLETE

## 🎯 Vấn đề đã fix

**Trước đây**: 
- ❌ Khi account bị "Vô hiệu hóa", không có cách nào để "Được Cứu" hoặc ghi nhận "Cứu Thất Bại"
- ❌ Mất button rescue từ context menu cũ

**Bây giờ**:
- ✅ Submenu "Trạng Thái" **dynamic** dựa trên status hiện tại
- ✅ Khi account bị disabled → Hiện 2 options: "Được Cứu" & "Cứu Thất Bại"

---

## 🎭 Logic Status Menu

### **Khi status = "active" hoặc "die":**
```
Trạng Thái ▶
  ├─ ✅ Available
  ├─ ❌ Die  
  └─ ⛔ Vô hiệu hóa
```

### **Khi status = "disabled":**
```
Trạng Thái ▶
  ├─ 💚 Được Cứu         ← Chuyển về Active + tăng rescue_success_count
  └─ 💔 Cứu Thất Bại     ← Giữ Disabled + tăng rescue_count
```

---

## ⚡ Logic Chi Tiết

### **1. Được Cứu (rescue-success)**
```javascript
- status: disabled → active
- die_date: set to NULL
- rescue_success_count: +1
- Toast: "✅ Đã cứu thành công!"
```

### **2. Cứu Thất Bại (rescue-failed)**
```javascript
- status: giữ nguyên disabled
- rescue_count: +1
- Toast: "📝 Đã ghi nhận cứu thất bại!"
```

---

## 📊 Database Tracking

### **Counters:**
- `rescue_count` - Số lần cứu thất bại
- `rescue_success_count` - Số lần cứu thành công
- `die_date` - Ngày bị vô hiệu hóa
- `secondary_*` - Tương tự cho account phụ

### **Backend API:**
```
POST /mxh/api/accounts/<id>/rescue
Body: {
  "result": "success" | "failed",
  "is_secondary": true | false
}
```

---

## 🔧 Code Changes

### 1. **HTML - Submenu Options** (mxh.html ~line 127)
```html
<div class="submenu" id="status-submenu">
    <!-- Normal status options -->
    <div class="menu-item status-normal" data-action="status-available">
        <i class="bi bi-check-circle-fill me-2 text-success"></i> Available
    </div>
    <div class="menu-item status-normal" data-action="status-die">
        <i class="bi bi-x-circle-fill me-2 text-danger"></i> Die
    </div>
    <div class="menu-item status-normal" data-action="status-disabled">
        <i class="bi bi-slash-circle me-2 text-warning"></i> Vô hiệu hóa
    </div>
    
    <!-- Rescue options (shown when disabled) -->
    <div class="menu-item status-rescue" data-action="rescue-success" style="display: none;">
        <i class="bi bi-heart-fill me-2 text-success"></i> Được Cứu
    </div>
    <div class="menu-item status-rescue" data-action="rescue-failed" style="display: none;">
        <i class="bi bi-heartbreak-fill me-2 text-danger"></i> Cứu Thất Bại
    </div>
</div>
```

### 2. **JavaScript - Show/Hide Logic** (mxh.html ~line 1295)
```javascript
// Configure status submenu based on current status
const currentStatus = isSecondary ? account.secondary_status : account.status;
const statusNormalItems = contextMenu.querySelectorAll('.status-normal');
const statusRescueItems = contextMenu.querySelectorAll('.status-rescue');

if (currentStatus === 'disabled') {
    // Hide normal options, show rescue options
    statusNormalItems.forEach(item => item.style.display = 'none');
    statusRescueItems.forEach(item => item.style.display = 'block');
} else {
    // Show normal options, hide rescue options
    statusNormalItems.forEach(item => item.style.display = 'block');
    statusRescueItems.forEach(item => item.style.display = 'none');
}
```

### 3. **JavaScript - Rescue Handler** (mxh.html ~line 1708)
```javascript
async function rescueAccountUnified(result) {
    const accountIndex = mxhAccounts.findIndex(acc => acc.id === currentContextAccountId);
    
    if (result === 'success') {
        // Chuyển về active + tăng success count
        mxhAccounts[accountIndex][statusKey] = 'active';
        mxhAccounts[accountIndex][rescueSuccessKey]++;
    } else {
        // Giữ disabled + tăng failed count
        mxhAccounts[accountIndex][rescueKey]++;
    }
    
    // Call API
    await fetch(`/mxh/api/accounts/${id}/rescue`, {
        method: 'POST',
        body: JSON.stringify({ result, is_secondary })
    });
}
```

### 4. **Event Listener** (mxh.html ~line 2310)
```javascript
case 'rescue-success':
    await rescueAccountUnified('success');
    break;
case 'rescue-failed':
    await rescueAccountUnified('failed');
    break;
```

---

## 🧪 Test Scenarios

### **Test 1: Normal Status → Disabled**
1. Right-click card với status "active"
2. Hover "Trạng Thái"
3. **Expected**: See options: Available, Die, Vô hiệu hóa
4. Click "Vô hiệu hóa"
5. Card chuyển sang màu cam ⛔

### **Test 2: Disabled → Show Rescue Options**
1. Right-click card với status "disabled" (màu cam)
2. Hover "Trạng Thái"
3. **Expected**: See options: Được Cứu 💚, Cứu Thất Bại 💔
4. **No longer see**: Available, Die, Vô hiệu hóa

### **Test 3: Rescue Success**
1. Right-click disabled card
2. Hover "Trạng Thái" → Click "Được Cứu"
3. **Expected**:
   - Card chuyển về màu trắng (Available)
   - Toast: "✅ Đã cứu thành công!"
   - `rescue_success_count` +1 trong DB

### **Test 4: Rescue Failed**
1. Right-click disabled card
2. Hover "Trạng Thái" → Click "Cứu Thất Bại"
3. **Expected**:
   - Card vẫn màu cam (Disabled)
   - Toast: "📝 Đã ghi nhận cứu thất bại!"
   - `rescue_count` +1 trong DB

### **Test 5: WeChat Secondary Account**
1. Right-click WeChat card back side (secondary account)
2. Test tương tự với `is_secondary=true`
3. Counters: `secondary_rescue_count`, `secondary_rescue_success_count`

---

## 📊 Visual Flow

```
┌─────────────────────────────────────────────────┐
│ CONTEXT MENU                                    │
├─────────────────────────────────────────────────┤
│                                                 │
│ IF status = "active" or "die":                  │
│   Trạng Thái ▶                                  │
│     ├─ Available                                │
│     ├─ Die                                      │
│     └─ Vô hiệu hóa                              │
│                                                 │
│ IF status = "disabled":                         │
│   Trạng Thái ▶                                  │
│     ├─ 💚 Được Cứu        → Active + success++  │
│     └─ 💔 Cứu Thất Bại    → Disabled + fail++   │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## ✅ Benefits

1. ✅ **Không mất chức năng rescue** - Vẫn track được rescue attempts
2. ✅ **UI gọn gàng hơn** - Không cần submenu riêng "Cứu tài khoản"
3. ✅ **Context-aware** - Menu thay đổi theo trạng thái
4. ✅ **Database persistence** - Đầy đủ counters và history
5. ✅ **Instant feedback** - Toast messages rõ ràng
6. ✅ **Support secondary accounts** - WeChat account phụ cũng ok

---

## 📁 Files Modified

1. **app/templates/mxh.html**
   - Line ~127: Add rescue options to submenu
   - Line ~1295: Show/hide logic based on status
   - Line ~1708: `rescueAccountUnified()` function
   - Line ~2310: Event listener for rescue actions

---

## 🎯 Summary

**Trước**: ❌ Mất button rescue, không cứu được account disabled

**Bây giờ**: ✅ Dynamic submenu với rescue options khi disabled

**Refresh trang** (F5) để test ngay! 🚀
