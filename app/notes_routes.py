import uuid
import os
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, send_from_directory
import sqlite3
from bs4 import BeautifulSoup

# --- CONFIG & HELPERS (Copied from temp_Main.pyw) ---
APP_ROOT = os.path.dirname(os.path.abspath(os.path.join(__file__, os.pardir)))
DATA_DIR = os.path.join(APP_ROOT, "data")
DATABASE_PATH = os.path.join(DATA_DIR, "Data.db")
SOUNDS_FOLDER = os.path.join(DATA_DIR, "sounds")

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# --- BLUEPRINT DEFINITION ---
notes_bp = Blueprint("notes_feature", __name__, url_prefix="/notes")

# --- GLOBAL VARS FOR NOTES (Copied from temp_Main.pyw) ---
NOTIFICATIONS_QUEUE = []

# --- CORE FUNCTIONS (Copied from temp_Main.pyw, lines 1459-1507) ---
def check_and_queue_reminders():
    """Checks for due reminders from SQLite and queues them for notification."""
    conn = get_db_connection()
    now_utc_iso = datetime.now(timezone.utc).isoformat()
    due_notes = conn.execute(
        "SELECT * FROM notes WHERE status = 'active' AND due_time IS NOT NULL AND due_time <= ?",
        (now_utc_iso,)
    ).fetchall()

    if not due_notes:
        conn.close()
        return

    sound_files = []
    if os.path.exists(SOUNDS_FOLDER):
        sound_files = [f for f in os.listdir(SOUNDS_FOLDER) if f.endswith((".wav", ".mp3", ".ogg"))]
    
    ids_to_update = []
    for note in due_notes:
        note_dict = dict(note)
        title_lower = (note_dict.get("title_html") or "").lower() # Use title_html
        sound_url = "/notes/sounds/notification.wav" # Default
        for sf in sound_files:
            if os.path.splitext(sf)[0].lower() in title_lower:
                sound_url = f"/notes/sounds/{sf}"
                break
        
        notification_payload = {
            "id": note_dict["id"],
            "title": BeautifulSoup(note_dict["title_html"], "html.parser").get_text(),
            "notes": note_dict.get("content_html", ""),
            "sound_url": sound_url
        }
        if not any(q['id'] == note_dict['id'] for q in NOTIFICATIONS_QUEUE):
            NOTIFICATIONS_QUEUE.append(notification_payload)
        
        ids_to_update.append(note_dict["id"])

    if ids_to_update:
        # Update status in bulk
        placeholders = ','.join('?' for _ in ids_to_update)
        conn.execute(f"UPDATE notes SET status = 'notified', due_time = NULL WHERE id IN ({placeholders})", ids_to_update)
        conn.commit()
    
    conn.close()

# --- API ROUTES (Copied from temp_Main.pyw, starting from line 1509) ---
@notes_bp.route("/api/get")
def api_get_notes():
    check_and_queue_reminders()
    conn = get_db_connection()
    notes_rows = conn.execute("SELECT * FROM notes ORDER BY modified_at DESC").fetchall()
    conn.close()
    return jsonify([dict(row) for row in notes_rows])

@notes_bp.route("/api/add", methods=["POST"])
def api_add_note():
    data = request.json
    title_html, content_html = data.get("title_html", "").strip(), data.get("content_html", "").strip()
    if not title_html and not content_html:
        return jsonify({"error": "Tiêu đề hoặc nội dung không được để trống"}), 400
    
    now = datetime.now(timezone.utc).isoformat()
    new_note = {
        "id": str(uuid.uuid4()), "title_html": title_html, "content_html": content_html,
        "due_time": data.get("due_time") or None, "status": "active" if data.get("due_time") else "none", "modified_at": now
    }

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO notes (id, title_html, content_html, due_time, status, modified_at) VALUES (?, ?, ?, ?, ?, ?)",
        (new_note['id'], new_note['title_html'], new_note['content_html'], new_note['due_time'], new_note['status'], new_note['modified_at'])
    )
    conn.commit()
    conn.close()
    return jsonify(new_note), 201

@notes_bp.route("/api/update/<note_id>", methods=["POST"])
def api_update_note(note_id):
    data = request.json
    title_html, content_html = data.get("title_html", "").strip(), data.get("content_html", "").strip()
    if not title_html and not content_html:
        return jsonify({"error": "Tiêu đề hoặc nội dung không được để trống"}), 400
    
    due_time = data.get("due_time") or None
    status = "active" if due_time else "none" # Simplified status logic, you may need to adjust if "notified" state is handled differently
    modified_at = datetime.now(timezone.utc).isoformat()

    conn = get_db_connection()
    cursor = conn.execute(
        "UPDATE notes SET title_html = ?, content_html = ?, due_time = ?, status = ?, modified_at = ? WHERE id = ?",
        (title_html, content_html, due_time, status, modified_at, note_id)
    )
    conn.commit()
    
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({"error": "Không tìm thấy ghi chú"}), 404
    
    updated_note = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    conn.close()
    return jsonify(dict(updated_note))

@notes_bp.route("/api/delete/<note_id>", methods=["POST"])
def api_delete_note(note_id):
    conn = get_db_connection()
    cursor = conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True}) if cursor.rowcount > 0 else (jsonify({"error": "Không tìm thấy ghi chú"}), 404)

@notes_bp.route("/api/mark/<note_id>", methods=["POST"])
def api_toggle_mark(note_id):
    conn = get_db_connection()
    note = conn.execute("SELECT is_marked FROM notes WHERE id = ?", (note_id,)).fetchone()
    if not note:
        conn.close()
        return jsonify({"error": "Không tìm thấy ghi chú"}), 404
    
    new_marked_state = not note["is_marked"]
    conn.execute("UPDATE notes SET is_marked = ? WHERE id = ?", (new_marked_state, note_id))
    conn.commit()
    
    updated_note = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    conn.close()
    return jsonify(dict(updated_note))

@notes_bp.route("/api/acknowledge-notification/<note_id>", methods=["POST"])
def acknowledge_notification(note_id):
    conn = get_db_connection()
    conn.execute("UPDATE notes SET status = 'notified', due_time = NULL WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@notes_bp.route("/api/check-notifications")
def api_check_notifications():
    """Endpoint để frontend kiểm tra xem có thông báo mới không."""
    check_and_queue_reminders()
    if NOTIFICATIONS_QUEUE:
        # Lấy thông báo đầu tiên và xóa khỏi hàng đợi
        notification_to_send = NOTIFICATIONS_QUEUE.pop(0)
        return jsonify(notification_to_send)
    return jsonify(None) # Trả về null nếu không có gì

@notes_bp.route("/sounds/<path:filename>")
def serve_sound(filename):
    return send_from_directory(os.path.join(DATA_DIR, "sounds"), filename)
