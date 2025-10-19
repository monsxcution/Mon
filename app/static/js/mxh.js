// MXH Module - Add Account Functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log('MXH module loaded - Add Account functionality ready');
    
    // Load cards when modal opens
    const addAccountBtn = document.getElementById('btn-add-account');
    const addAccountModal = document.getElementById('addAccountModal');
    const cardSelect = document.getElementById('cardSelect');
    const saveAccountBtn = document.getElementById('saveAccountBtn');
    
    if (addAccountBtn && addAccountModal) {
        addAccountBtn.addEventListener('click', function() {
            loadCards();
            const modal = new bootstrap.Modal(addAccountModal);
            modal.show();
        });
    }
    
    if (saveAccountBtn) {
        saveAccountBtn.addEventListener('click', function() {
            saveAccount();
        });
    }
    
    // Load cards from API
    async function loadCards() {
        try {
            const response = await fetch('/mxh/api/cards');
            if (!response.ok) {
                throw new Error('Failed to load cards');
            }
            
            const cards = await response.json();
            cardSelect.innerHTML = '<option value="">Chọn thẻ...</option>';
            
            cards.forEach(card => {
                const option = document.createElement('option');
                option.value = card.id;
                option.textContent = `${card.card_name} (${card.platform})`;
                cardSelect.appendChild(option);
            });
        } catch (error) {
            console.error('Error loading cards:', error);
            cardSelect.innerHTML = '<option value="">Lỗi tải danh sách thẻ</option>';
            showToast('Lỗi tải danh sách thẻ', 'error');
        }
    }
    
    // Save account
    async function saveAccount() {
        const cardId = cardSelect.value;
        const accountName = document.getElementById('accountName').value;
        const username = document.getElementById('username').value;
        const phone = document.getElementById('phone').value;
        const isPrimary = document.getElementById('isPrimary').checked;
        
        if (!cardId || !accountName || !username || !phone) {
            showToast('Vui lòng điền đầy đủ thông tin', 'warning');
            return;
        }
        
        try {
            const response = await fetch(`/mxh/api/cards/${cardId}/accounts`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    account_name: accountName,
                    username: username,
                    phone: phone,
                    is_primary: isPrimary ? 1 : 0
                })
            });

            if (response.ok) {
                showToast('Tạo tài khoản thành công', 'success');
                const modal = bootstrap.Modal.getInstance(addAccountModal);
                modal.hide();
                // Reset form
                document.getElementById('addAccountForm').reset();
            } else {
                const error = await response.json();
                showToast(error.error || 'Lỗi tạo tài khoản', 'error');
            }
        } catch (error) {
            console.error('Error saving account:', error);
            showToast('Lỗi kết nối máy chủ', 'error');
        }
    }
    
    // Toast notification function
    function showToast(message, type = 'info') {
        // Create toast element
        const toastContainer = document.getElementById('toast-container') || createToastContainer();
        const toastId = 'toast-' + Date.now();
        const bgClass = type === 'error' ? 'bg-danger' : (type === 'success' ? 'bg-success' : (type === 'warning' ? 'bg-warning' : 'bg-primary'));
        
        const toastHTML = `
            <div id="${toastId}" class="toast align-items-center text-white ${bgClass}" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">${message}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        `;
        
        toastContainer.insertAdjacentHTML('beforeend', toastHTML);
        const toastEl = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
        toast.show();
        
        toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
    }

    // Create toast container if it doesn't exist
    function createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
        return container;
    }
});