"""
error_reporting.py

Provides opt-in, anonymous error reporting for ManaBox Enhancer / FoS-DeckPro.

- Disabled by default. Users must explicitly enable in config.
- Reports are anonymous and contain only error type, message, and stack trace.
- No personal or sensitive data is collected or sent.
- Endpoint and enable flag are set in config.
"""
import traceback
import requests
from FoS_DeckPro.utils import config

def report_error(exc: Exception):
    """Send an anonymous error report if enabled in config."""
    if not getattr(config, 'ERROR_REPORTING_ENABLED', False):
        return
    endpoint = getattr(config, 'ERROR_REPORTING_ENDPOINT', None)
    if not endpoint:
        return
    payload = {
        'error_type': type(exc).__name__,
        'error_message': str(exc),
        'stack_trace': traceback.format_exc(),
        'app_version': getattr(config, 'APP_VERSION', 'unknown'),
    }
    try:
        requests.post(endpoint, json=payload, timeout=3)
    except Exception:
        pass  # Never crash the app due to error reporting 