# ⚡ Real-Time Quick Reference
## Cheat Sheet - Copy & Paste để implement nhanh

---

## 🎯 Core Pattern (NHỚ KỸ!)

```javascript
async function anyAction(itemId) {
    // 1️⃣ UPDATE LOCAL (< 10ms)
    const index = items.findIndex(item => item.id === itemId);
    if (index !== -1) {
        items[index].field = newValue;
    }
    
    // 2️⃣ RENDER NGAY (< 50ms)
    renderUI();
    
    // 3️⃣ API BACKGROUND
    try {
        await fetch(`/api/items/${itemId}`, { method: 'POST' });
        showToast('✅ Success!', 'success');
    } catch (error) {
        showToast('❌ Error!', 'error');
        await loadData(false); // Revert
    }
}
```

---

## 📋 Setup Template (Copy nguyên)

```javascript
// ===== CONFIG =====
const CONFIG = {
    AUTO_REFRESH_INTERVAL: 3000,
    ENABLE_AUTO_REFRESH: true
};

// ===== STATE =====
let items = [];
let isRendering = false;
let pendingUpdates = false;
let autoRefreshTimer = null;
let interactionPaused = false;

// ===== AUTO-REFRESH =====
function startAutoRefresh() {
    stopAutoRefresh();
    autoRefreshTimer = setInterval(() => {
        if (!interactionPaused) loadData(false);
    }, CONFIG.AUTO_REFRESH_INTERVAL);
}

function stopAutoRefresh() {
    if (autoRefreshTimer) clearInterval(autoRefreshTimer);
}

function pauseAutoRefresh() { interactionPaused = true; }
function resumeAutoRefresh() { interactionPaused = false; }

// ===== LOAD DATA =====
async function loadData(forceRender = true) {
    const response = await fetch('/api/items');
    const newItems = await response.json();
    const changed = JSON.stringify(newItems) !== JSON.stringify(items);
    items = newItems;
    
    if (forceRender || changed) {
        if (!isRendering) renderUI();
        else pendingUpdates = true;
    }
}

// ===== RENDER =====
function renderUI() {
    if (isRendering) { pendingUpdates = true; return; }
    isRendering = true;
    
    const scrollY = window.scrollY;
    const scrollX = window.scrollX;
    
    container.innerHTML = generateHTML();
    
    requestAnimationFrame(() => {
        window.scrollTo(scrollX, scrollY);
        setupEventListeners();
        isRendering = false;
        if (pendingUpdates) {
            pendingUpdates = false;
            setTimeout(() => renderUI(), 100);
        }
    });
}

// ===== INIT =====
document.addEventListener('DOMContentLoaded', async () => {
    await loadData(true);
    startAutoRefresh();
    
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('show.bs.modal', pauseAutoRefresh);
        modal.addEventListener('hide.bs.modal', resumeAutoRefresh);
    });
    
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) stopAutoRefresh();
        else { startAutoRefresh(); loadData(true); }
    });
});
```

---

## 🔥 Common Actions

### Toggle Status
```javascript
async function toggleStatus(id) {
    const i = items.findIndex(x => x.id === id);
    items[i].status = items[i].status === 'active' ? 'disabled' : 'active';
    renderUI();
    
    try {
        await fetch(`/api/items/${id}/toggle`, { method: 'POST' });
        showToast('✅ OK!', 'success');
    } catch (e) {
        showToast('❌ Error!', 'error');
        await loadData(false);
    }
}
```

### Delete
```javascript
async function deleteItem(id) {
    items = items.filter(x => x.id !== id);
    renderUI();
    
    try {
        await fetch(`/api/items/${id}`, { method: 'DELETE' });
        showToast('✅ Deleted!', 'success');
    } catch (e) {
        showToast('❌ Error!', 'error');
        await loadData(false);
    }
}
```

### Inline Edit
```javascript
async function handleEdit(element) {
    const id = parseInt(element.dataset.itemId);
    const field = element.dataset.field;
    const value = element.textContent.trim();
    
    const i = items.findIndex(x => x.id === id);
    items[i][field] = value;
    
    try {
        await fetch(`/api/items/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ [field]: value })
        });
        showToast('✅ Saved!', 'success');
    } catch (e) {
        showToast('❌ Error!', 'error');
        await loadData(false);
    }
}
```

### Update Field
```javascript
async function updateField(id, field, value) {
    const i = items.findIndex(x => x.id === id);
    items[i][field] = value;
    renderUI();
    
    try {
        await fetch(`/api/items/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ [field]: value })
        });
        showToast('✅ Updated!', 'success');
    } catch (e) {
        showToast('❌ Error!', 'error');
        await loadData(false);
    }
}
```

---

## 🎨 HTML Templates

### Editable Field
```html
<span 
    class="editable" 
    contenteditable="true"
    data-item-id="${item.id}"
    data-field="name"
    onblur="handleEdit(this)"
    onfocus="this.dataset.original = this.textContent"
    onkeydown="if(event.key==='Enter'){event.preventDefault();this.blur()}"
>${item.name}</span>
```

### Toggle Button
```html
<button onclick="toggleStatus(${item.id})" style="cursor: pointer;">
    ${item.status === 'active' ? '✅ Active' : '❌ Disabled'}
</button>
```

### Delete Button
```html
<button onclick="deleteItem(${item.id})" class="btn btn-danger btn-sm">
    <i class="bi bi-trash"></i> Delete
</button>
```

---

## 🛡️ Error Handling Pattern

```javascript
async function anyAction(id) {
    // Backup
    const backup = JSON.parse(JSON.stringify(items));
    
    // Optimistic update
    const i = items.findIndex(x => x.id === id);
    items[i].field = newValue;
    renderUI();
    
    try {
        const res = await fetch(`/api/items/${id}`, { method: 'POST' });
        if (!res.ok) throw new Error('Failed');
        showToast('✅ Success!', 'success');
    } catch (error) {
        // Revert
        items = backup;
        renderUI();
        showToast('❌ Error! Reverted.', 'error');
    }
}
```

---

## 🚦 Pause/Resume

```javascript
// Modal
document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('show.bs.modal', pauseAutoRefresh);
    modal.addEventListener('hide.bs.modal', resumeAutoRefresh);
});

// Context Menu
function showContextMenu(e, id) {
    pauseAutoRefresh();
    // ... show menu
}

function hideContextMenu() {
    resumeAutoRefresh();
    // ... hide menu
}

// Tab Visibility
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        stopAutoRefresh();
    } else {
        startAutoRefresh();
        loadData(true);
    }
});
```

---

## 📱 Toast Notification

```javascript
function showToast(message, type = 'success') {
    const toast = document.getElementById('liveToast');
    const toastBody = document.getElementById('toastBody');
    const toastHeader = document.getElementById('toastHeader');
    
    toastBody.textContent = message;
    toastHeader.className = 'toast-header';
    
    if (type === 'success') {
        toastHeader.classList.add('bg-success', 'text-white');
    } else {
        toastHeader.classList.add('bg-danger', 'text-white');
    }
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}
```

---

## ⚡ Performance Tips

### Use requestAnimationFrame
```javascript
requestAnimationFrame(() => {
    // DOM operations here
});
```

### Debounce
```javascript
const debounced = debounce((value) => {
    updateField(id, 'name', value);
}, 500);
```

### Batch Updates
```javascript
// Update multiple items at once
itemIds.forEach(id => {
    const i = items.findIndex(x => x.id === id);
    items[i].status = 'disabled';
});
renderUI(); // Only render once
```

---

## 🐛 Debug Tips

```javascript
// Log rendering
function renderUI() {
    console.log('🎨 Rendering...', items.length, 'items');
    // ... render code
}

// Log API calls
async function apiCall(url, options) {
    console.log('🌐 API:', url, options);
    const response = await fetch(url, options);
    console.log('✅ Response:', response.status);
    return response;
}

// Monitor auto-refresh
function startAutoRefresh() {
    console.log('▶️ Auto-refresh started');
    // ...
}
```

---

## ✅ Checklist

Setup:
- [ ] Global state variables
- [ ] Config object
- [ ] Auto-refresh functions
- [ ] Load data function
- [ ] Render function with scroll preservation

Actions:
- [ ] All actions follow: Local → Render → API pattern
- [ ] Error handling with revert
- [ ] Toast notifications

Lifecycle:
- [ ] DOMContentLoaded initialization
- [ ] Pause on modal open
- [ ] Pause on context menu
- [ ] Handle tab visibility

Testing:
- [ ] Test instant updates
- [ ] Test scroll preservation
- [ ] Test auto-refresh
- [ ] Test error handling

---

## 🎯 One-Liner Commands

```javascript
// Reload everything
await loadData(true);

// Refresh data only if changed
await loadData(false);

// Force render
renderUI();

// Pause refresh
pauseAutoRefresh();

// Resume refresh
resumeAutoRefresh();

// Stop refresh completely
stopAutoRefresh();

// Start fresh
startAutoRefresh();
```

---

## 🚀 Quick Start (3 bước)

1. **Copy template code** → Paste vào file .html
2. **Update `generateHTML()`** → Tạo HTML cho items
3. **Implement actions** → Toggle, Delete, Edit, etc.

Done! Real-time ready! ⚡

---

**Remember:** Local First → Render → API → Revert if Error

💡 Tip: Khi lỗi, luôn `await loadData(false)` để lấy data đúng từ server!
