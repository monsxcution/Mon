"""
Console Endpoint - Fallback In-Page Console Mirror
Receives console logs from frontend via POST /__console
"""
import os
import json
import logging
from flask import Blueprint, request, jsonify
from functools import wraps


console_bp = Blueprint('console', __name__)
logger = logging.getLogger('f12')
app_logger = logging.getLogger('app')


def require_dev_mode(f):
    """Decorator to restrict endpoint to dev mode only"""
    @wraps(f)
    def decorated(*args, **kwargs):
        env = os.getenv("ENV", "prod").lower()
        
        if env != "dev":
            return jsonify({"error": "Not available in production"}), 403
        
        # Check for optional dev token
        dev_token = os.getenv("DEV_CONSOLE_TOKEN")
        if dev_token:
            request_token = request.headers.get("X-Dev-Token")
            if request_token != dev_token:
                return jsonify({"error": "Invalid token"}), 401
        
        return f(*args, **kwargs)
    return decorated


@console_bp.route('/__console', methods=['POST'])
@require_dev_mode
def receive_console_logs():
    """
    Receive console logs from in-page console mirror
    
    Payload format (JSON):
    {
        "logs": [
            {
                "level": "error|warn|info|debug|log",
                "message": "error message",
                "stack": "stack trace (optional)",
                "url": "page url",
                "line": 123,
                "col": 45,
                "ts": 1234567890.123
            },
            ...
        ]
    }
    """
    try:
        # Parse payload
        if request.is_json:
            data = request.get_json()
        else:
            # Try parsing as text (for sendBeacon)
            data = json.loads(request.data.decode('utf-8'))
        
        # Limit batch size (prevent abuse)
        MAX_BATCH_SIZE = 512 * 1024  # 512KB
        if len(request.data) > MAX_BATCH_SIZE:
            app_logger.warning(f"[InPage] Rejected large batch: {len(request.data)} bytes")
            return jsonify({"error": "Batch too large"}), 413
        
        # Handle single log or batch
        logs = data.get('logs', [])
        if not logs and 'level' in data:
            # Single log object
            logs = [data]
        
        # Limit number of logs per batch
        MAX_LOGS_PER_BATCH = 50
        if len(logs) > MAX_LOGS_PER_BATCH:
            logs = logs[:MAX_LOGS_PER_BATCH]
            app_logger.warning(f"[InPage] Truncated batch to {MAX_LOGS_PER_BATCH} logs")
        
        # Process each log
        for log_entry in logs:
            try:
                level_str = log_entry.get('level', 'log').lower()
                message = log_entry.get('message', '')
                stack = log_entry.get('stack', '')
                url = log_entry.get('url', '')
                line = log_entry.get('line', 0)
                col = log_entry.get('col', 0)
                
                # Truncate long messages/stacks
                MAX_MESSAGE_LEN = 2000
                MAX_STACK_LEN = 2000
                if len(message) > MAX_MESSAGE_LEN:
                    message = message[:MAX_MESSAGE_LEN] + '... (truncated)'
                if len(stack) > MAX_STACK_LEN:
                    stack = stack[:MAX_STACK_LEN] + '... (truncated)'
                
                # Map level
                level_map = {
                    'debug': logging.DEBUG,
                    'log': logging.INFO,
                    'info': logging.INFO,
                    'warn': logging.WARNING,
                    'warning': logging.WARNING,
                    'error': logging.ERROR,
                }
                log_level = level_map.get(level_str, logging.INFO)
                
                # Format log message
                location = f"{url}:{line}:{col}" if url else "unknown"
                log_msg = f"[F12-InPage] [console.{level_str}] {message} | {location}"
                
                if stack:
                    # Add first few lines of stack
                    stack_lines = stack.split('\n')[:5]
                    log_msg += "\n" + "\n".join(stack_lines)
                
                # Write log
                logger.log(log_level, log_msg)
                
            except Exception as e:
                app_logger.error(f"[InPage] Error processing log entry: {e}")
        
        return '', 204  # No content
        
    except json.JSONDecodeError:
        app_logger.error("[InPage] Invalid JSON payload")
        return jsonify({"error": "Invalid JSON"}), 400
    except Exception as e:
        app_logger.error(f"[InPage] Error in console endpoint: {e}")
        return jsonify({"error": "Internal error"}), 500


def register_console_endpoint(app):
    """Register console endpoint blueprint"""
    mode = os.getenv("CONSOLE_BRIDGE_MODE", "cdp").lower()
    env = os.getenv("ENV", "prod").lower()
    
    if mode == "inpage" and env == "dev":
        app.register_blueprint(console_bp)
        app_logger.info("[InPage] Console endpoint registered at /__console")
        return True
    
    return False
