from flask import Flask


def create_app():
    """
    Hàm khởi tạo và cấu hình ứng dụng Flask.
    """
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
    
    return app
