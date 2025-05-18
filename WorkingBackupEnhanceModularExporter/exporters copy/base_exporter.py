# exporters/base_exporter.py
import io
import os
from abc import ABC, abstractmethod
from utils.helpers import apply_text_mods # Import necessary helpers

class BaseExporter(ABC):
    @abstractmethod
    def format_message(self, message, is_merge=False, chat_title=None): pass
    def format_header(self, title, options): return ""
    def format_footer(self, options): return ""
    def get_extension(self): raise NotImplementedError

    def generate_part_content(self, messages, title, options):
        part_content = io.StringIO()
        anonymize = options.get('anonymize', False)
        leet_speak = options.get('leet_speak', False)
        header = self.format_header(title, options)
        if header: part_content.write(header + ('\n' if not header.endswith('\n') else ''))
        for msg in messages:
            content_mod = apply_text_mods(msg['content'], anonymize, leet_speak)
            msg_to_format = {**msg, 'content': content_mod} # Use modified content
            is_merge = options.get('is_merge', False)
            msg_chat_title = msg.get('chat_title') if is_merge else None
            formatted = self.format_message(msg_to_format, is_merge, msg_chat_title)
            part_content.write(formatted + ('\n' if not formatted.endswith('\n') else ''))
        footer = self.format_footer(options)
        if footer: part_content.write(('\n' if not part_content.getvalue().endswith('\n') else '') + footer)
        return part_content.getvalue()