# exporters/csv_exporter.py
from .base_exporter import BaseExporter

class CsvExporter(BaseExporter):
    def get_extension(self): return "csv"
    def _escape_csv(self, field):
        fs = str(field); return f'"{fs.replace("\"", "\"\"")}"' if any(c in fs for c in '|\n"') else fs
    def format_header(self, title, options): return "Author|Timestamp|Message\n"
    def format_message(self, message, is_merge=False, chat_title=None):
        role = message.get('role','?'); ts = message.get('timestamp','?'); content = message.get('content','')
        return "|".join(map(self._escape_csv, [role, ts, content])) + "\n"