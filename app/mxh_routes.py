import sqlite3
import json
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, jsonify, render_template
from app.database import get_db_connection

# --- BLUEPRINT DEFINITION ---
mxh_bp = Blueprint("mxh", __name__, url_prefix="/mxh")


# ===== MXH PAGES =====
@mxh_bp.route("")
def mxh_page():
    """Render trang quản lý MXH."""
    return render_template("mxh.html", title="Mạng Xã Hội")


# ===== MXH GROUP API ROUTES =====
@mxh_bp.route("/api/groups", methods=["GET", "POST"])
def mxh_groups():
    """Get all groups or create a new group."""
    conn = get_db_connection()
    try:
        if request.method == "GET":
            groups = conn.execute(
                "SELECT * FROM mxh_groups ORDER BY created_at DESC"
            ).fetchall()
            return jsonify([dict(group) for group in groups])

        elif request.method == "POST":
            data = request.get_json()
            name = data.get("name")
            color = data.get("color")

            if not name or not color:
                return jsonify({"error": "Name and color are required"}), 400

            # Auto-assign platform icons based on group name
            platform_icons = {
                "wechat": "bi-wechat",
                "facebook": "bi-facebook",
                "instagram": "bi-instagram",
                "tiktok": "bi-tiktok",
                "youtube": "bi-youtube",
                "twitter": "bi-twitter",
                "linkedin": "bi-linkedin",
                "zalo": "bi-chat-dots",
                "telegram": "bi-telegram",
                "whatsapp": "bi-whatsapp",
            }
            icon = platform_icons.get(name.lower(), "bi-share-fill")

            try:
                cursor = conn.execute(
                    "INSERT INTO mxh_groups (name, color, icon, created_at) VALUES (?, ?, ?, ?)",
                    (name, color, icon, datetime.now().isoformat()),
                )
                conn.commit()
                group_id = cursor.lastrowid
                return (
                    jsonify(
                        {
                            "id": group_id,
                            "name": name,
                            "color": color,
                            "icon": icon,
                            "message": "Group created successfully",
                        }
                    ),
                    201,
                )
            except sqlite3.IntegrityError:
                return (
                    jsonify(
                        {"error": f'Nhóm "{name}" đã tồn tại. Vui lòng chọn tên khác.'}
                    ),
                    400,
                )

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@mxh_bp.route("/api/groups/<int:group_id>", methods=["DELETE"])
def delete_mxh_group(group_id):
    """Delete a group if it has no accounts."""
    conn = get_db_connection()
    try:
        # Check if group has accounts
        accounts = conn.execute(
            "SELECT COUNT(*) FROM mxh_accounts WHERE group_id = ?", (group_id,)
        ).fetchone()[0]
        if accounts > 0:
            return jsonify({"error": "Cannot delete group with existing accounts"}), 400

        conn.execute("DELETE FROM mxh_groups WHERE id = ?", (group_id,))
        conn.commit()
        return jsonify({"message": "Group deleted successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


# ===== MXH ACCOUNT API ROUTES =====
@mxh_bp.route("/api/accounts", methods=["GET", "POST"])
def mxh_accounts():
    """Get all cards with their sub-accounts or create a new card."""
    conn = get_db_connection()
    try:
        if request.method == "GET":
            # Get all cards with their group information
            cards = conn.execute(
                """
                SELECT c.*, g.name as group_name, g.color as group_color, g.icon as group_icon 
                FROM mxh_accounts c 
                LEFT JOIN mxh_groups g ON c.group_id = g.id 
                ORDER BY c.created_at DESC
            """
            ).fetchall()

            result = []
            for card in cards:
                card_dict = dict(card)
                
                # Get all sub-accounts for this card
                sub_accounts = conn.execute(
                    """
                    SELECT * FROM mxh_sub_accounts 
                    WHERE card_id = ? 
                    ORDER BY is_primary DESC, created_at ASC
                    """,
                    (card['id'],)
                ).fetchall()
                
                # Parse notice JSON field for each sub-account
                parsed_sub_accounts = []
                for sub_account in sub_accounts:
                    sub_dict = dict(sub_account)
                    
                    # Parse notice field if exists
                    if sub_dict.get("notice"):
                        try:
                            parsed = json.loads(sub_dict["notice"])
                            
                            # Normalize start_at to JavaScript-compatible ISO format
                            sa = parsed.get("start_at")
                            if sa:
                                try:
                                    dt = datetime.fromisoformat(sa.replace("Z", "+00:00"))
                                    sa_norm = (
                                        dt.astimezone(timezone.utc)
                                        .isoformat(timespec="milliseconds")
                                        .replace("+00:00", "Z")
                                    )
                                    parsed["start_at"] = sa_norm
                                except Exception:
                                    parsed["start_at"] = None
                            
                            sub_dict["notice"] = parsed
                        except Exception as e:
                            print(f"❌ Error parsing notice for sub-account {sub_dict.get('id')}: {e}")
                            sub_dict["notice"] = {
                                "enabled": False,
                                "title": "",
                                "days": 0,
                                "note": "",
                                "start_at": None,
                            }
                    else:
                        sub_dict["notice"] = {
                            "enabled": False,
                            "title": "",
                            "days": 0,
                            "note": "",
                            "start_at": None,
                        }
                    
                    parsed_sub_accounts.append(sub_dict)
                
                card_dict["sub_accounts"] = parsed_sub_accounts
                result.append(card_dict)

            return jsonify(result)

        elif request.method == "POST":
            data = request.get_json()
            card_name = data.get("card_name")
            group_id = data.get("group_id")
            platform = data.get("platform")
            username = data.get("username")
            url = data.get("url", "")
            phone = data.get("phone", "")
            login_username = data.get("login_username", "")
            login_password = data.get("login_password", "")

            # WeChat specific fields
            now = datetime.now()
            wechat_created_day = data.get("wechat_created_day", now.day)
            wechat_created_month = data.get("wechat_created_month", now.month)
            wechat_created_year = data.get("wechat_created_year", now.year)
            wechat_scan_create = data.get("wechat_scan_create", 0)
            wechat_scan_rescue = data.get("wechat_scan_rescue", 0)
            wechat_status = data.get("wechat_status", "available")

            if not all([card_name, group_id, platform, username]):
                return (
                    jsonify(
                        {
                            "error": "Card name, group, platform and username are required"
                        }
                    ),
                    400,
                )

            # Create the card first
            cursor = conn.execute(
                """INSERT INTO mxh_accounts (card_name, group_id, platform, created_at) 
                   VALUES (?, ?, ?, ?)""",
                (card_name, group_id, platform, datetime.now().isoformat())
            )
            card_id = cursor.lastrowid
            
            # Create the primary sub-account
            conn.execute(
                """INSERT INTO mxh_sub_accounts 
                   (card_id, is_primary, account_name, username, phone, url, login_username, login_password, created_at,
                    wechat_created_day, wechat_created_month, wechat_created_year,
                    wechat_scan_create, wechat_scan_rescue, wechat_status) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    card_id, 1, 'Tài khoản chính', username, phone, url, login_username, login_password, 
                    datetime.now().isoformat(), wechat_created_day, wechat_created_month, wechat_created_year,
                    wechat_scan_create, wechat_scan_rescue, wechat_status
                )
            )
            conn.commit()
            return jsonify({"message": "Card and primary account created successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@mxh_bp.route("/api/accounts/<int:card_id>", methods=["PUT", "DELETE"])
def update_delete_mxh_card(card_id):
    """Update card information or delete a card with all its sub-accounts."""
    print(f"\n{'='*60}", flush=True)
    print(
        f"🔔 ENDPOINT CALLED: {request.method} /api/accounts/{card_id}", flush=True
    )
    conn = get_db_connection()
    try:
        if request.method == "PUT":
            print(f"📝 Entering PUT block...", flush=True)
            data = request.get_json()
            print(f"   Parsed JSON data: {data}")

            if data is None:
                print("   ❌ ERROR: request.get_json() returned None!")
                return jsonify({"error": "Invalid JSON or empty body"}), 400

            # Separate card fields from sub-account fields
            card_fields = {
                "card_name": data.get("card_name"),
                "platform": data.get("platform")
            }
            
            # Filter out None values for card fields
            card_fields = {k: v for k, v in card_fields.items() if v is not None}
            
            # Update card information if there are card fields to update
            if card_fields:
                card_fields["updated_at"] = datetime.now().isoformat()
                set_clause = ", ".join([f"{key} = ?" for key in card_fields.keys()])
                params = list(card_fields.values()) + [card_id]
                sql = f"UPDATE mxh_accounts SET {set_clause} WHERE id = ?"
                print(f"   Card SQL: {sql}")
                conn.execute(sql, params)

            # Handle sub-account updates if specified
            sub_account_id = data.get("sub_account_id")
            if sub_account_id:
                sub_account_fields = {
                    "username": data.get("username"),
                    "phone": data.get("phone"),
                    "url": data.get("url"),
                    "login_username": data.get("login_username"),
                    "login_password": data.get("login_password"),
                    "wechat_created_day": data.get("wechat_created_day"),
                    "wechat_created_month": data.get("wechat_created_month"),
                    "wechat_created_year": data.get("wechat_created_year"),
                    "wechat_status": data.get("wechat_status"),
                    "status": data.get("status"),
                    "email_reset_date": data.get("email_reset_date"),
                    "notice": data.get("notice")
                }
                
                # Filter out None values
                sub_account_fields = {k: v for k, v in sub_account_fields.items() if v is not None}
                
                if sub_account_fields:
                    sub_account_fields["updated_at"] = datetime.now().isoformat()
                    set_clause = ", ".join([f"{key} = ?" for key in sub_account_fields.keys()])
                    params = list(sub_account_fields.values()) + [sub_account_id]
                    sql = f"UPDATE mxh_sub_accounts SET {set_clause} WHERE id = ?"
                    print(f"   Sub-account SQL: {sql}")
                    conn.execute(sql, params)

            conn.commit()
            print(f"   ✅ Updated successfully!")
            return jsonify({"message": "Card updated successfully"})

        elif request.method == "DELETE":
            # Delete card (this will cascade delete all sub-accounts due to FOREIGN KEY constraint)
            conn.execute("DELETE FROM mxh_accounts WHERE id = ?", (card_id,))
            conn.commit()
            return jsonify({"message": "Card and all sub-accounts deleted successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


# ===== QUICK UPDATE API (FOR INLINE EDITING) =====
@mxh_bp.route("/api/sub_accounts/<int:sub_account_id>/quick-update", methods=["POST"])
def quick_update_sub_account(sub_account_id):
    """Quick update for inline editing (username, phone, status) of a sub-account."""
    conn = get_db_connection()
    try:
        data = request.get_json()
        field = data.get("field")  # 'username', 'phone', or 'status'
        value = data.get("value")

        if not field:
            return jsonify({"error": "Field is required"}), 400

        column = field

        # Validate field name to prevent SQL injection
        allowed_fields = ["username", "phone", "status"]
        if column not in allowed_fields:
            return jsonify({"error": "Invalid field"}), 400

        conn.execute(
            f"UPDATE mxh_sub_accounts SET {column} = ?, updated_at = ? WHERE id = ?", 
            (value, datetime.now().isoformat(), sub_account_id)
        )
        conn.commit()

        return jsonify(
            {"message": "Field updated successfully", "field": field, "value": value}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


# ===== NOTICE API ROUTES =====
@mxh_bp.route("/api/sub_accounts/<int:sub_account_id>/notice", methods=["PUT"])
def api_set_notice(sub_account_id):
    """Set or update notice for a sub-account."""
    conn = get_db_connection()
    try:
        data = request.get_json(force=True) or {}
        title = str(data.get("title", "")).strip()
        days = int(data.get("days", 0))
        note = str(data.get("note", "")).strip()

        if not title or days <= 0:
            return jsonify({"error": "invalid"}), 400

        # Format time as ISO 8601 with milliseconds and Z (UTC) for JavaScript compatibility
        now_iso = (
            datetime.now(timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z")
        )
        notice_json = {
            "enabled": True,
            "title": title,
            "days": days,
            "note": note,
            "start_at": now_iso,
        }

        conn.execute(
            "UPDATE mxh_sub_accounts SET notice = ?, updated_at = ? WHERE id = ?",
            (json.dumps(notice_json), datetime.now().isoformat(), sub_account_id),
        )
        conn.commit()

        return jsonify({"ok": True, "notice": notice_json})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@mxh_bp.route("/api/sub_accounts/<int:sub_account_id>/notice", methods=["DELETE"])
def api_clear_notice(sub_account_id):
    """Clear notice for a sub-account."""
    conn = get_db_connection()
    try:
        notice_json = {
            "enabled": False,
            "title": "",
            "days": 0,
            "note": "",
            "start_at": None,
        }

        conn.execute(
            "UPDATE mxh_sub_accounts SET notice = ?, updated_at = ? WHERE id = ?",
            (json.dumps(notice_json), datetime.now().isoformat(), sub_account_id),
        )
        conn.commit()

        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


# ===== SCAN API ROUTES =====
@mxh_bp.route("/api/sub_accounts/<int:sub_account_id>/scan", methods=["POST"])
def mark_account_scanned(sub_account_id):
    """Mark sub-account as scanned or reset scan count."""
    conn = get_db_connection()
    try:
        data = request.get_json() or {}

        if data.get("reset"):
            # Reset scan count and last scan date
            conn.execute(
                """
                UPDATE mxh_sub_accounts SET 
                wechat_scan_count = 0,
                wechat_last_scan_date = NULL,
                updated_at = ?
                WHERE id = ?
            """,
                (datetime.now().isoformat(), sub_account_id),
            )
            conn.commit()
            return jsonify({"message": "Scan count reset successfully"})
        else:
            # Update scan count and last scan date
            current_date = datetime.now().isoformat()
            conn.execute(
                """
                UPDATE mxh_sub_accounts SET 
                wechat_scan_count = wechat_scan_count + 1,
                wechat_last_scan_date = ?,
                updated_at = ?
                WHERE id = ?
            """,
                (current_date, datetime.now().isoformat(), sub_account_id),
            )
            conn.commit()
            return jsonify({"message": "Account marked as scanned successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


# ===== STATUS TOGGLE API ROUTES =====
@mxh_bp.route("/api/sub_accounts/<int:sub_account_id>/toggle-status", methods=["POST"])
def toggle_account_status(sub_account_id):
    """Toggle sub-account status between active and disabled."""
    conn = get_db_connection()
    try:
        data = request.get_json() or {}

        # Toggle sub-account status
        conn.execute(
            """
            UPDATE mxh_sub_accounts 
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
        """,
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), datetime.now().isoformat(), sub_account_id),
        )

        conn.commit()
        return jsonify({"message": "Account status toggled successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


# ===== RESCUE API ROUTES =====
@mxh_bp.route("/api/sub_accounts/<int:sub_account_id>/rescue", methods=["POST"])
def rescue_account(sub_account_id):
    """Rescue a died sub-account."""
    conn = get_db_connection()
    try:
        data = request.get_json() or {}
        rescue_result = data.get("result")  # 'success' or 'failed'

        if rescue_result == "success":
            # Cứu thành công - chuyển về available và tăng success count
            conn.execute(
                """
                UPDATE mxh_sub_accounts 
                SET status = 'active',
                    die_date = NULL,
                    rescue_success_count = rescue_success_count + 1,
                    updated_at = ?
                WHERE id = ?
            """,
                (datetime.now().isoformat(), sub_account_id),
            )
            message = "Account rescued successfully!"
        elif rescue_result == "failed":
            # Cứu thất bại - tăng rescue count
            conn.execute(
                """
                UPDATE mxh_sub_accounts 
                SET rescue_count = rescue_count + 1,
                    updated_at = ?
                WHERE id = ?
            """,
                (datetime.now().isoformat(), sub_account_id),
            )
            message = "Rescue attempt failed. Rescue count increased."
        else:
            return jsonify({"error": "Invalid rescue result"}), 400

        conn.commit()
        return jsonify({"message": message})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@mxh_bp.route("/api/sub_accounts/<int:sub_account_id>/mark-die", methods=["POST"])
def mark_account_die(sub_account_id):
    """Mark sub-account as died."""
    conn = get_db_connection()
    try:
        data = request.get_json() or {}
        die_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn.execute(
            """
            UPDATE mxh_sub_accounts 
            SET status = 'disabled',
                die_date = ?,
                rescue_count = 0,
                updated_at = ?
            WHERE id = ?
        """,
            (die_date, datetime.now().isoformat(), sub_account_id),
        )

        conn.commit()
        return jsonify({"message": "Account marked as died", "die_date": die_date})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


# ===== SUB-ACCOUNT MANAGEMENT API ROUTES =====
@mxh_bp.route("/api/cards/<int:card_id>/sub_accounts", methods=["POST"])
def create_sub_account(card_id):
    """Create a new sub-account for a card."""
    conn = get_db_connection()
    try:
        data = request.get_json()
        
        # Validate required fields
        username = data.get("username")
        if not username:
            return jsonify({"error": "Username is required"}), 400
        
        # Check if card exists
        card = conn.execute("SELECT * FROM mxh_accounts WHERE id = ?", (card_id,)).fetchone()
        if not card:
            return jsonify({"error": "Card not found"}), 404
        
        # Create sub-account
        cursor = conn.execute(
            """INSERT INTO mxh_sub_accounts 
               (card_id, is_primary, account_name, username, phone, url, login_username, login_password, created_at,
                wechat_created_day, wechat_created_month, wechat_created_year,
                wechat_scan_create, wechat_scan_rescue, wechat_status, status) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                card_id, 0, data.get("account_name", "Tài khoản phụ"), username,
                data.get("phone", ""), data.get("url", ""), data.get("login_username", ""),
                data.get("login_password", ""), datetime.now().isoformat(),
                data.get("wechat_created_day", 1), data.get("wechat_created_month", 1),
                data.get("wechat_created_year", 2024), data.get("wechat_scan_create", 0),
                data.get("wechat_scan_rescue", 0), data.get("wechat_status", "available"),
                data.get("status", "active")
            )
        )
        
        conn.commit()
        sub_account_id = cursor.lastrowid
        
        return jsonify({
            "message": "Sub-account created successfully",
            "sub_account_id": sub_account_id
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@mxh_bp.route("/api/sub_accounts/<int:sub_account_id>", methods=["PUT"])
def update_sub_account(sub_account_id):
    """Update a sub-account."""
    conn = get_db_connection()
    try:
        data = request.get_json()
        
        # Get allowed fields for update
        allowed_fields = [
            "account_name", "username", "phone", "url", "login_username", "login_password",
            "wechat_created_day", "wechat_created_month", "wechat_created_year",
            "wechat_scan_create", "wechat_scan_rescue", "wechat_status", "status",
            "muted_until", "die_date", "wechat_scan_count", "wechat_last_scan_date",
            "rescue_count", "rescue_success_count", "email_reset_date", "notice"
        ]
        
        fields_to_update = {k: v for k, v in data.items() if k in allowed_fields and v is not None}
        
        if not fields_to_update:
            return jsonify({"message": "No fields to update"})
        
        # Add updated_at timestamp
        fields_to_update["updated_at"] = datetime.now().isoformat()
        
        set_clause = ", ".join([f"{key} = ?" for key in fields_to_update.keys()])
        params = list(fields_to_update.values()) + [sub_account_id]
        
        conn.execute(
            f"UPDATE mxh_sub_accounts SET {set_clause} WHERE id = ?",
            params
        )
        conn.commit()
        
        return jsonify({"message": "Sub-account updated successfully"})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@mxh_bp.route("/api/sub_accounts/<int:sub_account_id>", methods=["DELETE"])
def delete_sub_account(sub_account_id):
    """Delete a sub-account."""
    conn = get_db_connection()
    try:
        # Check if sub-account exists
        sub_account = conn.execute(
            "SELECT * FROM mxh_sub_accounts WHERE id = ?", (sub_account_id,)
        ).fetchone()
        
        if not sub_account:
            return jsonify({"error": "Sub-account not found"}), 404
        
        # Don't allow deletion of primary account
        if sub_account['is_primary']:
            return jsonify({"error": "Cannot delete primary account"}), 400
        
        # Delete the sub-account
        conn.execute("DELETE FROM mxh_sub_accounts WHERE id = ?", (sub_account_id,))
        conn.commit()
        
        return jsonify({"message": "Sub-account deleted successfully"})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()
