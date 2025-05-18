# exporters/sqlite_exporter.py (COMPLETE AND VERIFIED - Batch 3)
import io
import sqlite3
import traceback
# Import the base class we defined in the same directory
from .base_exporter import BaseExporter
# Import apply_text_mods specifically needed for this exporter
from utils.helpers import apply_text_mods

class SqliteExporter(BaseExporter):
    """
    Special exporter: Generates a complete SQLite DB file in memory as bytes.
    It doesn't use format_message line-by-line for generation.
    It overrides generate_part_content to return bytes directly.
    """
    def get_extension(self):
        """Returns the file extension 'sqlite'."""
        return "sqlite"

    def format_message(self, message, is_merge=False, chat_title=None):
        """
        This method is not directly used for the main SQLite generation logic.
        It's required by the abstract base class but can return an empty string.
        """
        return ""

    # This method generates the actual SQLite database bytes for a given set of messages
    # It's called directly by the service layer for this specific exporter type.
    def generate_single_file(self, messages, title, options):
        """
        Generates the entire SQLite DB file content as bytes for the given messages.
        Args:
            messages (list): List of message dictionaries for this export.
            title (str): Base title for the export (used as default chat_title if not merging).
            options (dict): Dictionary of export options.
        Returns:
            bytes: The byte content of the generated SQLite database file, or empty bytes on error.
        """
        db_buffer = io.BytesIO() # Create an in-memory bytes buffer to hold the result
        conn = None             # Initialize connection variable
        try:
            # print(f"[SQLITE EXPORTER DEBUG] Generating DB for: {title}")
            # Create the SQLite database entirely in memory for speed
            conn = sqlite3.connect(':memory:')
            cursor = conn.cursor()

            # Define the table schema - ensure it matches what you expect
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    chat_id TEXT,          -- Original chat ID or 'MERGED'
                    chat_title TEXT,       -- Original chat title or merged filename base
                    message_index INTEGER, -- Index within the original chat
                    author TEXT,           -- 'User' or 'ChatGPT'
                    timestamp TEXT,        -- Formatted timestamp string (YYYY-MM-DD HH:MM:SS)
                    datetime_iso TEXT,     -- ISO 8601 format timestamp (if available, for precise sorting/querying)
                    content TEXT,          -- The message content (potentially modified by anonymize/leet)
                    word_count INTEGER     -- Word count of the message
                )''')

            # Prepare data for insertion by iterating through messages
            anonymize = options.get('anonymize', False)
            leet_speak = options.get('leet_speak', False)
            is_merge = options.get('is_merge', False)
            # Get context passed from the service layer (used for non-merged rows)
            chat_id_context = options.get('chat_id', 'N/A')
            chat_title_context = options.get('chat_title', title) # Use the base title if not otherwise specified

            sqlite_data_to_insert = []
            for msg in messages:
                # Determine Chat ID and Title for this specific row
                # If merging, use the chat_id/chat_title attached to the message dict
                # Otherwise, use the context passed in via options
                current_chat_id = msg.get('chat_id', chat_id_context) if is_merge else chat_id_context
                current_chat_title = msg.get('chat_title', chat_title_context) if is_merge else chat_title_context

                # Apply text modifications to content before storing
                content_mod = apply_text_mods(msg.get('content',''), anonymize, leet_speak)

                # Get ISO timestamp if datetime object exists (preferred for DB)
                dt_iso = None
                if msg.get('datetime_obj'):
                    try:
                        dt_iso = msg['datetime_obj'].isoformat()
                    except AttributeError: # Handle cases where it might not be a datetime obj
                        dt_iso = None

                # Get pre-calculated word count, default to 0
                wc = msg.get('word_count', 0)

                # Append row data as a tuple, matching the table columns
                sqlite_data_to_insert.append((
                    current_chat_id,
                    current_chat_title,
                    msg.get('index', -1), # Use original message index if available, else -1
                    msg.get('role', 'Unknown'),
                    msg.get('timestamp', 'No Timestamp'), # Use formatted string timestamp
                    dt_iso,               # ISO format timestamp or None
                    content_mod,          # Store modified content
                    wc                    # Word count
                ))

            # Insert all prepared data rows efficiently using executemany
            if sqlite_data_to_insert:
                cursor.executemany(
                    'INSERT INTO messages (chat_id, chat_title, message_index, author, timestamp, datetime_iso, content, word_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                    sqlite_data_to_insert
                )
                conn.commit() # Commit the changes to the in-memory database
                # print(f"[SQLITE EXPORTER DEBUG] Inserted {len(sqlite_data_to_insert)} rows.")
            # else:
                # print("[SQLITE EXPORTER DEBUG] No data rows to insert.")

            # Dump the entire in-memory database to the BytesIO buffer
            # We use iterdump() which generates SQL statements as text
            # Use StringIO as an intermediate buffer for the text dump
            with io.StringIO() as sql_dump_stream:
                for line in conn.iterdump():
                    sql_dump_stream.write(f'{line}\n')
                # Encode the SQL text dump into bytes and write to the final buffer
                db_buffer.write(sql_dump_stream.getvalue().encode('utf-8'))

        except sqlite3.Error as e_sql: # Catch SQLite specific errors
            print(f"[SQLITE EXPORTER ERROR] SQLite specific error for '{title}': {e_sql}")
            traceback.print_exc()
            return b"" # Return empty bytes on failure
        except Exception as e: # Catch other potential errors during generation
            print(f"[SQLITE EXPORTER ERROR] General error generating SQLite DB for '{title}': {e}")
            traceback.print_exc()
            return b"" # Return empty bytes on failure
        finally:
            # Ensure the in-memory connection is always closed
            if conn:
                conn.close()

        db_buffer.seek(0) # Rewind the buffer to the beginning for reading
        # print(f"[SQLITE EXPORTER DEBUG] DB buffer size: {len(db_buffer.getvalue())} bytes.")
        # Return the raw bytes containing the SQL dump to recreate the DB
        return db_buffer.getvalue()

    # Override base generate_part_content because SQLite creates a single binary file
    def generate_part_content(self, messages, title, options):
         """
         For SQLite, generating a "part" means generating the whole DB file.
         This method returns BYTES directly by calling generate_single_file.
         """
         # Call the method that actually generates the DB bytes
         return self.generate_single_file(messages, title, options)