# exporters/html_exporter.py
import html
from .base_exporter import BaseExporter

class HtmlExporter(BaseExporter):
    def get_extension(self): return "html"
    def format_header(self, title, options):
        embed_css = options.get('html_embed_css', True)
        css = """<style>body{font-family:sans-serif;max-width:800px;margin:20px auto;padding:15px;border:1px solid #ddd;line-height:1.6;background-color:#fdfdfd}h1{text-align:center;border-bottom:1px solid #eee;padding-bottom:10px;margin-bottom:20px;color:#333}.message{margin-bottom:1em;padding:10px 12px;border-radius:6px;border:1px solid #eee}.message strong{display:block;margin-bottom:.3em;font-size:.9em;color:#111}.message .meta{font-size:.8em;color:#666;margin-bottom:.5em}.message .chat-title{font-weight:bold;color:#0056b3;margin-left:5px}.User{background-color:#eef7ff;border-color:#d1e9ff}.ChatGPT{background-color:#f1f8e9;border-color:#dcedc8}pre{background-color:#f0f0f0;border:1px solid #ddd;padding:10px;border-radius:4px;white-space:pre-wrap;word-wrap:break-word;font-family:monospace;font-size:.9em}blockquote{border-left:3px solid #ccc;padding-left:10px;margin-left:0;color:#555}</style>""" if embed_css else ""
        return f'<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{html.escape(title)}</title>{css}</head><body><h1>{html.escape(title)}</h1>'
    def format_footer(self, options): return "\n</body>\n</html>\n"
    def format_message(self, message, is_merge=False, chat_title=None):
        role = message.get('role', 'Unknown'); ts = message.get('timestamp', 'No Ts'); content = message.get('content', '')
        content_html = html.escape(content).replace('\n', '<br>\n')
        meta = f'<div class="meta">{ts}' + (f' | <span class="chat-title">{html.escape(chat_title)}</span>' if is_merge and chat_title else '') + '</div>'
        return f'<div class="message {role}"><strong>{role}</strong>{meta}{content_html}</div>\n'