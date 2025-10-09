# /stool_project/app/routes.py

from flask import render_template
from flask import current_app as app

@app.route('/')
def home():
    """Render trang chủ."""
    return render_template('home.html', title='Trang Chủ')

@app.route('/passwords')
def passwords():
    """Render trang quản lý mật khẩu."""
    # (Trong tương lai, bạn sẽ thêm logic lấy dữ liệu mật khẩu ở đây)
    return render_template('password.html', title='Quản Lý Mật Khẩu')

@app.route('/telegram')
def telegram():
    """Render trang quản lý Telegram."""
    # (Trong tương lai, bạn sẽ thêm logic cho Telegram ở đây)
    return render_template('telegram.html', title='Quản Lý Telegram')
# Bạn có thể thêm các route khác cho Ghi chú, MXH... ở đây
