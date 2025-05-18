# exporters/base_exporter.py (COMPLETE AND VERIFIED)
import io
import os
from abc import ABC, abstractmethod
# Import helpers specifically needed by the base or subclasses
from utils.helpers import apply_text_mods

class BaseExporter(ABC):
    """Abstract base class for all format exporters."""

    @abstractmethod
    def format_message(self, message, is_merge=False, chat_title=None):
        """
        Formats a single message dictionary.
        Subclasses MUST implement this.
        Should return a string (typically including a trailing newline).
        """
        pass

    def format_header(self, title, options):
        """
        Generates the header content for the start of a file/part (optional).
        Subclasses CAN override this.
        Should return a string.
        """
        return "" # Default: no header

    def format_footer(self, options):
        """
        Generates the footer content for the end of a file/part (optional).
        Subclasses CAN override this.
        Should return a string.
        """
        return "" # Default: no footer

    @abstractmethod
    def get_extension(self):
        """
        Returns the file extension string for this format (e.g., 'txt').
        Subclasses MUST implement this.
        """
        raise NotImplementedError

    def generate_part_content(self, messages, title, options):
        """
        Generates the full string content for a single file part by calling
        header, message formatting, and footer methods.
        Applies text mods internally before formatting each message.
        Returns a single string representing the content of one export file part.
        NOTE: This method assumes the exporter generates text-based content.
              Exporters generating binary data (like SQLite) MUST override this.
        """
        part_content_stream = io.StringIO() # Use StringIO to build the string efficiently
        anonymize = options.get('anonymize', False)
        leet_speak = options.get('leet_speak', False)

        # Write header if the subclass provides one
        header = self.format_header(title, options)
        if header and isinstance(header, str):
            part_content_stream.write(header)
            # Ensure newline after header if not already present
            if not header.endswith('\n'):
                part_content_stream.write('\n')

        # Write formatted messages
        for msg in messages:
            # Safely get original content, default to empty string if missing
            original_content = msg.get('content', '')
            # Apply text modifications
            content_mod = apply_text_mods(original_content, anonymize, leet_speak)

            # Prepare a dictionary to pass to format_message
            # Include essential keys, using defaults if necessary
            msg_to_format = {
                'role': msg.get('role', 'Unknown'),
                'timestamp': msg.get('timestamp', 'No Timestamp'), # Provide default
                'datetime_obj': msg.get('datetime_obj'), # Pass along if exists
                'content': content_mod # Use the potentially modified content
            }

            is_merge = options.get('is_merge', False)
            # Get chat title specifically for merge mode display within the message
            msg_chat_title = msg.get('chat_title') if is_merge else None # Relies on chat_title being added during merge prep

            # Call the specific exporter's format_message implementation
            formatted_message_str = self.format_message(msg_to_format, is_merge, msg_chat_title)

            # Append the formatted message string if it's valid
            if formatted_message_str and isinstance(formatted_message_str, str):
                part_content_stream.write(formatted_message_str)
                # Add a newline if the formatter didn't already include one
                # (helps ensure separation between messages)
                if not formatted_message_str.endswith('\n'):
                     part_content_stream.write('\n')
            # else: print(f"[BASE EXPORTER WARN] Formatter {type(self).__name__} returned empty or non-string.")


        # Write footer if the subclass provides one
        footer = self.format_footer(options)
        if footer and isinstance(footer, str):
             current_content_value = part_content_stream.getvalue()
             # Ensure newline before footer if content exists and doesn't end with one
             if current_content_value and not current_content_value.endswith('\n') and not footer.startswith('\n'):
                  part_content_stream.write('\n')
             part_content_stream.write(footer)

        # Get the complete string content for this part and close the stream
        final_content_string = part_content_stream.getvalue()
        part_content_stream.close() # Release memory
        return final_content_string