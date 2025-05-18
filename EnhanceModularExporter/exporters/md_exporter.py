# exporters/md_exporter.py (COMPLETE AND VERIFIED - Batch 2)
import os
import re # Import re for potential escaping
from .base_exporter import BaseExporter

class MdExporter(BaseExporter):
    """Exports chats to Markdown format."""

    def get_extension(self):
        """Returns the file extension 'md'."""
        return "md"

    def format_header(self, title, options):
        """Adds a main title (H1) to the Markdown file."""
        # Escape potential markdown characters in the title itself
        # Escape '*', '_', '#', '`', '[', ']'
        safe_title = re.sub(r'([*_#`\[\]])', r'\\\1', title)
        return f"# Chat Export: {safe_title}\n\n"

    def format_message(self, message, is_merge=False, chat_title=None):
        """Formats a single message for Markdown output."""
        role = message.get('role', 'Unknown')
        ts = message.get('timestamp', 'No Ts')
        content = message.get('content', '')

        # Format the header part of the message (bold role/timestamp)
        # Escape potential markdown in role/ts just in case
        safe_role = role.replace('*', '\\*').replace('_', '\\_')
        safe_ts = ts.replace('*', '\\*').replace('_', '\\_')
        header = f"**{safe_role} [{safe_ts}]**"

        # Add source chat title in italics if this is part of a merged export
        if is_merge and chat_title:
            # Escape potential markdown in chat title
            safe_chat_title = chat_title.replace('*', '\\*').replace('_', '\\_')
            header += f" _{safe_chat_title}_" # Use _ for italics

        # Handle content formatting (code blocks vs. blockquotes)
        # Escape backticks within the content first to avoid issues
        content_md = content.replace('`', r'\`')

        # Heuristic for code block detection vs. blockquote for multiline content
        if '\n' in content_md:
            # Basic check for common code characters/keywords/patterns
            code_indicators = ['def ', 'class ', 'import ', 'function(', '{', ';', '=>', '<div>', '</', 'SELECT ', 'FROM ', 'WHERE ', 'console.log', '#include']
            # Check if content has multiple lines AND likely contains code structure
            line_count = len(content_md.splitlines())
            # More robust check: first line indentation or common start chars
            likely_code_start = content_md.lstrip().startswith(('#', '//', '<', '{', 'import ', 'public ', 'private '))
            is_code = (any(ind in content_md for ind in code_indicators) or likely_code_start) and line_count > 1

            if is_code:
                 # Format as a Markdown code block
                 # We already escaped individual backticks, so ``` shouldn't cause issues.
                 formatted_md = f"```\n{content_md}\n```"
            else:
                # Treat other multiline content as a blockquote
                 # Escape '>' at the start of lines within blockquote content
                 escaped_lines = [('> ' + line.replace('>', r'\>')) for line in content_md.splitlines()]
                 formatted_md = os.linesep.join(escaped_lines)
        else:
            # Single line content remains as is (inline code using backticks is preserved)
            formatted_md = content_md

        # Ensure blank line separation after each message block for readability
        # The extra newline is added by the BaseExporter now if needed.
        return f"{header}\n\n{formatted_md}\n" # Return the block, BaseExporter handles final newline