import sqlite3
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, render_template
from app.database import get_db_connection

# --- BLUEPRINT DEFINITION ---
mxh_bp = Blueprint("mxh_feature", __name__, url_prefix="/mxh")

# ===== MXH PAGES =====
@mxh_bp.route('')
def mxh_page():
    """Render trang quản lý MXH."""
    return render_template('mxh.html', title='Mạng Xã Hội')

# ===== MXH GROUP API ROUTES =====
@mxh_bp.route('/api/groups', methods=['GET', 'POST'])
def mxh_groups():
    """Get all groups or create a new group."""
    conn = get_db_connection()
    try:
        if request.method == 'GET':
            groups = conn.execute('SELECT * FROM mxh_groups ORDER BY created_at DESC').fetchall()
            return jsonify([dict(group) for group in groups])
        
        elif request.method == 'POST':
            data = request.get_json()
            name = data.get('name')
            color = data.get('color')
            
            if not name or not color:
                return jsonify({'error': 'Name and color are required'}), 400
            
            # Auto-assign platform icons based on group name
            platform_icons = {
                'wechat': 'bi-wechat',
                'facebook': 'bi-facebook',
                'instagram': 'bi-instagram',
                'tiktok': 'bi-tiktok',
                'youtube': 'bi-youtube',
                'twitter': 'bi-twitter',
                'linkedin': 'bi-linkedin',
                'zalo': 'bi-chat-dots',
                'telegram': 'bi-telegram',
                'whatsapp': 'bi-whatsapp'
            }
            icon = platform_icons.get(name.lower(), 'bi-share-fill')
            
            try:
                cursor = conn.execute(
                    'INSERT INTO mxh_groups (name, color, icon, created_at) VALUES (?, ?, ?, ?)',
                    (name, color, icon, datetime.now().isoformat())
                )
                conn.commit()
                group_id = cursor.lastrowid
                return jsonify({
                    'id': group_id,
                    'name': name,
                    'color': color,
                    'icon': icon,
                    'message': 'Group created successfully'
                }), 201
            except sqlite3.IntegrityError:
                return jsonify({'error': f'Nhóm "{name}" đã tồn tại. Vui lòng chọn tên khác.'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@mxh_bp.route('/api/groups/<int:group_id>', methods=['DELETE'])
def delete_mxh_group(group_id):
    """Delete a group if it has no accounts."""
    conn = get_db_connection()
    try:
        # Check if group has accounts
        accounts = conn.execute('SELECT COUNT(*) FROM mxh_accounts WHERE group_id = ?', (group_id,)).fetchone()[0]
        if accounts > 0:
            return jsonify({'error': 'Cannot delete group with existing accounts'}), 400
        
        conn.execute('DELETE FROM mxh_groups WHERE id = ?', (group_id,))
        conn.commit()
        return jsonify({'message': 'Group deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


# ===== MXH ACCOUNT API ROUTES =====
@mxh_bp.route('/api/accounts', methods=['GET', 'POST'])
def mxh_accounts():
    """Get all accounts or create a new account."""
    conn = get_db_connection()
    try:
        if request.method == 'GET':
            accounts = conn.execute('''
                SELECT a.*, g.name as group_name, g.color as group_color, g.icon as group_icon 
                FROM mxh_accounts a 
                LEFT JOIN mxh_groups g ON a.group_id = g.id 
            ''').fetchall()
            return jsonify([dict(account) for account in accounts])
        
        elif request.method == 'POST':
            data = request.get_json()
            card_name = data.get('card_name')
            group_id = data.get('group_id')
            platform = data.get('platform')
            username = data.get('username')
            url = data.get('url', '')
            phone = data.get('phone', '')
            login_username = data.get('login_username', '')
            login_password = data.get('login_password', '')
            
            # WeChat specific fields
            now = datetime.now()
            wechat_created_day = data.get('wechat_created_day', now.day)
            wechat_created_month = data.get('wechat_created_month', now.month)
            wechat_created_year = data.get('wechat_created_year', now.year)
            wechat_scan_create = data.get('wechat_scan_create', 0)
            wechat_scan_rescue = data.get('wechat_scan_rescue', 0)
            wechat_status = data.get('wechat_status', 'available')
            
            if not all([card_name, group_id, platform, username]):
                return jsonify({'error': 'Card name, group, platform and username are required'}), 400
            
            conn.execute(
                '''INSERT INTO mxh_accounts 
                   (card_name, group_id, platform, username, phone, url, login_username, login_password, created_at, 
                    wechat_created_day, wechat_created_month, wechat_created_year,
                    wechat_scan_create, wechat_scan_rescue, wechat_status) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (card_name, group_id, platform, username, phone, url, login_username, login_password, datetime.now().isoformat(),
                 wechat_created_day, wechat_created_month, wechat_created_year,
                 wechat_scan_create, wechat_scan_rescue, wechat_status)
            )
            conn.commit()
            return jsonify({'message': 'Account created successfully'}), 201
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@mxh_bp.route('/api/accounts/<int:account_id>', methods=['PUT', 'DELETE'])
def update_delete_mxh_account(account_id):
    """Update or delete an account."""
    conn = get_db_connection()
    try:
        if request.method == 'PUT':
            data = request.get_json()
            is_secondary = data.get('is_secondary', False)

            fields_to_update = {
                'card_name': data.get('card_name'),
                'username': data.get('username'),
                'phone': data.get('phone'),
                'url': data.get('url'),
                'login_username': data.get('login_username'),
                'login_password': data.get('login_password'),
                'wechat_created_day': data.get('wechat_created_day'),
                'wechat_created_month': data.get('wechat_created_month'),
                'wechat_created_year': data.get('wechat_created_year'),
                'wechat_status': data.get('wechat_status'),
                'status': data.get('status')
            }
            
            # Use appropriate prefixes for secondary account
            if is_secondary:
                update_cols = {f"secondary_{key}": value for key, value in fields_to_update.items()}
            else:
                update_cols = fields_to_update

            # Filter out any keys with None values to avoid overwriting with null
            update_cols = {k: v for k, v in update_cols.items() if v is not None}
            
            if not update_cols:
                return jsonify({'message': 'No fields to update.'})
                
            set_clause = ", ".join([f"{key} = ?" for key in update_cols.keys()])
            params = list(update_cols.values()) + [account_id]

            conn.execute(f'UPDATE mxh_accounts SET {set_clause} WHERE id = ?', params)
            conn.commit()
            return jsonify({'message': 'Account updated successfully'})
        
        elif request.method == 'DELETE':
            conn.execute('DELETE FROM mxh_accounts WHERE id = ?', (account_id,))
            conn.commit()
            return jsonify({'message': 'Account deleted successfully'})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


# ===== QUICK UPDATE API (FOR INLINE EDITING) =====
@mxh_bp.route('/api/accounts/<int:account_id>/quick-update', methods=['POST'])
def quick_update_account(account_id):
    """Quick update for inline editing (username, phone, status)."""
    conn = get_db_connection()
    try:
        data = request.get_json()
        is_secondary = data.get('is_secondary', False)
        field = data.get('field')  # 'username', 'phone', or 'status'
        value = data.get('value')
        
        if not field:
            return jsonify({'error': 'Field is required'}), 400
        
        # Determine column name based on secondary flag
        if is_secondary:
            column = f"secondary_{field}"
        else:
            column = field
        
        # Validate field name to prevent SQL injection
        allowed_fields = ['username', 'phone', 'status', 'secondary_username', 'secondary_phone', 'secondary_status']
        if column not in allowed_fields:
            return jsonify({'error': 'Invalid field'}), 400
        
        conn.execute(f'UPDATE mxh_accounts SET {column} = ? WHERE id = ?', (value, account_id))
        conn.commit()
        
        return jsonify({'message': 'Field updated successfully', 'field': field, 'value': value})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


# ===== MUTE/UNMUTE API ROUTES =====
@mxh_bp.route('/api/accounts/<int:account_id>/mute', methods=['POST'])
def mute_mxh_account(account_id):
    """Mute an account for 30 days."""
    conn = get_db_connection()
    try:
        data = request.get_json()
        is_secondary = data.get('is_secondary', False)
        
        # Calculate mute until date (30 days from now)
        mute_until = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
        
        if is_secondary:
            conn.execute(
                'UPDATE mxh_accounts SET secondary_muted_until = ? WHERE id = ?',
                (mute_until, account_id)
            )
        else:
            conn.execute(
                'UPDATE mxh_accounts SET muted_until = ? WHERE id = ?',
                (mute_until, account_id)
            )
        conn.commit()
        
        return jsonify({'message': 'Account muted successfully for 30 days', 'muted_until': mute_until})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@mxh_bp.route('/api/accounts/<int:account_id>/unmute', methods=['POST'])
def unmute_mxh_account(account_id):
    """Unmute an account."""
    conn = get_db_connection()
    try:
        data = request.get_json()
        is_secondary = data.get('is_secondary', False)
        
        if is_secondary:
            conn.execute(
                'UPDATE mxh_accounts SET secondary_muted_until = NULL WHERE id = ?',
                (account_id,)
            )
        else:
            conn.execute(
                'UPDATE mxh_accounts SET muted_until = NULL WHERE id = ?',
                (account_id,)
            )
        conn.commit()
        
        return jsonify({'message': 'Account unmuted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


# ===== SCAN API ROUTES =====
@mxh_bp.route('/api/accounts/<int:account_id>/scan', methods=['POST'])
def mark_account_scanned(account_id):
    """Mark account as scanned or reset scan count."""
    conn = get_db_connection()
    try:
        data = request.get_json() or {}
        is_secondary = data.get('is_secondary', False)
        
        if data.get('reset'):
            # Reset scan count and last scan date
            if is_secondary:
                conn.execute('''
                    UPDATE mxh_accounts SET 
                    secondary_wechat_scan_count = 0,
                    secondary_wechat_last_scan_date = NULL
                    WHERE id = ?
                ''', (account_id,))
            else:
                conn.execute('''
                    UPDATE mxh_accounts SET 
                    wechat_scan_count = 0,
                    wechat_last_scan_date = NULL
                    WHERE id = ?
                ''', (account_id,))
            conn.commit()
            return jsonify({'message': 'Scan count reset successfully'})
        else:
            # Update scan count and last scan date
            current_date = datetime.now().isoformat()
            if is_secondary:
                conn.execute('''
                    UPDATE mxh_accounts SET 
                    secondary_wechat_scan_count = secondary_wechat_scan_count + 1,
                    secondary_wechat_last_scan_date = ?
                    WHERE id = ?
                ''', (current_date, account_id))
            else:
                conn.execute('''
                    UPDATE mxh_accounts SET 
                    wechat_scan_count = wechat_scan_count + 1,
                    wechat_last_scan_date = ?
                    WHERE id = ?
                ''', (current_date, account_id))
            conn.commit()
            return jsonify({'message': 'Account marked as scanned successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


# ===== STATUS TOGGLE API ROUTES =====
@mxh_bp.route('/api/accounts/<int:account_id>/toggle-status', methods=['POST'])
def toggle_account_status(account_id):
    """Toggle account status between active and disabled."""
    conn = get_db_connection()
    try:
        data = request.get_json() or {}
        is_secondary = data.get('is_secondary', False)
        
        if is_secondary:
            # Toggle secondary status
            conn.execute('''
                UPDATE mxh_accounts 
                SET secondary_status = CASE 
                    WHEN secondary_status = 'active' THEN 'disabled'
                    ELSE 'active'
                END,
                secondary_die_date = CASE 
                    WHEN secondary_status = 'active' THEN ?
                    ELSE NULL
                END
                WHERE id = ?
            ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), account_id))
        else:
            # Toggle primary status
            conn.execute('''
                UPDATE mxh_accounts 
                SET status = CASE 
                    WHEN status = 'disabled' THEN 'active'
                    ELSE 'disabled'
                END,
                die_date = CASE 
                    WHEN status = 'disabled' THEN ?
                    ELSE NULL
                END
                WHERE id = ?
            ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), account_id))
        
        conn.commit()
        return jsonify({'message': 'Account status toggled successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


# ===== RESCUE API ROUTES =====
@mxh_bp.route('/api/accounts/<int:account_id>/rescue', methods=['POST'])
def rescue_account(account_id):
    """Rescue a died account."""
    conn = get_db_connection()
    try:
        data = request.get_json() or {}
        is_secondary = data.get('is_secondary', False)
        rescue_result = data.get('result')  # 'success' or 'failed'
        
        if rescue_result == 'success':
            # Cứu thành công - chuyển về available và tăng success count
            if is_secondary:
                conn.execute('''
                    UPDATE mxh_accounts 
                    SET secondary_status = 'active',
                        secondary_die_date = NULL,
                        secondary_rescue_success_count = secondary_rescue_success_count + 1
                    WHERE id = ?
                ''', (account_id,))
            else:
                conn.execute('''
                    UPDATE mxh_accounts 
                    SET status = 'active',
                        die_date = NULL,
                        rescue_success_count = rescue_success_count + 1
                    WHERE id = ?
                ''', (account_id,))
            message = 'Account rescued successfully!'
        elif rescue_result == 'failed':
            # Cứu thất bại - tăng rescue count
            if is_secondary:
                conn.execute('''
                    UPDATE mxh_accounts 
                    SET secondary_rescue_count = secondary_rescue_count + 1
                    WHERE id = ?
                ''', (account_id,))
            else:
                conn.execute('''
                    UPDATE mxh_accounts 
                    SET rescue_count = rescue_count + 1
                    WHERE id = ?
                ''', (account_id,))
            message = 'Rescue attempt failed. Rescue count increased.'
        else:
            return jsonify({'error': 'Invalid rescue result'}), 400
        
        conn.commit()
        return jsonify({'message': message})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@mxh_bp.route('/api/accounts/<int:account_id>/mark-die', methods=['POST'])
def mark_account_die(account_id):
    """Mark account as died."""
    conn = get_db_connection()
    try:
        data = request.get_json() or {}
        is_secondary = data.get('is_secondary', False)
        die_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if is_secondary:
            conn.execute('''
                UPDATE mxh_accounts 
                SET secondary_status = 'disabled',
                    secondary_die_date = ?,
                    secondary_rescue_count = 0
                WHERE id = ?
            ''', (die_date, account_id))
        else:
            conn.execute('''
                UPDATE mxh_accounts 
                SET status = 'disabled',
                    die_date = ?,
                    rescue_count = 0
                WHERE id = ?
            ''', (die_date, account_id))
        
        conn.commit()
        return jsonify({'message': 'Account marked as died', 'die_date': die_date})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()
