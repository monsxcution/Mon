"""
CDP (Chrome DevTools Protocol) Console Bridge
Connects to Chrome with --remote-debugging-port to capture console logs
"""
import os
import json
import time
import logging
import threading
from typing import Optional

try:
    import pychrome
    CDP_AVAILABLE = True
except ImportError:
    CDP_AVAILABLE = False


class CDPConsoleBridge:
    """Bridge to capture browser console logs via Chrome DevTools Protocol"""
    
    def __init__(self, host='127.0.0.1', port=None):
        if not CDP_AVAILABLE:
            raise ImportError("pychrome not installed. Run: pip install pychrome")
        
        self.host = host
        self.port = port or int(os.getenv("CDP_PORT", "9222"))
        self.browser = None
        self.tab = None
        self.running = False
        self.thread = None
        self.logger = logging.getLogger('f12')
        self.app_logger = logging.getLogger('app')
        
    def connect(self):
        """Connect to Chrome DevTools Protocol"""
        try:
            self.app_logger.info(f"[CDP] Connecting to Chrome at {self.host}:{self.port}...")
            self.browser = pychrome.Browser(url=f"http://{self.host}:{self.port}")
            
            # Get existing tab or create new one
            tabs = self.browser.list_tab()
            if tabs:
                self.tab = tabs[0]
                self.app_logger.info(f"[CDP] Using existing tab: {self.tab.title}")
            else:
                self.tab = self.browser.new_tab()
                self.app_logger.info("[CDP] Created new tab")
            
            # Enable domains
            self.tab.start()
            self.tab.Runtime.enable()
            self.tab.Log.enable()
            self.tab.Page.enable()
            
            # Set up event handlers
            self.tab.Runtime.consoleAPICalled = self._on_console_api
            self.tab.Runtime.exceptionThrown = self._on_exception
            self.tab.Log.entryAdded = self._on_log_entry
            
            self.app_logger.info("[CDP] ✅ Console bridge active!")
            return True
            
        except Exception as e:
            self.app_logger.warning(f"[CDP] ⚠️ Failed to connect: {e}")
            self.app_logger.warning("[CDP] Make sure Chrome is running with: --remote-debugging-port=9222")
            return False
    
    def _on_console_api(self, **kwargs):
        """Handle console.log/warn/error calls"""
        try:
            console_type = kwargs.get('type', 'log')  # log, warn, error, debug, info
            args = kwargs.get('args', [])
            stack_trace = kwargs.get('stackTrace', {})
            
            # Stringify arguments
            messages = []
            for arg in args:
                if 'value' in arg:
                    messages.append(str(arg['value']))
                elif 'description' in arg:
                    messages.append(arg['description'])
                else:
                    messages.append(str(arg))
            
            message = ' '.join(messages)
            
            # Get call location
            call_frames = stack_trace.get('callFrames', [])
            location = ""
            if call_frames:
                frame = call_frames[0]
                location = f"{frame.get('url', 'unknown')}:{frame.get('lineNumber', 0)}:{frame.get('columnNumber', 0)}"
            
            # Map console type to log level
            level_map = {
                'debug': logging.DEBUG,
                'log': logging.INFO,
                'info': logging.INFO,
                'warn': logging.WARNING,
                'warning': logging.WARNING,
                'error': logging.ERROR,
            }
            level = level_map.get(console_type, logging.INFO)
            
            # Log with metadata
            log_msg = f"[F12-CDP] [console.{console_type}] {message}"
            if location:
                log_msg += f" | {location}"
            
            self.logger.log(level, log_msg)
            
        except Exception as e:
            self.app_logger.error(f"[CDP] Error in console handler: {e}")
    
    def _on_exception(self, **kwargs):
        """Handle JavaScript exceptions"""
        try:
            exception_details = kwargs.get('exceptionDetails', {})
            exception = exception_details.get('exception', {})
            text = exception_details.get('text', 'Unknown error')
            
            # Get error message
            if 'description' in exception:
                message = exception['description']
            elif 'value' in exception:
                message = str(exception['value'])
            else:
                message = text
            
            # Get location
            url = exception_details.get('url', 'unknown')
            line = exception_details.get('lineNumber', 0)
            col = exception_details.get('columnNumber', 0)
            location = f"{url}:{line}:{col}"
            
            # Get stack trace
            stack_trace = exception_details.get('stackTrace', {})
            call_frames = stack_trace.get('callFrames', [])
            stack_str = ""
            if call_frames:
                stack_lines = []
                for frame in call_frames[:5]:  # First 5 frames
                    func = frame.get('functionName', '(anonymous)')
                    url = frame.get('url', '')
                    line = frame.get('lineNumber', 0)
                    col = frame.get('columnNumber', 0)
                    stack_lines.append(f"  at {func} ({url}:{line}:{col})")
                stack_str = "\n" + "\n".join(stack_lines)
            
            log_msg = f"[F12-CDP] [Exception] {message} | {location}{stack_str}"
            self.logger.error(log_msg)
            
        except Exception as e:
            self.app_logger.error(f"[CDP] Error in exception handler: {e}")
    
    def _on_log_entry(self, **kwargs):
        """Handle Log.entryAdded events"""
        try:
            entry = kwargs.get('entry', {})
            source = entry.get('source', 'unknown')
            level = entry.get('level', 'info')
            text = entry.get('text', '')
            url = entry.get('url', '')
            line_number = entry.get('lineNumber', 0)
            
            # Map CDP log level to Python logging
            level_map = {
                'verbose': logging.DEBUG,
                'info': logging.INFO,
                'warning': logging.WARNING,
                'error': logging.ERROR,
            }
            log_level = level_map.get(level, logging.INFO)
            
            location = f"{url}:{line_number}" if url else ""
            log_msg = f"[F12-CDP] [{source}.{level}] {text}"
            if location:
                log_msg += f" | {location}"
            
            self.logger.log(log_level, log_msg)
            
        except Exception as e:
            self.app_logger.error(f"[CDP] Error in log handler: {e}")
    
    def start(self):
        """Start CDP bridge in background thread"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
    
    def _run(self):
        """Main loop - retry connection and wait for events"""
        retry_delay = 3  # seconds
        
        while self.running:
            try:
                if not self.tab:
                    if not self.connect():
                        time.sleep(retry_delay)
                        continue
                
                # Wait for events (tab.wait blocks until event)
                time.sleep(0.1)
                
            except Exception as e:
                self.app_logger.error(f"[CDP] Error in main loop: {e}")
                self.tab = None
                time.sleep(retry_delay)
    
    def stop(self):
        """Stop CDP bridge"""
        self.running = False
        if self.tab:
            try:
                self.tab.stop()
            except:
                pass
        if self.thread:
            self.thread.join(timeout=2)
        self.app_logger.info("[CDP] Console bridge stopped")


def start_cdp_bridge():
    """Start CDP bridge if conditions are met"""
    mode = os.getenv("CONSOLE_BRIDGE_MODE", "cdp").lower()
    
    if mode == "off":
        return None
    
    if mode == "cdp":
        if not CDP_AVAILABLE:
            logging.getLogger('app').warning("[CDP] pychrome not installed. Run: pip install pychrome")
            return None
        
        try:
            bridge = CDPConsoleBridge()
            bridge.start()
            return bridge
        except Exception as e:
            logging.getLogger('app').error(f"[CDP] Failed to start: {e}")
            return None
    
    return None
