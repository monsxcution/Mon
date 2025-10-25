from flask import render_template, request, jsonify
from flask import current_app as app
import logging
from datetime import datetime

@app.route('/')
def home():
    """Render trang chủ."""
    return render_template('home.html', title='Trang Chủ')

@app.route('/telegram')
def telegram():
    """Render trang quản lý Telegram."""
    return render_template('telegram.html', title='Quản Lý Telegram')

@app.route('/notes')
def notes():
    """Render trang ghi chú."""
    return render_template('notes.html', title='Ghi Chú')

@app.route('/debug/log', methods=['POST'])
def debug_log():
    """Nhận debug logs từ frontend và hiển thị trong terminal."""
    try:
        data = request.get_json()
        message = data.get('message', '')
        level = data.get('level', 'INFO')
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        
        # Format log message
        log_message = f"[{timestamp}] 🔍 DEBUG [{level}]: {message}"
        
        # Print to terminal (Flask console)
        print(log_message)
        
        # Also log to Flask logger
        if level == 'ERROR':
            app.logger.error(message)
        elif level == 'WARNING':
            app.logger.warning(message)
        else:
            app.logger.info(message)
            
        return jsonify({"success": True})
    except Exception as e:
        print(f"[ERROR] Debug log failed: {e}")
        return jsonify({"error": str(e)}), 500

