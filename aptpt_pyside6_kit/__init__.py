"""
APTPT + PySide6 Adaptive Developer Kit
A comprehensive toolkit for building robust, adaptive desktop applications.
"""

from .aptpt import aptpt_wrapper, log_aptpt_event
from .aptpt_error_ui import show_aptpt_error_dialog, show_aptpt_warning, APTPTErrorDialog
from .aptpt_monitor import APTPTMonitor
from .aptpt_config import get_config, update_config

__version__ = "1.0.0"
__all__ = [
    'aptpt_wrapper',
    'log_aptpt_event',
    'show_aptpt_error_dialog',
    'show_aptpt_warning',
    'APTPTErrorDialog',
    'APTPTMonitor',
    'get_config',
    'update_config'
] 