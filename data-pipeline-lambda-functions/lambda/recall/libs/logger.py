# logger.py
import logging
import json
from datetime import datetime, timezone
import json_log_formatter
import sys

class CustomJsonFormatter(json_log_formatter.JSONFormatter):
    def json_record(self, message: str, extra: dict, record: logging.LogRecord) -> dict:
        extra['message'] = message
        extra['severity'] = record.levelname
        extra['timestamp'] = datetime.now(timezone.utc).isoformat()
        extra['logger'] = record.name
        extra['function'] = record.funcName
        extra['line'] = record.lineno
        
        # Include exception info if present
        if record.exc_info:
            extra['exception'] = self.formatException(record.exc_info)
            
        # Include stack info if present
        if record.stack_info:
            extra['stack_info'] = self.formatStack(record.stack_info)
            
        return extra

def setup_logger(name: str) -> logging.Logger:
    """Setup structured logger for Lambda environment"""
    logger = logging.getLogger(name)
    
    # Clear any existing handlers
    if logger.handlers:
        logger.handlers.clear()
    
    # Prevent duplicate logs
    logger.propagate = False
    
    # Create handler
    handler = logging.StreamHandler(sys.stdout)  # Lambda best practice: write to stdout
    formatter = CustomJsonFormatter()
    handler.setFormatter(formatter)
    
    # Add handler and set level
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    return logger

# Create singleton logger instance
logger = setup_logger("RecallMastersIntegration")