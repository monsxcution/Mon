# 🚨 CRITICAL CODE PRESERVATION NOTICE

## ⚠️ **KHÔNG ĐƯỢC XÓA HOẶC THAY ĐỔI CÁC DÒNG CODE SAU**

### 1. **CHẾ ĐỘ XEM - LAYOUT CRITICAL CODE**

**File: `app/static/js/mxh.js` - Dòng 456**
```javascript
<div class="col" style="flex:0 0 calc(100% / var(--cardsPerRow, 12));max-width:calc(100% / var(--cardsPerRow, 12));padding:4px" data-account-id="${account.id}">
```

**File: `app/static/js/mxh.js` - Dòng 26**
```javascript
function applyViewMode(value){const n=Math.max(1,parseInt(value,10)||12);localStorage.setItem('mxh_cards_per_row',n);document.documentElement.style.setProperty('--cardsPerRow',n);const c=document.getElementById('mxh-accounts-container');if(c)c.style.setProperty('--cardsPerRow',n);}
```

**File: `app/templates/mxh.html` - Dòng 35**
```html
<div id="mxh-accounts-container" class="d-flex flex-wrap">
```

### 2. **TẠI SAO QUAN TRỌNG?**

- **Inline style** `flex:0 0 calc(100% / var(--cardsPerRow, 12))` **LUÔN THẮNG** mọi CSS ngoài
- **Container class** `d-flex flex-wrap` đảm bảo cards wrap đúng hàng
- **applyViewMode()** set biến CSS ở cả documentElement và container scope
- **Không được thay đổi** thành Bootstrap grid (`row g-2`) - sẽ làm vỡ layout

### 3. **HẬU QUẢ NẾU THAY ĐỔI:**
- ❌ Tất cả cards sẽ nằm trên 1 hàng
- ❌ "Chế Độ Xem" không hoạt động
- ❌ Layout responsive bị vỡ
- ❌ User experience tệ hại

### 4. **KIỂM TRA LOGIC SCAN WECHAT**

**Các action cần kiểm tra:**
- `mark-scanned` → `markAccountAsScanned()`
- `reset-scan` → `resetScanCount()`

**API endpoints:**
- `POST /api/mxh/accounts/mark-scanned`
- `POST /api/mxh/accounts/reset-scan`

---

## 🔒 **PRESERVATION RULES**

1. **KHÔNG BAO GIỜ** thay đổi inline style trong renderMXHAccounts()
2. **KHÔNG BAO GIỜ** thay đổi container class từ `d-flex flex-wrap`
3. **KHÔNG BAO GIỜ** thay đổi applyViewMode() function
4. **LUÔN GIỮ NGUYÊN** logic flexbox và CSS variables

**⚠️ AI DEV WARNING: Đây là code critical cho layout system. Thay đổi sẽ làm vỡ toàn bộ giao diện!**
