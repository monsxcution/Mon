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
        
    return app
