/**
 * STool Dashboard - Global JavaScript Functions
 * File này chứa các functions dùng chung cho toàn bộ ứng dụng
 */

// ===== TOAST NOTIFICATION FUNCTION =====
/**
 * Hiển thị toast notification (Bootstrap Toast)
 * @param {string} message - Nội dung thông báo
 * @param {string} type - Loại thông báo ('success', 'error', 'info')
 * @param {string} title - Tiêu đề tùy chỉnh (optional)
 */
function showToast(message, type = 'success', title = 'Thông báo') {
    const toastEl = document.getElementById('liveToast');
    const toastHeader = document.getElementById('toastHeader');
    const toastTitle = document.getElementById('toastTitle');
    const toastBody = document.getElementById('toastBody');
    
    if (!toastEl) {
        console.warn('Toast element not found!');
        return;
    }
    
    // Set message
    toastBody.textContent = message;
    
    // Reset header classes
    toastHeader.className = 'toast-header';
    
    // Apply styling based on type
    if (type === 'success') {
        toastHeader.classList.add('bg-success', 'text-white');
        toastTitle.textContent = '✅ Thành công';
    } else if (type === 'error') {
        toastHeader.classList.add('bg-danger', 'text-white');
        toastTitle.textContent = '❌ Lỗi';
    } else if (type === 'warning') {
        toastHeader.classList.add('bg-warning', 'text-dark');
        toastTitle.textContent = '⚠️ Cảnh báo';
    } else {
        toastHeader.classList.add('bg-info', 'text-white');
        toastTitle.textContent = title;
    }
    
    // Show toast
    const toast = new bootstrap.Toast(toastEl);
    toast.show();
}

// ===== GLOBAL HELPERS =====
// Bạn có thể thêm các helper functions khác vào đây
// Ví dụ: formatDate, formatNumber, debounce, throttle, etc.

// ===== MODAL KEYBOARD SHORTCUTS =====
/**
 * Xử lý phím Enter và Esc cho tất cả modal
 * - Enter: Kích hoạt nút primary/danger trong modal
 * - Esc: Đóng modal (Bootstrap tự xử lý, nhưng có thể custom)
 */
document.addEventListener('DOMContentLoaded', function() {
    // Lắng nghe sự kiện khi modal được hiển thị
    document.addEventListener('shown.bs.modal', function(event) {
        const modal = event.target;
        
        // Tìm nút primary hoặc danger trong modal (ưu tiên danger cho modal xóa)
        const dangerBtn = modal.querySelector('.modal-footer .btn-danger');
        const primaryBtn = modal.querySelector('.modal-footer .btn-primary');
        const actionBtn = dangerBtn || primaryBtn;
        
        // Handler cho phím Enter
        const enterHandler = function(e) {
            if (e.key === 'Enter' && !e.shiftKey && !e.ctrlKey && !e.altKey) {
                // Không áp dụng nếu đang focus vào textarea
                if (document.activeElement.tagName === 'TEXTAREA') {
                    return;
                }
                
                e.preventDefault();
                if (actionBtn && !actionBtn.disabled) {
                    actionBtn.click();
                }
            }
        };
        
        // Thêm event listener
        modal.addEventListener('keydown', enterHandler);
        
        // Cleanup khi modal bị đóng
        modal.addEventListener('hidden.bs.modal', function() {
            modal.removeEventListener('keydown', enterHandler);
        }, { once: true });
    });
});

