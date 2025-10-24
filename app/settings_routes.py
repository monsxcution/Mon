"""
Settings Dashboard Routes
Quản lý cài đặt dashboard với real-time updates
"""
from flask import Blueprint, render_template, request, jsonify
import os
import json
import platform  # New Import
import subprocess  # New Import
import sys # New Import

# Conditional import for Windows Registry
try:
    if platform.system() == 'Windows':
        import winreg
except ImportError:
    pass  # winreg is not available on non-Windows systems

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

# Path to dashboard settings file
DASHBOARD_SETTINGS_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'dashboard_settings.json')

def load_dashboard_settings():
    """Load dashboard settings from JSON file."""
    if os.path.exists(DASHBOARD_SETTINGS_FILE):
        with open(DASHBOARD_SETTINGS_FILE, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            # Ensure the new setting exists in loaded data, default to 15 seconds (15000 ms)
            if 'mxh_refresh_interval' not in settings:
                settings['mxh_refresh_interval'] = 15000
            return settings
    return {
        'auto_start': False, 
        'auto_open_dashboard': True,
        'shutdown_timer': {'enabled': False, 'hours': 0, 'minutes': 0},
        'notification_timer': {'enabled': False, 'hours': 0, 'minutes': 0, 'message': ''},
        'mxh_refresh_interval': 15000  # Default 15000 ms (15 seconds)
    }

def save_dashboard_settings(settings):
    """Save dashboard settings to JSON file."""
    os.makedirs(os.path.dirname(DASHBOARD_SETTINGS_FILE), exist_ok=True)
    with open(DASHBOARD_SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)

# NEW FUNCTION: Handle OS-level auto-start configuration (Windows-centric)
def handle_auto_start_os_config(enabled):
    """Adds or removes the application from the Windows startup list (via Registry)."""
    if platform.system() != 'Windows':
        print("Auto-start feature is only implemented for Windows.")
        return

    try:
        # Get the absolute path to run.pyw (assuming run.py was renamed and is in the root directory)
        app_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        
        # Find pythonw.exe more reliably
        pythonw_path = None
        
        # Method 1: Try to find pythonw.exe in the same directory as python.exe
        if sys.executable:
            python_dir = os.path.dirname(sys.executable)
            pythonw_candidate = os.path.join(python_dir, "pythonw.exe")
            if os.path.exists(pythonw_candidate):
                pythonw_path = pythonw_candidate
        
        # Method 2: Try to find pythonw.exe in sys.base_prefix
        if not pythonw_path and hasattr(sys, 'base_prefix'):
            base_prefix = sys.base_prefix
            pythonw_candidate = os.path.join(base_prefix, "pythonw.exe")
            if os.path.exists(pythonw_candidate):
                pythonw_path = pythonw_candidate
        
        # Method 3: Try to find pythonw.exe in sys.prefix
        if not pythonw_path and hasattr(sys, 'prefix'):
            prefix = sys.prefix
            pythonw_candidate = os.path.join(prefix, "pythonw.exe")
            if os.path.exists(pythonw_candidate):
                pythonw_path = pythonw_candidate
        
        # Method 4: Fallback to replacing python.exe with pythonw.exe
        if not pythonw_path and sys.executable:
            pythonw_path = sys.executable.replace("python.exe", "pythonw.exe")
        
        if not pythonw_path:
            raise Exception("Could not find pythonw.exe")
        
        # Ensure the run.pyw file exists
        run_pyw_path = os.path.join(app_root, "run.pyw")
        if not os.path.exists(run_pyw_path):
            raise Exception(f"run.pyw not found at {run_pyw_path}")
        
        # Create command with proper working directory and error handling
        # Use cmd /c to ensure proper working directory and environment
        run_command = f'cmd /c "cd /d \\"{app_root}\\" && \\"{pythonw_path}\\" \\"{run_pyw_path}\\""'

        # Windows Registry path for startup programs
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "MonDashboard"

        # NOTE: winreg is imported conditionally in the global scope
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS) as key:
            if enabled:
                # Add to startup
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, run_command)
                print(f"[SUCCESS] Added to Windows startup: {run_command}")
            else:
                # Remove from startup
                try:
                    winreg.DeleteValue(key, app_name)
                    print("[SUCCESS] Removed from Windows startup.")
                except FileNotFoundError:
                    pass  # Already removed
    except Exception as e:
        print(f"[ERROR] Error configuring Windows startup: {e}")
        # NOTE: The subordinate AI must ensure the main application path/command is correctly determined.

# ===== PAGE ROUTES =====
@settings_bp.route('/')
def settings_page():
    """Render settings page."""
    return render_template('settings.html', title='Cài Đặt Dashboard')

# ===== API ROUTES =====
@settings_bp.route('/api/settings', methods=['GET'])
def get_settings():
    """Get all dashboard settings."""
    try:
        settings = load_dashboard_settings()
        return jsonify(settings)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/api/settings', methods=['POST'])
def update_settings():
    """Update dashboard settings."""
    try:
        data = request.get_json()
        settings = load_dashboard_settings()
        settings.update(data)
        save_dashboard_settings(settings)
        return jsonify({'success': True, 'settings': settings})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/api/settings/auto-start', methods=['PUT'])
def toggle_auto_start():
    """Toggle auto-start setting and configure OS startup."""
    try:
        data = request.get_json()
        enabled = data.get('enabled', False)  # Capture state here
        settings = load_dashboard_settings()
        
        # 1. Update OS configuration (CRITICAL FIX)
        handle_auto_start_os_config(enabled) 
        
        # 2. Save setting to JSON
        settings['auto_start'] = enabled
        save_dashboard_settings(settings)
        
        return jsonify({'success': True, 'auto_start': settings['auto_start']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/api/settings/auto-open-dashboard', methods=['PUT'])
def toggle_auto_open_dashboard():
    """Toggle auto-open dashboard setting."""
    try:
        data = request.get_json()
        settings = load_dashboard_settings()
        settings['auto_open_dashboard'] = data.get('enabled', False)
        save_dashboard_settings(settings)
        return jsonify({'success': True, 'auto_open_dashboard': settings['auto_open_dashboard']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/api/settings/shutdown-timer', methods=['PUT'])
def update_shutdown_timer():
    """Update shutdown timer settings."""
    try:
        data = request.get_json()
        settings = load_dashboard_settings()
        settings['shutdown_timer'] = {
            'enabled': data.get('enabled', False),
            'hours': data.get('hours', 0),
            'minutes': data.get('minutes', 0)
        }
        save_dashboard_settings(settings)
        return jsonify({'success': True, 'shutdown_timer': settings['shutdown_timer']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/api/settings/notification-timer', methods=['PUT'])
def update_notification_timer():
    """Update notification timer settings."""
    try:
        data = request.get_json()
        settings = load_dashboard_settings()
        settings['notification_timer'] = {
            'enabled': data.get('enabled', False),
            'hours': data.get('hours', 0),
            'minutes': data.get('minutes', 0),
            'message': data.get('message', '')
        }
        save_dashboard_settings(settings)
        return jsonify({'success': True, 'notification_timer': settings['notification_timer']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/api/settings/mxh-refresh-interval', methods=['PUT'])
def update_mxh_refresh_interval():
    """Update MXH dashboard auto-refresh interval (in milliseconds)."""
    try:
        data = request.get_json()
        interval = data.get('interval_ms')  # Expecting milliseconds, e.g., 15000
        if not isinstance(interval, int) or interval < 3000:  # Enforce minimum 3 seconds (3000ms)
            return jsonify({'error': 'Interval must be an integer >= 3000ms'}), 400
            
        settings = load_dashboard_settings()
        settings['mxh_refresh_interval'] = interval
        save_dashboard_settings(settings)
        return jsonify({'success': True, 'mxh_refresh_interval': settings['mxh_refresh_interval']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/api/system/shutdown', methods=['POST'])
def system_shutdown():
    """Shutdown system (Windows only)."""
    try:
        import platform
        if platform.system() == 'Windows':
            import subprocess
            subprocess.Popen(['shutdown', '/s', '/t', '0'])
            return jsonify({'success': True, 'message': 'Shutting down...'})
        else:
            return jsonify({'error': 'Only supported on Windows'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
