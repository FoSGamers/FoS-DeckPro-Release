"""APTPT logging module."""

import json
import traceback
from datetime import datetime
from typing import Any, Dict, Optional
import threading

# Global variable to track if log_aptpt_event is currently being executed
_logging_lock = threading.Lock()

def log_aptpt_event(
    level: str,
    description: str,
    variables: Optional[Dict[str, Any]] = None,
    exception: Optional[Exception] = None
) -> None:
    """Log an APTPT event with full context."""
    with _logging_lock:
        try:
            event = {
                'timestamp': datetime.now().isoformat(),
                'level': level,
                'description': description,
                'variables': variables or {},
            }
            
            if exception:
                event['exception'] = {
                    'type': type(exception).__name__,
                    'message': str(exception),
                    'traceback': traceback.format_exc()
                }
            
            # Write to log file
            with open('aptpt_error_log.jsonl', 'a') as f:
                f.write(json.dumps(event) + '\n')
        except Exception as e:
            print(f"Failed to log APTPT event: {e}") 