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

// ===== VIEW MODE LOGIC (FLEXBOX + CSS VARIABLE) =====

/**
 * Áp dụng và lưu chế độ xem bằng cách set biến CSS.
 * @param {number | string} value - Số lượng card mong muốn trên một hàng.
 */
function applyViewMode(value){const n=Math.max(1,parseInt(value,10)||12);localStorage.setItem('mxh_cards_per_row',n);document.documentElement.style.setProperty('--cardsPerRow',n);const c=document.getElementById('mxh-accounts-container');if(c)c.style.setProperty('--cardsPerRow',n);}

/**
 * Khởi tạo chức năng "Chế Độ Xem".
 */
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

            // Không cần render lại, CSS sẽ tự cập nhật.
            // Chỉ cần đóng modal và thông báo.
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

            // Get platform color for this group
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
     * VIẾT LẠI: Render các card tài khoản sử dụng Bootstrap row và class .col đơn giản.
     */
    function renderMXHAccounts() {
        if (isRendering) {
            pendingUpdates = true;
            return;
        }
        isRendering = true;

        const container = document.getElementById('mxh-accounts-container');
        const scrollY = window.scrollY;

        // Clear all old notice elements before rendering
        container.querySelectorAll('.notice-indicator,.notice-line,.notice-tooltip').forEach(e => e.remove());

        const filteredAccounts = activeGroupId
            ? mxhAccounts.filter(acc => String(acc.group_id) === String(activeGroupId))
            : mxhAccounts;

        if (filteredAccounts.length === 0) {
            container.innerHTML = `<div class="col-12"><div class="card"><div class="card-body text-center text-muted"><i class="bi bi-inbox fs-1 opacity-25"></i><h5 class="mt-3">Không có tài khoản nào</h5></div></div></div>`;
            isRendering = false;
            return;
        }

        // Sort accounts by card_name numerically (allow duplicates)
        filteredAccounts.sort((a, b) => {
            const numA = parseInt(a.card_name) || 0;
            const numB = parseInt(b.card_name) || 0;
            return numA === numB ? (b.id - a.id) : (numA - numB);
        });

        const cardsHtml = filteredAccounts.map(account => {
            // --- LOGIC XÁC ĐỊNH VIỀN MÀU ---
            let borderClass = '';
            const now = new Date();
            const noticeObj = ensureNoticeParsed(account.notice);

            // ==== State flags (áp dụng cho mọi MXH) ====
            const isDie = ['disabled', 'die', 'banned', 'blocked']
                .includes(String(account.status || '').toLowerCase()) || !!account.die_date;

            const hasNotice = !!(noticeObj && (noticeObj.enabled === true || noticeObj.enabled === 1 || Number(noticeObj.days) > 0));

            // ==== Logic viền mới cho WeChat ====
            const isWechat = String(account.platform || '').toLowerCase() === 'wechat';
            const isHK = /^\+?852/.test(account.phone || '');
            const y = +account.wechat_created_year || 0;
            const m = (+account.wechat_created_month || 1) - 1;
            const d = +account.wechat_created_day || 1;
            const ageDays = isFinite(new Date(y, m, d)) ? Math.floor((Date.now() - new Date(y, m, d).getTime()) / 86400000) : 0;

            // ==== Gán class viền theo ưu tiên: Đỏ > Cam > Xanh > Trắng ====
            let blinkClass = '';
            if (isDie) {
                borderClass = 'mxh-border-red';
                console.log(`Account ${account.id} (${account.card_name}): DIE -> RED border`);
            } else if (hasNotice) {
                borderClass = 'mxh-border-orange';
                console.log(`Account ${account.id} (${account.card_name}): NOTICE -> ORANGE border`);
            } else if (isWechat && ageDays >= 365 && isHK) {
                borderClass = 'mxh-border-green';
                console.log(`Account ${account.id} (${account.card_name}): WECHAT HK ANNIVERSARY -> GREEN border`);
            } else if (isWechat && ageDays >= 365 && !isHK) {
                borderClass = 'mxh-border-white';
                blinkClass = 'anniversary-blink';
                console.log(`Account ${account.id} (${account.card_name}): WECHAT ANNIVERSARY -> WHITE border + BLINK`);
            }
            
            // Debug: Log status and border class
            console.log(`Account ${account.id}: status=${account.status}, isDie=${isDie}, hasNotice=${hasNotice}, borderClass="${borderClass}"`);
            
            // FORCE BORDER STYLES FOR TESTING (30% thinner)
            let inlineStyle = '';
            if (borderClass === 'mxh-border-red') {
                inlineStyle = 'border: 1.4px solid #ff4d4f !important;';
                console.log(`FORCE: Setting red border for account ${account.id}`);
            } else if (borderClass === 'mxh-border-orange') {
                inlineStyle = 'border: 1.4px solid #ffa500 !important;';
                console.log(`FORCE: Setting orange border for account ${account.id}`);
            } else if (borderClass === 'mxh-border-green') {
                inlineStyle = 'border: 1.4px solid #2fe56a !important;';
                console.log(`FORCE: Setting green border for account ${account.id}`);
            } else if (borderClass === 'mxh-border-white') {
                inlineStyle = 'border: 1.4px solid #fff !important;';
                console.log(`FORCE: Setting white border for account ${account.id}`);
            }
            
            // --- KẾT THÚC LOGIC VIỀN MÀU ---

            // --- TÍNH TOÁN THÔNG TIN HIỂN THỊ ---
            let accountAgeDisplay = '';
            let ageColor = '#6c757d';
            
            // Tính tuổi tài khoản WeChat
            if (account.platform === 'wechat' && account.wechat_created_year) {
                const createdDate = new Date(account.wechat_created_year, (account.wechat_created_month || 1) - 1, account.wechat_created_day || 1);
                const diffDays = Math.ceil((now - createdDate) / (1000 * 60 * 60 * 24));
                
                if (diffDays >= 365) {
                    const years = Math.floor(diffDays / 365);
                    accountAgeDisplay = `${years}Y`;
                    ageColor = '#2fe56a'; // Xanh lá cho anniversary
                } else if (diffDays >= 30) {
                    const months = Math.floor(diffDays / 30);
                    accountAgeDisplay = `${months}M`;
                    ageColor = '#6c757d';
                } else {
                    accountAgeDisplay = `${diffDays}D`;
                    ageColor = '#6c757d';
                }
            }

            // Tính lượt quét và countdown (copy từ MXH_Old)
            let scanCountdown = '';
            if (account.platform === 'wechat') {
                const currentScanCount = account.wechat_scan_count || 0;
                const maxScans = 3;

                if (currentScanCount >= maxScans) {
                    // Đã hết lượt - QR đỏ
                    scanCountdown = `<i class="bi bi-qr-code me-1" style="color: #dc3545;"></i>${maxScans}/${maxScans}`;
                } else if (account.wechat_last_scan_date) {
                    // Có lịch sử quét - kiểm tra thời gian
                    const lastScanDate = new Date(account.wechat_last_scan_date);
                    const daysSinceScan = Math.floor((now - lastScanDate) / (1000 * 60 * 60 * 24));
                    const remainingDays = 30 - daysSinceScan;

                    if (remainingDays > 0) {
                        // Còn thời gian chờ - hiển thị countdown
                        const hoursSinceScan = Math.floor((now - lastScanDate) / (1000 * 60 * 60));
                        const remainingHours = (30 * 24) - hoursSinceScan;

                        if (remainingHours < 24) {
                            // Gần hết thời gian - QR cam
                            scanCountdown = `<i class="bi bi-qr-code me-1" style="color: #ff8c00;"></i>${currentScanCount}/${maxScans} <small class="text-warning">(${remainingHours}h)</small>`;
                        } else if (remainingDays < 7) {
                            // Còn ít ngày - QR cam
                            scanCountdown = `<i class="bi bi-qr-code me-1" style="color: #ff8c00; font-size: 1.3em;"></i>${currentScanCount}/${maxScans} <small class="text-warning">(${remainingDays}d)</small>`;
                        } else {
                            // Còn nhiều thời gian - QR trắng
                            scanCountdown = `<i class="bi bi-qr-code me-1" style="color: #ffffff; font-size: 1.3em;"></i>${currentScanCount}/${maxScans} <small class="text-warning">(${remainingDays}d)</small>`;
                        }
                    } else {
                        // Đủ điều kiện quét tiếp - QR xanh
                        scanCountdown = `<i class="bi bi-qr-code me-1" style="color: #07c160; font-size: 1.3em;"></i>${currentScanCount}/${maxScans}`;
                    }
                } else {
                    // Chưa quét lần nào
                    if (account.wechat_created_year) {
                        const createdDate = new Date(account.wechat_created_year, (account.wechat_created_month || 1) - 1, account.wechat_created_day || 1);
                        const diffDays = Math.ceil((now - createdDate) / (1000 * 60 * 60 * 24));
                        
                        if (diffDays < 90) {
                            scanCountdown = `Còn ${90 - diffDays} ngày`;
                        } else {
                            // Đủ điều kiện quét lần đầu - QR xanh
                            scanCountdown = `<i class="bi bi-qr-code me-1" style="color: #07c160; font-size: 1.3em;"></i>${currentScanCount}/${maxScans}`;
                        }
                    } else {
                        // Không có ngày tạo - QR xanh
                        scanCountdown = `<i class="bi bi-qr-code me-1" style="color: #07c160; font-size: 1.3em;"></i>${currentScanCount}/${maxScans}`;
                    }
                }
            }

            // Notice logic (copy từ MXH_Old)
            let noticeHtml = '';
            let extraClass = '';
            let tipHtml = '';
            const n = ensureNoticeParsed(account.notice);

            if (n.enabled && n.start_at && n.days > 0) {
                const start = new Date(n.start_at);
                const end = new Date(start.getTime() + n.days * 86400000);
                const remainMs = end - now;
                const remainDays = Math.ceil(remainMs / 86400000);

                if (remainMs > 0) {
                    let timeDisplay;
                    if (remainDays >= 30) {
                        const remainMonths = Math.floor(remainDays / 30);
                        timeDisplay = `${remainMonths}m`;
                    } else {
                        timeDisplay = `${remainDays}d`;
                    }
                    noticeHtml = `<div class="notice-line">${escapeHtml(n.title)}: ${timeDisplay}</div>`;
                } else {
                    noticeHtml = `<div class="notice-line expired">${escapeHtml(n.title)}: đã đến hạn</div>`;
                    extraClass = 'notice-expired-blink';
                }

                // Tooltip
                let tooltipTime;
                if (n.days >= 30) {
                    const months = Math.floor(n.days / 30);
                    tooltipTime = `${months}m`;
                } else {
                    tooltipTime = `${n.days}d`;
                }
                tipHtml = `<div class="notice-tooltip"><div class="notice-tooltip-title">${escapeHtml(n.title)} – ${tooltipTime}</div><div class="notice-tooltip-note">${escapeHtml(n.note || '')}</div></div>`;
            }

            // Disable bell badge: follow MXH_OLD
            let noticeIndicator = '';

            // Trạng thái và icon (copy từ MXH_Old)
            let statusClass = 'account-status-available';
            let statusIcon = '';
            let accountStatus = account.status || 'active';

            if (accountStatus === 'die') {
                statusClass = 'account-status-die';
                statusIcon = '<i class="bi bi-x-circle-fill status-icon" style="color: #dc3545;"></i>';
            } else if (accountStatus === 'disabled') {
                statusClass = 'account-status-disabled';
                statusIcon = '<i class="bi bi-slash-circle status-icon" style="color: #ff8c00;"></i>';
            }
            
            // Platform functions (copy từ MXH_Old)
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

            return `
                <div class="col mxh-item" style="flex:0 0 calc(100% / var(--cardsPerRow, 12));max-width:calc(100% / var(--cardsPerRow, 12));padding:4px" data-account-id="${account.id}">
                    <div class="card tool-card mxh-card ${borderClass} ${extraClass} ${blinkClass}" id="card-${account.id}" oncontextmenu="handleCardContextMenu(event, ${account.id}, '${account.platform}'); return false;" style="position:relative; ${inlineStyle}">
                        ${noticeIndicator}
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
                                    ${isDie ?
                                        `<div class="d-flex align-items-center justify-content-between">
                                            <div class="text-center">
                                                <small class="text-danger" style="font-size: 0.77rem;">Ngày:</small>
                                                <div class="text-danger" style="font-size: 0.77rem; font-weight: 600;">${account.die_date ? Math.ceil((now - new Date(account.die_date)) / (1000 * 60 * 60 * 24)) : 0}</div>
                                            </div>
                                            <div class="text-center">
                                                <small style="font-size: 0.77rem;">Lượt cứu:</small>
                                                <div style="font-size: 0.77rem; font-weight: 600;"><span class="text-danger">${account.rescue_count || 0}</span>-<span class="text-success">${account.rescue_success_count || 0}</span></div>
                                            </div>
                                        </div>` :
                                        `<div class="text-center mt-1">
                                            ${scanCountdown ? `<small style="font-size: 0.7rem;">${scanCountdown}</small>` : ''}
                                        </div>`
                                    }
                                </div>
                            ` : ''}
                            
                            ${noticeHtml}
                            ${tipHtml}
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = cardsHtml;
        window.scrollTo(0, scrollY);
        
        // Áp dụng ring state cho tất cả grid cells
        filteredAccounts.forEach(account => {
            const cell = document.querySelector(`.mxh-item[data-account-id="${account.id}"]`);
            if (cell) {
                paintRing(cell, account);
            }
        });
        
        // GỌI HÀM SETUP SAU KHI RENDER XONG
        setupEditableFields();

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

/**
 * Gán sự kiện cho các trường có thể chỉnh sửa trực tiếp trên card.
 */
function setupEditableFields() {
    const editableFields = document.querySelectorAll('.editable-field');

    editableFields.forEach(field => {
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
                e.target.blur(); // Trigger blur event to save
            }
        });
        
        field.addEventListener('focus', (e) => {
             // Select all text on focus
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

/**
 * Gửi yêu cầu cập nhật nhanh một trường dữ liệu đến server.
 * @param {number} accountId ID của tài khoản
 * @param {string} field Tên trường (e.g., 'username', 'phone')
 * @param {string} value Giá trị mới
 */
async function quickUpdateField(accountId, field, value) {
    try {
        const response = await fetch(`/mxh/api/accounts/${accountId}/quick-update`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ field, value })
        });

        if (response.ok) {
            showToast(`Đã cập nhật ${field === 'username' ? 'tên' : 'SĐT'}!`, 'success');
            // Cập nhật lại dữ liệu local để giao diện đồng bộ
            const accountIndex = mxhAccounts.findIndex(acc => acc.id === accountId);
            if (accountIndex !== -1) {
                mxhAccounts[accountIndex][field] = value;
            }
        } else {
            const error = await response.json();
            showToast(error.error || 'Lỗi khi cập nhật!', 'error');
            await loadMXHData(true); // Tải lại toàn bộ nếu lỗi
        }
    } catch (error) {
        showToast('Lỗi kết nối!', 'error');
        await loadMXHData(true);
    }
}

/**
 * Mở modal và điền thông tin của một tài khoản cụ thể để chỉnh sửa.
 * @param {number} accountId - ID của tài khoản cần chỉnh sửa.
 */
function openAccountModalForEdit(accountId) {
    const account = mxhAccounts.find(acc => acc.id === accountId);
    if (!account) {
        showToast('Không tìm thấy dữ liệu tài khoản!', 'error');
        return;
    }

    // Hiện tại ta dùng chung modal 'wechat-account-modal'
    // Tương lai có thể tạo các modal khác cho từng platform
    const modalEl = document.getElementById('wechat-account-modal');
    if (!modalEl) {
        showToast('Lỗi: Không tìm thấy modal!', 'error');
        return;
    }

    // Điền dữ liệu vào form
    modalEl.querySelector('#wechat-card-name').value = account.card_name || '';
    modalEl.querySelector('#wechat-username').value = account.username || '';
    modalEl.querySelector('#wechat-phone').value = account.phone || '';
    modalEl.querySelector('#wechat-day').value = account.wechat_created_day || '';
    modalEl.querySelector('#wechat-month').value = account.wechat_created_month || '';
    modalEl.querySelector('#wechat-year').value = account.wechat_created_year || '';

    // Xử lý status
    let currentStatus = account.status || 'active';
    if (account.muted_until && new Date(account.muted_until) > new Date()) {
        currentStatus = 'muted';
    }
    modalEl.querySelector('#wechat-status').value = currentStatus;

    // Hiển thị modal
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
        
    // Configure status submenu based on current status (giống 100% MXH_Old)
    const currentStatus = account.status;
    const statusNormalItems = contextMenu.querySelectorAll('.status-normal');
    const statusRescueItems = contextMenu.querySelectorAll('.status-rescue');

    if (currentStatus === 'disabled') {
        // Khi disabled: Ẩn Available/Die/Vô hiệu hóa, hiện Được Cứu/Cứu Thất Bại
        statusNormalItems.forEach(item => item.style.display = 'none');
        statusRescueItems.forEach(item => item.style.display = 'block');
    } else {
        // Khi không disabled: Hiện Available/Die/Vô hiệu hóa, ẩn Được Cứu/Cứu Thất Bại
        statusNormalItems.forEach(item => item.style.display = 'block');
        statusRescueItems.forEach(item => item.style.display = 'none');
    }
        
        // Smart positioning logic
        const menuWidth = 200;
        const menuHeight = 300;
        const buffer = 50;
        
        const mouseX = event.pageX;
        const mouseY = event.pageY;
        const windowWidth = window.innerWidth;
        const windowHeight = window.innerHeight;
        
        let finalX = mouseX;
        let finalY = mouseY;
        
        // Smart X positioning
        if (mouseX < buffer) {
            finalX = mouseX + 20; // Show to the right
        } else if (mouseX > windowWidth - menuWidth - buffer) {
            finalX = mouseX - menuWidth - 20; // Show to the left
        }
        
        // Smart Y positioning
        if (mouseY < buffer) {
            finalY = mouseY + 20; // Show below
        } else if (mouseY > windowHeight - menuHeight - buffer) {
            finalY = mouseY - menuHeight - 20; // Show above
        }
        
        // Position and show menu with smooth animation
        contextMenu.style.display = 'block';
        contextMenu.style.left = finalX + 'px';
        contextMenu.style.top = finalY + 'px';
        contextMenu.style.opacity = '0';
        contextMenu.style.transform = 'scale(0.8)';
        
        // Smooth fade in animation
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
    
    // Smooth fade out animation
    contextMenu.style.transition = 'opacity 0.15s ease, transform 0.15s ease';
    contextMenu.style.opacity = '0';
    contextMenu.style.transform = 'scale(0.9)';
    
    // Hide after animation completes
    setTimeout(() => {
        contextMenu.style.display = 'none';
        contextMenu.style.transition = '';
        contextMenu.style.opacity = '';
        contextMenu.style.transform = '';
    }, 150);
    
    resumeAutoRefresh();
}

// Handle Card Context Menu - Use Unified Menu with Flip Card Integration
window.handleCardContextMenu = function (event, accountId, platform) {
    event.preventDefault();
    event.stopPropagation();
    
    // Lấy card_id từ account để sử dụng cho flip logic
    const account = mxhAccounts.find(acc => acc.id === accountId);
    const cardId = account?.card_id || accountId; // fallback to accountId if no card_id
    
    // Tích hợp flip card logic vào context menu
    showUnifiedContextMenuWithFlip(event, accountId, platform, cardId);
}

// Enhanced context menu with flip card integration
function showUnifiedContextMenuWithFlip(event, accountId, platform, cardId) {
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
        
    // Configure status submenu based on current status (giống 100% MXH_Old)
    const currentStatus = account.status;
    const statusNormalItems = contextMenu.querySelectorAll('.status-normal');
    const statusRescueItems = contextMenu.querySelectorAll('.status-rescue');

    if (currentStatus === 'disabled') {
        // Khi disabled: Ẩn Available/Die/Vô hiệu hóa, hiện Được Cứu/Cứu Thất Bại
        statusNormalItems.forEach(item => item.style.display = 'none');
        statusRescueItems.forEach(item => item.style.display = 'block');
    } else {
        // Khi không disabled: Hiện Available/Die/Vô hiệu hóa, ẩn Được Cứu/Cứu Thất Bại
        statusNormalItems.forEach(item => item.style.display = 'block');
        statusRescueItems.forEach(item => item.style.display = 'none');
    }

    // ===== FLIP CARD INTEGRATION =====
    // Tạo submenu "Tài khoản" với flip logic
    const accountsSubmenu = contextMenu.querySelector('#accounts-submenu');
    if (accountsSubmenu) {
        // Khởi tạo flip skeleton nếu chưa có
        const st = _readPrimaryFromDOM(cardId);
        
        // Xóa nội dung cũ
        accountsSubmenu.innerHTML = '';
        
        // Thêm các tài khoản hiện có
        st.accounts.forEach(acc => {
            const isActive = acc.id === st.activeId;
            const item = document.createElement('div');
            item.className = 'menu-item';
            item.dataset.ctx = 'switchAccount';
            item.dataset.cardId = cardId;
            item.dataset.accountId = acc.id;
            item.innerHTML = `
                <i class="bi bi-person me-2"></i> 
                ${acc.label}${isActive ? ' ✓' : ''}
            `;
            accountsSubmenu.appendChild(item);
        });
        
        // Bỏ separator để tránh khoảng trống "ảo" trong dark theme
        
        // Thêm nút "Thêm Tài Khoản"
        const addItem = document.createElement('div');
        addItem.className = 'menu-item';
        addItem.dataset.ctx = 'addAccount';
        addItem.dataset.cardId = cardId;
        addItem.innerHTML = '<i class="bi bi-plus-circle me-2"></i> Thêm Tài Khoản';
        accountsSubmenu.appendChild(addItem);
    }
        
    // Smart positioning logic
    const menuWidth = 200;
    const menuHeight = 300;
    const buffer = 50;
    
    const mouseX = event.pageX;
    const mouseY = event.pageY;
    const windowWidth = window.innerWidth;
    const windowHeight = window.innerHeight;
    
    let finalX = mouseX;
    let finalY = mouseY;
    
    // Smart X positioning
    if (mouseX < buffer) {
        finalX = mouseX + 20; // Show to the right
    } else if (mouseX > windowWidth - menuWidth - buffer) {
        finalX = mouseX - menuWidth - 20; // Show to the left
    }
    
    // Smart Y positioning
    if (mouseY < buffer) {
        finalY = mouseY + 20; // Show below
    } else if (mouseY > windowHeight - menuHeight - buffer) {
        finalY = mouseY - menuHeight - 20; // Show above
    }
    
    // Position and show menu with smooth animation
    contextMenu.style.display = 'block';
    contextMenu.style.left = finalX + 'px';
    contextMenu.style.top = finalY + 'px';
    contextMenu.style.opacity = '0';
    contextMenu.style.transform = 'scale(0.8)';
    
    // Smooth fade in animation
    setTimeout(() => {
        contextMenu.style.transition = 'opacity 0.2s ease, transform 0.2s ease';
        contextMenu.style.opacity = '1';
        contextMenu.style.transform = 'scale(1)';
    }, 10);
    
    setTimeout(() => {
        document.addEventListener('click', hideUnifiedContextMenu, { once: true });
    }, 100);
}

// Event delegation cho context menu items (cũ - giữ để tương thích)
document.addEventListener('pointerdown', function(e) {
    const el = e.target.closest('.menu-item[data-ctx-type]');
    if (!el) return;

    const type = el.dataset.ctxType;
    const cardId = +el.dataset.cardId || 0;
    const accountId = el.dataset.accountId || null;

    e.preventDefault();
    e.stopPropagation();

    if (type === 'addAccount') {
        MXH.addSubAccount(cardId);
        hideUnifiedContextMenu();
        return;
    }
    
    if (type === 'switchAccount') {
        MXH.switchAccount(cardId, accountId);
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
            
            // Auto reload trang nhưng giữ vị trí đang xem
            setTimeout(() => {
                window.location.reload();
            }, 1000); // Delay 1 giây để user thấy toast
        } else {
            const error = await response.json();
            showToast(error.error || 'Lỗi đổi số hiệu', 'error');
        }
    } catch (error) {
        console.error('Error changing number:', error);
        showToast('Lỗi kết nối', 'error');
    }
}

// Global function for modal button
window.submitChangeNumber = submitChangeNumber;

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
    
    // ===== SUBMENU LOGIC (from MXH_Old) =====
    let currentSubmenu = null;
    let hideTimeout = null;
    
    // Function to show submenu
    function showSubmenu(menuItem) {
        // Hide current submenu if different
        if (currentSubmenu && currentSubmenu !== menuItem) {
            const currentSubmenuEl = currentSubmenu.querySelector('.submenu');
            if (currentSubmenuEl) {
                currentSubmenuEl.classList.remove('show');
            }
        }
        
        // Show new submenu
        const submenuEl = menuItem.querySelector('.submenu');
        if (submenuEl) {
            submenuEl.classList.add('show');
            currentSubmenu = menuItem;
        }
        
        // Clear any pending hide timeout
        if (hideTimeout) {
            clearTimeout(hideTimeout);
            hideTimeout = null;
        }
    }
    
    // Function to hide submenu with delay
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
    
    // Enhanced submenu hover handling
    document.addEventListener('mouseover', function(event) {
        const menuItem = event.target.closest('.menu-item.has-submenu');
        const submenu = event.target.closest('.submenu');
        
        if (menuItem) {
            showSubmenu(menuItem);
        } else if (submenu) {
            // Keep submenu open when hovering over submenu
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
            // Hide submenu when leaving all related elements
            hideSubmenu();
        }
    });

    // ===== EVENT LISTENERS =====
document.addEventListener('DOMContentLoaded', function() {
  // Khởi tạo và áp dụng ngay Chế Độ Xem
  initializeViewMode();
  applyViewMode(localStorage.getItem('mxh_cards_per_row') || 12);

  // Tải dữ liệu và bắt đầu auto-refresh
  loadMXHData(true);
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
                // GỌI HÀM MỚI TẠI ĐÂY
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
            case 'change-number':
                changeCardNumber(e);
                break;
            case 'delete':
                // Lấy card_id từ account hiện tại
                const account = mxhAccounts.find(acc => acc.id === currentContextAccountId);
                if (account && account.card_id) {
                    handleDeleteCard(account.card_id);
                } else {
                    showToast('Không tìm thấy card để xóa', 'error');
                }
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
    
    // === THÊM EVENT LISTENER CHO NÚT RESET TRONG MODAL THÔNG TIN ===
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

    // === THÊM EVENT LISTENER CHO NÚT APPLY TRONG MODAL THÔNG TIN ===
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

        // Thu thập dữ liệu từ modal
        const newCardName = modalEl.querySelector('#wechat-card-name').value;
        const payload = {
            card_name: newCardName,
            username: modalEl.querySelector('#wechat-username').value,
            phone: modalEl.querySelector('#wechat-phone').value,
            wechat_created_day: parseInt(modalEl.querySelector('#wechat-day').value) || null,
            wechat_created_month: parseInt(modalEl.querySelector('#wechat-month').value) || null,
            wechat_created_year: parseInt(modalEl.querySelector('#wechat-year').value) || null,
        };
        
        // Kiểm tra nếu có thay đổi số card
        const cardNameChanged = originalAccount.card_name !== newCardName;

        // Xử lý logic trạng thái phức tạp giống hệt file MXH_Old
        if (selectedStatus === 'muted') {
            const muteUntilDate = new Date();
            muteUntilDate.setDate(muteUntilDate.getDate() + 30);
            payload.muted_until = muteUntilDate.toISOString();
            payload.status = originalAccount.status; // Giữ status cũ khi mute
            payload.wechat_status = originalAccount.wechat_status; // Giữ wechat_status cũ khi mute
        } else {
            payload.muted_until = null; // Gỡ mute
            // Mapping status
            // Đồng bộ hóa 'status' và 'wechat_status' một cách nhất quán
            if (selectedStatus === 'available') {
                payload.status = 'active'; // Ánh xạ 'available' của UI thành 'active' của DB
            } else {
                payload.status = selectedStatus; // Sử dụng trực tiếp các giá trị khác: 'die', 'disabled', 'muted'
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
                
                // Nếu có thay đổi số card thì auto reload trang
                if (cardNameChanged) {
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000); // Delay 1 giây để user thấy toast
                } else {
                    await loadMXHData(true); // Tải lại toàn bộ dữ liệu để đảm bảo đồng bộ
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
    
    // Hide all context menus on regular click
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
    if (typeof v === 'number') return new Date(v > 1e12 ? v : v * 1000); // ms hoặc s
    if (typeof v === 'string') {
        const s = v.trim();
        // Ưu tiên ISO (YYYY-MM-DD hoặc có time)
        if (/^\d{4}[-/]\d{1,2}[-/]\d{1,2}/.test(s)) return new Date(s.replace(/-/g, '/'));
        // dd/mm/yyyy hoặc dd-mm-yyyy
        const m = s.match(/^(\d{1,2})[\/-](\d{1,2})[\/-](\d{2,4})/);
        if (m) { const d = +m[1], mo = +m[2] - 1, y = (+m[3] < 100 ? 2000 + +m[3] : +m[3]); return new Date(y, mo, d); }
        const t = Date.parse(s); if (!isNaN(t)) return new Date(t);
    }
    return null;
}

function resolveState(acc) {
    const s = String(acc?.status ?? acc?.state ?? '').toLowerCase();
    const isDie = s === 'die' || s === 'dead' || s === 'banned' || acc?.is_die === true;
    const isDisabled = ['disabled', 'inactive', 'deactivated', 'locked', 'suspended'].includes(s) || acc?.is_disabled === true;
    const created = acc?.created_at ?? acc?.account_created_at ?? acc?.wechat_created_at;
    const dt = created ? new Date(created) : null;
    const gt1y = dt ? (Date.now() - dt.getTime()) >= 365 * 24 * 60 * 60 * 1000 : false;
    
    if (isDie) return 'die';
    if (isDisabled) return 'disabled';
    if (gt1y) return '1y';
    return 'default';
}

function paintRing(gridCellEl, acc) {
    const map = { die: '#FF3B30', disabled: '#FF8F00', '1y': '#07C160', default: '#D1D5DB' };
    gridCellEl.style.setProperty('--mxh-ring', map[resolveState(acc)]);
}

function onAccountUpdated(account) {
    const cell = document.querySelector(`.mxh-item[data-account-id="${account.id}"]`);
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
            
            // Cập nhật ring ngay lập tức
            const account = mxhAccounts.find(acc => acc.id === currentContextAccountId);
            if (account) {
                // Đồng bộ logic mapping với modal
                if (status === 'available') {
                    account.status = 'active'; // Ánh xạ 'available' của UI thành 'active' của DB
                } else {
                    account.status = status; // Sử dụng trực tiếp: 'die', 'disabled', 'muted'
                }
                const cell = document.querySelector(`.mxh-item[data-account-id="${currentContextAccountId}"]`);
                if (cell) {
                    paintRing(cell, account);
                }
            }
            
            await loadMXHData(true); // Reload data to reflect changes
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
            await loadMXHData(true); // Reload data to reflect changes
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

    // ===== NOTICE MANAGEMENT (from MXH_Old) =====
let noticeTargetId = null;

// Helper functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function ensureNoticeParsed(notice) {
    let n = (typeof notice === 'string') ? (() => { try { return JSON.parse(notice) } catch { return {} } })() : (notice || {});
    if (n && n.start_at) n.start_at = normalizeISOForJS(n.start_at);
    return n;
}

function normalizeISOForJS(iso) {
    let s = iso;
    if (s.includes('+')) s = s.split('+')[0];
    if (s.includes('Z')) s = s.replace('Z', '');
    s = s.replace(/(\.\d{3})\d+/, '$1');
    return s;
}

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

            // Update local data immediately
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
            
            // Update local data immediately
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

function changeCardNumber(e) {
    showToast('Chức năng đang phát triển', 'info');
}

function showDeleteConfirm(e) {
    // Function này không còn được sử dụng, logic đã chuyển vào case 'delete'
    showToast('Chức năng đang phát triển', 'info');
}

function switchToAccount(accountIndex) {
    showToast('Chức năng đang phát triển', 'info');
}

function addNewAccount() {
    showToast('Chức năng đang phát triển', 'info');
}

// ===== CARD DELETE FUNCTIONALITY =====

// API helpers
async function apiGetAccountCount(cardId) {
    const res = await fetch(`/mxh/api/cards/${cardId}/account-count`, { credentials: "same-origin" });
    if (!res.ok) throw new Error(await res.text());
    return res.json(); // { card_id, account_count }
}

async function apiDeleteCard(cardId, force = false) {
    const url = `/mxh/api/cards/${cardId}` + (force ? `?force=true` : ``);
    const res = await fetch(url, { method: "DELETE", credentials: "same-origin" });
    if (res.status === 409) {
        return { requires_confirmation: true, ...(await res.json()) }; // {requires_confirmation, account_count, message}
    }
    if (!res.ok) throw new Error(await res.text());
    return res.json(); // {deleted_card_id, deleted_accounts, ok:true}
}

// Reusable Dashboard Confirm Modal
// Trả về Promise<boolean> => true khi OK, false khi Cancel
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

// UI helper: xóa card khỏi DOM
function removeCardFromDOM(cardId) {
    const card = document.getElementById(`card-${cardId}`);
    // card có thể nằm trong .mxh-item
    const container = card?.closest(".mxh-item") || card;
    if (container) container.remove();
}

// Toast helpers (chỉ dùng toast system có sẵn, không fallback alert)
function toastSuccess(msg){ 
    if (typeof showToast === 'function') {
        showToast(msg, 'success');
    }
    // Không fallback alert để tránh browser popup
}
function toastError(msg){ 
    if (typeof showToast === 'function') {
        showToast(msg, 'error');
    }
    // Không fallback alert để tránh browser popup
}

// Action: Delete Card flow
let _deleteBusy = new Set(); // tránh double click
async function handleDeleteCard(cardId) {
    if (_deleteBusy.has(cardId)) return;
    _deleteBusy.add(cardId);

    try {
        // 1) Hỏi BE số lượng account để hiển thị modal phù hợp
        const { account_count } = await apiGetAccountCount(cardId);

        // 2) Tạo nội dung modal
        const title = "Xóa Card";
        const html = (account_count > 1)
            ? `Card này đang có: <b>${account_count}</b> tài khoản phụ.<br>Bạn chắc chắn muốn xóa?`
            : `Bạn chắc chắn muốn xóa card này?`;

        // 3) Hiện modal xác nhận
        const ok = await showConfirmModal({ title, html, okText: "Xóa", cancelText: "Hủy" });
        if (!ok) return;

        // 4) Gọi API xóa (force=true để bỏ qua confirm phía BE)
        const res = await apiDeleteCard(cardId, true);

        // 5) Cập nhật UI
        removeCardFromDOM(cardId);
        toastSuccess(`Đã xóa card #${cardId}` + (res.deleted_accounts ? ` cùng ${res.deleted_accounts} tài khoản` : ""));
        
        // 6) Đóng modal sau khi xóa thành công
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

// Event delegation: nút xóa card
// Thêm attribute data-action="delete-card" data-card-id="..."
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

// Export functions for global access
window.handleDeleteCard = handleDeleteCard;
window.showConfirmModal = showConfirmModal;

// ====== FLIP 3D CARD LOGIC - MULTIPLE ACCOUNTS ======

// ===== Flip core, LITE & LAZY =====
window.MXH = window.MXH || {};
MXH.cards = MXH.cards || new Map(); // Map<cardId,{accounts:[{id,label,createdAt,fields}],activeId}>

const _uuid = ()=>crypto?.randomUUID?.()||('acc_'+Math.random().toString(36).slice(2));
const _nowISO = ()=>new Date().toISOString();
const _fmtVN  = iso=>new Date(iso).toLocaleDateString('vi-VN',{day:'2-digit',month:'2-digit',year:'numeric'});

const _SEL = {
  username: ['[data-field="username"]','.mxh-username','.username','.user'],
  phone:    ['[data-field="phone"]','.mxh-phone','.phone','.tel'],
  created:  ['[data-field="createdAt"]','.mxh-created','.created-at']
};
const _q = (root, sels)=>sels.map(s=>root.querySelector(s)).find(Boolean)||null;

function _getCard(cardId){ if(!MXH.cards.has(cardId)) MXH.cards.set(cardId,{accounts:[],activeId:null}); return MXH.cards.get(cardId); }
function _active(st){ return st.accounts.find(a=>a.id===st.activeId)||null; }

// Lấy TK1 từ DOM, NHƯNG chỉ khi cần
function _readPrimaryFromDOM(cardId){
  const st=_getCard(cardId);
  if (st.accounts.length) return st;
  const root=document.getElementById(`card-${cardId}`); if(!root) return st;
  const uEl=_q(root,_SEL.username), pEl=_q(root,_SEL.phone);
  const acc1={ id:_uuid(), label:'Tài Khoản 1', createdAt:_nowISO(), fields:{username:uEl?.textContent?.trim()||'', phone:pEl?.textContent?.trim()||''}};
  st.accounts=[acc1]; st.activeId=acc1.id;
  return st;
}

// Chỉ tạo skeleton khi THÊM/SWITCH
function _ensureFlipSkeleton(cardId){
  const cardEl=document.getElementById(`card-${cardId}`); if(!cardEl) return null;
  if (cardEl.querySelector('.mxh-card-inner')) return cardEl;        // đã có
  const body=cardEl.querySelector('.card-body')||cardEl;

  // Khóa chiều cao hiện tại để tránh kéo dài
  const h=Math.max(120, Math.round(body.getBoundingClientRect().height));
  const inner=document.createElement('div'); inner.className='mxh-card-inner'; inner.style.height=`${h}px`;

  // Mặt A = giữ NGUYÊN giao diện hiện có
  const faceA=document.createElement('div'); faceA.className='mxh-card-face face-a';
  while (body.firstChild) faceA.appendChild(body.firstChild);

  // Mặt B = clone cấu trúc A để có cùng vị trí field
  const faceB=document.createElement('div'); faceB.className='mxh-card-face face-b';
  faceB.innerHTML=faceA.innerHTML; faceB.querySelectorAll('[id]').forEach(n=>n.removeAttribute('id'));

  inner.append(faceA,faceB); body.appendChild(inner);
  cardEl.dataset.front='a';
  return cardEl;
}
function _face(cardId,which){ const el=document.getElementById(`card-${cardId}`); return el?.querySelector(`.mxh-card-face.face-${which}`)||null; }
function _setFields(faceEl, acc){
  if(!faceEl||!acc) return;
  const u=_q(faceEl,_SEL.username), p=_q(faceEl,_SEL.phone), c=_q(faceEl,_SEL.created);
  if(u) u.textContent = acc.fields?.username ?? '.';
  if(p) p.textContent = acc.fields?.phone ?? '.';
  if(c) c.textContent = `Ngày tạo: ${_fmtVN(acc.createdAt)}`;
}
function _flipTo(cardId, acc){
  const cardEl=_ensureFlipSkeleton(cardId); if(!cardEl) return;
  const front=(cardEl.dataset.front==='b')?'b':'a';
  const back =(front==='a')?'b':'a';
  _setFields(_face(cardId, back), acc);
  if (back==='b') cardEl.classList.add('is-flipped'); else cardEl.classList.remove('is-flipped');
  cardEl.dataset.front=back;
  _getCard(cardId).activeId=acc.id;
}

// === API Helper ===
async function postJSON(url, payload) {
  const res = await fetch(url, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(payload ?? {})
  });
  let data = null;
  try { data = await res.json(); } catch (_) {}
  if (!res.ok) {
    const msg = (data && (data.message || data.error)) || `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return data;
}

async function createSubAccount(cardId) {
  const res = await fetch(`/mxh/api/cards/${cardId}/accounts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      platform: "wechat",
      username: ".",   // <- yêu cầu Sếp
      phone: "."       // <- yêu cầu Sếp
    })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.message || data.error || `HTTP ${res.status}`);
  return data.account;
}

function setActiveAccount(cardId, accountId) {
  const cardEl = document.getElementById(`card-${cardId}`);
  if (cardEl) {
    cardEl.dataset.activeAccountId = accountId;
  }
  // Cập nhật state
  const st = _getCard(cardId);
  st.activeId = accountId;
}

// === Actions ===
MXH.addSubAccount = async (cardId)=>{
  const st=_readPrimaryFromDOM(cardId);
  
  try {
    const acc = await createSubAccount(cardId);
    
    // Tạo account object từ response
    const accountObj = {
      id: String(acc.id),
      label: acc.label,
      createdAt: acc.created_at,
      fields: { 
        username: acc.username || '.', 
        phone: acc.phone || '.' 
      }
    };
    
    st.accounts.push(accountObj);
    setActiveAccount(cardId, accountObj.id);
    _flipTo(cardId, accountObj);
    
    // Cập nhật lại context menu
    generateAccountsSubmenu(cardId);
    
    window.showToast?.('Đã tạo tài khoản phụ','success');
  } catch (err) {
    if (err instanceof TypeError) {
      // network/offline
      window.showToast?.('API không phản hồi (mất kết nối)','warning');
    } else {
      // lỗi hợp lệ từ server (400/422/500...)
      window.showToast?.(`Tạo tài khoản phụ thất bại: ${err.message}`,'error');
    }
  }
};

MXH.switchAccount = (cardId, accountId)=>{
  const st=_readPrimaryFromDOM(cardId);
  const acc=st.accounts.find(a=>a.id==accountId); if(!acc) return;
  _flipTo(cardId, acc);
};

// Submenu không "nuốt click", không separator "trống"
window.generateAccountsSubmenu = (cardId)=>{
  const st=_readPrimaryFromDOM(cardId);
  const items = st.accounts.map(a=>({
    type:'item',
    label:`${a.label}${a.id===st.activeId?' ✓':''}`,
    // để renderer đổ ra: data-ctx="switchAccount" data-card-id=".." data-account-id=".."
    data:{ctx:'switchAccount', cardId, accountId:a.id}
  }));
  items.push({ type:'item', label:'Thêm Tài Khoản', data:{ctx:'addAccount', cardId} });
  return items;
};

// Bắt 1 lần – an toàn trên mọi renderer
document.addEventListener('pointerdown', (e)=>{
  const n=e.target.closest('[data-ctx]'); if(!n) return;
  const {ctx, cardId, accountId}=n.dataset;
  if (ctx==='addAccount'){ 
    e.preventDefault(); 
    MXH.addSubAccount(+cardId); 
    window.hideContextMenu?.(); 
  }
  if (ctx==='switchAccount'){ 
    e.preventDefault(); 
    MXH.switchAccount(+cardId, accountId); 
    window.hideContextMenu?.(); 
  }
});