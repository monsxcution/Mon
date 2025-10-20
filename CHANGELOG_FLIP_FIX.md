# THAY ĐỔI QUAN TRỌNG - 2025-10-20 v2

## 🔧 Các sửa chữa chính

### 1. ✅ Sửa Double-Click Card Flip Bug

**Vấn đề:** Phải click 2 lần mới chuyển được tài khoản, hiện tại đang render 2 mặt card giống nhau.

**Giải pháp:**
- **Trước**: Render cả front và back với activeAccount → cả 2 giống nhau
- **Sau**: Chỉ render front, back được tạo khi click chuyển account

**Code thay đổi:**
```javascript
// TRƯỚC (SAI):
${renderCardFace(activeAccount, accounts, 'front')}
${renderCardFace(activeAccount, accounts, 'back')}  // ← Giống front!

// SAU (ĐÚNG):
${renderCardFace(activeAccount, accounts, 'front')}
<!-- Mặt sau được cập nhật khi click chuyển account -->
```

**Flip Logic:**
```javascript
function flipCardToAccount(cardId, accountId) {
    // 1. Cập nhật state và add flip class NGAY
    state.isFlipped = true;
    state.activeAccountId = accountId;
    wrapper.classList.add('flipped');  // ← CSS flip ngay lập tức
    
    // 2. Sau 150ms: Render mặt sau (back) với account mới
    setTimeout(() => {
        // Xóa back cũ, render back mới
        cardInner.insertAdjacentHTML('beforeend', renderCardFace(...));
    }, 150);
    
    // 3. Sau 300ms: Swap front/back, reset isFlipped
    setTimeout(() => {
        // Đổi class: front ↔ back
        // Reset flip state
    }, 300);
}
```

**Kết quả:** Click 1 lần → card flip ngay → hiển thị account được chọn ✅

### 2. ✅ Hiển thị Quét WeChat và Trạng Thái Disable

**MXH OLD logic:**
- **Active**: Hiển thị số lượt quét
- **Disabled**: Hiển thị "Ngày bị vô hiệu", "Lượt cứu - Lượt cứu thành công"

**Code thêm vào renderCardFace():**
```javascript
let wechatInfo = '';
if (platform === 'wechat') {
    const isDisabled = account.status === 'disabled';
    
    if (isDisabled && account.die_date) {
        // Khi disabled: Ngày bị vô hiệu, Lượt cứu, Lượt cứu thành công
        wechatInfo = `
            <div class="mt-auto">
                <small class="text-danger">Ngày: ${disableDays}</small>
                <small>Lượt cứu: ${rescue_count}-${rescue_success_count}</small>
            </div>
        `;
    } else if (!isDisabled) {
        // Khi active: Số lượt quét
        wechatInfo = `
            <div class="mt-auto text-center">
                <small>Quét: <strong>${account.wechat_scan_count || 0}</strong></small>
                <small>Lần cuối: ${wechat_last_scan_date}</small>
            </div>
        `;
    }
}
```

### 3. ✅ Modal WeChat (Không cần sửa)

Modal WeChat trong file mới **đã đúng** - không có trường "Mật khẩu", chỉ có:
- Số Card
- Ngày Tạo (Ngày/Tháng/Năm)
- Trạng Thái
- Tên Người Dùng
- Số Điện Thoại

## 📂 Files đã thay đổi

| File | Thay đổi |
|------|----------|
| `app/templates/mxh.html` | • Xóa render back cùng front (dòng ~1130-1131)<br>• Sửa hàm flipCardToAccount() - 3 bước xử lý<br>• Thêm renderCardFace() - hiển thị quét/disable |

## 🎯 Kết quả

✅ **Click 1 lần → Chuyển account ngay** (không cần click 2 lần)
✅ **Hiển thị quét WeChat** khi active
✅ **Hiển thị ngày/lượt cứu** khi disabled
✅ **Modal WeChat đúng** (Số Card, Ngày Tạo, Trạng Thái, SĐT)

## 🧪 Test

```javascript
// Kiểm tra flip logic:
1. Mở MXH → Card hiển thị tài khoản primary
2. Click chuột phải → Tài Khoản → Chọn tài khoản 2
3. ✅ Card flip ngay, hiển thị tài khoản 2 (KHÔNG CẦN CLICK 2 LẦN)
4. Kiểm tra "Quét" hiện thị đúng
5. Nếu disabled, kiểm tra "Ngày/Lượt cứu" hiển thị đúng
```

## 📝 Lưu ý

- Card flip animation: 300ms (CSS 3D transition)
- Back face render sớm: 150ms (trước animation xong)
- Swap front/back classes: 300ms (khi flip hoàn thành)
- isFlipped state: `false` khi render xong (để flip lần sau hoạt động đúng)

---

**Version:** MXH NEW (1-N model) v2
**Status:** Ready to test ✅
