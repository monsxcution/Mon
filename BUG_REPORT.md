# 🐛 BÁO CÁO LỖI: CSS Variable --cardsPerRow Không Hoạt Động

## **Mô tả vấn đề**
- **Triệu chứng**: Toast báo "Đã áp dụng số cards mỗi hàng: 12" nhưng layout vẫn hiển thị tất cả 13 cards trên cùng một hàng
- **Mục tiêu**: 12 cards mỗi hàng, card thứ 13 phải xuống hàng mới
- **Kết quả thực tế**: Tất cả cards vẫn nằm trên cùng một hàng

## **Files liên quan**
1. `app/static/css/mxh.css` - CSS chính cho layout
2. `app/static/css/style.css` - CSS tổng thể (có thể conflict)
3. `app/static/js/mxh.js` - JavaScript logic
4. `app/templates/mxh.html` - HTML template

## **CSS hiện tại**
```css
/* mxh.css */
#mxh-accounts-container .col {
  flex: 0 0 calc(100% / var(--cardsPerRow, 6)) !important;
  max-width: calc(100% / var(--cardsPerRow, 6)) !important;
  border: 2px solid red !important; /* DEBUG: Remove this line */
}
```

## **JavaScript hiện tại**
```javascript
function applyViewMode(value) {
  var n = Math.max(1, Number(value || localStorage.getItem('mxh_cards_per_row') || 6));
  localStorage.setItem('mxh_cards_per_row', n);

  // đặt CSS var cho container và :root (phòng khi CSS ăn var từ 2 nơi)
  var container = document.getElementById('mxh-accounts-container');
  if (container) container.style.setProperty('--cardsPerRow', n);
  document.documentElement.style.setProperty('--cardsPerRow', n);
}
```

## **HTML structure**
```html
<div id="mxh-accounts-container" style="--cardsPerRow: 6;">
  <div class="row">
    <div class="col">Card 1</div>
    <div class="col">Card 2</div>
    <!-- ... more cards ... -->
  </div>
</div>
```

## **Nguyên nhân có thể**
1. **CSS selector không match đúng HTML structure**
2. **CSS variable không được set đúng cách trong JavaScript**
3. **CSS không được load đúng thứ tự hoặc bị override**
4. **Bootstrap CSS đang override custom CSS**

## **Debug steps đã thử**
1. ✅ Thêm `!important` vào CSS
2. ✅ Xóa CSS trùng lặp trong `style.css`
3. ✅ Thêm border debug (đỏ) để kiểm tra CSS có được áp dụng không
4. ✅ Kiểm tra CSS variable được set đúng cách
5. ✅ Kiểm tra HTML structure

## **Kết quả debug**
- CSS selector: `#mxh-accounts-container .col` ✅
- CSS variable: `--cardsPerRow` được set ✅
- JavaScript: `applyViewMode()` được gọi ✅
- Toast: Hiển thị thành công ✅
- Layout: KHÔNG thay đổi ❌

## **Yêu cầu hỗ trợ**
Cần ChatGPT phân tích và đưa ra giải pháp để:
1. CSS variable `--cardsPerRow` hoạt động đúng
2. Layout thay đổi theo số cards mỗi hàng
3. Cards wrap xuống hàng mới khi vượt quá số cards mỗi hàng
