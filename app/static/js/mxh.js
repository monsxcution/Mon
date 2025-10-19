// MXH Module - Complete Implementation
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
    
    function renderMXHAccounts() {
        if (isRendering) {
            pendingUpdates = true;
            return;
        }
        
        isRendering = true;
        const container = document.getElementById('mxh-accounts-container');
        const scrollY = window.scrollY;
        
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
        
        let content = '<div class="row">';
        filteredCards.forEach(card => {
            // Find primary account (is_primary = 1) or first account
            const primaryAccount = card.sub_accounts ? 
                card.sub_accounts.find(acc => acc.is_primary === 1) || card.sub_accounts[0] : 
                null;
            
            if (primaryAccount) {
                content += renderAccountCard(card, primaryAccount);
            }
        });
        content += '</div>';
        
        container.innerHTML = content;
        window.scrollTo(0, scrollY);
        
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
    
    function renderAccountCard(card, account) {
        const { days: wechatAgeDays, text: wechatAgeText } = calculateWeChatAge(
            account.wechat_created_day, 
            account.wechat_created_month, 
            account.wechat_created_year
        );
        
        const statusInfo = getAccountStatusInfo(account);
        const borderClass = getWeChatBorderClass(account, wechatAgeDays);
        const cardId = `card-${card.id}-account-${account.id}`;
        
        // Account switcher icons if multiple accounts
        const accountIcons = card.sub_accounts && card.sub_accounts.length > 1 
            ? `<div class="account-switcher-icons">${card.sub_accounts.map(acc => 
                `<i class="bi ${getPlatformIcon(acc.platform || card.platform)} ${acc.id === account.id ? 'active' : ''}" 
                     onclick="switchToAccount(${card.id}, ${acc.id})" title="${acc.account_name || 'Account'}"></i>`
            ).join('')}</div>`
            : '';
        
        return `
            <div class="col" id="card-wrapper-${card.id}">
                <div class="card h-100 card-mxh ${borderClass}" id="${cardId}" 
                     oncontextmenu="handleCardContextMenu(event, ${card.id}, ${account.id})">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <strong class="card-name-display">${card.card_name}</strong>
                        <span class="badge ${statusInfo.className}" onclick="toggleAccountStatus(event, ${account.id})">${statusInfo.text}</span>
                    </div>
                    <div class="card-body">
                        ${accountIcons}
                        <p class="card-text editable-field" contenteditable="true" 
                           data-account-id="${account.id}" data-field="username">${account.username || 'Click để nhập'}</p>
                        <p class="card-text editable-field" contenteditable="true" 
                           data-account-id="${account.id}" data-field="phone">
                            ${account.phone ? `📞 ${account.phone}` : '📞 Click để nhập'}
                        </p>
                        ${card.platform === 'wechat' ? `
                        <p class="card-text small text-muted" 
                           title="Ngày tạo: ${account.wechat_created_day}/${account.wechat_created_month}/${account.wechat_created_year}">
                            <i class="bi bi-calendar-check"></i> ${wechatAgeText}
                        </p>
                        ` : ''}
                        ${account.notice ? `
                        <div class="alert alert-warning mt-2 p-2 notice-alert" onclick="openNoticeModal(event, ${account.id})">
                            <p class="mb-1"><strong><i class="bi bi-bell-fill"></i> ${account.notice.title || 'Notice'}</strong></p>
                            <p class="mb-0 small">${account.notice.content || account.notice}</p>
                        </div>
                        ` : ''}
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
                    <i class="bi ${getPlatformIcon(acc.platform || card.platform)} me-2"></i>
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
    function calculateWeChatAge(day, month, year) {
        if (!day || !month || !year) return { days: 0, text: 'Thiếu ngày tạo' };
        const createdDate = new Date(year, month - 1, day);
        const now = new Date();
        const diffTime = Math.abs(now - createdDate);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        return { days: diffDays, text: `${diffDays} ngày` };
    }
    
    function getAccountStatusInfo(account) {
        if (account.status === 'disabled') {
            return { text: 'Vô hiệu hóa', className: 'status-disabled' };
        }
        if (account.status === 'die') {
            return { text: 'Die', className: 'status-die' };
        }
        return { text: 'Hoạt động', className: 'status-active' };
    }
    
    function getWeChatBorderClass(account, wechatAgeDays) {
        const isHK = account.username && account.username.toLowerCase().includes('hk');
        const hasNotice = account.notice && (!account.muted_until || new Date(account.muted_until) < new Date());
        
        if (account.status === 'die') return 'border-danger';
        if (hasNotice) return 'border-warning';
        if (account.status === 'disabled') return 'border-secondary';
        
        if (isHK) {
            return wechatAgeDays >= 13 ? 'border-success' : 'border-primary';
        } else {
            return wechatAgeDays >= 28 ? 'border-success' : 'border-primary';
        }
    }
    
    function getPlatformIcon(platform) {
        switch (platform) {
            case 'wechat': return 'bi-wechat';
            case 'telegram': return 'bi-telegram';
            case 'facebook': return 'bi-facebook';
            case 'instagram': return 'bi-instagram';
            case 'twitter': return 'bi-twitter';
            case 'zalo': return 'bi-chat-dots';
            case 'whatsapp': return 'bi-whatsapp';
            default: return 'bi-person-badge';
        }
    }
    
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
    
    window.handleCardContextMenu = handleCardContextMenu;
    window.toggleAccountStatus = function(event, accountId) {
        event.stopPropagation();
        // TODO: Implement status toggle
        showToast('Chức năng đang phát triển', 'info');
    };
    
    window.openNoticeModal = function(event, accountId) {
        if (event) event.stopPropagation();
        // TODO: Implement notice modal
        showToast('Chức năng đang phát triển', 'info');
    };
    
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
                // TODO: Open edit modal
                showToast('Chức năng đang phát triển', 'info');
                break;
            case 'delete':
                if (confirm('Bạn có chắc muốn xóa card này?')) {
                    // TODO: Delete card
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
                    // This will create the primary account
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
                document.getElementById('mxh-addAccountModal').querySelector('form').reset();
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