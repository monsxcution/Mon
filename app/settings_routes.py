"""
Settings Dashboard Routes
Quản lý cài đặt dashboard với real-time updates
"""
from flask import Blueprint, render_template, request, jsonify
import os
import json

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

# Path to dashboard settings file
DASHBOARD_SETTINGS_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'dashboard_settings.json')

def load_dashboard_settings():
    """Load dashboard settings from JSON file."""
    if os.path.exists(DASHBOARD_SETTINGS_FILE):
        with open(DASHBOARD_SETTINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'auto_start': False, 
        'auto_open_dashboard': True,
        'shutdown_timer': {'enabled': False, 'hours': 0, 'minutes': 0},
        'notification_timer': {'enabled': False, 'hours': 0, 'minutes': 0, 'message': ''}
    }

def save_dashboard_settings(settings):
    """Save dashboard settings to JSON file."""
    os.makedirs(os.path.dirname(DASHBOARD_SETTINGS_FILE), exist_ok=True)
    with open(DASHBOARD_SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)

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
    """Toggle auto-start setting."""
    try:
        data = request.get_json()
        settings = load_dashboard_settings()
        settings['auto_start'] = data.get('enabled', False)
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
