// Telegram Management JavaScript
class TelegramManager {
    constructor() {
        this.sidebar = null;
        this.currentView = 'manager';
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeSidebar();
    }

    setupEventListeners() {
        // Sidebar toggle
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('sidebar-toggle')) {
                this.toggleSidebar();
            }
        });

        // Navigation items
        document.addEventListener('click', (e) => {
            if (e.target.closest('.nav-item')) {
                const navItem = e.target.closest('.nav-item');
                const view = navItem.dataset.view;
                if (view) {
                    this.navigateToView(view);
                }
            }
        });
    }

    initializeSidebar() {
        this.sidebar = document.querySelector('.telegram-sidebar');
        if (!this.sidebar) return;

        // Add animation classes
        this.sidebar.classList.add('slide-in-left');
        
        // Initialize collapsed state from localStorage
        const isCollapsed = localStorage.getItem('telegram-sidebar-collapsed') === 'true';
        if (isCollapsed) {
            this.sidebar.classList.add('collapsed');
        }
    }

    toggleSidebar() {
        if (!this.sidebar) return;
        
        this.sidebar.classList.toggle('collapsed');
        const isCollapsed = this.sidebar.classList.contains('collapsed');
        localStorage.setItem('telegram-sidebar-collapsed', isCollapsed);
        
        // Trigger resize event for responsive adjustments
        window.dispatchEvent(new Event('resize'));
    }

    navigateToView(view) {
        // Remove active class from all nav items
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });

        // Add active class to current nav item
        const activeItem = document.querySelector(`[data-view="${view}"]`);
        if (activeItem) {
            activeItem.classList.add('active');
        }

        this.currentView = view;
        this.loadViewContent(view);
    }

    loadViewContent(view) {
        const contentArea = document.querySelector('.telegram-main-content');
        if (!contentArea) return;

        contentArea.classList.add('fade-in');
        
        switch (view) {
            case 'manager':
                this.renderManager();
                break;
            case 'group':
                this.renderGroup();
                break;
            default:
                this.renderManager();
        }
    }

    renderManager() {
        const contentArea = document.querySelector('.telegram-main-content');
        contentArea.innerHTML = `
            <div class="content-header">
                <h1 class="content-title">Manager</h1>
                <p class="content-subtitle">Quản lý Manager</p>
            </div>
            
            <div class="content-body">
                <p>Chức năng quản lý Manager sẽ được phát triển ở đây.</p>
                <p>Bạn có thể tự setup giao diện và chức năng theo ý muốn.</p>
            </div>
        `;
    }

    renderGroup() {
        const contentArea = document.querySelector('.telegram-main-content');
        contentArea.innerHTML = `
            <div class="content-header">
                <h1 class="content-title">Group</h1>
                <p class="content-subtitle">Quản lý Group</p>
            </div>
            
            <div class="content-body">
                <p>Chức năng quản lý Group sẽ được phát triển ở đây.</p>
                <p>Bạn có thể tự setup giao diện và chức năng theo ý muốn.</p>
            </div>
        `;
    }
}

// Initialize Telegram Manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.telegramManager = new TelegramManager();
});

// Export for global access
window.TelegramManager = TelegramManager;