"""
Authentication module for STool Dashboard
Handles login, password hashing, and session management
"""

import hashlib
import secrets
import sqlite3
import os
from functools import wraps
from flask import session, request, redirect, url_for, render_template_string, jsonify

# Database path for authentication
AUTH_DB_PATH = os.path.join("data", "auth.db")

def init_auth_db():
    """Initialize authentication database with default user."""
    conn = sqlite3.connect(AUTH_DB_PATH)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Check if default user exists
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", ("Mon",))
    if cursor.fetchone()[0] == 0:
        # Create default user: Mon / Khongnho1
        salt = secrets.token_hex(32)
        password_hash = hashlib.pbkdf2_hmac('sha256', 
                                          "Khongnho1".encode('utf-8'), 
                                          salt.encode('utf-8'), 
                                          100000)
        
        cursor.execute("""
        INSERT INTO users (username, password_hash, salt) 
        VALUES (?, ?, ?)
        """, ("Mon", password_hash.hex(), salt))
    
    conn.commit()
    conn.close()

def verify_password(username, password):
    """Verify username and password against database."""
    conn = sqlite3.connect(AUTH_DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT password_hash, salt FROM users WHERE username = ?
    """, (username,))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return False
    
    stored_hash, salt = result
    password_hash = hashlib.pbkdf2_hmac('sha256', 
                                      password.encode('utf-8'), 
                                      salt.encode('utf-8'), 
                                      100000)
    
    return password_hash.hex() == stored_hash

def login_required(f):
    """Decorator to require login for protected routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            if request.is_json or request.path.startswith('/api/') or request.path.startswith('/telegram/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Login page HTML template
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>STool Dashboard - Đăng nhập</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .login-container {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
            padding: 2.5rem;
            width: 100%;
            max-width: 400px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .login-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        .login-header i {
            font-size: 3rem;
            color: #667eea;
            margin-bottom: 1rem;
        }
        .login-header h2 {
            color: #333;
            font-weight: 300;
            margin-bottom: 0.5rem;
        }
        .login-header p {
            color: #666;
            font-size: 0.9rem;
        }
        .form-floating {
            margin-bottom: 1.5rem;
        }
        .form-control {
            border: 2px solid rgba(102, 126, 234, 0.1);
            border-radius: 12px;
            padding: 1rem;
            transition: all 0.3s ease;
        }
        .form-control:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
        }
        .btn-login {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            border-radius: 12px;
            padding: 1rem 2rem;
            font-weight: 500;
            transition: all 0.3s ease;
            width: 100%;
        }
        .btn-login:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        .alert {
            border-radius: 12px;
            border: none;
        }
        .input-group-text {
            border: 2px solid rgba(102, 126, 234, 0.1);
            border-right: none;
            border-radius: 12px 0 0 12px;
            background: rgba(102, 126, 234, 0.05);
        }
        .password-toggle {
            border: 2px solid rgba(102, 126, 234, 0.1);
            border-left: none;
            border-radius: 0 12px 12px 0;
            background: rgba(102, 126, 234, 0.05);
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .password-toggle:hover {
            background: rgba(102, 126, 234, 0.1);
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="login-header">
            <i class="bi bi-shield-lock"></i>
            <h2>STool Dashboard</h2>
            <p>Vui lòng đăng nhập để tiếp tục</p>
        </div>
        
        {% if error %}
        <div class="alert alert-danger" role="alert">
            <i class="bi bi-exclamation-triangle me-2"></i>
            {{ error }}
        </div>
        {% endif %}
        
        <form method="POST" id="loginForm">
            <div class="input-group mb-3">
                <span class="input-group-text">
                    <i class="bi bi-person"></i>
                </span>
                <div class="form-floating">
                    <input type="text" class="form-control" id="username" name="username" 
                           placeholder="Tên đăng nhập" required autocomplete="username">
                    <label for="username">Tên đăng nhập</label>
                </div>
            </div>
            
            <div class="input-group mb-4">
                <span class="input-group-text">
                    <i class="bi bi-key"></i>
                </span>
                <div class="form-floating flex-grow-1">
                    <input type="password" class="form-control" id="password" name="password" 
                           placeholder="Mật khẩu" required autocomplete="current-password">
                    <label for="password">Mật khẩu</label>
                </div>
                <span class="password-toggle" onclick="togglePassword()">
                    <i class="bi bi-eye" id="passwordIcon"></i>
                </span>
            </div>
            
            <button type="submit" class="btn btn-primary btn-login">
                <i class="bi bi-box-arrow-in-right me-2"></i>
                Đăng nhập
            </button>
        </form>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function togglePassword() {
            const passwordInput = document.getElementById('password');
            const passwordIcon = document.getElementById('passwordIcon');
            
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                passwordIcon.className = 'bi bi-eye-slash';
            } else {
                passwordInput.type = 'password';
                passwordIcon.className = 'bi bi-eye';
            }
        }
        
        // Auto focus on username field
        document.getElementById('username').focus();
        
        // Handle form submission
        document.getElementById('loginForm').addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Đang đăng nhập...';
            submitBtn.disabled = true;
        });
    </script>
</body>
</html>
"""
