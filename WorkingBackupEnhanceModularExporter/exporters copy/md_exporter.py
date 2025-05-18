# exporters/md_exporter.py
import os
from .base_exporter import BaseExporter

class MdExporter(BaseExporter):
    def get_extension(self): return "md"
    def format_header(self, title, options): return f"# Chat Export: {title}\n\n"
    def format_message(self, message, is_merge=False, chat_title=None):
        role = message.get('role', 'Unknown'); ts = message.get('timestamp', 'No Ts'); content = message.get('content', '')
        header = f"**{role} [{ts}]**" + (f" _(From: {chat_title})_" if is_merge and chat_title else "")
        content_md = content.replace('```', '\\`\\`\\`')
        if '\n' in content_md:
            code_indicators = ['def ', 'class ', 'import ', 'function(', '{', ';']
            is_code = any(ind in content_md for ind in code_indicators) and len(content_md.splitlines()) > 1
            formatted_md = f"```\n{content_md}\n```" if is_code else os.linesep.join(['> ' + line for line in content_md.splitlines()])
        else: formatted_md = content_md
        return f"{header}\n\n{formatted_md}\n\n" # Double newline for spacing