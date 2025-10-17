import sqlite3
import json
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, render_template
from app.database import get_db_connection

mxh_bp = Blueprint("mxh", __name__, url_prefix="/mxh")

@mxh_bp.route("")
def mxh_page():
    return render_template("mxh.html", title="Mạng Xã Hội")

@mxh_bp.route("/api/groups", methods=["GET", "POST"])
def mxh_groups():
    # This function for managing groups remains the same
    conn = get_db_connection()
    try:
        if request.method == "GET":
            groups = conn.execute("SELECT * FROM mxh_groups ORDER BY created_at DESC").fetchall()
            return jsonify([dict(g) for g in groups])
        elif request.method == "POST":
            data = request.get_json()
            name, color = data.get("name"), data.get("color")
            if not name or not color: return jsonify({"error": "Name and color are required"}), 400
            platform_icons = {"wechat": "bi-wechat", "facebook": "bi-facebook", "instagram": "bi-instagram", "tiktok": "bi-tiktok", "youtube": "bi-youtube", "twitter": "bi-twitter", "linkedin": "bi-linkedin", "zalo": "bi-chat-dots", "telegram": "bi-telegram", "whatsapp": "bi-whatsapp"}
            icon = platform_icons.get(name.lower(), "bi-share-fill")
            try:
                cursor = conn.execute("INSERT INTO mxh_groups (name, color, icon, created_at) VALUES (?, ?, ?, ?)", (name, color, icon, datetime.now().isoformat()))
                conn.commit()
                return jsonify({"id": cursor.lastrowid, "name": name, "color": color, "icon": icon, "message": "Group created"}), 201
            except sqlite3.IntegrityError:
                return jsonify({"error": f'Group "{name}" already exists.'}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@mxh_bp.route("/api/accounts", methods=["GET", "POST"])
def mxh_cards_and_sub_accounts():
    conn = get_db_connection()
    try:
        if request.method == "GET":
            # Lấy thông tin card từ mxh_cards
            cards = conn.execute("SELECT c.*, g.name as group_name, g.color as group_color, g.icon as group_icon FROM mxh_cards c LEFT JOIN mxh_groups g ON c.group_id = g.id ORDER BY CAST(c.card_name AS INTEGER)").fetchall()
            result = [dict(c) for c in cards]
            card_ids = [c['id'] for c in result]
            
            # Lấy tất cả sub-accounts liên quan
            if card_ids:
                placeholders = ','.join('?' for _ in card_ids)
                sub_accounts = conn.execute(f"SELECT * FROM mxh_sub_accounts WHERE card_id IN ({placeholders}) ORDER BY is_primary DESC, id ASC", card_ids).fetchall()
                # Gán sub-accounts vào card tương ứng
                for card in result:
                    card['sub_accounts'] = [dict(sa) for sa in sub_accounts if sa['card_id'] == card['id']]
            return jsonify(result)

        elif request.method == "POST":
            data = request.get_json()
            now_iso = datetime.now().isoformat()
            
            # 1. Tạo card trong mxh_cards
            cursor = conn.execute("INSERT INTO mxh_cards (card_name, group_id, platform, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (data.get('card_name'), data.get('group_id'), data.get('platform'), now_iso, now_iso))
            card_id = cursor.lastrowid
            
            # 2. Tạo sub-account chính trong mxh_sub_accounts
            conn.execute("""INSERT INTO mxh_sub_accounts (card_id, is_primary, account_name, username, phone, url, login_username, login_password, created_at, updated_at, wechat_created_day, wechat_created_month, wechat_created_year, status) 
                            VALUES (?, 1, 'Tài khoản chính', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (card_id, data.get('username'), data.get('phone'), data.get('url'), data.get('login_username'), data.get('login_password'), now_iso, now_iso, data.get('wechat_created_day'), data.get('wechat_created_month'), data.get('wechat_created_year'), 'active'))
            
            conn.commit()
            return jsonify({"message": "Card created", "card_id": card_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@mxh_bp.route("/api/cards/<int:card_id>", methods=["PUT", "DELETE"])
def update_delete_card(card_id):
    conn = get_db_connection()
    try:
        if request.method == "PUT":
            data = request.get_json()
            # Hàm này CHỈ cập nhật thông tin của card (bảng mxh_cards)
            conn.execute("UPDATE mxh_cards SET card_name = ?, updated_at = ? WHERE id = ?", 
                         (data.get('card_name'), datetime.now().isoformat(), card_id))
            conn.commit()
            return jsonify({"message": "Card updated"})
        elif request.method == "DELETE":
            # Xóa card sẽ tự động xóa các sub-accounts liên quan nhờ 'ON DELETE CASCADE'
            conn.execute("DELETE FROM mxh_cards WHERE id = ?", (card_id,))
            conn.commit()
            return jsonify({"message": "Card and all associated sub-accounts deleted"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@mxh_bp.route("/api/accounts/<int:account_id>/quick-update", methods=["POST"])
def quick_update_account(account_id):
    conn = get_db_connection()
    try:
        data = request.get_json()
        fields = {k: v for k, v in data.items() if v is not None}
        if not fields: return jsonify({'message': 'No fields to update.'})
        fields['updated_at'] = datetime.now().isoformat()
        set_clause = ", ".join([f"{key} = ?" for key in fields.keys()])
        params = list(fields.values()) + [account_id]
        conn.execute(f'UPDATE mxh_accounts SET {set_clause} WHERE id = ?', params)
        conn.commit()
        updated = conn.execute("SELECT * FROM mxh_accounts WHERE id = ?", (account_id,)).fetchone()
        return jsonify(dict(updated))
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@mxh_bp.route("/api/cards/<int:card_id>", methods=["PUT", "DELETE"])
def update_delete_card(card_id):
    conn = get_db_connection()
    try:
        if request.method == "PUT":
            data = request.get_json()
            conn.execute("UPDATE mxh_cards SET card_name = ?, updated_at = ? WHERE id = ?", (data.get('card_name'), datetime.now().isoformat(), card_id))
            conn.commit()
            return jsonify({"message": "Card updated"})
        elif request.method == "DELETE":
            conn.execute("DELETE FROM mxh_cards WHERE id = ?", (card_id,))
            conn.commit()
            return jsonify({"message": "Card and sub-accounts deleted"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@mxh_bp.route("/api/cards/<int:card_id>/sub_accounts", methods=["POST"])
def add_sub_account(card_id):
    conn = get_db_connection()
    try:
        now_iso = datetime.now().isoformat()
        cursor = conn.execute("INSERT INTO mxh_sub_accounts (card_id, is_primary, created_at, updated_at, account_name) VALUES (?, 0, ?, ?, ?)", 
                              (card_id, now_iso, now_iso, 'Tài khoản phụ'))
        sub_account_id = cursor.lastrowid
        conn.commit()
        new_sub = conn.execute("SELECT * FROM mxh_sub_accounts WHERE id = ?", (sub_account_id,)).fetchone()
        return jsonify(dict(new_sub)), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@mxh_bp.route("/api/sub_accounts/<int:sub_account_id>", methods=["PUT", "DELETE"])
def manage_sub_account(sub_account_id):
    conn = get_db_connection()
    try:
        if request.method == "PUT":
            data = request.get_json()
            # Lọc ra các trường cần cập nhật, loại bỏ các giá trị None
            fields = {k: v for k, v in data.items() if v is not None}
            if 'card_name' in fields:
                # Không cho phép cập nhật card_name ở đây
                del fields['card_name']

            if not fields: 
                return jsonify({'message': 'No fields to update.'})

            fields['updated_at'] = datetime.now().isoformat()
            
            set_clause = ", ".join([f"{key} = ?" for key in fields.keys()])
            params = list(fields.values()) + [sub_account_id]
            
            conn.execute(f'UPDATE mxh_sub_accounts SET {set_clause} WHERE id = ?', params)
            conn.commit()
            
            updated = conn.execute("SELECT * FROM mxh_sub_accounts WHERE id = ?", (sub_account_id,)).fetchone()
            return jsonify(dict(updated))

        elif request.method == "DELETE":
            sub_account = conn.execute("SELECT is_primary FROM mxh_sub_accounts WHERE id = ?", (sub_account_id,)).fetchone()
            if sub_account and sub_account['is_primary']:
                return jsonify({"error": "Cannot delete the primary sub-account"}), 400
            
            conn.execute("DELETE FROM mxh_sub_accounts WHERE id = ?", (sub_account_id,))
            conn.commit()
            return jsonify({"message": "Sub-account deleted"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# Refactored endpoints to target sub-accounts
@mxh_bp.route("/api/sub_accounts/<int:sub_account_id>/scan", methods=["POST"])
def scan_sub_account(sub_account_id):
    conn = get_db_connection()
    try:
        data = request.get_json() or {}
        now_iso = datetime.now().isoformat()
        if data.get('reset'):
            conn.execute("UPDATE mxh_sub_accounts SET wechat_scan_count = 0, wechat_last_scan_date = NULL, updated_at = ? WHERE id = ?", (now_iso, sub_account_id))
        else:
            conn.execute("UPDATE mxh_sub_accounts SET wechat_scan_count = wechat_scan_count + 1, wechat_last_scan_date = ?, updated_at = ? WHERE id = ?", (now_iso, now_iso, sub_account_id))
        conn.commit()
        return jsonify({"message": "Scan status updated"})
    finally: conn.close()

@mxh_bp.route("/api/sub_accounts/<int:sub_account_id>/toggle-status", methods=["POST"])
def toggle_sub_account_status(sub_account_id):
    conn = get_db_connection()
    try:
        now_iso = datetime.now().isoformat()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("UPDATE mxh_sub_accounts SET status = CASE WHEN status = 'disabled' THEN 'active' ELSE 'disabled' END, die_date = CASE WHEN status = 'disabled' THEN NULL ELSE ? END, updated_at = ? WHERE id = ?", (now_str, now_iso, sub_account_id))
        conn.commit()
        return jsonify({"message": "Status toggled"})
    finally: conn.close()

@mxh_bp.route("/api/sub_accounts/<int:sub_account_id>/rescue", methods=["POST"])
def rescue_sub_account(sub_account_id):
    conn = get_db_connection()
    try:
        result = request.get_json().get('result')
        now_iso = datetime.now().isoformat()
        if result == 'success':
            conn.execute("UPDATE mxh_sub_accounts SET status = 'active', die_date = NULL, rescue_success_count = rescue_success_count + 1, updated_at = ? WHERE id = ?", (now_iso, sub_account_id))
            message = "Rescued successfully"
        elif result == 'failed':
            conn.execute("UPDATE mxh_sub_accounts SET rescue_count = rescue_count + 1, updated_at = ? WHERE id = ?", (now_iso, sub_account_id))
            message = "Rescue attempt failed"
        else:
            return jsonify({"error": "Invalid result"}), 400
        conn.commit()
        return jsonify({"message": message})
    finally: conn.close()

@mxh_bp.route("/api/sub_accounts/<int:sub_account_id>/mark-die", methods=["POST"])
def mark_sub_account_die(sub_account_id):
    conn = get_db_connection()
    try:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        now_iso = datetime.now().isoformat()
        conn.execute("UPDATE mxh_sub_accounts SET status = 'disabled', die_date = ?, rescue_count = 0, updated_at = ? WHERE id = ?", (now_str, now_iso, sub_account_id))
        conn.commit()
        return jsonify({"message": "Marked as died", "die_date": now_str})
    finally: conn.close()

@mxh_bp.route("/api/sub_accounts/<int:sub_account_id>/notice", methods=["PUT", "DELETE"])
def notice_sub_account(sub_account_id):
    conn = get_db_connection()
    try:
        if request.method == "PUT":
            data = request.get_json()
            notice = json.dumps({"enabled": True, "title": data.get("title"), "days": data.get("days"), "note": data.get("note"), "start_at": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")})
            conn.execute("UPDATE mxh_sub_accounts SET notice = ?, updated_at = ? WHERE id = ?", (notice, datetime.now().isoformat(), sub_account_id))
            conn.commit()
            return jsonify({"message": "Notice set", "notice": json.loads(notice)})
        elif request.method == "DELETE":
            notice = json.dumps({"enabled": False, "title": "", "days": 0, "note": "", "start_at": None})
            conn.execute("UPDATE mxh_sub_accounts SET notice = ?, updated_at = ? WHERE id = ?", (notice, datetime.now().isoformat(), sub_account_id))
            conn.commit()
            return jsonify({"message": "Notice cleared"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()