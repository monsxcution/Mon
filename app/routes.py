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

# ===== MXH API ROUTES =====

@app.route('/mxh/api/groups', methods=['GET', 'POST'])
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


@app.route('/mxh/api/groups/<int:group_id>', methods=['DELETE'])
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


@app.route('/mxh/api/accounts', methods=['GET', 'POST'])
def mxh_accounts():
    """Get all accounts or create a new account."""
    conn = get_db_connection()
    try:
        if request.method == 'GET':
            # Check for a timestamp query parameter to implement delta updates
            last_updated_at = request.args.get('last_updated_at')
            
            query = '''
                SELECT a.*, g.name as group_name, g.color as group_color, g.icon as group_icon 
                FROM mxh_accounts a 
                LEFT JOIN mxh_groups g ON a.group_id = g.id 
            '''
            params = []
            
            if last_updated_at:
                # IMPORTANT: Only fetch records that have been modified (updated_at > timestamp)
                # The 'updated_at' column is crucial for this optimization.
                query += ' WHERE a.updated_at > ?'
                params.append(last_updated_at)
                
            query += ' ORDER BY a.group_id, a.card_name'
            
            accounts = conn.execute(query, tuple(params)).fetchall()
            
            # The client (JS in mxh.html) will need to handle merging these changes (delta update)
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
            wechat_status = data.get('wechat_status', 'active')
            
            if not all([card_name, group_id, platform, username]):
                return jsonify({'error': 'Card name, group, platform and username are required'}), 400
            
            current_timestamp = datetime.now().isoformat()  # Use ISO format for consistency
            conn.execute(
                '''INSERT INTO mxh_accounts 
                   (card_name, group_id, platform, username, phone, url, login_username, login_password, created_at, updated_at,
                    wechat_created_day, wechat_created_month, wechat_created_year,
                    wechat_scan_create, wechat_scan_rescue, wechat_status) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (card_name, group_id, platform, username, phone, url, login_username, login_password, current_timestamp, current_timestamp,
                 wechat_created_day, wechat_created_month, wechat_created_year,
                 wechat_scan_create, wechat_scan_rescue, wechat_status)
            )
            conn.commit()
            return jsonify({'message': 'Account created successfully'}), 201
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/mxh/api/accounts/<int:account_id>', methods=['PUT', 'DELETE'])
def update_delete_mxh_account(account_id):
    """Update or delete an account."""
    conn = get_db_connection()
    try:
        if request.method == 'PUT':
            data = request.get_json()
            is_secondary = data.get('is_secondary', False)

            # NEW LOGIC: Status Harmonization (Primary Status)
            primary_status = data.get('status')
            primary_wechat_status = data.get('wechat_status')

            if primary_status == 'available':  # Frontend still uses 'available' sometimes
                primary_status = 'active'
            if primary_status == 'die':  # Frontend modal bug fix
                primary_status = 'disabled'
                primary_wechat_status = 'die'
            if primary_status:
                data['status'] = primary_status
            if primary_wechat_status:
                data['wechat_status'] = primary_wechat_status

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
            params = list(update_cols.values()) + [datetime.now().isoformat(), account_id]

            conn.execute(f'UPDATE mxh_accounts SET {set_clause}, updated_at = ? WHERE id = ?', params)
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


@app.route('/mxh/api/accounts/<int:account_id>/mute', methods=['POST'])
def mute_mxh_account(account_id):
    """Mute an account for 30 days."""
    conn = get_db_connection()
    try:
        data = request.get_json()
        is_secondary = data.get('is_secondary', False)
        
        # Calculate mute until date (30 days from now)
        mute_until = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
        
        current_timestamp = datetime.now().isoformat()
        if is_secondary:
            conn.execute(
                'UPDATE mxh_accounts SET secondary_muted_until = ?, updated_at = ? WHERE id = ?',
                (mute_until, current_timestamp, account_id)
            )
        else:
            conn.execute(
                'UPDATE mxh_accounts SET muted_until = ?, updated_at = ? WHERE id = ?',
                (mute_until, current_timestamp, account_id)
            )
        conn.commit()
        
        return jsonify({'message': 'Account muted successfully for 30 days', 'muted_until': mute_until})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/mxh/api/accounts/<int:account_id>/unmute', methods=['POST'])
def unmute_mxh_account(account_id):
    """Unmute an account."""
    conn = get_db_connection()
    try:
        data = request.get_json()
        is_secondary = data.get('is_secondary', False)
        
        current_timestamp = datetime.now().isoformat()
        if is_secondary:
            conn.execute(
                'UPDATE mxh_accounts SET secondary_muted_until = NULL, updated_at = ? WHERE id = ?',
                (current_timestamp, account_id)
            )
        else:
            conn.execute(
                'UPDATE mxh_accounts SET muted_until = NULL, updated_at = ? WHERE id = ?',
                (current_timestamp, account_id)
            )
        conn.commit()
        
        return jsonify({'message': 'Account unmuted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/mxh/api/accounts/<int:account_id>/scan', methods=['POST'])
def mark_account_scanned(account_id):
    """Mark account as scanned or reset scan count."""
    conn = get_db_connection()
    try:
        data = request.get_json() or {}
        is_secondary = data.get('is_secondary', False)
        
        current_timestamp = datetime.now().isoformat()
        if data.get('reset'):
            # Reset scan count and last scan date
            if is_secondary:
                conn.execute('''
                    UPDATE mxh_accounts SET 
                    secondary_wechat_scan_count = 0,
                    secondary_wechat_last_scan_date = NULL,
                    updated_at = ?
                    WHERE id = ?
                ''', (current_timestamp, account_id))
            else:
                conn.execute('''
                    UPDATE mxh_accounts SET 
                    wechat_scan_count = 0,
                    wechat_last_scan_date = NULL,
                    updated_at = ?
                    WHERE id = ?
                ''', (current_timestamp, account_id))
            conn.commit()
            return jsonify({'message': 'Scan count reset successfully'})
        else:
            # Update scan count and last scan date
            current_date = datetime.now().isoformat()
            if is_secondary:
                conn.execute('''
                    UPDATE mxh_accounts SET 
                    secondary_wechat_scan_count = secondary_wechat_scan_count + 1,
                    secondary_wechat_last_scan_date = ?,
                    updated_at = ?
                    WHERE id = ?
                ''', (current_date, current_timestamp, account_id))
            else:
                conn.execute('''
                    UPDATE mxh_accounts SET 
                    wechat_scan_count = wechat_scan_count + 1,
                    wechat_last_scan_date = ?,
                    updated_at = ?
                    WHERE id = ?
                ''', (current_date, current_timestamp, account_id))
            conn.commit()
            return jsonify({'message': 'Account marked as scanned successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/mxh/api/accounts/<int:account_id>/toggle-status', methods=['POST'])
def toggle_account_status(account_id):
    """Toggle account status between active and disabled."""
    conn = get_db_connection()
    try:
        data = request.get_json() or {}
        is_secondary = data.get('is_secondary', False)
        
        current_timestamp = datetime.now().isoformat()
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
                END,
                updated_at = ?
                WHERE id = ?
            ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), current_timestamp, account_id))
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
                END,
                updated_at = ?
                WHERE id = ?
            ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), current_timestamp, account_id))
        
        conn.commit()
        return jsonify({'message': 'Account status toggled successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/mxh/api/accounts/<int:account_id>/rescue', methods=['POST'])
def rescue_account(account_id):
    """Rescue a died account."""
    conn = get_db_connection()
    try:
        data = request.get_json() or {}
        is_secondary = data.get('is_secondary', False)
        rescue_result = data.get('result')  # 'success' or 'failed'
        
        current_timestamp = datetime.now().isoformat()
        
        if rescue_result == 'success':
            # Cứu thành công - chuyển về available và tăng success count
            if is_secondary:
                conn.execute('''
                    UPDATE mxh_accounts 
                    SET secondary_status = 'active',
                        secondary_wechat_status = 'available',
                        secondary_die_date = NULL,
                        secondary_rescue_count = 0,
                        secondary_rescue_success_count = secondary_rescue_success_count + 1,
                        updated_at = ?
                    WHERE id = ?
                ''', (current_timestamp, account_id))
            else:
                conn.execute('''
                    UPDATE mxh_accounts 
                    SET status = 'active',
                        wechat_status = 'available',
                        die_date = NULL,
                        rescue_count = 0,
                        rescue_success_count = rescue_success_count + 1,
                        updated_at = ?
                    WHERE id = ?
                ''', (current_timestamp, account_id))
            message = 'Account rescued successfully!'
        elif rescue_result == 'failed':
            # Cứu thất bại - tăng rescue count
            if is_secondary:
                conn.execute('''
                    UPDATE mxh_accounts 
                    SET secondary_rescue_count = secondary_rescue_count + 1,
                        updated_at = ?
                    WHERE id = ?
                ''', (current_timestamp, account_id))
            else:
                conn.execute('''
                    UPDATE mxh_accounts 
                    SET rescue_count = rescue_count + 1,
                        updated_at = ?
                    WHERE id = ?
                ''', (current_timestamp, account_id))
            message = 'Rescue attempt failed. Rescue count increased.'
        else:
            return jsonify({'error': 'Invalid rescue result'}), 400
        
        conn.commit()
        return jsonify({'message': message})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/mxh/api/accounts/<int:account_id>/mark-die', methods=['POST'])
def mark_account_die(account_id):
    """Mark account as died."""
    conn = get_db_connection()
    try:
        data = request.get_json() or {}
        is_secondary = data.get('is_secondary', False)
        die_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        current_timestamp = datetime.now().isoformat()  # New variable
        
        if is_secondary:
            conn.execute('''
                UPDATE mxh_accounts 
                SET secondary_status = 'disabled',
                    secondary_wechat_status = 'die',
                    secondary_die_date = ?,
                    secondary_rescue_count = 0,
                    updated_at = ?
                WHERE id = ?
            ''', (die_date, current_timestamp, account_id))
        else:
            conn.execute('''
                UPDATE mxh_accounts 
                SET status = 'disabled',
                    wechat_status = 'die',
                    die_date = ?,
                    rescue_count = 0,
                    updated_at = ?
                WHERE id = ?
            ''', (die_date, current_timestamp, account_id))
        
        conn.commit()
        return jsonify({'message': 'Account marked as died', 'die_date': die_date})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

