// ===== MXH REAL-TIME CONFIGURATION =====
const MXH_CONFIG = {
    AUTO_REFRESH_INTERVAL: 15000, // Changed from 3000 to 15000ms (15 seconds)
    DEBOUNCE_DELAY: 500, // Debounce for inline editing
    RENDER_BATCH_SIZE: 50, // Cards to render per batch (for smooth rendering)
    ENABLE_AUTO_REFRESH: true // Changed from false to true
};


// MXH Global State
    let mxhGroups = [];
let mxhAccounts = [];
    let currentContextAccountId = null;
let autoRefreshTimer = null;
    let isRendering = false;
    let pendingUpdates = false;
let activeGroupId = null;
let lastUpdateTime = null; // NEW: Store the timestamp of the last successful data load // null = show all groups, otherwise show specific group only

// ===== VIEW MODE CONFIGURATION =====
/**
 * Áp dụng giá trị số card mỗi hàng vào CSS và lưu vào localStorage.
 * @param {number | string} value - Số lượng card mong muốn trên một hàng.
 */
function applyViewMode(value) {
  // Đảm bảo giá trị là một số hợp lệ, tối thiểu là 1, mặc định là 12.
  var n = Math.max(1, Number(value || localStorage.getItem('mxh_cards_per_row') || 12));
  
  // Lưu giá trị vào localStorage để ghi nhớ cho lần sau.
  localStorage.setItem('mxh_cards_per_row', n);

  // Lấy container chính và đặt giá trị cho biến CSS `--cardsPerRow`.
  var container = document.getElementById('mxh-accounts-container');
  if (container) {
    container.style.setProperty('--cardsPerRow', n);
  }
}

/**
 * Khởi tạo chức năng "Chế Độ Xem" khi trang được tải.
 * - Lấy giá trị đã lưu từ localStorage.
 * - Gán giá trị vào input.
 * - Thêm sự kiện 'click' cho nút "Áp dụng".
 */
function initializeViewMode() {
  var input = document.getElementById('mxh-cards-per-row');
  var btn = document.getElementById('mxh-apply-view-mode-btn');
  var savedValue = localStorage.getItem('mxh_cards_per_row') || 12;

  if (input) {
    input.value = savedValue;
  }
  
  // Áp dụng giá trị đã lưu ngay khi tải trang.
  applyViewMode(savedValue);

  if (btn) {
    btn.addEventListener('click', function() {
      var currentValue = (input && input.value) ? input.value : 12;
      applyViewMode(currentValue);

      // Đóng modal sau khi áp dụng.
        var modalEl = document.getElementById('mxh-view-mode-modal');
      if (modalEl && typeof bootstrap !== 'undefined') {
        var modalInstance = bootstrap.Modal.getInstance(modalEl);
        if (modalInstance) {
          modalInstance.hide();
        }
      }

      // Hiển thị thông báo thành công.
      if (typeof showToast === 'function') {
        showToast('Đã áp dụng ' + currentValue + ' card mỗi hàng!', 'success');
      }
    });
  }
}

// ===== PERFORMANCE OPTIMIZATION UTILITIES =====
// Debounce function - prevents excessive API calls
function debounce(func, delay) {
    let timeoutId;
    return function (...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
}

// Throttle function - ensures function runs at most once per interval
function throttle(func, interval) {
    let lastCall = 0;
    return function (...args) {
        const now = Date.now();
        if (now - lastCall >= interval) {
            lastCall = now;
            func.apply(this, args);
        }
    };
}


// ===== REAL-TIME DATA LOADING WITH SMART UPDATES =====
// Load MXH data from API with optimized rendering
async function loadMXHData(forceRender = true) {
    try {
        // Check lastUpdateTime for delta polling
        const accountsUrl = lastUpdateTime 
            ? `/mxh/api/accounts?last_updated_at=${lastUpdateTime}` 
            : '/mxh/api/accounts';
            
        // Parallel loading for speed
        const [groupsResponse, accountsResponse] = await Promise.all([
            fetch('/mxh/api/groups'),
            fetch(accountsUrl) // Use the dynamic URL
        ]);

        if (groupsResponse.ok) {
            mxhGroups = await groupsResponse.json();
        }

        if (accountsResponse.ok) {
            const newAccountsDelta = await accountsResponse.json();
            
            let dataChanged = false;

            if (newAccountsDelta.length > 0) {
                dataChanged = true;
                // MERGE LOGIC: Replace/Update existing accounts with delta
                const accountMap = new Map(mxhAccounts.map(acc => [acc.id, acc]));
                
                newAccountsDelta.forEach(deltaAcc => {
                    accountMap.set(deltaAcc.id, deltaAcc);
                });
                
                mxhAccounts = Array.from(accountMap.values());
                
                // Update lastUpdateTime with the latest timestamp from the delta
                // Use the *current* time if the delta is empty or the updated_at field is missing
                const latestTimestamp = newAccountsDelta.reduce((latest, acc) => {
                    return (acc.updated_at && acc.updated_at > latest) ? acc.updated_at : latest;
                }, lastUpdateTime || new Date(0).toISOString());
                
                lastUpdateTime = latestTimestamp;
            }

            // Debug: log first account with notice
            const accWithNotice = mxhAccounts.find(a => a.notice && a.notice.enabled);
            if (accWithNotice) {
                // Debug disabled
            }

            // console.log('loadMXHData:', { forceRender, dataChanged, totalAccounts: mxhAccounts.length });

            if (forceRender || dataChanged) {
                renderGroupsNav(); // Render groups navigation first
                if (!isRendering) {
                    renderMXHAccounts();
                } else {
                    pendingUpdates = true;
                }
            }
        }
    } catch (error) {
        console.error('Error loading MXH data:', error);
        document.getElementById('mxh-accounts-container').innerHTML = `
        <div class="alert alert-danger">
            <i class="bi bi-exclamation-triangle me-2"></i>
            Lỗi kết nối API! Đang thử kết nối lại...
        </div>
    `;
    }
}

// ===== AUTO-REFRESH SYSTEM =====
function startAutoRefresh() {
    if (!MXH_CONFIG.ENABLE_AUTO_REFRESH) return;

    stopAutoRefresh(); // Clear any existing timer

    autoRefreshTimer = setInterval(async () => {
        await loadMXHData(false); // Don't force render, only if data changed
    }, MXH_CONFIG.AUTO_REFRESH_INTERVAL);

    // console.log('✅ MXH Auto-refresh enabled (every', MXH_CONFIG.AUTO_REFRESH_INTERVAL / 1000, 'seconds)');
}

function stopAutoRefresh() {
    if (autoRefreshTimer) {
        clearInterval(autoRefreshTimer);
        autoRefreshTimer = null;
    }
}

// Pause auto-refresh when user is interacting (context menu open, modal open, etc.)
let interactionPaused = false;
function pauseAutoRefresh() {
    interactionPaused = true;
}

function resumeAutoRefresh() {
    interactionPaused = false;
}

// Ensure platform group exists
async function ensurePlatformGroup(platform) {
    const existingGroup = mxhGroups.find(g => g.name.toLowerCase() === platform.toLowerCase());
    if (existingGroup) {
        return existingGroup.id;
    }

    try {
        const response = await fetch('/mxh/api/groups', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: platform.charAt(0).toUpperCase() + platform.slice(1),
                color: getPlatformColor(platform)
            })
        });

        if (response.ok) {
            const newGroup = await response.json();
            mxhGroups.push(newGroup);
            return newGroup.id;
        } else {
            throw new Error('Failed to create group');
        }
    } catch (error) {
        console.error('Error creating platform group:', error);
        throw error;
    }
}

// Get platform color
    function getPlatformColor(platform) {
        const colors = {
            'facebook': '#1877f2',
            'instagram': '#e4405f',
            'twitter': '#1da1f2',
            'zalo': '#0068ff',
            'wechat': '#07c160',
            'telegram': '#0088cc',
            'whatsapp': '#25d366'
        };
        return colors[platform] || '#6c757d';
    }

    function getPlatformIconClass(platform) {
        const p = String(platform || '').toLowerCase();
        return ({
            wechat: 'bi-wechat',
            telegram: 'bi-telegram',
            facebook: 'bi-facebook',
            instagram: 'bi-instagram',
        zalo: 'bi-chat-dots-fill',   // không có icon Zalo -> dùng chat
            twitter: 'bi-twitter',
            whatsapp: 'bi-whatsapp'
        }[p]) || 'bi-person-badge';
    }

    // Global flip card function
    window.flipCard = function (el, event) {
        if (event) { event.preventDefault(); event.stopPropagation(); }
        const wrap = el.closest('.mxh-card-container');
        if (wrap) wrap.classList.toggle('flipped');
    };

// Get next card number (per platform/group)
async function getNextCardNumber(groupId) {
    // Get all accounts in the same group (using group_id from joined data)
    const groupAccounts = mxhAccounts.filter(acc => acc.group_id === groupId);
    const numbers = groupAccounts.map(acc => parseInt(acc.card_name)).filter(n => !isNaN(n));

    if (numbers.length === 0) return 1;

    // Find first available number starting from 1
    for (let i = 1; i <= numbers.length + 1; i++) {
        if (!numbers.includes(i)) {
            return i;
        }
    }
    return Math.max(...numbers) + 1;
}

// Toggle group visibility
// ===== RENDER GROUP NAVIGATION WITH BADGES =====
    function renderGroupsNav() {
    const groupsNavContainer = document.getElementById('mxh-groups-nav');
    if (!groupsNavContainer) return;

    let html = '';

    // Get unique groups from accounts
    const uniqueGroupIds = [...new Set(mxhAccounts.map(acc => acc.group_id).filter(id => id))];

    uniqueGroupIds.forEach(groupId => {
        const group = mxhGroups.find(g => g.id == groupId);
        if (group) {
            // Calculate badge count for this group
            const badgeCount = calculateGroupBadge(groupId);
            const isActive = activeGroupId === groupId;

            html += `
                <button class="btn btn-sm ${isActive ? 'btn-primary' : 'btn-outline-primary'}" 
                        onclick="selectGroup(${groupId})">
                    <i class="bi ${group.icon} me-1"></i>
                    ${group.name}
                    <span class="badge bg-secondary ms-1">${badgeCount}</span>
                </button>
            `;
        }
    });

    groupsNavContainer.innerHTML = html;
}

// Calculate badge count for a group
function calculateGroupBadge(groupId) {
    return mxhAccounts.filter(acc => acc.group_id === groupId).length;
}

// Select group function
window.selectGroup = function(groupId) {
    activeGroupId = groupId;
    renderGroupsNav();
    renderMXHAccounts();
};

    /**
     * VIẾT LẠI HOÀN TOÀN: Render các card tài khoản.
     * Hàm này giờ sẽ tạo ra một cấu trúc HTML phẳng, các card là con trực tiếp của grid container.
     */
    function renderMXHAccounts() {
        if (isRendering) {
            pendingUpdates = true;
            return;
        }
        isRendering = true;

        const container = document.getElementById('mxh-accounts-container');
        const scrollY = window.scrollY; // Lưu vị trí cuộn

        // Lọc tài khoản theo group đang chọn
        const filteredAccounts = activeGroupId
            ? mxhAccounts.filter(acc => String(acc.group_id) === String(activeGroupId))
            : mxhAccounts;

        // Trường hợp không có tài khoản nào
    if (filteredAccounts.length === 0) {
            container.innerHTML = `
                <div class="card" style="grid-column: 1 / -1;">
                    <div class="card-body text-center text-muted">
                        <i class="bi bi-inbox" style="font-size: 3rem; opacity: 0.3;"></i>
                        <h5 class="mt-3">Không có tài khoản nào</h5>
                        <p>Nhấn "Thêm Tài Khoản" để bắt đầu.</p>
                    </div>
                </div>`;
            isRendering = false;
            return;
        }

        // Sắp xếp theo card_name dạng số
    filteredAccounts.sort((a, b) => {
            const numA = parseInt(a.card_name, 10);
            const numB = parseInt(b.card_name, 10);
            // Nếu không phải số thì đẩy xuống cuối
            if (isNaN(numA)) return 1;
            if (isNaN(numB)) return -1;
                return numA - numB;
        });

        // Tạo HTML cho tất cả các card
        const cardsHtml = filteredAccounts.map(account => {
            // (Toàn bộ logic tính toán `age`, `scan`, `notice`, `status`, `border` của bạn sẽ nằm ở đây)
            // VÍ DỤ LOGIC ĐƠN GIẢN ĐỂ DEMO:
            const now = new Date();
            const isDisabled = account.status === 'disabled';
            let ageDisplay = '';
            let scanDisplay = '';
            let noticeHtml = '';
            let borderClass = 'mxh-border-white';
            let extraClass = '';
            let ageInDays = 0;

        if (account.platform === 'wechat' && account.wechat_created_year) {
                const createDate = new Date(account.wechat_created_year, (account.wechat_created_month || 1) - 1, account.wechat_created_day || 1);
                ageInDays = Math.floor((now - createDate) / (1000 * 60 * 60 * 24));
                ageDisplay = `${ageInDays}d`;
            }

            const isDie = account.status === 'die';
            if(isDie) borderClass = 'mxh-border-red';
            
            // QUAN TRỌNG: KHÔNG còn thẻ <div class="col"> bao ngoài, chỉ có thẻ card
            return `
                <div class="card tool-card mxh-card ${borderClass} ${extraClass}" 
                     data-account-id="${account.id}"
                         oncontextmenu="handleCardContextMenu(event, ${account.id}, '${account.platform}'); return false;">
                    
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center">
                            <span class="fw-bold">${account.card_name}</span>
                            <span class="text-muted small">${ageDisplay}</span>
                                        </div>
                        <div class="text-center my-2">
                            <div class="text-truncate">${account.username || '...'}</div>
                            <div class="text-muted small">📞 ${account.phone || '...'}</div>
                            <div class="text-danger small">${isDie ? 'DIE' : ''}</div>
                                </div>
                            </div>
                        </div>
                `;
        }).join('');

        // Gán HTML vào container
        container.innerHTML = cardsHtml;

        // DEBUG: Log để kiểm tra
        console.log('🔍 MXH Debug Info:');
        console.log('- Container classes:', container.className);
        console.log('- CSS variable --cardsPerRow:', getComputedStyle(container).getPropertyValue('--cardsPerRow'));
        console.log('- Grid display:', getComputedStyle(container).display);
        console.log('- Grid template columns:', getComputedStyle(container).gridTemplateColumns);
        console.log('- Number of cards rendered:', filteredAccounts.length);

        // Khôi phục vị trí cuộn và các tác vụ sau khi render
        window.scrollTo(0, scrollY);
        // setupEditableFields(); // Bật lại nếu bạn có hàm này
        isRendering = false;

    if (pendingUpdates) {
        pendingUpdates = false;
            setTimeout(renderMXHAccounts, 50);
    }
}

// ===== UTILITY FUNCTIONS =====
function ensureNoticeParsed(notice) {
    let n = (typeof notice === 'string') ? (() => { try { return JSON.parse(notice) } catch { return {} } })() : (notice || {});
    if (n && n.start_at) n.start_at = normalizeISOForJS(n.start_at);
    return n;
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    };
    return String(text).replace(/[&<>"']/g, m => map[m]);
}

function normalizeISOForJS(iso) {
    if (!iso) return null;
    try {
        return new Date(iso).toISOString();
    } catch {
        return null;
    }
}

// ===== CONTEXT MENU FUNCTIONS =====
function showUnifiedContextMenu(event, accountId, platform) {
        event.preventDefault();
        event.stopPropagation();
        currentContextAccountId = accountId;
    pauseAutoRefresh();

        const contextMenu = document.getElementById('unified-context-menu');
    const account = mxhAccounts.find(acc => acc.id === accountId);

    if (!account) return;

    // Show/hide WeChat-specific items
    const wechatOnlyItems = contextMenu.querySelectorAll('.wechat-only');
    wechatOnlyItems.forEach(item => {
        item.style.display = platform === 'wechat' ? 'block' : 'none';
    });

    // Show/hide phone item if phone exists
    const copyPhoneItem = contextMenu.querySelector('#copy-phone-item');
    const phone = account.phone;
    if (copyPhoneItem) {
        copyPhoneItem.style.display = phone ? 'block' : 'none';
    }

    // Configure notice toggle
    const noticeToggle = contextMenu.querySelector('#unified-notice-toggle');
    if (noticeToggle) {
        const noticeObj = ensureNoticeParsed(account.notice);
        const hasNotice = !!(noticeObj && noticeObj.enabled);
        noticeToggle.dataset.action = hasNotice ? 'clear-notice' : 'set-notice';
        noticeToggle.innerHTML = hasNotice
            ? '<i class="bi bi-bell-slash-fill me-2"></i> Hủy thông báo'
            : '<i class="bi bi-bell-fill me-2"></i> Thông báo';
        }
        
        // Position and show menu
        contextMenu.style.display = 'block';
    contextMenu.style.left = event.pageX + 'px';
    contextMenu.style.top = event.pageY + 'px';
        
        setTimeout(() => {
        document.addEventListener('click', hideUnifiedContextMenu, { once: true });
    }, 100);
}

function hideUnifiedContextMenu() {
    document.getElementById('unified-context-menu').style.display = 'none';
    resumeAutoRefresh();
}

// Handle Card Context Menu - Use Unified Menu
window.handleCardContextMenu = function (event, accountId, platform) {
    event.preventDefault();
    event.stopPropagation();
    showUnifiedContextMenu(event, accountId, platform);
}

// ===== TOAST NOTIFICATIONS =====
    function showToast(message, type = 'info') {
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
    
    function createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
        return container;
    }
    
// ===== INLINE EDITING FUNCTIONS =====
async function quickUpdateField(accountId, field, value) {
    try {
        // INSTANT LOCAL UPDATE - Update UI immediately
        const accountIndex = mxhAccounts.findIndex(acc => acc.id === accountId);
        if (accountIndex !== -1) {
            mxhAccounts[accountIndex][field] = value;
        }

        // API call in background
        const response = await fetch(`/mxh/api/accounts/${accountId}/quick-update`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                field: field,
                value: value
            })
        });

        if (response.ok) {
            showToast(`Đã lưu ${field === 'username' ? 'tên' : 'SĐT'}!`, 'success');
            return true;
        } else {
            // Revert on error
            const error = await response.json();
            showToast(error.error || 'Lỗi khi cập nhật!', 'error');
            await loadMXHData(false); // Reload to get correct data
            return false;
        }
    } catch (error) {
        showToast('Lỗi kết nối!', 'error');
        await loadMXHData(false); // Reload to get correct data
        return false;
    }
}

// Setup contenteditable fields
function setupEditableFields() {
    const editableFields = document.querySelectorAll('.editable-field');

    editableFields.forEach(field => {
        // Store original value
        field.dataset.originalValue = field.textContent.trim();

        // Handle Enter key - save and blur
        field.addEventListener('keydown', async (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                field.blur();
            }
        });

        // Handle Escape key - cancel and restore
        field.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                e.preventDefault();
                field.textContent = field.dataset.originalValue;
                field.blur();
            }
        });

        // Handle blur - save changes
        field.addEventListener('blur', async (e) => {
            let newValue = e.target.textContent.trim();
            const accountId = parseInt(e.target.dataset.accountId);
            const fieldName = e.target.dataset.field;

            // Remove emoji prefix for phone
            if (fieldName === 'phone') {
                newValue = newValue.replace(/^📞\s*/, '').trim();
            }
            
            // Check if value is the same or if it's just the placeholder being edited
            const isNoChange = newValue === field.dataset.originalValue || 
                                (newValue === '' && field.dataset.originalValue === '.') || 
                                (newValue === 'Click để nhập' && field.dataset.originalValue === '');
                                
            if (isNoChange) {
                // Restore the visual placeholder if needed
                if (fieldName === 'phone') {
                    e.target.textContent = field.dataset.originalValue ? `📞 ${field.dataset.originalValue}` : '📞 Click để nhập';
                } else {
                    e.target.textContent = field.dataset.originalValue || 'Click để nhập';
                }
                return;
            }
            
            // If the value is a placeholder 'Click để nhập', treat as empty string '.'
            if (newValue === 'Click để nhập') {
                newValue = '.'; // Use '.' as the internal empty value marker
            }

            // Save to backend
            const success = await quickUpdateField(accountId, fieldName, newValue);

            if (success) {
                field.dataset.originalValue = newValue;
                // Update display with emoji if phone
                if (fieldName === 'phone') {
                    e.target.textContent = `📞 ${newValue}`;
                }
            } else {
                // Restore original value on failure
                if (fieldName === 'phone') {
                    e.target.textContent = field.dataset.originalValue ? `📞 ${field.dataset.originalValue}` : '📞 Click để nhập';
                } else {
                    e.target.textContent = field.dataset.originalValue || 'Click để nhập';
                }
            }
        });

        // Select all text on focus
        field.addEventListener('focus', (e) => {
            // Remove emoji prefix for easier editing
            if (e.target.dataset.field === 'phone') {
                const phone = e.target.textContent.replace(/^📞\s*/, '').replace('Click để nhập', '').trim();
                e.target.textContent = phone;
            } else if (e.target.textContent.trim() === 'Click để nhập') {
                e.target.textContent = '';
            }

            // Select all text
            setTimeout(() => {
                const range = document.createRange();
                range.selectNodeContents(e.target);
                const selection = window.getSelection();
                selection.removeAllRanges();
                selection.addRange(range);
            }, 0);
        });
    });
}
    
    // ===== EVENT LISTENERS =====
document.addEventListener('DOMContentLoaded', function() {
  // Khởi tạo Chế Độ Xem trước tiên.
  initializeViewMode();

  // Sau đó tải dữ liệu và các thành phần khác.
  if (typeof loadMXHData === 'function') {
    loadMXHData(true);
  }
  if (typeof startAutoRefresh === 'function') {
    startAutoRefresh();
  }

    // Unified context menu event listener
    document.getElementById('unified-context-menu').addEventListener('click', async (e) => {
        const menuItem = e.target.closest('.menu-item');
        if (!menuItem) return;
        
        e.preventDefault();
        e.stopPropagation();
        
        const action = menuItem.dataset.action;
        if (!action) return;

        switch (action) {
            case 'edit':
                showToast('Chức năng đang phát triển', 'info');
                break;
            case 'status-available':
                await updateAccountStatus('active');
                break;
            case 'status-die':
                await updateAccountStatus('die');
                break;
            case 'status-disabled':
                await updateAccountStatus('disabled');
                break;
            case 'rescue-success':
                await rescueAccountUnified('success');
                break;
            case 'rescue-failed':
                await rescueAccountUnified('failed');
                break;
            case 'mark-scanned':
                markAccountAsScanned(e);
                break;
            case 'set-notice':
                openNoticeModal(e);
                break;
            case 'clear-notice':
                clearNotice(e);
                break;
            case 'copy-phone':
                copyPhoneNumber(e);
                break;
            case 'copy-email':
                copyEmail(e);
                break;
            case 'reset-scan':
                resetScanCount(e);
                break;
            case 'change-number':
                changeCardNumber(e);
                break;
            case 'delete':
                showDeleteConfirm(e);
                break;
            case 'switch-account':
                const accountIndex = parseInt(menuItem.dataset.accountIndex);
                switchToAccount(accountIndex);
                break;
            case 'add-new-account':
                addNewAccount();
                break;
        }

        // Hide menu after action
        hideUnifiedContextMenu();
    });

    // Add Account Modal - Create new card with primary account
    document.getElementById('mxh-save-account-btn').addEventListener('click', async () => {
        const username = document.getElementById('mxh-username').value;
        const platform = document.getElementById('mxh-platform').value;
        const password = document.getElementById('mxh-password').value;
        const phone = document.getElementById('mxh-phone').value;
        const url = document.getElementById('mxh-url').value;
        const day = document.getElementById('mxh-day').value;
        const month = document.getElementById('mxh-month').value;
        const year = document.getElementById('mxh-year').value;
        
        if (!platform) {
            showToast('Vui lòng chọn nền tảng', 'warning');
            return;
        }
        
        try {
            // Ensure platform group exists
            const groupId = await ensurePlatformGroup(platform);
            
            // Get next card name for the specific group (THIS IS THE FIX)
            const nextCardName = String(await getNextCardNumber(groupId));
            
            // Auto-fill "." for empty fields (except URL)
            const autoFillValue = (value, isUrl = false) => {
                if (isUrl) return value || ""; // URL can be empty
                return value || "."; // Other fields get "." if empty
            };
            
            // Create card with primary account
            const response = await fetch('/mxh/api/cards', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
          card_name: nextCardName,
                    group_id: groupId,
          platform: platform,
                    username: autoFillValue(username),
                    phone: autoFillValue(phone),
                    url: autoFillValue(url, true), // URL can be empty
                    login_username: autoFillValue(username),
                    login_password: autoFillValue(password),
          wechat_created_day: day,
          wechat_created_month: month,
          wechat_created_year: year
                })
            });
            
            if (response.ok) {
                showToast('Tạo tài khoản thành công', 'success');
        await loadMXHData(true);
                bootstrap.Modal.getInstance(document.getElementById('mxh-addAccountModal')).hide();
                document.getElementById('mxh-add-card-form').reset();
      } else {
                const error = await response.json();
                showToast(error.error || 'Lỗi tạo tài khoản', 'error');
            }
        } catch (error) {
            console.error('Error creating account:', error);
            showToast('Lỗi kết nối máy chủ', 'error');
        }
    });
    
    // Auto-fill date when opening add account modal
    document.getElementById('mxh-addAccountModal').addEventListener('shown.bs.modal', function () {
        const today = new Date();
        const day = today.getDate();
        const month = today.getMonth() + 1;
        const year = today.getFullYear();
        
        document.getElementById('mxh-day').value = day;
        document.getElementById('mxh-month').value = month;
        document.getElementById('mxh-year').value = year;
    });
    
    // Hide all context menus on regular click
    document.addEventListener('click', function (event) {
        if (!event.target.closest('.custom-context-menu')) {
            document.querySelectorAll('.custom-context-menu').forEach(menu => {
                menu.style.display = 'none';
            });
        }
    });
});

// ===== PLACEHOLDER FUNCTIONS (TO BE IMPLEMENTED) =====
async function updateAccountStatus(status) {
    showToast('Chức năng đang phát triển', 'info');
}

async function rescueAccountUnified(result) {
    showToast('Chức năng đang phát triển', 'info');
}

function markAccountAsScanned(e) {
    showToast('Chức năng đang phát triển', 'info');
}

function openNoticeModal(e) {
    showToast('Chức năng đang phát triển', 'info');
}

function clearNotice(e) {
    showToast('Chức năng đang phát triển', 'info');
}

function copyPhoneNumber(e) {
    showToast('Chức năng đang phát triển', 'info');
}

function copyEmail(e) {
    showToast('Chức năng đang phát triển', 'info');
}

function resetScanCount(e) {
    showToast('Chức năng đang phát triển', 'info');
}

function changeCardNumber(e) {
    showToast('Chức năng đang phát triển', 'info');
}

function showDeleteConfirm(e) {
    showToast('Chức năng đang phát triển', 'info');
}

function switchToAccount(accountIndex) {
    showToast('Chức năng đang phát triển', 'info');
}

function addNewAccount() {
    showToast('Chức năng đang phát triển', 'info');
}