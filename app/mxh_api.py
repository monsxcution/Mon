import sqlite3
import json
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from app.database import get_db_connection

mxh_api_bp = Blueprint("mxh_api", __name__, url_prefix="/mxh/api")


@mxh_api_bp.route("/cards", methods=["POST"])
def create_card():
    """
    POST /mxh/api/cards
    Create a new card with validation for unique card_name within group_id.
    """
    conn = get_db_connection()
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        # Validate required fields
        card_name = data.get("card_name")
        group_id = data.get("group_id")
        platform = data.get("platform")
        
        if not card_name:
            return jsonify({"error": "card_name is required", "field": "card_name"}), 400
        if not group_id:
            return jsonify({"error": "group_id is required", "field": "group_id"}), 400
        if not platform:
            return jsonify({"error": "platform is required", "field": "platform"}), 400
        
        # Check if card_name is unique within the same group_id
        existing_card = conn.execute(
            "SELECT id FROM mxh_card WHERE card_name = ? AND group_id = ?",
            (card_name, group_id)
        ).fetchone()
        
        if existing_card:
            return jsonify({
                "error": f"Card name '{card_name}' already exists in group {group_id}",
                "field": "card_name"
            }), 400
        
        # Create the card
        now = datetime.now(timezone.utc).astimezone().isoformat()
        cursor = conn.execute(
            "INSERT INTO mxh_card (card_name, group_id, platform, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (card_name, group_id, platform, now, now)
        )
        card_id = cursor.lastrowid
        
        conn.commit()
        
        # Return the created card
        new_card = conn.execute("SELECT * FROM mxh_card WHERE id = ?", (card_id,)).fetchone()
        card_dict = dict(new_card)
        card_dict["accounts"] = []  # Empty accounts array as specified
        
        return jsonify(card_dict), 201
        
    except sqlite3.IntegrityError as e:
        conn.rollback()
        return jsonify({"error": f"Database constraint violation: {str(e)}"}), 400
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@mxh_api_bp.route("/cards", methods=["GET"])
def get_cards():
    """
    GET /mxh/api/cards?group_id=&platform=
    Return a list of cards with accounts_summary.
    """
    conn = get_db_connection()
    try:
        group_id = request.args.get("group_id")
        platform = request.args.get("platform")
        
        # Build query with optional filters
        query = "SELECT * FROM mxh_card WHERE 1=1"
        params = []
        
        if group_id:
            query += " AND group_id = ?"
            params.append(group_id)
        
        if platform:
            query += " AND platform = ?"
            params.append(platform)
        
        query += " ORDER BY card_name"
        
        cards = conn.execute(query, params).fetchall()
        
        # Convert to list of dictionaries with accounts_summary
        result = []
        for card in cards:
            card_dict = dict(card)
            # Static accounts_summary as specified
            card_dict["accounts_summary"] = {
                "count": 0,
                "primary_account_id": None
            }
            result.append(card_dict)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@mxh_api_bp.route("/cards/<int:card_id>/accounts", methods=["POST"])
def create_account(card_id):
    """
    POST /mxh/api/cards/<card_id>/accounts
    Create a new account under the specified card.
    """
    conn = get_db_connection()
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        # Validate required fields
        account_name = data.get("account_name")
        username = data.get("username")
        phone = data.get("phone")
        
        if not account_name:
            return jsonify({"error": "account_name is required", "field": "account_name"}), 400
        if not username:
            return jsonify({"error": "username is required", "field": "username"}), 400
        if not phone:
            return jsonify({"error": "phone is required", "field": "phone"}), 400
        
        # Check if card exists
        card = conn.execute("SELECT id FROM mxh_card WHERE id = ?", (card_id,)).fetchone()
        if not card:
            return jsonify({"error": "Card not found"}), 404
        
        # Create the account
        now = datetime.now(timezone.utc).astimezone().isoformat()
        cursor = conn.execute(
            """INSERT INTO mxh_accounts (
                card_id, is_primary, account_name, username, phone, url, 
                login_username, login_password, wechat_created_day, wechat_created_month, 
                wechat_created_year, wechat_status, status, die_date, wechat_scan_count, 
                wechat_last_scan_date, rescue_count, rescue_success_count, email_reset_date, 
                notice, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                card_id,
                data.get("is_primary", 0),
                account_name,
                username,
                phone,
                data.get("url", ""),
                data.get("login_username", ""),
                data.get("login_password", ""),
                data.get("wechat_created_day"),
                data.get("wechat_created_month"),
                data.get("wechat_created_year"),
                data.get("wechat_status", "available"),
                data.get("status", "active"),
                data.get("die_date"),
                0,  # wechat_scan_count
                data.get("wechat_last_scan_date"),
                0,  # rescue_count
                0,  # rescue_success_count
                data.get("email_reset_date"),
                data.get("notice"),
                now,
                now
            )
        )
        account_id = cursor.lastrowid
        
        conn.commit()
        
        # Return the created account
        new_account = conn.execute("SELECT * FROM mxh_accounts WHERE id = ?", (account_id,)).fetchone()
        return jsonify(dict(new_account)), 201
        
    except sqlite3.IntegrityError as e:
        conn.rollback()
        return jsonify({"error": f"Database constraint violation: {str(e)}"}), 400
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()
