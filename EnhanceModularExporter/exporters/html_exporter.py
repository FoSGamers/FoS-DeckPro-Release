# exporters/html_exporter.py (COMPLETE AND VERIFIED - Batch 2)
import html
from .base_exporter import BaseExporter

class HtmlExporter(BaseExporter):
    """Exports chats to HTML format."""

    def get_extension(self):
        """Returns the file extension 'html'."""
        return "html"

    def format_header(self, title, options):
        """Generates the HTML header, including CSS if requested."""
        embed_css = options.get('html_embed_css', True)
        # Define CSS rules as a multi-line string
        # Includes basic styling for messages, roles, meta, code, blockquotes
        # Refined CSS for better appearance
        css_rules = """
<style>
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji';
        max-width: 850px;
        margin: 25px auto;
        padding: 20px 25px;
        border: 1px solid #d1d1d1;
        border-radius: 8px;
        line-height: 1.65;
        background-color: #ffffff;
        color: #202124; /* Google Docs text color */
        font-size: 15px; /* Slightly larger base font */
    }
    h1 {
        text-align: center;
        border-bottom: 1px solid #e0e0e0;
        padding-bottom: 15px;
        margin-top: 0;
        margin-bottom: 25px;
        color: #1c1e21;
        font-size: 1.8em;
        font-weight: 500;
    }
    .message {
        margin-bottom: 1.5em; /* More space between messages */
        padding: 12px 18px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        overflow-wrap: break-word; /* Ensure long words wrap */
        word-wrap: break-word;
         -webkit-hyphens: auto;
         -moz-hyphens: auto;
         hyphens: auto;
    }
    .message strong { /* Role */
        display: block;
        margin-bottom: 0.4em;
        font-size: 1.0em; /* Slightly larger role name */
        color: #111;
        font-weight: 600;
    }
    .message .meta { /* Timestamp and source chat */
        font-size: 0.8em;
        color: #5f6368; /* Google meta text color */
        margin-bottom: 0.7em;
    }
    .message .chat-title { /* Source chat title in merge */
        font-weight: 500; /* Less bold than role */
        color: #1a0dab; /* Google link blue */
        margin-left: 5px;
    }
    /* Role-specific styling */
    .User {
        background-color: #f1f3f4; /* Google message background */
        border-color: #dadce0;
    }
    .User strong {
        color: #1a73e8; /* Google Blue */
    }
    .ChatGPT {
        background-color: #e6f4ea; /* Lighter Google Green */
        border-color: #ceead6;
    }
    .ChatGPT strong {
        color: #137333; /* Google Green */
    }
    /* Code block styling */
    pre {
        background-color: #f8f9fa; /* Standard code background */
        border: 1px solid #dee2e6;
        padding: 12px 15px;
        border-radius: 6px;
        white-space: pre-wrap;   /* Wrap long lines in code blocks */
        word-wrap: break-word;   /* Break long words if needed */
        font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace;
        font-size: 0.9em;
        line-height: 1.5;        /* Improve code readability */
        overflow-x: auto;        /* Add horizontal scroll for very wide code */
        margin-top: 0.5em;
        margin-bottom: 0.5em;
    }
    /* Inline code styling */
    code {
        font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace;
        background-color: #f1f3f4;
        padding: 0.15em 0.4em;
        border-radius: 4px;
        font-size: 0.9em;
        color: #3c4043;
    }
    pre code { /* Reset background for code inside pre */
       background-color: transparent;
       padding: 0;
       border-radius: 0;
    }
    /* Blockquote styling */
    blockquote {
        border-left: 4px solid #d1d1d1;
        padding-left: 15px;
        margin-left: 0; /* Override default blockquote margin */
        margin-right: 0;
        color: #5f6368;
        font-style: italic;
    }
</style>
"""
        css_section = css_rules if embed_css else ""
        # Construct the full HTML header, escaping the title for safety
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)}</title>
    {css_section}
</head>
<body>
    <h1>{html.escape(title)}</h1>
<!-- Start of messages -->
"""

    def format_footer(self, options):
        """Generates the HTML footer."""
        # Simple closing tags
        return """
<!-- End of messages -->
</body>
</html>
""" # Added newline for consistency

    def format_message(self, message, is_merge=False, chat_title=None):
        """Formats a single message for HTML output."""
        role = message.get('role', 'Unknown')
        ts = message.get('timestamp', 'No Ts')
        content = message.get('content', '')

        # Escape content to prevent HTML injection, then convert newlines to <br> tags
        content_html = html.escape(content).replace('\n', '<br>\n')

        # Create the metadata line including timestamp
        meta_line = f'<div class="meta">{ts}'
        # Add source chat title if this is part of a merged export
        if is_merge and chat_title:
            # Escape the chat title in case it contains HTML characters
            meta_line += f' | <span class="chat-title">{html.escape(chat_title)}</span>'
        meta_line += '</div>'

        # Construct the message div with appropriate class for styling based on role
        # Add newline after closing div for better source formatting and separation
        # Use the role directly as the class name (User, ChatGPT)
        # Ensure role name is sanitized if other roles are possible later
        safe_role_class = html.escape(role) # Basic safety for class name
        return f'<div class="message {safe_role_class}"><strong>{safe_role_class}</strong>{meta_line}{content_html}</div>\n'