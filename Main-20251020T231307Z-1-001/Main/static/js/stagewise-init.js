// Stagewise Toolbar Integration
// This file initializes the stagewise toolbar for development mode

// Check if we're in development mode
function isDevelopmentMode() {
    return window.location.hostname === 'localhost' || 
           window.location.hostname === '127.0.0.1' || 
           window.location.hostname.includes('dev') ||
           window.location.port || // If there's a port, assume dev mode
           window.location.search.includes('dev=true'); // Allow dev mode via query param
}

// Initialize stagewise toolbar
async function initStagewise() {
    if (!isDevelopmentMode()) {
        console.log('Stagewise: Not in development mode, skipping toolbar initialization');
        return;
    }

    console.log('Stagewise: Development mode detected, initializing toolbar...');

    try {
        // Import the stagewise toolbar module
        const stagewiseModule = await import('./stagewise-toolbar.js');
        
        if (!stagewiseModule.initToolbar) {
            throw new Error('initToolbar function not found in stagewise module');
        }

        // Initialize the toolbar with configuration
        stagewiseModule.initToolbar({
            plugins: [] // Add custom plugins here if needed
        });
        
        console.log('Stagewise: Toolbar initialized successfully');
        
        // Add a small visual indicator that stagewise is active (for debugging)
        if (window.location.search.includes('debug=true')) {
            const indicator = document.createElement('div');
            indicator.style.position = 'fixed';
            indicator.style.top = '10px';
            indicator.style.left = '10px';
            indicator.style.background = '#4CAF50';
            indicator.style.color = 'white';
            indicator.style.padding = '5px 10px';
            indicator.style.borderRadius = '3px';
            indicator.style.fontSize = '12px';
            indicator.style.zIndex = '10000';
            indicator.textContent = 'Stagewise Active';
            document.body.appendChild(indicator);
            
            setTimeout(() => {
                if (document.body.contains(indicator)) {
                    document.body.removeChild(indicator);
                }
            }, 3000);
        }
        
    } catch (error) {
        console.error('Stagewise: Failed to initialize toolbar:', error);
        console.log('Stagewise: Make sure the VS Code extension is installed and active');
        console.log('Stagewise: If you need help, reach out via Discord: https://discord.gg/gkdGsDYaKA');
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initStagewise);
} else {
    initStagewise();
}
