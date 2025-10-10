# 🤖 AI Prompt Template - Real-Time System
## Copy & Paste prompt này cho AI để implement real-time cho tab mới

---

## 📝 Prompt Template Cơ Bản

```
Tôi cần implement real-time system cho tab [TÊN_TAB] trong Flask app.

REQUIREMENTS:
✅ Auto-refresh mỗi 3 giây
✅ Instant local updates - không refresh trang khi user thao tác
✅ Scroll position preservation - giữ nguyên vị trí scroll
✅ Pause auto-refresh khi modal/context menu mở
✅ Error handling với revert changes nếu API lỗi
✅ Toast notifications cho mọi action

DATA STRUCTURE:
[MÔ TẢ CHI TIẾT DATA CỦA BẠN]

ACTIONS CẦN IMPLEMENT:
[LIST CÁC ACTIONS]

PATTERN BẮT BUỘC:
User Action → Update Local State → Render UI Immediately → Background API Call
- Nếu API success: Keep changes
- Nếu API error: Revert changes + Reload data

Hãy implement theo:
1. REALTIME_BLUEPRINT.md - Kiến trúc tổng thể
2. REALTIME_QUICK_REFERENCE.md - Code templates
3. app/templates/mxh.html - Example hoàn chỉnh

Bắt đầu với setup template từ REALTIME_QUICK_REFERENCE.md
```

---

## 🎯 Prompt Chi Tiết (Cho AI khác/mới)

```
# NHIỆM VỤ: Implement Real-Time System cho Tab [TÊN_TAB]

## 1️⃣ CONTEXT
Đây là Flask application với Bootstrap UI. Tab hiện tại load data bằng cách refresh trang toàn bộ. 
Cần nâng cấp thành real-time system với instant updates.

## 2️⃣ YÊU CẦU KỸ THUẬT

### Frontend (JavaScript):
1. **Global State Management**
   - Biến toàn cục lưu data array
   - Render lock mechanism (isRendering)
   - Pending updates queue
   - Auto-refresh timer control

2. **Auto-Refresh System** (3 giây)
   - Smart data comparison (chỉ render nếu data thay đổi)
   - Pause khi modal/context menu mở
   - Pause khi tab ẩn
   - Resume tự động

3. **Instant Local Updates**
   - User action → Update local state NGAY
   - Render UI NGAY (< 50ms)
   - API call chạy background
   - Nếu error → Revert + Reload

4. **Scroll Preservation**
   - Lưu scrollY/scrollX trước render
   - Khôi phục sau render trong requestAnimationFrame

5. **Error Handling**
   - Backup state trước update
   - Revert nếu API lỗi
   - Toast notification
   - Auto-reload để sync

### Backend (Flask):
- Giữ nguyên API hiện tại
- Đảm bảo trả JSON đúng format
- Error responses rõ ràng

## 3️⃣ DATA STRUCTURE

### Current Data:
```python
# Python (Flask)
[
    {
        'id': 1,
        'name': 'Item 1',
        'status': 'active',
        'created_at': '2024-01-01'
    }
]
```

### JavaScript State:
```javascript
let items = []; // Main data array
```

## 4️⃣ ACTIONS CẦN IMPLEMENT

### A. Toggle Status
- Click button → Thay đổi status ngay
- Active ↔ Disabled
- API: POST /api/items/{id}/toggle-status

### B. Inline Edit Fields
- Click vào text → Edit trực tiếp
- Blur → Save tự động
- Fields: name, description, phone, etc.
- API: PUT /api/items/{id}

### C. Delete Item
- Click delete → Item biến mất ngay
- API: DELETE /api/items/{id}

### D. Add New Item
- Submit form → Reload để lấy item mới
- API: POST /api/items

### E. [CÁC ACTIONS KHÁC...]

## 5️⃣ IMPLEMENTATION STEPS

### Step 1: Setup Template
Copy template từ REALTIME_QUICK_REFERENCE.md:
- Config object
- State variables
- Auto-refresh functions
- loadData() function
- renderUI() function

### Step 2: Implement Rendering
```javascript
function renderUI() {
    // Save scroll
    const scrollY = window.scrollY;
    
    // Generate HTML
    container.innerHTML = generateHTML();
    
    // Restore scroll + setup listeners
    requestAnimationFrame(() => {
        window.scrollTo(0, scrollY);
        setupEventListeners();
    });
}

function generateHTML() {
    return items.map(item => `
        <!-- HTML template cho mỗi item -->
    `).join('');
}
```

### Step 3: Implement Actions
Mỗi action theo pattern:
```javascript
async function actionName(itemId) {
    // 1. Update local
    const index = items.findIndex(x => x.id === itemId);
    items[index].field = newValue;
    
    // 2. Render
    renderUI();
    
    // 3. API
    try {
        await fetch(...);
        showToast('✅ Success!', 'success');
    } catch (error) {
        showToast('❌ Error!', 'error');
        await loadData(false);
    }
}
```

### Step 4: Setup Pause/Resume
- Modal events
- Context menu
- Tab visibility

### Step 5: Initialize
```javascript
document.addEventListener('DOMContentLoaded', async () => {
    await loadData(true);
    startAutoRefresh();
    setupPauseResume();
});
```

## 6️⃣ CODE REFERENCES

Tham khảo file:
- `REALTIME_BLUEPRINT.md` - Chi tiết kiến trúc
- `REALTIME_QUICK_REFERENCE.md` - Code templates
- `app/templates/mxh.html` - Example hoàn chỉnh

## 7️⃣ TESTING CHECKLIST

Sau khi implement, test:
- [ ] Click toggle status → Instant change
- [ ] Edit text inline → Save ngay
- [ ] Delete item → Biến mất ngay
- [ ] Scroll xuống dưới → Edit item → Vẫn ở vị trí cũ
- [ ] Mở modal → Auto-refresh pause
- [ ] Đóng modal → Auto-refresh resume
- [ ] Mở 2 tab → Edit tab 1 → Tab 2 tự động update sau 3s
- [ ] Lỗi API → Revert changes + Toast error

## 8️⃣ PERFORMANCE TARGETS

- Instant update: < 50ms
- Render time: < 100ms
- Auto-refresh: 3 seconds
- No page refresh
- No scroll jump

## 9️⃣ OUTPUT FORMAT

Trả về:
1. Complete HTML template với embedded JavaScript
2. Giải thích các phần chính
3. Note về các edge cases
4. Testing instructions

## 🔟 IMPORTANT NOTES

⚠️ KHÔNG ĐƯỢC:
- Refresh trang sau mọi action
- Block UI chờ API response
- Render mà không lưu scroll position
- Bỏ qua error handling

✅ PHẢI:
- Update local state TRƯỚC khi gọi API
- Render UI NGAY sau local update
- API call chạy background
- Revert nếu API lỗi
- Giữ scroll position
- Pause auto-refresh khi user tương tác

---

Bắt đầu implement theo steps trên. Hỏi nếu cần clarification!
```

---

## 🎨 Prompt Cho Specific Features

### Prompt cho Toggle Status:
```
Implement toggle status action theo real-time pattern:

REQUIREMENTS:
- Click button → Status thay đổi NGAY (active ↔ disabled)
- Không chờ API response
- Visual feedback ngay lập tức
- API call background
- Revert nếu error

CODE PATTERN:
```javascript
async function toggleStatus(itemId) {
    // 1. Local update
    const index = items.findIndex(item => item.id === itemId);
    if (index !== -1) {
        items[index].status = items[index].status === 'active' ? 'disabled' : 'active';
    }
    
    // 2. Render
    renderUI();
    
    // 3. API
    try {
        await fetch(`/api/items/${itemId}/toggle-status`, { method: 'POST' });
        showToast('✅ Đã thay đổi!', 'success');
    } catch (error) {
        showToast('❌ Lỗi!', 'error');
        await loadData(false);
    }
}
```

HTML:
```html
<button onclick="toggleStatus(${item.id})">
    ${item.status === 'active' ? 'Active' : 'Disabled'}
</button>
```

Implement và test!
```

### Prompt cho Inline Edit:
```
Implement inline edit field theo real-time pattern:

HTML:
```html
<span 
    class="editable" 
    contenteditable="true"
    data-item-id="${item.id}"
    data-field="name"
    onblur="handleEdit(this)"
    onkeydown="if(event.key==='Enter'){event.preventDefault();this.blur()}"
>${item.name}</span>
```

JAVASCRIPT:
```javascript
async function handleEdit(element) {
    const itemId = parseInt(element.dataset.itemId);
    const field = element.dataset.field;
    const newValue = element.textContent.trim();
    
    // 1. Update local
    const index = items.findIndex(item => item.id === itemId);
    if (index !== -1) {
        items[index][field] = newValue;
    }
    
    // 2. API (không cần render vì text đã thay đổi rồi)
    try {
        await fetch(`/api/items/${itemId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ [field]: newValue })
        });
        showToast('✅ Đã lưu!', 'success');
    } catch (error) {
        showToast('❌ Lỗi!', 'error');
        await loadData(false);
    }
}
```

FEATURES:
- Enter → Blur → Save
- Escape → Revert
- Auto-save on blur
- Toast notification

Implement!
```

---

## 🔥 Prompt Troubleshooting

### Khi trang vẫn bị refresh:
```
PROBLEM: Trang vẫn bị refresh sau action

DEBUG:
1. Kiểm tra có `await loadData(true)` sau mỗi action không?
   → Bỏ đi, chỉ dùng `renderUI()`

2. Kiểm tra có `window.location.reload()` không?
   → Bỏ đi

3. Kiểm tra form submit có preventDefault() không?
   → Thêm `event.preventDefault()`

CORRECT PATTERN:
```javascript
async function action(id) {
    // Update local
    items[i].field = newValue;
    
    // Render NGAY - không chờ API
    renderUI();
    
    // API background
    try {
        await fetch(...);
    } catch (e) {
        await loadData(false); // Chỉ reload nếu lỗi
    }
}
```
```

### Khi scroll bị nhảy:
```
PROBLEM: Scroll nhảy lên đầu trang sau action

FIX: Lưu và khôi phục scroll position

```javascript
function renderUI() {
    // LƯU SCROLL
    const scrollY = window.scrollY;
    const scrollX = window.scrollX;
    
    // Render
    container.innerHTML = html;
    
    // KHÔI PHỤC SCROLL
    requestAnimationFrame(() => {
        window.scrollTo(scrollX, scrollY);
    });
}
```
```

---

## 📚 Example Prompts Đã Test

### Example 1: Notes Tab
```
Implement real-time cho Notes Tab với data:
- id, title, content, created_at, pinned

Actions:
- Toggle pin
- Inline edit title/content
- Delete note
- Add new note

Follow REALTIME_BLUEPRINT.md pattern.
```

### Example 2: User Management
```
Implement real-time cho User Management với data:
- id, name, email, role, status, last_login

Actions:
- Toggle status (active/banned)
- Change role (admin/user/moderator)
- Delete user
- Inline edit name/email

Follow REALTIME_QUICK_REFERENCE.md templates.
```

### Example 3: Todo List
```
Implement real-time Todo List với data:
- id, text, completed, priority, due_date

Actions:
- Toggle completed
- Inline edit text
- Change priority (dropdown)
- Delete todo
- Reorder (drag & drop - advanced)

Pattern: Local → Render → API → Revert on error
```

---

## 💡 Tips for AI

### Khi chat với AI mới:
1. **Upload 3 files reference:**
   - REALTIME_BLUEPRINT.md
   - REALTIME_QUICK_REFERENCE.md
   - MXH_REALTIME_UPDATE.md (hoặc mxh.html)

2. **Provide context:**
   - Flask app with Bootstrap
   - Current tab structure
   - API endpoints available
   - Data structure

3. **Be specific:**
   - List exact actions needed
   - Specify which fields are editable
   - Mention any special behaviors

4. **Ask for:**
   - Complete code (not snippets)
   - Explanation of key parts
   - Testing checklist

### Red flags (AI làm sai):
- ❌ `await loadData(true)` sau mỗi action
- ❌ `window.location.reload()`
- ❌ Không lưu scroll position
- ❌ Không có error handling
- ❌ Blocking UI chờ API

### Green flags (AI làm đúng):
- ✅ Local update trước
- ✅ `renderUI()` ngay
- ✅ API call background
- ✅ Scroll preservation
- ✅ Error handling với revert
- ✅ Toast notifications

---

**Với 3 file này, bất kỳ AI nào cũng có thể replicate được hệ thống real-time! 🚀**

Files:
1. `REALTIME_BLUEPRINT.md` - Architecture & patterns
2. `REALTIME_QUICK_REFERENCE.md` - Code templates
3. `AI_PROMPT_TEMPLATE.md` - This file (prompts)

Bonus: `app/templates/mxh.html` - Working example
