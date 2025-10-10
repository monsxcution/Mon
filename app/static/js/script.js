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

