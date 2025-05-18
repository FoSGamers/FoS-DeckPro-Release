# exporters/txt_exporter.py
import os
from .base_exporter import BaseExporter

class TxtExporter(BaseExporter):
    def get_extension(self): return "txt"
    def format_message(self, message, is_merge=False, chat_title=None):
        role = message.get('role', 'Unknown'); ts = message.get('timestamp', 'No Ts'); content = message.get('content', '')
        header = f"{role} [{ts}]" + (f" (From: {chat_title})" if is_merge and chat_title else "")
        content_lines = content.splitlines()
        if not content_lines: return f"{header}:\n"
        elif len(content_lines) == 1: return f"{header}: {content_lines[0]}\n"
        else: return f"{header}:{os.linesep}{os.linesep.join(['  ' + line for line in content_lines])}\n"