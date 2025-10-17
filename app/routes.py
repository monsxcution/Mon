# /Mon/app/routes.py

from flask import render_template, jsonify, request
from flask import current_app as app
from app.database import get_db_connection
import json
import os
import sqlite3
from datetime import datetime, timedelta

@app.route('/')
def home():
    """Render trang chủ."""
    return render_template('home.html', title='Trang Chủ')

@app.route('/telegram')
def telegram():
    """Render trang quản lý Telegram."""
    # (Trong tương lai, bạn sẽ thêm logic cho Telegram ở đây)
    return render_template('telegram.html', title='Quản Lý Telegram')

@app.route('/notes')
def notes():
    """Render trang ghi chú."""
    return render_template('notes.html', title='Ghi Chú')

# Bạn có thể thêm các route khác ở đây

