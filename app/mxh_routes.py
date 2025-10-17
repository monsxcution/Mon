import sqlite3
import json
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, render_template
from app.database import get_db_connection

mxh_bp = Blueprint("mxh", __name__, url_prefix="/mxh")

# ===== MXH PAGES =====
@mxh_bp.route("")
def mxh_page():
    return render_template("mxh.html", title="Mạng Xã Hội")

# ===== MXH CARD (was Group) API ROUTES =====
@mxh_bp.route("/api/groups", methods=["GET", "POST"])
def mxh_groups():
    conn = get_db_connection()
    try:
        if request.method == "GET":
            groups = conn.execute("SELECT * FROM mxh_groups ORDER BY created_at DESC").fetchall()
            return jsonify([dict(g) for g in groups])
        elif request.method == "POST":
            # ... (This function remains unchanged as it manages groups, not accounts)
            data = request.get_json()
            name = data.get("name")
            color = data.get("color")
            if not name or not color: return jsonify({"error": "Name and color are required"}), 400
            icon = {'wechat': 'bi-wechat', 'facebook': 'bi-facebook'}.get(name.lower(), 'bi-share-fill')
            cursor = conn.execute("INSERT INTO mxh_groups (name, color, icon, created_at) VALUES (?, ?, ?, ?)", (name, color, icon, datetime.now().isoformat()))
            conn.commit()
            return jsonify({"id": cursor.lastrowid, "name": name, "color": color, "icon": icon}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# ===== MXH CARD & SUB-ACCOUNT API ROUTES =====

@mxh_bp.route("/api/accounts", methods=["GET", "POST"])
def mxh_cards():
    conn = get_db_connection()
    try:
        if request.method == "GET":
            cards_query = """
                SELECT a.*, g.name as group_name, g.color as group_color, g.icon as group_icon 
                FROM mxh_accounts a 
                LEFT JOIN mxh_groups g ON a.group_id = g.id ORDER BY a.card_name
            """
            cards = conn.execute(cards_query).fetchall()
            card_ids = [c['id'] for c in cards]
            
            result = [dict(c) for c in cards]
            
            if card_ids:
                sub_accounts_query = f"SELECT * FROM mxh_sub_accounts WHERE card_id IN ({','.join('?' for _ in card_ids)}) ORDER BY is_primary DESC, id ASC"
                sub_accounts = conn.execute(sub_accounts_query, card_ids).fetchall()
                
                for card in result:
                    card['sub_accounts'] = [dict(sa) for sa in sub_accounts if sa['card_id'] == card['id']]
            
            return jsonify(result)

        elif request.method == "POST": # Creates a new CARD with one PRIMARY sub-account
            data = request.get_json()
            now_iso = datetime.now().isoformat()
            
            # Insert the main card
            cursor = conn.execute(
                "INSERT INTO mxh_accounts (card_name, group_id, platform, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (data.get('card_name'), data.get('group_id'), data.get('platform'), now_iso, now_iso)
            )
            card_id = cursor.lastrowid
            
            # Insert the primary sub-account
            conn.execute(
                """INSERT INTO mxh_sub_accounts (card_id, is_primary, account_name, username, phone, url, login_username, login_password, created_at, updated_at, wechat_created_day, wechat_created_month, wechat_created_year, status) 
                   VALUES (?, 1, 'Tài khoản chính', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (card_id, data.get('username'), data.get('phone'), data.get('url'), data.get('login_username'), data.get('login_password'), now_iso, now_iso, data.get('wechat_created_day'), data.get('wechat_created_month'), data.get('wechat_created_year'), 'active')
            )
            
            conn.commit()
            return jsonify({"message": "Card and primary account created", "card_id": card_id}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@mxh_bp.route("/api/cards/<int:card_id>", methods=["PUT", "DELETE"])
def update_delete_mxh_card(card_id):
    conn = get_db_connection()
    try:
        if request.method == "PUT": # Updates card-level info like card_name
            data = request.get_json()
            conn.execute(
                "UPDATE mxh_accounts SET card_name = ?, updated_at = ? WHERE id = ?",
                (data.get('card_name'), datetime.now().isoformat(), card_id)
            )
            conn.commit()
            return jsonify({"message": "Card updated successfully"})
        elif request.method == "DELETE": # Deletes a card and all its sub-accounts (ON DELETE CASCADE)
            conn.execute("DELETE FROM mxh_accounts WHERE id = ?", (card_id,))
            conn.commit()
            return jsonify({"message": "Card and all sub-accounts deleted"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()
        
@mxh_bp.route("/api/cards/<int:card_id>/sub_accounts", methods=["POST"])
def add_sub_account(card_id):
    conn = get_db_connection()
    try:
        data = request.get_json() or {}
        now_iso = datetime.now().isoformat()
        
        cursor = conn.execute(
            """INSERT INTO mxh_sub_accounts (card_id, is_primary, account_name, username, created_at, updated_at)
               VALUES (?, 0, ?, ?, ?, ?)""",
            (card_id, data.get('account_name', 'Tài khoản phụ'), data.get('username', ''), now_iso, now_iso)
        )
        sub_account_id = cursor.lastrowid
        conn.commit()
        
        new_sub_account = conn.execute("SELECT * FROM mxh_sub_accounts WHERE id = ?", (sub_account_id,)).fetchone()
        
        return jsonify(dict(new_sub_account)), 201
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
            fields_to_update = {k: v for k, v in data.items() if v is not None}
            if not fields_to_update:
                return jsonify({'message': 'No fields to update.'})
            
            fields_to_update['updated_at'] = datetime.now().isoformat()
            
            set_clause = ", ".join([f"{key} = ?" for key in fields_to_update.keys()])
            params = list(fields_to_update.values()) + [sub_account_id]
            
            conn.execute(f'UPDATE mxh_sub_accounts SET {set_clause} WHERE id = ?', params)
            conn.commit()
            
            updated_sub_account = conn.execute("SELECT * FROM mxh_sub_accounts WHERE id = ?", (sub_account_id,)).fetchone()
            return jsonify(dict(updated_sub_account))
            
        elif request.method == "DELETE":
            sub_account = conn.execute("SELECT is_primary FROM mxh_sub_accounts WHERE id = ?", (sub_account_id,)).fetchone()
            if sub_account and sub_account['is_primary']:
                return jsonify({"error": "Cannot delete the primary sub-account."}), 400
                
            conn.execute("DELETE FROM mxh_sub_accounts WHERE id = ?", (sub_account_id,))
            conn.commit()
            return jsonify({"message": "Sub-account deleted"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# Keep other endpoints like /scan, /toggle-status, /rescue but modify them to accept sub_account_id
# Example for /scan:
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
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# You would similarly refactor toggle-status, rescue, mark-die, notice, etc. to operate on mxh_sub_accounts with a sub_account_id.