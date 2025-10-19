# MXH Card Layout System - CRITICAL COMPONENT

## ⚠️ QUAN TRỌNG: KHÔNG ĐƯỢC PHÁ VỠ HỆ THỐNG NÀY

### Tổng quan
Hệ thống layout card trong MXH được thiết kế để hiển thị các card tài khoản theo số lượng hàng có thể tùy chỉnh thông qua nút "Chế Độ Xem". **Nếu phá vỡ hoặc thay đổi bất kỳ thành phần nào dưới đây, tất cả các card sẽ bị lỗi hiển thị cùng 1 hàng thay vì sắp xếp đúng theo số lượng trong chế độ xem.**

## 🔧 Các thành phần CRITICAL

### 1. Container HTML (app/templates/mxh.html)
```html
<div id="mxh-accounts-container" class="d-flex flex-wrap">
```
**KHÔNG ĐƯỢC THAY ĐỔI:** Class `d-flex flex-wrap` là bắt buộc để container có thể wrap các card xuống hàng mới.

### 2. Card Width Inline Style (app/static/js/mxh.js)
```javascript
<div class="col" style="flex:0 0 calc(100% / var(--cardsPerRow, 12));max-width:calc(100% / var(--cardsPerRow, 12));padding:4px">
```
**KHÔNG ĐƯỢC THAY ĐỔI:** 
- Inline style này ép buộc width của từng card theo biến CSS `--cardsPerRow`
- `flex:0 0 calc(100% / var(--cardsPerRow, 12))` đảm bảo mỗi card chiếm đúng 1/N của container
- `max-width:calc(100% / var(--cardsPerRow, 12))` ngăn card bị stretch
- `padding:4px` tạo khoảng cách giữa các card

### 3. CSS Variable System (app/static/js/mxh.js)
```javascript
function applyViewMode(value){
    const n=Math.max(1,parseInt(value,10)||12);
    localStorage.setItem('mxh_cards_per_row',n);
    document.documentElement.style.setProperty('--cardsPerRow',n);
    const c=document.getElementById('mxh-accounts-container');
    if(c)c.style.setProperty('--cardsPerRow',n);
}
```
**KHÔNG ĐƯỢC THAY ĐỔI:**
- Hàm này set biến CSS `--cardsPerRow` ở cả document root và container
- Biến này được sử dụng trong inline style của mỗi card
- Nếu không set đúng, cards sẽ không hiển thị đúng số lượng mỗi hàng

## 🚨 Hậu quả nếu phá vỡ hệ thống

### Nếu thay đổi container class:
- **Mất `d-flex`**: Cards sẽ xếp dọc thay vì ngang
- **Mất `flex-wrap`**: Tất cả cards sẽ nằm trên 1 hàng dài

### Nếu thay đổi inline style:
- **Mất `flex:0 0 calc(...)`**: Cards sẽ không có width cố định
- **Mất `max-width:calc(...)`**: Cards có thể bị stretch không đều
- **Mất `padding:4px`**: Cards sẽ dính nhau

### Nếu thay đổi CSS variable logic:
- **Mất `--cardsPerRow`**: Cards sẽ dùng default 12 cards/hàng
- **Mất scope container**: Cards có thể không nhận được giá trị đúng

## ⚠️ VẤN ĐỀ QUAN TRỌNG: borderClass bị rỗng

### Triệu chứng:
```html
<div class="card tool-card mxh-card  " id="card-12">
```
↑ Có **2 khoảng trắng** giữa `mxh-card` và `id` → `borderClass` = `""` hoặc `" "`

### Nguyên nhân:
- `borderClass` được tính toán nhưng **không được sử dụng** trong HTML template
- Logic `isDie`, `hasNotice` có thể không hoạt động đúng
- CSS selector có thể bị override

### Giải pháp:
1. **Kiểm tra console logs** để debug `borderClass` value
2. **Đảm bảo** `${borderClass}` được sử dụng trong HTML template
3. **Thêm CSS với specificity cao** để override
4. **Test với inline CSS** để xác nhận

## 🎯 Cách hoạt động

1. **User chọn số cards/hàng** trong modal "Chế Độ Xem"
2. **applyViewMode()** được gọi với giá trị mới
3. **CSS variable `--cardsPerRow`** được set trên container
4. **Mỗi card** sử dụng `calc(100% / var(--cardsPerRow, 12))` để tính width
5. **Container với `d-flex flex-wrap`** tự động wrap cards xuống hàng mới

## ⚡ Performance Notes

- **Inline style** có độ ưu tiên cao nhất, thắng mọi CSS external
- **CSS variables** được tính toán real-time, không cần re-render
- **Flexbox** tự động handle responsive layout

## 🔒 Bảo vệ hệ thống

**KHÔNG BAO GIỜ:**
- Xóa class `d-flex flex-wrap` khỏi container
- Thay đổi inline style trong renderMXHAccounts()
- Sửa logic CSS variable trong applyViewMode()
- Thêm CSS external override cho `.col` width

**CHỈ ĐƯỢC:**
- Thay đổi giá trị default của `--cardsPerRow` (hiện tại là 12)
- Thay đổi padding value (hiện tại là 4px)
- Thêm CSS cho styling khác (màu sắc, border, etc.)

---

## 🔴 VẤN ĐỀ VIỀN CARD MÀU ĐỎ - TỔNG KẾT GIẢI PHÁP

### 🚨 Vấn đề ban đầu:
**Viền card không hiển thị màu đỏ** cho các tài khoản có trạng thái "Die" hoặc có thông báo.

### 🔍 Nguyên nhân gốc rễ:

#### 1. **borderClass không được sử dụng trong HTML template**
```html
<!-- TRƯỚC (SAI): -->
<div class="card tool-card mxh-card " id="card-12">
<!-- ↑ Có 2 khoảng trắng → borderClass = "" -->

<!-- SAU (ĐÚNG): -->
<div class="card tool-card mxh-card ${borderClass}" id="card-12">
<!-- ↑ borderClass được sử dụng đúng -->
```

#### 2. **CSS specificity không đủ cao**
- CSS rules bị override bởi Bootstrap hoặc style.css
- Cần specificity cao hơn để thắng các rules khác

#### 3. **Logic JavaScript không hoạt động đúng**
- `isDie` logic có thể không detect đúng trạng thái
- `hasNotice` logic có thể miss các trường hợp

### 🛠️ Quá trình giải quyết:

#### **Bước 1: Debug và xác định vấn đề**
```javascript
// Thêm console.log để debug
console.log(`Account ${account.id}: status=${account.status}, isDie=${isDie}, hasNotice=${hasNotice}, borderClass="${borderClass}"`);
```

#### **Bước 2: Sửa HTML template**
```javascript
// Đảm bảo borderClass được sử dụng
<div class="card tool-card mxh-card ${borderClass} ${extraClass}" id="card-${account.id}">
```

#### **Bước 3: Tăng CSS specificity**
```css
/* CSS với specificity cực cao */
html body #mxh-accounts-container .tool-card.mxh-card.mxh-border-red {
    border: 2px solid #ff4d4f !important;
    box-shadow: none !important;
}
```

#### **Bước 4: Thêm inline style backup**
```javascript
// Inline style với !important để đảm bảo 100% hiển thị
let inlineStyle = '';
if (borderClass === 'mxh-border-red') {
    inlineStyle = 'border: 2px solid #ff4d4f !important;';
}
```

### ✅ Giải pháp cuối cùng:

#### **1. HTML Template (app/static/js/mxh.js)**
```javascript
<div class="card tool-card mxh-card ${borderClass} ${extraClass}" id="card-${account.id}" style="position:relative; ${inlineStyle}">
```

#### **2. CSS với 3 lớp bảo vệ (app/static/css/mxh.css)**
```css
/* Lớp 1: CSS thông thường */
.tool-card.mxh-card.mxh-border-red {
    border: 2px solid #ff4d4f !important;
}

/* Lớp 2: CSS với specificity cao */
#mxh-accounts-container .tool-card.mxh-card.mxh-border-red {
    border: 2px solid #ff4d4f !important;
}

/* Lớp 3: CSS với specificity cực cao */
html body #mxh-accounts-container .tool-card.mxh-card.mxh-border-red {
    border: 2px solid #ff4d4f !important;
    box-shadow: none !important;
}
```

#### **3. JavaScript với inline style backup**
```javascript
// Force inline style cho red border
let inlineStyle = '';
if (borderClass === 'mxh-border-red') {
    inlineStyle = 'border: 2px solid #ff4d4f !important;';
}
```

### 🎯 Kết quả:
- **Viền đỏ hiển thị đúng** cho tài khoản Die/Notice
- **Không chói mắt** - chỉ là đường line 2px đơn giản
- **3 lớp bảo vệ** - đảm bảo hiển thị trong mọi trường hợp
- **Debug logs** - dễ dàng troubleshoot nếu có vấn đề

### 📝 Bài học:
1. **Luôn kiểm tra HTML output** - đảm bảo variables được sử dụng đúng
2. **CSS specificity quan trọng** - cần specificity cao để override
3. **Inline style là backup tốt nhất** - luôn thắng external CSS
4. **Debug logs cần thiết** - giúp xác định vấn đề nhanh chóng

---

**LƯU Ý CHO AI KHÁC:** Đây là hệ thống layout core của MXH. Mọi thay đổi đều phải được test kỹ lưỡng để đảm bảo cards hiển thị đúng số lượng mỗi hàng theo chế độ xem đã chọn.
