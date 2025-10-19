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
function initializeViewMode() {
    // Initialize cards per row setting
    const savedCardsPerRow = localStorage.getItem('mxh_cards_per_row') || 6; // Default to 6 instead of 12
    const cardsPerRowInput = document.getElementById('mxh-cards-per-row');
    if (cardsPerRowInput) {
        cardsPerRowInput.value = savedCardsPerRow;
    }
    
    // Apply saved setting
    applyViewMode(savedCardsPerRow);
    
    // Add event listener for apply button
    const applyBtn = document.getElementById('mxh-apply-view-mode-btn');
    if (applyBtn) {
        applyBtn.addEventListener('click', () => {
            const cardsPerRow = document.getElementById('mxh-cards-per-row').value;
            localStorage.setItem('mxh_cards_per_row', cardsPerRow);
            applyViewMode(cardsPerRow);
            showToast(`Đã áp dụng ${cardsPerRow} cards/hàng!`, 'success');
            bootstrap.Modal.getInstance(document.getElementById('mxh-view-mode-modal')).hide();
        });
    }
}

function applyViewMode(cardsPerRow) {
    // Set CSS variable on the root element
    document.documentElement.style.setProperty('--cardsPerRow', cardsPerRow);
    
    // Also apply directly to the grid container for immediate effect
    const grid = document.getElementById('mxh-cards-grid');
    if (grid) {
        grid.style.setProperty('--cardsPerRow', cardsPerRow);
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

    // ===== COMPLEX RENDERING LOGIC (ADAPTED FROM OLD FILE) =====
    function renderMXHAccounts() {
        if (isRendering) {
            pendingUpdates = true;
            return;
        }

        isRendering = true;
        const container = document.getElementById('mxh-accounts-container');

        // 💾 SAVE SCROLL POSITION BEFORE RENDER
        const scrollY = window.scrollY || window.pageYOffset;
        const scrollX = window.scrollX || window.pageXOffset;

    if (mxhAccounts.length === 0) {
            container.innerHTML = `
            <div class="card">
                <div class="card-body text-center text-muted">
                    <i class="bi bi-share-fill" style="font-size: 3rem; opacity: 0.3;"></i>
                    <h5 class="mt-3">Chưa có tài khoản MXH nào</h5>
                    <p>Nhấn "Thêm Tài Khoản MXH" để bắt đầu.</p>
                </div>
            </div>
        `;
            isRendering = false;
            return;
        }

    // Filter accounts based on active group
    const filteredAccounts = activeGroupId === null
        ? mxhAccounts 
        : mxhAccounts.filter(acc => acc.group_id === activeGroupId);

    if (filteredAccounts.length === 0) {
            container.innerHTML = `
                <div class="card">
                    <div class="card-body text-center text-muted">
                        <i class="bi bi-share-fill" style="font-size: 3rem; opacity: 0.3;"></i>
                        <h5 class="mt-3">Chưa có tài khoản MXH nào</h5>
                        <p>Nhấn "Thêm Tài Khoản MXH" để bắt đầu.</p>
                    </div>
                </div>
            `;
            isRendering = false;
            return;
        }

    // Sort accounts by card_name (numeric if possible)
    filteredAccounts.sort((a, b) => {
            const numA = parseInt(a.card_name, 10);
            const numB = parseInt(b.card_name, 10);
            if (!isNaN(numA) && !isNaN(numB)) {
                return numA - numB;
            }
            return a.card_name.localeCompare(b.card_name);
        });

        // Use DocumentFragment for better performance
        const fragment = document.createDocumentFragment();
        const tempDiv = document.createElement('div');
        let html = '';

    // Group accounts by group_id
    const accountsByGroup = {};
    filteredAccounts.forEach(account => {
        const groupId = account.group_id || 'no-group';
        if (!accountsByGroup[groupId]) {
            accountsByGroup[groupId] = [];
        }
        accountsByGroup[groupId].push(account);
    });

    Object.keys(accountsByGroup).forEach(groupId => {
        const accounts = accountsByGroup[groupId];
            const group = mxhGroups.find(g => g.id == groupId);

            if (group) {
                const cardsContainerId = `cards-${groupId}`;

            // Render group header with toggle
                html += `
                <div class="mb-4">
                    <div class="d-flex align-items-center justify-content-between mb-2">
                        <h6 class="mb-0">
                            <i class="bi ${group.icon} me-2" style="color: ${group.color};"></i>
                            ${group.name}
                            <span class="badge bg-secondary ms-2">${accounts.length}</span>
                        </h6>
                        <button class="btn btn-sm btn-outline-secondary" id="toggle-${groupId}" 
                                onclick="toggleGroupVisibility(${groupId})">
                            <i class="bi bi-eye-fill"></i>
                        </button>
                    </div>
                    <div class="row g-2" id="${cardsContainerId}">
                `;

            accounts.forEach(account => {
                // Calculate age for WeChat accounts
        let accountAgeDisplay = '';
        let ageColor = '#fff';
        let scanCountdown = '';

        if (account.platform === 'wechat' && account.wechat_created_year) {
            const createdDate = new Date(account.wechat_created_year, account.wechat_created_month - 1, account.wechat_created_day);
                    const diffDays = Math.ceil((new Date() - createdDate) / (1000 * 60 * 60 * 24));

            if (diffDays >= 365) {
                const years = Math.floor(diffDays / 365);
                const months = Math.floor((diffDays % 365) / 30);
                accountAgeDisplay = `${years}năm ${months}th`;
                ageColor = '#07c160';
            } else if (diffDays >= 30) {
                const months = Math.floor(diffDays / 30);
                accountAgeDisplay = `${months}th ${diffDays % 30}d`;
            } else {
                accountAgeDisplay = `${diffDays}d`;
            }

            // Calculate scan countdown with QR icon
            const currentScanCount = account.wechat_scan_count || 0;
            const maxScans = 3;
            const remainingScans = Math.max(0, maxScans - currentScanCount);
            if (remainingScans > 0) {
                scanCountdown = `<i class="bi bi-qr-code me-1"></i>${remainingScans}`;
            }
        }

        // Notice handling
        const notice = ensureNoticeParsed(account.notice);
        const hasNotice = notice && notice.title;
                const isNoticeExpired = hasNotice && notice.end_at && new Date(notice.end_at) < new Date();
        const noticeClass = isNoticeExpired ? 'expired' : '';
        const noticeText = hasNotice ? escapeHtml(notice.title) : '';

        // Status and border classes
        let statusClass = 'account-status-available';
        let borderClass = '';
        let statusIcon = '';

        if (account.status === 'die') {
            statusClass = 'account-status-die';
            borderClass = 'mxh-border-red';
            statusIcon = '<i class="bi bi-x-circle-fill status-icon"></i>';
        } else if (account.status === 'disabled') {
            statusClass = 'account-status-disabled';
            borderClass = 'mxh-border-orange';
            statusIcon = '<i class="bi bi-slash-circle status-icon"></i>';
        } else {
            // Available status with age-based colors
            if (account.platform === 'wechat' && accountAgeDisplay) {
                        if (accountAgeDisplay.includes('năm')) {
                    borderClass = 'mxh-border-green';
                } else if (accountAgeDisplay.includes('th') && parseInt(accountAgeDisplay) >= 13) {
                    borderClass = 'mxh-border-green';
                } else {
                    borderClass = 'mxh-border-white';
                }
            } else {
                borderClass = 'mxh-border-white';
            }
        }

                html += `
                    <div class="col" style="padding: 2px;" data-account-id="${account.id}">
                        <div class="card tool-card mxh-card ${borderClass} ${noticeClass}" 
                             oncontextmenu="handleCardContextMenu(event, ${account.id}, '${account.platform}'); return false;">
                    <div class="card-body">
                                <div class="d-flex align-items-center justify-content-between mb-1">
                                    <div class="d-flex align-items-center gap-1">
                                        <h6 class="card-title mb-0 card-number" style="font-size: 1.26rem; font-weight: 600;">${account.card_name}</h6>
                                        <i class="bi ${getPlatformIconClass(account.platform)}" title="${account.platform}" style="font-size: 0.9rem; color: ${getPlatformColor(account.platform)};"></i>
                                        </div>
                                    <div class="d-flex align-items-center gap-1">
                                        ${accountAgeDisplay ? `<small style="color: ${ageColor}; font-size: 0.7rem; font-weight: 500;">${accountAgeDisplay}</small>` : ''}
                                        </div>
                                    </div>
                                    
                                <div class="text-center mb-0">
                                    <small 
                                        class="${statusClass} editable-field" 
                                        contenteditable="true" 
                                        data-account-id="${account.id}" 
                                        data-field="username" 
                                        data-is-secondary="false"
                                        style="font-size: 0.84rem; cursor: text; padding: 2px 4px; border-radius: 4px; transition: background-color 0.2s; display: inline-block;"
                                        onmouseenter="this.style.backgroundColor='rgba(255,255,255,0.1)'"
                                        onmouseleave="this.style.backgroundColor='transparent'"
                                        onclick="event.stopPropagation()"
                                    >${account.username || 'Click để nhập'}${statusIcon}</small>
                                    <small 
                                        class="text-muted editable-field" 
                                        contenteditable="true" 
                                        data-account-id="${account.id}" 
                                        data-field="phone" 
                                        data-is-secondary="false"
                                        style="font-size: 0.84rem; cursor: text; padding: 2px 4px; border-radius: 4px; transition: background-color 0.2s; display: block; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;"
                                        onmouseenter="this.style.backgroundColor='rgba(255,255,255,0.1)'"
                                        onmouseleave="this.style.backgroundColor='transparent'"
                                        onclick="event.stopPropagation()"
                                    >📞 ${account.phone || 'Click để nhập'}</small>
                                    </div>
                                    
                                ${account.platform === 'wechat' ? `
                                    <div class="mt-auto">
                                        ${account.status === 'disabled' ?
                                            `<div class="d-flex align-items-center justify-content-between">
                                                <small class="text-danger" style="font-size: 0.77rem;">Ngày: ${account.die_date ? Math.ceil((new Date() - new Date(account.die_date)) / (1000 * 60 * 60 * 24)) : 0}</small>
                                                <small style="font-size: 0.77rem;">Lần cứu: <span class="text-danger">${account.rescue_count || 0}</span>-<span class="text-success">${account.rescue_success_count || 0}</span></small>
                                            </div>` :
                                            `<div class="text-center mt-1">
                                                ${scanCountdown ? `<small style="font-size: 0.7rem;">${scanCountdown}</small>` : ''}
                                            </div>`
                                        }
                                    </div>
                        ` : ''}
                                    
                                    ${hasNotice ? `
                                    <div class="notice-line ${noticeClass}">
                                        <i class="bi bi-bell-fill me-1"></i>${noticeText}
                        </div>
                        ` : ''}
                                </div>
                            </div>
                        </div>
                `;
            });

            html += `
                </div>
            </div>
        `;
    }
    });

    tempDiv.innerHTML = html;
    container.innerHTML = '';
    container.appendChild(tempDiv);

    // Restore scroll position
    window.scrollTo(scrollX, scrollY);

    // Setup inline editing after render
    setupEditableFields();

    isRendering = false;
    if (pendingUpdates) {
        pendingUpdates = false;
        renderMXHAccounts();
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
    // Initialize view mode
    initializeViewMode();
    
    // Initialize data loading
    loadMXHData(true);
    
    // Start auto-refresh
    startAutoRefresh();

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