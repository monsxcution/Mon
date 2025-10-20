import os
import logging
from flask import Flask

# Import logging configuration
try:
    from logging_conf import init_logging
    from web_console_bridge import start_cdp_bridge
    from console_endpoint import register_console_endpoint
    LOGGING_AVAILABLE = True
except ImportError as e:
    LOGGING_AVAILABLE = False
    print(f"[Warning] Logging modules not available: {e}")


def create_app():
    """
    Hàm khởi tạo và cấu hình ứng dụng Flask.
    """
    # === Initialize Unified Logging ===
    if LOGGING_AVAILABLE:
        try:
            app_logger, f12_logger = init_logging()
            app_logger.info("=== MonDashboard Starting ===")
        except Exception as e:
            print(f"[Error] Failed to initialize logging: {e}")
    else:
        app_logger = logging.getLogger('app')
    
    app = Flask(__name__)
    
    # Thiết lập một secret key cho ứng dụng
    app.config['SECRET_KEY'] = 'your_super_secret_key_for_flask_app'
    
    # Đăng ký các routes từ file routes.py
    with app.app_context():
        from . import routes
        from . import notes_routes
        from . import mxh_routes
        from . import mxh_api
        from . import settings_routes
        from . import image_routes
        app.register_blueprint(notes_routes.notes_bp)
        app.register_blueprint(mxh_routes.mxh_bp)
        app.register_blueprint(mxh_api.mxh_api_bp)
        app.register_blueprint(settings_routes.settings_bp)
        app.register_blueprint(image_routes.image_bp)
        
        # === Register Console Endpoint (In-Page Fallback) ===
        if LOGGING_AVAILABLE:
            try:
                register_console_endpoint(app)
            except Exception as e:
                app_logger.error(f"Failed to register console endpoint: {e}")
    
    # === Start CDP Console Bridge ===
    if LOGGING_AVAILABLE:
        mode = os.getenv("CONSOLE_BRIDGE_MODE", "cdp").lower()
        if mode == "cdp":
            try:
                cdp_bridge = start_cdp_bridge()
                if cdp_bridge:
                    app_logger.info(f"[CDP] Bridge started on port {cdp_bridge.port}")
                else:
                    app_logger.warning("[CDP] Bridge failed to start - will fallback to in-page if enabled")
            except Exception as e:
                app_logger.error(f"[CDP] Error starting bridge: {e}")
        elif mode == "inpage":
            app_logger.info("[InPage] Console mirror mode enabled")
        elif mode == "off":
            app_logger.info("[Console Bridge] Disabled")
    
    return app
