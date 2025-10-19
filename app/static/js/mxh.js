// ===== MXH REAL-TIME CONFIGURATION =====
const MXH_CONFIG = {
    AUTO_REFRESH_INTERVAL: 15000,
    DEBOUNCE_DELAY: 500,
    RENDER_BATCH_SIZE: 50,
    ENABLE_AUTO_REFRESH: true
};

// ===== GLOBAL STATE MANAGEMENT =====
let mxhGroups = [];
let mxhAccounts = [];
let currentContextAccountId = null;
let autoRefreshTimer = null;
let isRendering = false;
let pendingUpdates = false;
let activeGroupId = null;
let lastUpdateTime = null;

// ===== WINDOW.MXH: State Manager cho Flip Cards =====
window.MXH = window.MXH || {};
// Map<cardId, {accounts: [], activeId: null, isFlipped: false, frontAccount: null, backAccount: null}>
MXH.cards = MXH.cards || new Map();

// ===== VIEW MODE LOGIC (FLEXBOX + CSS VARIABLE) =====
function applyViewMode(value) {
    const n = Math.max(1, parseInt(value, 10) || 12);
    localStorage.setItem('mxh_cards_per_row', n);
    document.documentElement.style.setProperty('--cardsPerRow', n);
    const c = document.getElementById('mxh-accounts-container');
    if (c) c.style.setProperty('--cardsPerRow', n);
}

function initializeViewMode() {
    const input = document.getElementById('mxh-cards-per-row');
    const btn = document.getElementById('mxh-apply-view-mode-btn');
    const savedValue = localStorage.getItem('mxh_cards_per_row') || 12;

    if (input) {
        input.value = savedValue;
    }

    if (btn) {
        btn.addEventListener('click', function() {
            const currentValue = input ? input.value : 12;
            applyViewMode(currentValue);

            const modalEl = document.getElementById('mxh-view-mode-modal');
            if (modalEl && typeof bootstrap !== 'undefined') {
                const modalInstance = bootstrap.Modal.getInstance(modalEl);
                if (modalInstance) modalInstance.hide();
            }
            if (typeof showToast === 'function') {
                showToast(`Đã áp dụng ${currentValue} card mỗi hàng!`, 'success');
            }
        });
    }
}

// ===== PERFORMANCE OPTIMIZATION UTILITIES =====
function debounce(func, delay) {
    let timeoutId;
    return function (...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
}

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
async function loadMXHData(forceRender = true) {
    try {
        const accountsUrl = lastUpdateTime
            ? `/mxh/api/accounts?last_updated_at=${lastUpdateTime}`
            : '/mxh/api/accounts';

        const [groupsResponse, accountsResponse] = await Promise.all([
            fetch('/mxh/api/groups'),
            fetch(accountsUrl)
        ]);

        if (groupsResponse.ok) {
            mxhGroups = await groupsResponse.json();
        }

        if (accountsResponse.ok) {
            const newAccountsDelta = await accountsResponse.json();

            let dataChanged = false;

            if (newAccountsDelta.length > 0) {
                dataChanged = true;
                const accountMap = new Map(mxhAccounts.map(acc => [acc.id, acc]));

                newAccountsDelta.forEach(deltaAcc => {
                    accountMap.set(deltaAcc.id, deltaAcc);
                });

                mxhAccounts = Array.from(accountMap.values());

                const latestTimestamp = newAccountsDelta.reduce((latest, acc) => {
                    return (acc.updated_at && acc.updated_at > latest) ? acc.updated_at : latest;
                }, lastUpdateTime || new Date(0).toISOString());

                lastUpdateTime = latestTimestamp;
            }

            if (forceRender || dataChanged) {
                renderGroupsNav();
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

    stopAutoRefresh();

    autoRefreshTimer = setInterval(async () => {
        await loadMXHData(false);
    }, MXH_CONFIG.AUTO_REFRESH_INTERVAL);
}

function stopAutoRefresh() {
    if (autoRefreshTimer) {
        clearInterval(autoRefreshTimer);
        autoRefreshTimer = null;
    }
}

let interactionPaused = false;
function pauseAutoRefresh() {
    interactionPaused = true;
}

function resumeAutoRefresh() {
    interactionPaused = false;
}

// ===== PLATFORM UTILITIES =====
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
        zalo: 'bi-chat-dots-fill',
        twitter: 'bi-twitter',
        whatsapp: 'bi-whatsapp'
    }[p]) || 'bi-person-badge';
}

async function getNextCardNumber(groupId) {
    const groupAccounts = mxhAccounts.filter(acc => acc.group_id === groupId);
    const numbers = groupAccounts.map(acc => parseInt(acc.card_name)).filter(n => !isNaN(n));

    if (numbers.length === 0) return 1;

    for (let i = 1; i <= numbers.length + 1; i++) {
        if (!numbers.includes(i)) {
            return i;
        }
    }
    return Math.max(...numbers) + 1;
}

// ===== RENDER GROUP NAVIGATION WITH BADGES =====
function renderGroupsNav() {
    const groupsNavContainer = document.getElementById('mxh-groups-nav');
    if (!groupsNavContainer) return;

    let html = '';

    const uniqueGroupIds = [...new Set(mxhAccounts.map(acc => acc.group_id).filter(id => id))];

    uniqueGroupIds.forEach(groupId => {
        const group = mxhGroups.find(g => g.id == groupId);
        if (group) {
            const badgeCount = calculateGroupBadge(groupId);
            const isActive = activeGroupId === groupId;

            const platformColor = getPlatformColor(group.name.toLowerCase());
            const activeStyle = isActive ? `background-color: ${platformColor}; border-color: ${platformColor}; color: white;` : `color: ${platformColor}; border-color: ${platformColor};`;
            
            html += `
                <button class="btn btn-sm"
                        style="${activeStyle}"
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

function calculateGroupBadge(groupId) {
    return mxhAccounts.filter(acc => acc.group_id === groupId).length;
}

window.selectGroup = function(groupId) {
    activeGroupId = groupId;
    renderGroupsNav();
    renderMXHAccounts();
};

// ===== CORE STATE MANAGEMENT FUNCTIONS =====

/**
 * Lấy hoặc khởi tạo state cho một card.
 * @param {number} cardId - ID của card
 * @returns {object} State object của card
 */
function _getCardState(cardId) {
    if (!MXH.cards.has(cardId)) {
        MXH.cards.set(cardId, {
            accounts: [],
            activeId: null,
            isFlipped: false,
            frontAccount: null,
            backAccount: null
        });
    }
    return MXH.cards.get(cardId);
}

/**
 * Cập nhật state của card với danh sách tài khoản mới.
 * @param {number} cardId - ID của card
 * @param {array} accounts - Danh sách tài khoản thuộc card này
 */
function _updateCardState(cardId, accounts) {
    const state = _getCardState(cardId);
    state.accounts = accounts;
    
    // Nếu chưa có activeId, set mặc định là tài khoản chính
    if (!state.activeId && accounts.length > 0) {
        const primary = accounts.find(a => a.is_primary) || accounts[0];
        state.activeId = primary.id;
        state.frontAccount = primary.id;
    }
}

/**
 * VIẾT LẠI: Render các card tài khoản, gom nhóm các tài khoản theo card_id.
 * Mỗi card_id chỉ render MỘT div.mxh-item với cấu trúc flip 3D.
 */
function renderMXHAccounts() {
    if (isRendering) {
        pendingUpdates = true;
        return;
    }
    isRendering = true;

    const container = document.getElementById('mxh-accounts-container');
    const scrollY = window.scrollY;

    // --- LOGIC GOM NHÓM TÀI KHOẢN THEO CARD_ID ---
    const cardsMap = new Map();
    const filteredAccounts = activeGroupId
        ? mxhAccounts.filter(acc => String(acc.group_id) === String(activeGroupId))
        : mxhAccounts;

    for (const account of filteredAccounts) {
        const cardId = account.card_id;
        if (!cardsMap.has(cardId)) {
            cardsMap.set(cardId, {
                card_info: {
                    id: account.card_id,
                    card_name: account.card_name,
                    group_id: account.group_id,
                    platform: account.platform,
                },
                accounts: []
            });
        }
        cardsMap.get(cardId).accounts.push(account);
    }
    // --- KẾT THÚC LOGIC GOM NHÓM ---

    // Cập nhật state cho tất cả các cards
    cardsMap.forEach((cardData, cardId) => {
        _updateCardState(cardId, cardData.accounts);
    });

    const sortedCards = Array.from(cardsMap.values()).sort((a, b) => {
        const numA = parseInt(a.card_info.card_name) || 0;
        const numB = parseInt(b.card_info.card_name) || 0;
        return numA - numB;
    });

    if (sortedCards.length === 0) {
        container.innerHTML = `<div class="col-12"><div class="card"><div class="card-body text-center text-muted"><i class="bi bi-inbox fs-1 opacity-25"></i><h5 class="mt-3">Không có tài khoản nào</h5></div></div></div>`;
        isRendering = false;
        return;
    }

    const cardsHtml = sortedCards.map(cardData => {
        const cardId = cardData.card_info.id;
        const state = _getCardState(cardId);
        
        // Xác định tài khoản nào hiển thị ở mặt trước và mặt sau
        const primaryAccount = cardData.accounts.find(a => a.is_primary) || cardData.accounts[0];
        if (!primaryAccount) return '';

        // Lấy tài khoản đang active từ state
        const activeAccount = cardData.accounts.find(a => a.id === state.activeId) || primaryAccount;
        
        // Xác định tài khoản cho mặt trước và mặt sau dựa trên state
        let frontAccount, backAccount;
        if (state.isFlipped) {
            // Nếu đang lật, mặt sau (hiện tại đang nhìn thấy) hiển thị account active
            backAccount = activeAccount;
            frontAccount = state.frontAccount ? cardData.accounts.find(a => a.id === state.frontAccount) : primaryAccount;
        } else {
            // Nếu không lật, mặt trước hiển thị account active
            frontAccount = activeAccount;
            backAccount = state.backAccount ? cardData.accounts.find(a => a.id === state.backAccount) : null;
        }

        // Render card với cấu trúc lật
        const flippedClass = state.isFlipped ? 'is-flipped' : '';
        
        return `
            <div class="col mxh-item" style="flex:0 0 calc(100% / var(--cardsPerRow, 12));max-width:calc(100% / var(--cardsPerRow, 12));padding:4px" data-card-id="${cardId}">
                <div class="card tool-card mxh-card ${flippedClass}" id="card-${cardId}" oncontextmenu="handleCardContextMenu(event, ${activeAccount.id}, '${activeAccount.platform}'); return false;">
                    <div class="card-body">
                        <div class="mxh-card-inner">
                            <div class="mxh-card-face face-a">
                                ${renderAccountFace(frontAccount, cardData.accounts)}
                            </div>
                            <div class="mxh-card-face face-b">
                                ${renderAccountFace(backAccount, cardData.accounts)}
                            </div>
                        </div>
                    </div>
                </div>
            </div>`;
    }).join('');

    container.innerHTML = cardsHtml;
    window.scrollTo(0, scrollY);
    
    // Áp dụng lại trạng thái viền cho từng card sau khi render
    sortedCards.forEach(cardData => {
        const cardId = cardData.card_info.id;
        const state = _getCardState(cardId);
        
        // Dùng account đang active, không phải primary
        const activeAccount = cardData.accounts.find(a => a.id === state.activeId) 
                           || cardData.accounts.find(a => a.is_primary) 
                           || cardData.accounts[0];
        
        const cell = document.querySelector(`.mxh-item[data-card-id="${cardId}"]`);
        if (cell && activeAccount) {
            paintRing(cell, activeAccount);
        }
    });
    
    setupEditableFields();
    isRendering = false;

    if (pendingUpdates) {
        pendingUpdates = false;
        setTimeout(renderMXHAccounts, 50);
    }
}

/**
 * Hàm phụ trợ để render nội dung cho MỘT mặt của card (trước hoặc sau).
 * @param {object | null} account - Đối tượng tài khoản để render.
 * @param {array} allAccountsOnCard - Tất cả tài khoản thuộc card này (để tính toán nếu cần)
 * @returns {string} - Chuỗi HTML cho nội dung của một mặt card.
 */
function renderAccountFace(account, allAccountsOnCard = []) {
    if (!account) return '<div class="text-center p-3 text-muted small">...</div>';

    const now = new Date();
    let accountAgeDisplay = '';
    let ageColor = '#6c757d';

    // Tính tuổi tài khoản (nếu là WeChat)
    if (account.platform === 'wechat' && account.wechat_created_year) {
        const createdDate = new Date(
            account.wechat_created_year,
            (account.wechat_created_month || 1) - 1,
            account.wechat_created_day || 1
        );
        const diffDays = Math.ceil((now - createdDate) / (1000 * 60 * 60 * 24));
        if (diffDays >= 365) {
            accountAgeDisplay = `${Math.floor(diffDays / 365)}Y`;
            ageColor = '#2fe56a';
        } else {
            accountAgeDisplay = `${diffDays}D`;
        }
    }
    
    // Xác định trạng thái Die/Disabled
    const isDisabled = String(account.status || '').toLowerCase() === 'disabled';
    const isDie = ['die', 'banned', 'blocked'].includes(String(account.status || '').toLowerCase()) || !!account.die_date;
    
    let statusClass = 'account-status-available';
    let statusIcon = '';
    if (isDie) {
        statusClass = 'account-status-die';
        statusIcon = '<i class="bi bi-x-circle-fill status-icon"></i>';
    } else if (isDisabled) {
        statusClass = 'account-status-disabled';
        statusIcon = '<i class="bi bi-slash-circle status-icon"></i>';
    }

    // Xử lý scan countdown (cho WeChat)
    let scanCountdown = '';
    if (account.platform === 'wechat' && !isDisabled && !isDie) {
        const scanCount = account.wechat_scan_count || 0;
        const lastScanDate = account.wechat_last_scan_date ? new Date(account.wechat_last_scan_date) : null;
        if (lastScanDate) {
            const nextScanDate = new Date(lastScanDate.getTime() + 7 * 24 * 60 * 60 * 1000); // +7 days
            const remainMs = nextScanDate - now;
            const remainDays = Math.ceil(remainMs / (1000 * 60 * 60 * 24));
            if (remainDays > 0) {
                scanCountdown = `<span style="color: #07c160;">Q:${scanCount}</span> | ${remainDays}d`;
            } else {
                scanCountdown = `<span style="color: #ff4d4f;">Q:${scanCount}</span> | Cần quét`;
            }
        } else {
            scanCountdown = `<span style="color: #ffa500;">Q:${scanCount}</span> | Chưa quét`;
        }
    }

    // Xử lý thông báo (notice)
    const noticeObj = ensureNoticeParsed(account.notice);
    let noticeHtml = '', tipHtml = '';
    if (noticeObj.enabled && noticeObj.start_at && noticeObj.days > 0) {
        const start = new Date(noticeObj.start_at);
        const end = new Date(start.getTime() + noticeObj.days * 86400000);
        const remainMs = end - now;
        const remainDays = Math.ceil(remainMs / 86400000);
        if (remainMs > 0) {
            noticeHtml = `<div class="notice-line">${escapeHtml(noticeObj.title)}: ${remainDays}d</div>`;
        } else {
            noticeHtml = `<div class="notice-line expired">${escapeHtml(noticeObj.title)}: hết hạn</div>`;
        }
        tipHtml = `<div class="notice-tooltip"><div class="notice-tooltip-title">${escapeHtml(noticeObj.title)}</div><div class="notice-tooltip-note">${escapeHtml(noticeObj.note || '')}</div></div>`;
    }

    return `
        <div class="d-flex align-items-center justify-content-between mb-1">
            <div class="d-flex align-items-center gap-1">
                <h6 class="card-title mb-0 card-number" style="font-size: 1.26rem; font-weight: 600;">${account.card_name}</h6>
                <i class="bi ${getPlatformIconClass(account.platform)}" style="font-size: 0.9rem; color: ${getPlatformColor(account.platform)};"></i>
                ${allAccountsOnCard.length > 1 ? `<span class="badge bg-secondary" style="font-size: 0.6rem;">${allAccountsOnCard.findIndex(a => a.id === account.id) + 1}/${allAccountsOnCard.length}</span>` : ''}
            </div>
            ${accountAgeDisplay ? `<small style="color: ${ageColor}; font-size: 0.7rem; font-weight: 500;">${accountAgeDisplay}</small>` : ''}
        </div>
        <div class="text-center mb-0">
            <small class="${statusClass} editable-field" contenteditable="true" data-account-id="${account.id}" data-field="username" style="font-size: 0.84rem; display: inline-block;">${account.username || '...'}${statusIcon}</small>
            <small class="text-muted editable-field" contenteditable="true" data-account-id="${account.id}" data-field="phone" style="font-size: 0.84rem; display: block;">📞 ${account.phone || '...'}</small>
        </div>
        ${account.platform === 'wechat' ? `
            <div class="mt-auto">
                ${isDisabled || isDie ?
                    `<div class="d-flex align-items-center justify-content-between">
                        <small class="text-danger" style="font-size: 0.77rem;">Ngày: ${account.die_date ? Math.ceil((now - new Date(account.die_date)) / (1000 * 60 * 60 * 24)) : 0}</small>
                        <small style="font-size: 0.77rem;">Lượt cứu: <span class="text-danger">${account.rescue_count || 0}</span>-<span class="text-success">${account.rescue_success_count || 0}</span></small>
                    </div>` :
                    `<div class="text-center mt-1">
                        ${scanCountdown ? `<small style="font-size: 0.7rem;">${scanCountdown}</small>` : ''}
                    </div>`
                }
            </div>
        ` : ''}
        ${noticeHtml}
        ${tipHtml}
    `;
}

// ===== FLIP CARD CORE LOGIC =====

/**
 * Hàm cốt lõi để lật card sang tài khoản khác.
 * @param {number} cardId - ID của card cần lật
 * @param {object} account - Tài khoản mới cần hiển thị
 */
function _flipTo(cardId, account) {
    if (!account) return;

    const state = _getCardState(cardId);
    const cardEl = document.getElementById(`card-${cardId}`);
    if (!cardEl) return;

    // Lưu lại account cũ TRƯỚC KHI cập nhật
    const oldActiveId = state.activeId;

    // Tìm mặt đang ẩn (để render thông tin mới vào đó)
    const hiddenFace = state.isFlipped ? 'a' : 'b';
    
    // Render thông tin account mới vào mặt ẩn
    const hiddenFaceEl = cardEl.querySelector(`.mxh-card-face.face-${hiddenFace}`);
    if (hiddenFaceEl) {
        hiddenFaceEl.innerHTML = renderAccountFace(account, state.accounts);
    }

    // Toggle class is-flipped để kích hoạt animation CSS
    cardEl.classList.toggle('is-flipped');

    // Cập nhật state
    state.isFlipped = !state.isFlipped;
    state.activeId = account.id;
    
    if (state.isFlipped) {
        // Sau khi lật, mặt B đang hiển thị
        state.backAccount = account.id;
        state.frontAccount = oldActiveId; // Lưu lại account cũ
    } else {
        // Sau khi lật, mặt A đang hiển thị
        state.frontAccount = account.id;
        state.backAccount = oldActiveId; // Lưu lại account cũ
    }

    // Re-setup editable fields cho mặt mới
    setupEditableFields();
}

// ===== MXH PUBLIC API =====

/**
 * Thêm tài khoản phụ vào một card.
 * Sau khi thành công, card sẽ tự động lật ra mặt sau để hiển thị tài khoản mới.
 * @param {number} cardId - ID của card
 */
MXH.addSubAccount = async (cardId) => {
    const state = _getCardState(cardId);
    
    try {
        // Gọi API để tạo tài khoản phụ
        const response = await fetch(`/mxh/api/cards/${cardId}/accounts`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                account_name: "Tài khoản phụ",
                platform: "wechat",
                username: ".",
                phone: "."
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || error.error || `HTTP ${response.status}`);
        }
        
        const newAccount = await response.json();
        
        // Cập nhật mxhAccounts global
        mxhAccounts.push(newAccount);
        
        // Cập nhật state của card
        state.accounts.push(newAccount);
        
        // Lật card sang tài khoản mới
        _flipTo(cardId, newAccount);
        
        showToast('Đã tạo tài khoản phụ!', 'success');
        
    } catch (err) {
        if (err instanceof TypeError) {
            showToast('API không phản hồi (mất kết nối)', 'warning');
        } else {
            showToast(`Tạo tài khoản phụ thất bại: ${err.message}`, 'error');
        }
    }
};

/**
 * Chuyển đổi hiển thị sang tài khoản khác trên cùng một card.
 * @param {number} cardId - ID của card
 * @param {number} accountId - ID của tài khoản cần chuyển sang
 */
MXH.switchAccount = (cardId, accountId) => {
    const state = _getCardState(cardId);
    const account = state.accounts.find(a => a.id == accountId);
    
    if (!account) {
        console.warn(`Account ${accountId} not found in card ${cardId}`);
        return;
    }
    
    // Nếu đã đang hiển thị account này rồi thì không làm gì
    if (state.activeId === account.id) {
        return;
    }
    
    // Lật card sang account mới
    _flipTo(cardId, account);
};

// ===== UTILITY FUNCTIONS =====
function ensureNoticeParsed(notice) {
    let n = (typeof notice === 'string') ? (() => { try { return JSON.parse(notice) } catch { return {} } })() : (notice || {});
    if (n && n.start_at) n.start_at = normalizeISOForJS(n.start_at);
    return n;
}

function setupEditableFields() {
    const editableFields = document.querySelectorAll('.editable-field');

    editableFields.forEach(field => {
        // Remove old listeners by cloning
        const newField = field.cloneNode(true);
        field.parentNode.replaceChild(newField, field);
    });

    // Re-select after cloning
    document.querySelectorAll('.editable-field').forEach(field => {
        field.addEventListener('blur', async (e) => {
            const accountId = parseInt(e.target.dataset.accountId);
            const fieldName = e.target.dataset.field;
            let newValue = e.target.textContent.trim();

            if (fieldName === 'phone') {
                newValue = newValue.replace(/^📞\s*/, '').trim();
            }

            const originalAccount = mxhAccounts.find(acc => acc.id === accountId);
            if (originalAccount && originalAccount[fieldName] !== newValue) {
                await quickUpdateField(accountId, fieldName, newValue);
            }
        });

        field.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                e.target.blur();
            }
        });
        
        field.addEventListener('focus', (e) => {
            setTimeout(() => {
                const selection = window.getSelection();
                const range = document.createRange();
                range.selectNodeContents(e.target);
                selection.removeAllRanges();
                selection.addRange(range);
            }, 0);
        });
    });
}

async function quickUpdateField(accountId, field, value) {
    try {
        const response = await fetch(`/mxh/api/accounts/${accountId}/quick-update`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ field, value })
        });

        if (response.ok) {
            showToast(`Đã cập nhật ${field === 'username' ? 'tên' : 'SĐT'}!`, 'success');
            const accountIndex = mxhAccounts.findIndex(acc => acc.id === accountId);
            if (accountIndex !== -1) {
                mxhAccounts[accountIndex][field] = value;
            }
        } else {
            const error = await response.json();
            showToast(error.error || 'Lỗi khi cập nhật!', 'error');
            await loadMXHData(true);
        }
    } catch (error) {
        showToast('Lỗi kết nối!', 'error');
        await loadMXHData(true);
    }
}

function openAccountModalForEdit(accountId) {
    const account = mxhAccounts.find(acc => acc.id === accountId);
    if (!account) {
        showToast('Không tìm thấy dữ liệu tài khoản!', 'error');
        return;
    }

    const modalEl = document.getElementById('wechat-account-modal');
    if (!modalEl) {
        showToast('Lỗi: Không tìm thấy modal!', 'error');
        return;
    }

    modalEl.querySelector('#wechat-card-name').value = account.card_name || '';
    modalEl.querySelector('#wechat-username').value = account.username || '';
    modalEl.querySelector('#wechat-phone').value = account.phone || '';
    modalEl.querySelector('#wechat-day').value = account.wechat_created_day || '';
    modalEl.querySelector('#wechat-month').value = account.wechat_created_month || '';
    modalEl.querySelector('#wechat-year').value = account.wechat_created_year || '';

    let currentStatus = account.status || 'active';
    if (account.muted_until && new Date(account.muted_until) > new Date()) {
        currentStatus = 'muted';
    }
    modalEl.querySelector('#wechat-status').value = currentStatus;

    const modalInstance = new bootstrap.Modal(modalEl);
    modalInstance.show();
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

    const wechatOnlyItems = contextMenu.querySelectorAll('.wechat-only');
    wechatOnlyItems.forEach(item => {
        item.style.display = platform === 'wechat' ? 'block' : 'none';
    });

    const copyPhoneItem = contextMenu.querySelector('#copy-phone-item');
    const phone = account.phone;
    if (copyPhoneItem) {
        copyPhoneItem.style.display = phone ? 'block' : 'none';
    }

    const noticeToggle = contextMenu.querySelector('#unified-notice-toggle');
    if (noticeToggle) {
        const noticeObj = ensureNoticeParsed(account.notice);
        const hasNotice = !!(noticeObj && noticeObj.enabled);
        noticeToggle.dataset.action = hasNotice ? 'clear-notice' : 'set-notice';
        noticeToggle.innerHTML = hasNotice
            ? '<i class="bi bi-bell-slash-fill me-2"></i> Hủy thông báo'
            : '<i class="bi bi-bell-fill me-2"></i> Thông báo';
    }
        
    const currentStatus = account.status;
    const statusNormalItems = contextMenu.querySelectorAll('.status-normal');
    const statusRescueItems = contextMenu.querySelectorAll('.status-rescue');

    if (currentStatus === 'disabled') {
        statusNormalItems.forEach(item => item.style.display = 'none');
        statusRescueItems.forEach(item => item.style.display = 'block');
    } else {
        statusNormalItems.forEach(item => item.style.display = 'block');
        statusRescueItems.forEach(item => item.style.display = 'none');
    }
        
    const menuWidth = 200;
    const menuHeight = 300;
    const buffer = 50;
    
    const mouseX = event.pageX;
    const mouseY = event.pageY;
    const windowWidth = window.innerWidth;
    const windowHeight = window.innerHeight;
    
    let finalX = mouseX;
    let finalY = mouseY;
    
    if (mouseX < buffer) {
        finalX = mouseX + 20;
    } else if (mouseX > windowWidth - menuWidth - buffer) {
        finalX = mouseX - menuWidth - 20;
    }
    
    if (mouseY < buffer) {
        finalY = mouseY + 20;
    } else if (mouseY > windowHeight - menuHeight - buffer) {
        finalY = mouseY - menuHeight - 20;
    }
    
    contextMenu.style.display = 'block';
    contextMenu.style.left = finalX + 'px';
    contextMenu.style.top = finalY + 'px';
    contextMenu.style.opacity = '0';
    contextMenu.style.transform = 'scale(0.8)';
    
    setTimeout(() => {
        contextMenu.style.transition = 'opacity 0.2s ease, transform 0.2s ease';
        contextMenu.style.opacity = '1';
        contextMenu.style.transform = 'scale(1)';
    }, 10);
    
    setTimeout(() => {
        document.addEventListener('click', hideUnifiedContextMenu, { once: true });
    }, 100);
}

function hideUnifiedContextMenu() {
    const contextMenu = document.getElementById('unified-context-menu');
    
    contextMenu.style.transition = 'opacity 0.15s ease, transform 0.15s ease';
    contextMenu.style.opacity = '0';
    contextMenu.style.transform = 'scale(0.9)';
    
    setTimeout(() => {
        contextMenu.style.display = 'none';
        contextMenu.style.transition = '';
        contextMenu.style.opacity = '';
        contextMenu.style.transform = '';
    }, 150);
    
    resumeAutoRefresh();
}

window.handleCardContextMenu = function (event, accountId, platform) {
    event.preventDefault();
    event.stopPropagation();
    
    const account = mxhAccounts.find(acc => acc.id === accountId);
    const cardId = account?.card_id || accountId;
    
    showUnifiedContextMenuWithFlip(event, accountId, platform, cardId);
}

function showUnifiedContextMenuWithFlip(event, accountId, platform, cardId) {
    event.preventDefault();
    event.stopPropagation();
    currentContextAccountId = accountId;
    pauseAutoRefresh();

    const contextMenu = document.getElementById('unified-context-menu');
    const account = mxhAccounts.find(acc => acc.id === accountId);

    if (!account) return;

    const wechatOnlyItems = contextMenu.querySelectorAll('.wechat-only');
    wechatOnlyItems.forEach(item => {
        item.style.display = platform === 'wechat' ? 'block' : 'none';
    });

    const copyPhoneItem = contextMenu.querySelector('#copy-phone-item');
    const phone = account.phone;
    if (copyPhoneItem) {
        copyPhoneItem.style.display = phone ? 'block' : 'none';
    }

    const noticeToggle = contextMenu.querySelector('#unified-notice-toggle');
    if (noticeToggle) {
        const noticeObj = ensureNoticeParsed(account.notice);
        const hasNotice = !!(noticeObj && noticeObj.enabled);
        noticeToggle.dataset.action = hasNotice ? 'clear-notice' : 'set-notice';
        noticeToggle.innerHTML = hasNotice
            ? '<i class="bi bi-bell-slash-fill me-2"></i> Hủy thông báo'
            : '<i class="bi bi-bell-fill me-2"></i> Thông báo';
    }
        
    const currentStatus = account.status;
    const statusNormalItems = contextMenu.querySelectorAll('.status-normal');
    const statusRescueItems = contextMenu.querySelectorAll('.status-rescue');

    if (currentStatus === 'disabled') {
        statusNormalItems.forEach(item => item.style.display = 'none');
        statusRescueItems.forEach(item => item.style.display = 'block');
    } else {
        statusNormalItems.forEach(item => item.style.display = 'block');
        statusRescueItems.forEach(item => item.style.display = 'none');
    }

    // ===== FLIP CARD INTEGRATION: Tạo submenu "Tài khoản" =====
    const accountsSubmenu = contextMenu.querySelector('#accounts-submenu');
    if (accountsSubmenu) {
        const state = _getCardState(cardId);
        
        accountsSubmenu.innerHTML = '';
        
        state.accounts.forEach((acc, index) => {
            const isActive = acc.id === state.activeId;
            const item = document.createElement('div');
            item.className = 'menu-item';
            item.dataset.ctx = 'switchAccount';
            item.dataset.cardId = cardId;
            item.dataset.accountId = acc.id;
            item.innerHTML = `
                <i class="bi bi-person me-2"></i> 
                ${acc.account_name || `Tài khoản ${index + 1}`}${isActive ? ' ✓' : ''}
            `;
            accountsSubmenu.appendChild(item);
        });
        
        const addItem = document.createElement('div');
        addItem.className = 'menu-item';
        addItem.dataset.ctx = 'addAccount';
        addItem.dataset.cardId = cardId;
        addItem.innerHTML = '<i class="bi bi-plus-circle me-2"></i> Thêm Tài Khoản';
        accountsSubmenu.appendChild(addItem);
    }
        
    const menuWidth = 200;
    const menuHeight = 300;
    const buffer = 50;
    
    const mouseX = event.pageX;
    const mouseY = event.pageY;
    const windowWidth = window.innerWidth;
    const windowHeight = window.innerHeight;
    
    let finalX = mouseX;
    let finalY = mouseY;
    
    if (mouseX < buffer) {
        finalX = mouseX + 20;
    } else if (mouseX > windowWidth - menuWidth - buffer) {
        finalX = mouseX - menuWidth - 20;
    }
    
    if (mouseY < buffer) {
        finalY = mouseY + 20;
    } else if (mouseY > windowHeight - menuHeight - buffer) {
        finalY = mouseY - menuHeight - 20;
    }
    
    contextMenu.style.display = 'block';
    contextMenu.style.left = finalX + 'px';
    contextMenu.style.top = finalY + 'px';
    contextMenu.style.opacity = '0';
    contextMenu.style.transform = 'scale(0.8)';
    
    setTimeout(() => {
        contextMenu.style.transition = 'opacity 0.2s ease, transform 0.2s ease';
        contextMenu.style.opacity = '1';
        contextMenu.style.transform = 'scale(1)';
    }, 10);
    
    setTimeout(() => {
        document.addEventListener('click', hideUnifiedContextMenu, { once: true });
    }, 100);
}

// Event delegation cho context menu items
document.addEventListener('pointerdown', function(e) {
    const el = e.target.closest('[data-ctx]');
    if (!el) return;

    const ctx = el.dataset.ctx;
    const cardId = +el.dataset.cardId || 0;
    const accountId = el.dataset.accountId || null;

    e.preventDefault();
    e.stopPropagation();

    if (ctx === 'addAccount') {
        MXH.addSubAccount(cardId);
        hideUnifiedContextMenu();
        return;
    }
    
    if (ctx === 'switchAccount') {
        MXH.switchAccount(cardId, +accountId);
        hideUnifiedContextMenu();
        return;
    }
});

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

// ===== CHANGE NUMBER FUNCTIONS =====
function openChangeNumberModal() {
    const account = mxhAccounts.find(acc => acc.id === currentContextAccountId);
    if (!account) return;
    
    document.getElementById('newCardNumber').value = account.card_name;
    const modal = new bootstrap.Modal(document.getElementById('changeNumberModal'));
    modal.show();
}

async function submitChangeNumber() {
    const newNumber = document.getElementById('newCardNumber').value;
    if (!newNumber || newNumber < 1) {
        showToast('Vui lòng nhập số hiệu hợp lệ', 'warning');
        return;
    }
    
    try {
        const response = await fetch(`/mxh/api/accounts/${currentContextAccountId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                card_name: newNumber
            })
        });
        
        if (response.ok) {
            showToast('Đổi số hiệu thành công', 'success');
            bootstrap.Modal.getInstance(document.getElementById('changeNumberModal')).hide();
            
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            const error = await response.json();
            showToast(error.error || 'Lỗi đổi số hiệu', 'error');
        }
    } catch (error) {
        console.error('Error changing number:', error);
        showToast('Lỗi kết nối', 'error');
    }
}

window.submitChangeNumber = submitChangeNumber;

// ===== SUBMENU LOGIC =====
let currentSubmenu = null;
let hideTimeout = null;

function showSubmenu(menuItem) {
    if (currentSubmenu && currentSubmenu !== menuItem) {
        const currentSubmenuEl = currentSubmenu.querySelector('.submenu');
        if (currentSubmenuEl) {
            currentSubmenuEl.classList.remove('show');
        }
    }
    
    const submenuEl = menuItem.querySelector('.submenu');
    if (submenuEl) {
        submenuEl.classList.add('show');
        currentSubmenu = menuItem;
    }
    
    if (hideTimeout) {
        clearTimeout(hideTimeout);
        hideTimeout = null;
    }
}

function hideSubmenu(delay = 300) {
    if (hideTimeout) {
        clearTimeout(hideTimeout);
    }
    hideTimeout = setTimeout(() => {
        if (currentSubmenu) {
            const submenuEl = currentSubmenu.querySelector('.submenu');
            if (submenuEl) {
                submenuEl.classList.remove('show');
            }
            currentSubmenu = null;
        }
    }, delay);
}

document.addEventListener('mouseover', function(event) {
    const menuItem = event.target.closest('.menu-item.has-submenu');
    const submenu = event.target.closest('.submenu');
    
    if (menuItem) {
        showSubmenu(menuItem);
    } else if (submenu) {
        if (currentSubmenu) {
            const submenuEl = currentSubmenu.querySelector('.submenu');
            if (submenuEl) {
                submenuEl.classList.add('show');
            }
            if (hideTimeout) {
                clearTimeout(hideTimeout);
                hideTimeout = null;
            }
        }
    }
});

document.addEventListener('mouseout', function(event) {
    const menuItem = event.target.closest('.menu-item.has-submenu');
    const submenu = event.target.closest('.submenu');
    
    if (!menuItem && !submenu) {
        hideSubmenu();
    }
});

// ===== EVENT LISTENERS =====
document.addEventListener('DOMContentLoaded', function() {
    initializeViewMode();
    applyViewMode(localStorage.getItem('mxh_cards_per_row') || 12);

    loadMXHData(true);
    startAutoRefresh();

    document.getElementById('unified-context-menu').addEventListener('click', async (e) => {
        const menuItem = e.target.closest('.menu-item');
        if (!menuItem) return;
        
        e.preventDefault();
        e.stopPropagation();
        
        const action = menuItem.dataset.action;
        if (!action) return;

        switch (action) {
            case 'edit':
                openAccountModalForEdit(currentContextAccountId);
                break;
            case 'status-available':
                await updateAccountStatus('available');
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
            case 'change-number':
                openChangeNumberModal();
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
            case 'delete':
                const account = mxhAccounts.find(acc => acc.id === currentContextAccountId);
                if (account && account.card_id) {
                    handleDeleteCard(account.card_id);
                } else {
                    showToast('Không tìm thấy card để xóa', 'error');
                }
                break;
        }

        hideUnifiedContextMenu();
    });

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
            const groupId = await ensurePlatformGroup(platform);
            const nextCardName = String(await getNextCardNumber(groupId));
            
            const autoFillValue = (value, isUrl = false) => {
                if (isUrl) return value || "";
                return value || ".";
            };
            
            const response = await fetch('/mxh/api/cards', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    card_name: nextCardName,
                    group_id: groupId,
                    platform: platform,
                    username: autoFillValue(username),
                    phone: autoFillValue(phone),
                    url: autoFillValue(url, true),
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
    
    document.getElementById('mxh-addAccountModal').addEventListener('shown.bs.modal', function () {
        const today = new Date();
        const day = today.getDate();
        const month = today.getMonth() + 1;
        const year = today.getFullYear();
        
        document.getElementById('mxh-day').value = day;
        document.getElementById('mxh-month').value = month;
        document.getElementById('mxh-year').value = year;
    });
    
    const resetBtn = document.getElementById('wechat-reset-btn');
    if (resetBtn) {
        resetBtn.addEventListener('click', async () => {
            if (!currentContextAccountId) {
                showToast('Lỗi: Không có tài khoản được chọn!', 'error');
                return;
            }

            try {
                const response = await fetch(`/mxh/api/accounts/${currentContextAccountId}/reset`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });

                if (response.ok) {
                    showToast('Reset thống kê thành công!', 'success');
                    await loadMXHData(true);
                    bootstrap.Modal.getInstance(document.getElementById('wechat-account-modal')).hide();
                } else {
                    const error = await response.json();
                    showToast(error.error || 'Lỗi khi reset!', 'error');
                }
            } catch (error) {
                console.error('Reset error:', error);
                showToast('Lỗi kết nối khi reset!', 'error');
            }
        });
    }

    const applyBtn = document.getElementById('wechat-apply-btn');
    if (applyBtn) {
        applyBtn.addEventListener('click', async () => {
            if (!currentContextAccountId) {
                showToast('Lỗi: Không có tài khoản được chọn!', 'error');
                return;
            }

            const modalEl = document.getElementById('wechat-account-modal');
            const originalAccount = mxhAccounts.find(acc => acc.id === currentContextAccountId);
            if (!originalAccount) {
                showToast('Lỗi: Không tìm thấy tài khoản để cập nhật!', 'error');
                return;
            }

            const selectedStatus = modalEl.querySelector('#wechat-status').value;

            const newCardName = modalEl.querySelector('#wechat-card-name').value;
            const payload = {
                card_name: newCardName,
                username: modalEl.querySelector('#wechat-username').value,
                phone: modalEl.querySelector('#wechat-phone').value,
                wechat_created_day: parseInt(modalEl.querySelector('#wechat-day').value) || null,
                wechat_created_month: parseInt(modalEl.querySelector('#wechat-month').value) || null,
                wechat_created_year: parseInt(modalEl.querySelector('#wechat-year').value) || null,
            };
            
            const cardNameChanged = originalAccount.card_name !== newCardName;

            if (selectedStatus === 'muted') {
                const muteUntilDate = new Date();
                muteUntilDate.setDate(muteUntilDate.getDate() + 30);
                payload.muted_until = muteUntilDate.toISOString();
                payload.status = originalAccount.status;
                payload.wechat_status = originalAccount.wechat_status;
            } else {
                payload.muted_until = null;
                if (selectedStatus === 'available') {
                    payload.status = 'active';
                } else {
                    payload.status = selectedStatus;
                }
                payload.wechat_status = selectedStatus;
            }

            try {
                const response = await fetch(`/mxh/api/accounts/${currentContextAccountId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (response.ok) {
                    showToast('Cập nhật thông tin thành công!', 'success');
                    bootstrap.Modal.getInstance(modalEl).hide();
                    
                    if (cardNameChanged) {
                        setTimeout(() => {
                            window.location.reload();
                        }, 1000);
                    } else {
                        await loadMXHData(true);
                    }
                } else {
                    const error = await response.json();
                    showToast(error.error || 'Lỗi khi cập nhật!', 'error');
                }
            } catch (error) {
                console.error('Update error:', error);
                showToast('Lỗi kết nối khi cập nhật!', 'error');
            }
        });
    }
    
    document.addEventListener('click', function (event) {
        if (!event.target.closest('.custom-context-menu')) {
            document.querySelectorAll('.custom-context-menu').forEach(menu => {
                menu.style.display = 'none';
            });
        }
    });
});

// ===== BORDER STATE FUNCTIONS =====
function parseDateAny(v) {
    if (!v) return null;
    if (typeof v === 'number') return new Date(v > 1e12 ? v : v * 1000);
    if (typeof v === 'string') {
        const s = v.trim();
        if (/^\d{4}[-/]\d{1,2}[-/]\d{1,2}/.test(s)) return new Date(s.replace(/-/g, '/'));
        const m = s.match(/^(\d{1,2})[\/-](\d{1,2})[\/-](\d{2,4})/);
        if (m) { const d = +m[1], mo = +m[2] - 1, y = (+m[3] < 100 ? 2000 + +m[3] : +m[3]); return new Date(y, mo, d); }
        const t = Date.parse(s); if (!isNaN(t)) return new Date(t);
    }
    return null;
}

function resolveState(acc) {
    const s = String(acc?.status ?? acc?.state ?? '').toLowerCase();
    const isDie = s === 'die' || s === 'dead' || s === 'banned' || acc?.is_die === true || !!acc?.die_date;
    const isDisabled = ['disabled', 'inactive', 'deactivated', 'locked', 'suspended'].includes(s) || acc?.is_disabled === true;
    
    // Tính tuổi tài khoản từ wechat_created_year hoặc created_at
    let gt1y = false;
    if (acc?.wechat_created_year) {
        const createdDate = new Date(
            acc.wechat_created_year,
            (acc.wechat_created_month || 1) - 1,
            acc.wechat_created_day || 1
        );
        gt1y = (Date.now() - createdDate.getTime()) >= 365 * 24 * 60 * 60 * 1000;
    } else {
        const created = acc?.created_at ?? acc?.account_created_at;
        const dt = created ? new Date(created) : null;
        gt1y = dt ? (Date.now() - dt.getTime()) >= 365 * 24 * 60 * 60 * 1000 : false;
    }
    
    if (isDie) return 'die';
    if (isDisabled) return 'disabled';
    if (gt1y) return '1y';
    return 'default';
}

function paintRing(gridCellEl, acc) {
    const map = { die: '#FF3B30', disabled: '#FF8F00', '1y': '#07C160', default: '#D1D5DB' };
    const state = resolveState(acc);
    const color = map[state];
    gridCellEl.style.setProperty('--mxh-ring', color);
}

function onAccountUpdated(account) {
    const cell = document.querySelector(`.mxh-item[data-card-id="${account.card_id}"]`);
    if (cell) paintRing(cell, account);
}

// ===== STATUS UPDATE FUNCTIONS =====
async function updateAccountStatus(status) {
    if (!currentContextAccountId) {
        showToast('Lỗi: Không có tài khoản được chọn!', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/mxh/api/accounts/${currentContextAccountId}/status`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: status })
        });
        
        if (response.ok) {
            const result = await response.json();
            showToast(result.message, 'success');
            
            const account = mxhAccounts.find(acc => acc.id === currentContextAccountId);
            if (account) {
                if (status === 'available') {
                    account.status = 'active';
                } else {
                    account.status = status;
                }
                const cell = document.querySelector(`.mxh-item[data-card-id="${account.card_id}"]`);
                if (cell) {
                    paintRing(cell, account);
                }
            }
            
            await loadMXHData(true);
            hideUnifiedContextMenu();
        } else {
            const error = await response.json();
            showToast(error.error || 'Lỗi khi cập nhật trạng thái!', 'error');
        }
    } catch (error) {
        console.error('Error updating status:', error);
        showToast('Lỗi kết nối!', 'error');
    }
}

async function rescueAccountUnified(result) {
    if (!currentContextAccountId) {
        showToast('Lỗi: Không có tài khoản được chọn!', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/mxh/api/accounts/${currentContextAccountId}/rescue`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ result: result })
        });
        
        if (response.ok) {
            const data = await response.json();
            showToast(data.message, 'success');
            await loadMXHData(true);
            hideUnifiedContextMenu();
        } else {
            const error = await response.json();
            showToast(error.error || 'Lỗi khi cứu tài khoản!', 'error');
        }
    } catch (error) {
        console.error('Error rescuing account:', error);
        showToast('Lỗi kết nối!', 'error');
    }
}

async function markAccountAsScanned(e) {
    const accountId = currentContextAccountId;
    if (!accountId) return;
    
    try {
        const response = await fetch('/mxh/api/accounts/mark-scanned', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ account_id: accountId })
        });
        
        if (response.ok) {
            showToast('Đã đánh dấu đã quét!', 'success');
            await loadMXHData(true);
            hideUnifiedContextMenu();
        } else {
            showToast('Lỗi khi đánh dấu đã quét!', 'error');
        }
    } catch (error) {
        console.error('Error marking as scanned:', error);
        showToast('Lỗi kết nối!', 'error');
        hideUnifiedContextMenu();
    }
}

// ===== NOTICE MANAGEMENT =====
let noticeTargetId = null;

function openNoticeModal(e) {
    if (e) {
        e.preventDefault();
        e.stopPropagation();
    }
    if (!currentContextAccountId) return;

    noticeTargetId = currentContextAccountId;
    document.getElementById('noticeTitle').value = 'Reg';
    document.getElementById('noticeDays').value = 7;
    document.getElementById('noticeNote').value = '';

    const modal = new bootstrap.Modal(document.getElementById('noticeModal'));
    modal.show();

    hideUnifiedContextMenu();
}

async function submitNotice() {
    const title = document.getElementById('noticeTitle').value.trim();
    const days = parseInt(document.getElementById('noticeDays').value, 10) || 0;
    const note = document.getElementById('noticeNote').value.trim();

    if (!noticeTargetId || !title || days <= 0) {
        showToast('Vui lòng điền đầy đủ thông tin!', 'error');
        return;
    }

    try {
        const response = await fetch(`/mxh/api/accounts/${noticeTargetId}/notice`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, days, note })
        });

        if (response.ok) {
            showToast('✅ Đã đặt thông báo!', 'success');
            const modal = bootstrap.Modal.getInstance(document.getElementById('noticeModal'));
            modal.hide();

            const account = mxhAccounts.find(a => a.id === noticeTargetId);
            if (account) {
                account.notice = {
                    enabled: true,
                    title: title,
                    days: days,
                    note: note,
                    start_at: new Date().toISOString()
                };
            }

            await loadMXHData(true);
        } else {
            showToast('Lỗi khi đặt thông báo!', 'error');
        }
    } catch (error) {
        console.error('Error setting notice:', error);
        showToast('Lỗi kết nối!', 'error');
    }
}

async function clearNotice(e) {
    if (!currentContextAccountId) return;

    try {
        const response = await fetch(`/mxh/api/accounts/${currentContextAccountId}/notice`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showToast('✅ Đã hủy thông báo!', 'success');
            
            const account = mxhAccounts.find(a => a.id === currentContextAccountId);
            if (account) {
                account.notice = null;
            }

            await loadMXHData(true);
            hideUnifiedContextMenu();
        } else {
            showToast('Lỗi khi hủy thông báo!', 'error');
        }
    } catch (error) {
        console.error('Error clearing notice:', error);
        showToast('Lỗi kết nối!', 'error');
    }
}

function copyPhoneNumber(e) {
    if (e) {
        e.preventDefault();
        e.stopPropagation();
    }
    if (!currentContextAccountId) return;

    const account = mxhAccounts.find(acc => acc.id === currentContextAccountId);
    if (account && account.phone) {
        navigator.clipboard.writeText(account.phone).then(() => {
            showToast('Đã copy SĐT!', 'success');
        }).catch(() => {
            showToast('Lỗi khi copy SĐT!', 'error');
        });
    } else {
        showToast('Không có số điện thoại để copy!', 'warning');
    }
    hideUnifiedContextMenu();
}

function copyEmail(e) {
    showToast('Chức năng đang phát triển', 'info');
}

async function resetScanCount(e) {
    const accountId = currentContextAccountId;
    if (!accountId) return;
    
    try {
        const response = await fetch('/mxh/api/accounts/reset-scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ account_id: accountId })
        });
        
        if (response.ok) {
            showToast('Đã reset lượt quét!', 'success');
            await loadMXHData(true);
            hideUnifiedContextMenu();
        } else {
            showToast('Lỗi khi reset lượt quét!', 'error');
        }
    } catch (error) {
        console.error('Error resetting scan count:', error);
        showToast('Lỗi kết nối!', 'error');
        hideUnifiedContextMenu();
    }
}

// ===== CARD DELETE FUNCTIONALITY =====
async function apiGetAccountCount(cardId) {
    const res = await fetch(`/mxh/api/cards/${cardId}/account-count`, { credentials: "same-origin" });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}

async function apiDeleteCard(cardId, force = false) {
    const url = `/mxh/api/cards/${cardId}` + (force ? `?force=true` : ``);
    const res = await fetch(url, { method: "DELETE", credentials: "same-origin" });
    if (res.status === 409) {
        return { requires_confirmation: true, ...(await res.json()) };
    }
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}

function showConfirmModal({ title = "Xác nhận", html = "", okText = "OK", cancelText = "Cancel" } = {}) {
    return new Promise((resolve) => {
        const modalEl = document.getElementById("confirmModal");
        const titleEl = document.getElementById("confirmModalTitle");
        const bodyEl  = document.getElementById("confirmModalBody");
        const okBtn   = document.getElementById("confirmModalOk");
        const cancelBtn = document.getElementById("confirmModalCancel");

        titleEl.textContent = title;
        bodyEl.innerHTML = html;
        okBtn.textContent = okText;
        cancelBtn.textContent = cancelText;

        const bsModal = bootstrap.Modal.getOrCreateInstance(modalEl, { backdrop: 'static', keyboard: false });

        const onOk = () => { cleanup(); resolve(true); };
        const onCancel = () => { cleanup(); resolve(false); };
        function cleanup() {
            okBtn.removeEventListener("click", onOk);
            modalEl.removeEventListener("hidden.bs.modal", onCancel);
        }

        okBtn.addEventListener("click", onOk, { once: true });
        modalEl.addEventListener("hidden.bs.modal", onCancel, { once: true });

        bsModal.show();
    });
}

function removeCardFromDOM(cardId) {
    const card = document.getElementById(`card-${cardId}`);
    const container = card?.closest(".mxh-item") || card;
    if (container) container.remove();
}

function toastSuccess(msg){
    if (typeof showToast === 'function') {
        showToast(msg, 'success');
    }
}
function toastError(msg){
    if (typeof showToast === 'function') {
        showToast(msg, 'error');
    }
}

let _deleteBusy = new Set();
async function handleDeleteCard(cardId) {
    if (_deleteBusy.has(cardId)) return;
    _deleteBusy.add(cardId);

    try {
        const { account_count } = await apiGetAccountCount(cardId);

        const title = "Xóa Card";
        const html = (account_count > 1)
            ? `Card này đang có: <b>${account_count}</b> tài khoản phụ.<br>Bạn chắc chắn muốn xóa?`
            : `Bạn chắc chắn muốn xóa card này?`;

        const ok = await showConfirmModal({ title, html, okText: "Xóa", cancelText: "Hủy" });
        if (!ok) return;

        const res = await apiDeleteCard(cardId, true);

        removeCardFromDOM(cardId);
        toastSuccess(`Đã xóa card #${cardId}` + (res.deleted_accounts ? ` cùng ${res.deleted_accounts} tài khoản` : ""));
        
        const modalEl = document.getElementById("confirmModal");
        if (modalEl) {
            const bsModal = bootstrap.Modal.getInstance(modalEl);
            if (bsModal) {
                bsModal.hide();
            }
        }

    } catch (err) {
        toastError(`Xóa thất bại: ${err.message || err}`);
    } finally {
        _deleteBusy.delete(cardId);
    }
}

document.addEventListener("click", (ev) => {
    const btn = ev.target.closest("[data-action='delete-card']");
    if (!btn) return;
    const cardId = parseInt(btn.getAttribute("data-card-id"), 10);
    if (!Number.isFinite(cardId)) {
        toastError("Thiếu cardId hợp lệ.");
        return;
    }
    handleDeleteCard(cardId);
});

window.handleDeleteCard = handleDeleteCard;
window.showConfirmModal = showConfirmModal;
window.submitNotice = submitNotice;
