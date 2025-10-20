"""
Unified Logging Configuration
Backend + Browser Console (F12) Integration
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def init_logging():
    """Initialize logging system with file rotation"""
    
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Get log level from ENV (default: INFO)
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    
    # Format: [%(asctime)s] [%(levelname)s] [%(name)s] %(message)s
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # === Backend App Logger ===
    app_logger = logging.getLogger('app')
    app_logger.setLevel(log_level)
    app_logger.handlers.clear()  # Remove existing handlers
    
    # File handler for backend (5MB x 5 files)
    app_file_handler = RotatingFileHandler(
        logs_dir / 'app.log',
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=5,
        encoding='utf-8'
    )
    app_file_handler.setFormatter(formatter)
    app_logger.addHandler(app_file_handler)
    
    # Console handler for backend
    app_console_handler = logging.StreamHandler()
    app_console_handler.setFormatter(formatter)
    app_logger.addHandler(app_console_handler)
    
    # === F12 Console Logger ===
    f12_logger = logging.getLogger('f12')
    f12_logger.setLevel(logging.DEBUG)  # Always DEBUG for F12
    f12_logger.handlers.clear()
    
    # File handler for F12 console (5MB x 5 files)
    f12_file_handler = RotatingFileHandler(
        logs_dir / 'f12_console.log',
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    f12_file_handler.setFormatter(formatter)
    f12_logger.addHandler(f12_file_handler)
    
    # Console handler for F12 (also print to terminal)
    f12_console_handler = logging.StreamHandler()
    
    # Colorized formatter for terminal (optional)
    try:
        import colorama
        colorama.init(autoreset=True)
        
        class ColoredFormatter(logging.Formatter):
            COLORS = {
                'DEBUG': colorama.Fore.CYAN,
                'INFO': colorama.Fore.GREEN,
                'WARNING': colorama.Fore.YELLOW,
                'ERROR': colorama.Fore.RED,
                'CRITICAL': colorama.Fore.RED + colorama.Style.BRIGHT,
            }
            
            def format(self, record):
                color = self.COLORS.get(record.levelname, '')
                record.levelname = f"{color}{record.levelname}{colorama.Style.RESET_ALL}"
                return super().format(record)
        
        colored_formatter = ColoredFormatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        f12_console_handler.setFormatter(colored_formatter)
    except ImportError:
        # No colorama, use regular formatter
        f12_console_handler.setFormatter(formatter)
    
    f12_logger.addHandler(f12_console_handler)
    
    # Also log Flask app logs
    flask_logger = logging.getLogger('werkzeug')
    flask_logger.setLevel(log_level)
    
    app_logger.info("=== Logging System Initialized ===")
    app_logger.info(f"Log Level: {log_level_str}")
    app_logger.info(f"App Log: {logs_dir / 'app.log'}")
    app_logger.info(f"F12 Log: {logs_dir / 'f12_console.log'}")
    
    return app_logger, f12_logger
