# exporters/csv_exporter.py (COMPLETE AND VERIFIED - Batch 2)
# Note: Exports pipe-separated values with a .csv extension, matching the 'db' intent.
import csv
import io # Use io.StringIO to handle CSV writing easily if needed, though direct string building is fine here
from .base_exporter import BaseExporter

class CsvExporter(BaseExporter):
    """Exports chats to pipe-separated values (CSV) format."""

    def get_extension(self):
        """Returns the file extension 'csv'."""
        # Although the Tkinter app might have used '.db', the format is CSV.
        # Using '.csv' is standard and more recognized by spreadsheet programs.
        return "csv"

    def _escape_csv(self, field):
        """
        Helper for basic CSV quoting if needed (using pipe delimiter).
        Ensures fields containing the delimiter, quotes, or newlines are quoted.
        Follows basic RFC 4180 rules for quoting and escaping internal quotes.
        """
        field_str = str(field) # Ensure string conversion
        # Quote if field contains delimiter (|), newline (\n or \r), or double quote (")
        if '|' in field_str or '\n' in field_str or '\r' in field_str or '"' in field_str:
             # Replace internal double quotes with two double quotes
            escaped_field = field_str.replace('"', '""')
            return f'"{escaped_field}"'
        # Otherwise, return the field as is
        return field_str

    def format_header(self, title, options):
         """Writes the CSV header row."""
         # Use pipe as delimiter as intended by original Tkinter app's 'db' format
         # Ensure header row also ends with a newline
         return "Author|Timestamp|Message\n"

    def format_message(self, message, is_merge=False, chat_title=None):
        """Formats a single message as a pipe-separated row."""
        role = message.get('role', 'Unknown')
        ts = message.get('timestamp', 'No Ts')
        content = message.get('content', '')

        # Apply escaping to each field before joining
        cols = [
            self._escape_csv(role),
            self._escape_csv(ts),
            self._escape_csv(content)
        ]
        # Join with pipe delimiter and add newline for the data row
        return "|".join(cols) + "\n"

    # Overriding generate_part_content is generally not needed if
    # format_message handles newlines correctly. The base class implementation
    # will correctly concatenate the results from format_message.