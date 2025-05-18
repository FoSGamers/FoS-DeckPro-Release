# exporters/txt_exporter.py (COMPLETE AND VERIFIED - Batch 2)
import os
# Import the base class we defined in the same directory
from .base_exporter import BaseExporter

class TxtExporter(BaseExporter):
    """Exports chats to plain text format."""

    def get_extension(self):
        """Returns the file extension 'txt'."""
        return "txt"

    def format_message(self, message, is_merge=False, chat_title=None):
        """Formats a single message dictionary for TXT output.

        Args:
            message (dict): Dictionary containing message details ('role', 'timestamp', 'content').
            is_merge (bool): Flag indicating if this is part of a merged export.
            chat_title (str | None): The title of the source chat if merging.

        Returns:
            str: The formatted message string, including a trailing newline.
        """
        # Safely get message details with defaults
        role = message.get('role', 'Unknown')
        ts = message.get('timestamp', 'No Timestamp') # Provide default if missing
        content = message.get('content', '')   # Provide default if missing

        # Construct the header line for this message
        header_line = f"{role} [{ts}]"
        # Append source chat title if merging
        if is_merge and chat_title:
            header_line += f" (From: {chat_title})"

        content_lines = content.splitlines()

        if not content_lines:
            # Ensure a newline after the header even if content is empty
            return f"{header_line}:\n"
        elif len(content_lines) == 1:
            # If content is a single line, put it after the header
            # Ensure trailing newline
            return f"{header_line}: {content_lines[0]}\n"
        else:
            # If content is multi-line, indent subsequent lines
            # Use os.linesep for platform compatibility (\n on Unix, \r\n on Windows)
            indented_content = os.linesep.join(['  ' + line for line in content_lines])
            # Header on its own line, followed by indented content, ending with a newline
            return f"{header_line}:{os.linesep}{indented_content}\n"

    # --- Optional Customization ---
    # Uncomment and modify these if you want a specific header/footer for TXT files

    # def format_header(self, title, options):
    #     """Adds a header to the beginning of the TXT file."""
    #     from datetime import datetime # Import if needed
    #     timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    #     return f"--- Chat Export: {title} ---\nExported on: {timestamp}\n\n"

    # def format_footer(self, options):
    #      """Adds a footer to the end of the TXT file."""
    #      return "\n--- End of Export ---\n"