// MXH Module - Complete Implementation with Original UI/UX
document.addEventListener('DOMContentLoaded', function() {
    console.log('MXH module loaded - Complete implementation ready');

    // Global state
    let mxhGroups = [];
    let mxhCards = [];
    let currentContextCardId = null;
    let currentContextAccountId = null;
    let activeGroupId = 'all';
    let isRendering = false;
    let pendingUpdates = false;
    
    // Configuration
    const MXH_CONFIG = {
        AUTO_REFRESH_INTERVAL: 15000,
        DEBOUNCE_DELAY: 800,
        RENDER_BATCH_SIZE: 50,
    };
    
    // ===== HELPER FUNCTIONS =====
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

    // Global flip card function
    window.flipCard = function (el, event) {
        if (event) { event.preventDefault(); event.stopPropagation(); }
        const wrap = el.closest('.mxh-card-container');
        if (wrap) wrap.classList.toggle('flipped');
    };

    // ===== CORE DATA LOADING =====
    async function loadMXHData(forceRender = true) {
        try {
            // Load groups and cards in parallel
            const [groupsResponse, cardsResponse] = await Promise.all([
                fetch('/mxh/api/groups'),
                fetch('/mxh/api/cards')
            ]);
            
            if (groupsResponse.ok) {
                mxhGroups = await groupsResponse.json();
                renderGroupsNav();
            }
            
            if (cardsResponse.ok) {
                mxhCards = await cardsResponse.json();
                if (forceRender) {
                    renderMXHAccounts();
                }
            }
            
            updateNavBadge();

        } catch (error) {
            console.error('Error loading MXH data:', error);
            showToast('Lỗi tải dữ liệu!', 'error');
        }
    }
    
    // ===== RENDERING FUNCTIONS =====
    function renderGroupsNav() {
        const container = document.getElementById('mxh-groups-nav');
        if (!container) return;

        // Calculate counts for each group
        const counts = {};
        mxhCards.forEach(card => {
            const groupId = card.group_id;
            if (!counts[groupId]) {
                counts[groupId] = { total: 0, notice: 0 };
            }
            counts[groupId].total += card.sub_accounts ? card.sub_accounts.length : 0;
            
            // Count notices
            if (card.sub_accounts) {
                card.sub_accounts.forEach(account => {
            if (account.notice && (!account.muted_until || new Date(account.muted_until) < new Date())) {
                        counts[groupId].notice++;
                    }
                });
            }
        });
        
        // Calculate total counts
        const totalCounts = Object.values(counts).reduce((acc, val) => {
            acc.total += val.total;
            acc.notice += val.notice;
            return acc;
        }, { total: 0, notice: 0 });

        let html = `<button class="btn btn-sm ${activeGroupId === 'all' ? 'btn-primary' : 'btn-outline-primary'}" onclick="selectGroup('all')">
            Tất cả <span class="badge bg-secondary ms-1">${totalCounts.total}</span>
        </button>`;

        mxhGroups.forEach(group => {
            const groupCounts = counts[group.id] || { total: 0, notice: 0 };
            const isActive = activeGroupId === group.id;
            html += `<button class="btn btn-sm ${isActive ? 'btn-primary' : 'btn-outline-primary'}" onclick="selectGroup(${group.id})">
                ${group.name} <span class="badge bg-secondary ms-1">${groupCounts.total}</span>
                ${groupCounts.notice > 0 ? `<span class="badge bg-danger ms-1">${groupCounts.notice}</span>` : ''}
            </button>`;
        });
        
        container.innerHTML = html;
    }

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

        if (mxhCards.length === 0) {
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

        // Filter cards based on active group
        const filteredCards = activeGroupId === 'all'
            ? mxhCards 
            : mxhCards.filter(card => card.group_id === activeGroupId);

        if (filteredCards.length === 0) {
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

        // Sort cards by name
        filteredCards.sort((a, b) => {
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

        // Group cards by group_id
        const cardsByGroup = {};
            filteredCards.forEach(card => {
            const groupId = card.group_id || 'no-group';
            if (!cardsByGroup[groupId]) {
                cardsByGroup[groupId] = [];
            }
            cardsByGroup[groupId].push(card);
        });

        Object.keys(cardsByGroup).forEach(groupId => {
            const cards = cardsByGroup[groupId];
            const group = mxhGroups.find(g => g.id == groupId);

            if (group) {
                const cardsContainerId = `cards-${groupId}`;

                // Render cards container
                html += `
                <div class="mb-4">
                    <div class="row g-2" id="${cardsContainerId}">
                `;

                cards.forEach(card => {
                    // Find primary account (is_primary = 1) or first account
                    const primaryAccount = card.sub_accounts ? 
                        card.sub_accounts.find(acc => acc.is_primary === 1) || card.sub_accounts[0] : 
                        null;
                    
                    if (primaryAccount) {
                        // Combine card and account data for rendering
                        const combinedData = {
                            ...card,
                            ...primaryAccount,
                            // Override with account data
                            username: primaryAccount.username,
                            phone: primaryAccount.phone,
                            status: primaryAccount.status,
                            wechat_status: primaryAccount.wechat_status,
                            notice: primaryAccount.notice
                        };
                        
                        html += renderAccountCard(combinedData);
                    }
                });

                html += `
                    </div>
                </div>
                `;
            }
        });

        tempDiv.innerHTML = html;
        while (tempDiv.firstChild) {
            fragment.appendChild(tempDiv.firstChild);
        }

        container.innerHTML = '';
        container.appendChild(fragment);

        // Restore scroll position
        window.scrollTo(scrollX, scrollY);

        // Initialize tooltips
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });

        isRendering = false;
        if (pendingUpdates) {
            pendingUpdates = false;
            renderMXHAccounts();
        }
    }

    function renderAccountCard(account) {
        const now = new Date();
        const isDisabled = account.status === 'disabled';
        let isAnniversary = false;

        // Calculate age for WeChat primary with color
        let accountAgeDisplay = '';
        let ageColor = '#fff';
        let scanCountdown = '';

        if (account.platform === 'wechat' && account.wechat_created_year) {
            const createdDate = new Date(account.wechat_created_year, account.wechat_created_month - 1, account.wechat_created_day);
            const diffDays = Math.ceil((now - createdDate) / (1000 * 60 * 60 * 24));

            if (diffDays >= 365) {
                const years = Math.floor(diffDays / 365);
                const months = Math.floor((diffDays % 365) / 30);
                accountAgeDisplay = `${years}năm ${months}th`;
                ageColor = '#07c160';
                isAnniversary = true;
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
        const isNoticeExpired = hasNotice && notice.end_at && new Date(notice.end_at) < now;
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
                if (isAnniversary) {
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

        // Account switcher icons if multiple accounts
        const accountIcons = account.sub_accounts && account.sub_accounts.length > 1 
            ? `<div class="account-switcher-icons">${account.sub_accounts.map(acc => 
                `<i class="bi ${getPlatformIconClass(acc.platform || account.platform)} ${acc.id === account.id ? 'active' : ''}" 
                     onclick="switchToAccount(${account.id}, ${acc.id})" title="${acc.account_name || 'Account'}"></i>`
            ).join('')}</div>`
            : '';

        return `
            <div class="col" id="card-wrapper-${account.id}">
                <div class="mxh-card-container" onclick="handleCardClick(event, ${account.id})">
                    <div class="mxh-card-inner">
                        <div class="mxh-card-front">
                            <div class="card mxh-card ${borderClass}" id="card-${account.id}">
                    <div class="card-body">
                                    <div class="d-flex justify-content-between align-items-center mb-2">
                                        <h6 class="card-title mb-0 card-number">${account.card_name}</h6>
                                        <div class="d-flex align-items-center">
                                            <span class="badge ${statusClass}">${statusIcon}${account.status || 'active'}</span>
                                        </div>
                                    </div>
                                    
                                    <div class="mxh-card-icon" style="background-color: ${getPlatformColor(account.platform)}">
                                        <i class="${getPlatformIconClass(account.platform)}"></i>
                                    </div>
                                    
                                    <p class="card-text mb-1" style="font-size: 0.9rem; font-weight: 500;">
                                        ${escapeHtml(account.username || 'N/A')}
                                    </p>
                                    
                                    <p class="card-text mb-1 phone-line" style="font-size: 0.8rem; color: #ccc;">
                                        📞 ${escapeHtml(account.phone || 'N/A')}
                                    </p>
                                    
                                    ${account.platform === 'wechat' && accountAgeDisplay ? `
                                    <p class="card-text small" style="color: ${ageColor}; font-weight: 600;">
                                        <i class="bi bi-calendar-check me-1"></i>${accountAgeDisplay}
                                        ${scanCountdown ? `<span class="ms-2">${scanCountdown}</span>` : ''}
                        </p>
                        ` : ''}
                                    
                                    ${hasNotice ? `
                                    <div class="notice-line ${noticeClass}">
                                        <i class="bi bi-bell-fill me-1"></i>${noticeText}
                        </div>
                        ` : ''}
                                    
                                    ${accountIcons}
                                </div>
                            </div>
                        </div>
                        
                        <div class="mxh-card-back">
                            <div class="card mxh-card ${borderClass}">
                                <div class="card-body">
                                    <h6 class="card-title">Back of Card</h6>
                                    <p class="card-text">Additional info here</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // ===== CONTEXT MENU =====
    function handleCardContextMenu(event, cardId, accountId) {
        event.preventDefault();
        event.stopPropagation();

        currentContextCardId = cardId;
        currentContextAccountId = accountId;

        const card = mxhCards.find(c => c.id === cardId);
        const account = card.sub_accounts ? card.sub_accounts.find(a => a.id === accountId) : null;
        
        if (!card || !account) return;

        showUnifiedContextMenu(event, card, account);
    }

    function showUnifiedContextMenu(event, card, account) {
        const contextMenu = document.getElementById('unified-context-menu');
        if (!contextMenu) return;
        
        // Clear previous content
        const accountsSubmenu = document.getElementById('accounts-submenu');
        if (accountsSubmenu) {
            accountsSubmenu.innerHTML = '';
        }
        
        // Populate accounts submenu if multiple accounts
        if (card.sub_accounts && card.sub_accounts.length > 1) {
            card.sub_accounts.forEach(acc => {
                const menuItem = document.createElement('div');
                menuItem.className = `menu-item ${acc.id === account.id ? 'disabled' : ''}`;
                menuItem.setAttribute('data-action', 'switch-account');
                menuItem.setAttribute('data-account-id', acc.id);
                menuItem.innerHTML = `
                    <i class="bi ${getPlatformIconClass(acc.platform || card.platform)} me-2"></i>
                    ${acc.account_name || `Account #${acc.id}`}
                    ${acc.id === account.id ? '<i class="bi bi-check-lg float-end"></i>' : ''}
                `;
                accountsSubmenu.appendChild(menuItem);
            });
        }
        
        // Show/hide platform-specific items
        const scanOptionsItem = document.getElementById('scan-options-item');
        if (scanOptionsItem) {
            scanOptionsItem.style.display = card.platform === 'wechat' ? 'block' : 'none';
        }
        
        // Position and show menu
        contextMenu.style.display = 'block';
        contextMenu.style.visibility = 'hidden';
        
        setTimeout(() => {
            const menuRect = contextMenu.getBoundingClientRect();
            let left = event.pageX;
            let top = event.pageY;
            
            if (left + menuRect.width > window.innerWidth) {
                left = window.innerWidth - menuRect.width - 10;
            }
            if (top + menuRect.height > window.innerHeight) {
                top = window.innerHeight - menuRect.height - 10;
            }
            
            contextMenu.style.left = `${left}px`;
            contextMenu.style.top = `${top}px`;
            contextMenu.style.visibility = 'visible';
        }, 10);
    }

    // ===== UTILITY FUNCTIONS =====
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
    
    function updateNavBadge() {
        const noticeCount = mxhCards.reduce((count, card) => {
            if (!card.sub_accounts) return count;
            return count + card.sub_accounts.filter(acc => 
                acc.notice && (!acc.muted_until || new Date(acc.muted_until) < new Date())
            ).length;
        }, 0);
        
        const navBadge = document.getElementById('mxh-nav-badge');
        if (navBadge) {
            if (noticeCount > 0) {
                navBadge.textContent = noticeCount;
                navBadge.style.display = 'inline-block';
        } else {
                navBadge.style.display = 'none';
            }
        }
    }
    
    // ===== GLOBAL FUNCTIONS (called from HTML) =====
    window.selectGroup = function(groupId) {
        activeGroupId = groupId;
        renderGroupsNav();
        renderMXHAccounts();
    };
    
    window.switchToAccount = function(cardId, accountId) {
        const card = mxhCards.find(c => c.id === cardId);
        if (!card) return;
        
        const account = card.sub_accounts ? card.sub_accounts.find(a => a.id === accountId) : null;
        if (!account) return;
        
        // Re-render the card with the new account
        renderMXHAccounts();
    };
    
    window.handleCardClick = function(event, accountId) {
        event.preventDefault();
        event.stopPropagation();
        // Handle card click - could open edit modal or flip card
        console.log('Card clicked:', accountId);
    };
    
    window.handleCardContextMenu = handleCardContextMenu;
    
    // ===== EVENT LISTENERS =====
    
    // Context menu event listeners
    document.getElementById('unified-context-menu').addEventListener('click', async (e) => {
        const menuItem = e.target.closest('.menu-item');
        if (!menuItem) return;
        
        e.preventDefault();
        e.stopPropagation();
        
        const action = menuItem.dataset.action;
        if (!action) return;

        switch (action) {
            case 'switch-account':
                const accountId = parseInt(menuItem.dataset.accountId);
                switchToAccount(currentContextCardId, accountId);
                break;
            case 'edit':
                showToast('Chức năng đang phát triển', 'info');
                break;
            case 'delete':
                if (confirm('Bạn có chắc muốn xóa card này?')) {
                    showToast('Chức năng đang phát triển', 'info');
                }
                break;
            default:
                showToast('Chức năng đang phát triển', 'info');
        }
        
        document.getElementById('unified-context-menu').style.display = 'none';
    });
    
    // Hide context menu on click outside
    document.addEventListener('click', function (event) {
        if (!event.target.closest('.custom-context-menu')) {
            document.querySelectorAll('.custom-context-menu').forEach(menu => {
                menu.style.display = 'none';
            });
        }
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
        
        if (!username || !platform) {
            showToast('Vui lòng nhập đầy đủ thông tin', 'warning');
            return;
        }
        
        try {
            // Get next card name
            const cardNumbers = mxhCards.map(c => parseInt(c.card_name, 10)).filter(n => !isNaN(n));
            const nextCardName = String((cardNumbers.length ? Math.max(...cardNumbers) : 0) + 1);
            
            // Get the first available group_id
            const groupsResponse = await fetch('/mxh/api/groups');
            const groups = await groupsResponse.json();
            const defaultGroupId = groups.length > 0 ? groups[0].id : 1;
            
            // Create card with primary account
            const response = await fetch('/mxh/api/cards', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
          card_name: nextCardName,
                    group_id: defaultGroupId,
          platform: platform,
                    username: username,
                    phone: phone,
                    url: url,
          login_username: username,
          login_password: password,
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
    
    // ===== INITIALIZATION =====
    loadMXHData(true);
    
    // Auto-refresh
    setInterval(() => loadMXHData(false), MXH_CONFIG.AUTO_REFRESH_INTERVAL);
});