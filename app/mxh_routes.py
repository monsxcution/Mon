import sqlite3
import json
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, render_template
from app.database import get_db_connection

mxh_bp = Blueprint("mxh", __name__, url_prefix="/mxh")

@mxh_bp.route("")
def mxh_page():
    """Render the MXH page with clean placeholder content."""
    return render_template("mxh.html", title="Mạng Xã Hội")