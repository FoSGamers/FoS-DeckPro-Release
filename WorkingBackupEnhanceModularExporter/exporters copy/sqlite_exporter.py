# exporters/sqlite_exporter.py
import io, sqlite3, traceback
from .base_exporter import BaseExporter
from utils.helpers import apply_text_mods

class SqliteExporter(BaseExporter):
    def get_extension(self): return "sqlite"
    def format_message(self, message, is_merge=False, chat_title=None): return "" # Not used
    def generate_single_file(self, messages, title, options): # Special method for SQLite
        db_buffer = io.BytesIO(); conn = None
        try:
            conn = sqlite3.connect(':memory:')
            cur = conn.cursor()
            cur.execute('CREATE TABLE messages (chat_id TEXT, chat_title TEXT, message_index INTEGER, author TEXT, timestamp TEXT, datetime_iso TEXT, content TEXT, word_count INTEGER)')
            anonymize = options.get('anonymize', False); leet = options.get('leet_speak', False)
            is_merge = options.get('is_merge', False)
            cid = options.get('chat_id', 'N/A'); ctitle = options.get('chat_title', title)
            data = []
            for msg in messages:
                mcid = cid if not is_merge else msg.get('chat_id', 'MERGED')
                mctitle = ctitle if not is_merge else msg.get('chat_title', 'MERGED')
                cont = apply_text_mods(msg['content'], anonymize, leet);
                dt_iso = msg['datetime_obj'].isoformat() if msg.get('datetime_obj') else None
                wc = msg.get('word_count', 0)
                data.append((mcid, mctitle, msg.get('index',-1), msg['role'], msg['timestamp'], dt_iso, cont, wc))
            cur.executemany('INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?, ?, ?)', data)
            conn.commit()
            with io.StringIO() as s:
                for line in conn.iterdump(): s.write(f'{line}\n')
                db_buffer.write(s.getvalue().encode('utf-8'))
        except Exception as e: print(f"SQLite Error: {e}\n{traceback.format_exc()}"); return b""
        finally:
            if conn: conn.close()
        db_buffer.seek(0)
        return db_buffer.getvalue()
    def generate_part_content(self, messages, title, options): # Overrides base
         # For SQLite, part generation *is* single file generation
         return self.generate_single_file(messages, title, options) # Return bytes directly