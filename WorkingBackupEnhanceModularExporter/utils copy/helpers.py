# utils/helpers.py
import re
import time
from datetime import datetime
import random # Keep for leet_speak

# --- Constants ---
ANONYMIZATION_PATTERNS = {
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b': '[EMAIL REDACTED]',
    r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b': '[PHONE REDACTED]',
}

LEET_MAP = {'a': '4', 'e': '3', 'g': '6', 'i': '1', 'o': '0', 's': '5', 't': '7',
            'A': '4', 'E': '3', 'G': '6', 'I': '1', 'O': '0', 'S': '5', 'T': '7'}

SMART_FOLDER_KEYWORDS = {
    'programming': 'Programming', 'python': 'Programming', 'code': 'Programming',
    'script': 'Programming', 'javascript': 'Programming', 'java': 'Programming',
    'c++': 'Programming', 'debug': 'Programming', 'error': 'Programming',
    'algorithm': 'Programming', 'story': 'Story_Writing', 'writing': 'Story_Writing',
    'novel': 'Story_Writing', 'character': 'Story_Writing', 'plot': 'Story_Writing',
    'lore': 'Story_Lore', 'worldbuilding': 'Story_Lore', 'deckbuilding': 'Deckbuilding',
    'mtg': 'Deckbuilding', 'magic: the gathering': 'Deckbuilding', 'yugioh': 'Deckbuilding',
    'pokemon tcg': 'Deckbuilding', 'vault': 'Vault_Adventures', 'idea': 'Ideas',
    'brainstorm': 'Ideas', 'project': 'Projects', 'plan': 'Projects',
    'research': 'Research', 'summary': 'Summaries', 'translate': 'Translation',
    'email': 'Communication', 'letter': 'Communication', 'recipe': 'Recipes',
    'food': 'Recipes', 'travel': 'Travel', 'history': 'History', 'science': 'Science',
    'learning': 'Learning', 'tutorial': 'Learning',
}
SMART_FOLDER_OTHER = 'Other_Chats'
DEFAULT_SPLIT_VALUE = 10

# --- Helper Functions ---

def sanitize_filename(name):
    """Removes or replaces characters invalid in filenames."""
    if not name: name = "Untitled"
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = re.sub(r'[^\w\s.-]', '', name).strip()
    name = re.sub(r'\s+', '_', name).strip()
    name = name if name else "Untitled_Chat"
    max_len = 150
    if len(name) > max_len:
        cut_pos = name[:max_len].rfind('_')
        if cut_pos > max_len / 2:
            name = name[:cut_pos]
        else:
            name = name[:max_len]
    return name

def format_timestamp(unix_ts):
    """Converts Unix timestamp to 'YYYY-MM-DD HH:MM:SS' string and datetime object."""
    try:
        if unix_ts is None: return "No Timestamp", None
        ts_float = float(unix_ts)
        if ts_float < 0 or ts_float > time.time() + 315360000: # ~10 years buffer
            return "Invalid Timestamp Range", None
        dt_obj = datetime.fromtimestamp(ts_float)
        return dt_obj.strftime('%Y-%m-%d %H:%M:%S'), dt_obj
    except (ValueError, TypeError, OSError):
        return "Invalid Timestamp Format", None

def get_display_title(chat_data, index):
    """Gets a display title for a chat, handling untitled chats."""
    raw_title = chat_data.get("title")
    title = str(raw_title).strip() if raw_title else ""
    if not title:
        try:
            mapping = chat_data.get("mapping", {})
            if mapping:
                root_node_id = min(mapping, key=lambda k: mapping[k].get("message", {}).get("create_time", float('inf')), default=None)
                current_node_data = mapping.get(root_node_id) if root_node_id else None
                msg_count = 0
                while current_node_data and msg_count < 5:
                    msg = current_node_data.get("message")
                    if msg and msg.get("author", {}).get("role") == "user":
                        content = msg.get("content", {}).get("parts", [])
                        if content and isinstance(content[0], str):
                            title = f"Untitled: {content[0][:60].strip()}..."
                            break
                    children = current_node_data.get("children", [])
                    next_node_id = children[0] if children else None
                    current_node_data = mapping.get(next_node_id) if next_node_id else None
                    msg_count += 1
        except Exception:
            pass
        if not title:
            chat_id_hint = chat_data.get("conversation_id", chat_data.get("id"))
            title = f"Untitled Chat ({chat_id_hint})" if chat_id_hint else f"Untitled Chat {index + 1}"
    return title

def apply_text_mods(content, anonymize, leet_speak):
    """Applies anonymization and leet speak if enabled."""
    if anonymize:
        for pattern, replacement in ANONYMIZATION_PATTERNS.items():
            try:
                content = re.sub(pattern, replacement, content)
            except Exception as re_err:
                print(f"Warning: Regex error during anonymization: {re_err}")
    if leet_speak:
        try:
            new_content = [LEET_MAP[c] if c in LEET_MAP and random.random() < 0.3 else c for c in content]
            content = "".join(new_content)
        except Exception as leet_err:
             print(f"Warning: Error applying leet speak: {leet_err}")
    return content

# Moved from export_logic as it's a core data extraction step
def extract_messages_from_chat(chat_data, chat_title):
    """Extracts and sorts messages. Returns list of message dicts or None."""
    messages = []
    mapping = chat_data.get("mapping")
    if not isinstance(mapping, dict):
        print(f"Warning: Chat '{chat_title}' has invalid/missing 'mapping'. Skipping.")
        return None

    message_nodes = []
    for node_id, node_data in mapping.items():
        if not isinstance(node_data, dict): continue
        msg = node_data.get("message")
        if not isinstance(msg, dict): continue
        author = msg.get("author")
        content = msg.get("content")
        create_time = msg.get("create_time")
        if (isinstance(author, dict) and author.get("role") in ["user", "assistant"] and
            isinstance(content, dict) and content.get("content_type") == "text" and
            isinstance(content.get("parts"), list) and create_time is not None):
             valid_parts = [p for p in content["parts"] if isinstance(p, str)]
             if len(valid_parts) == len(content["parts"]):
                 message_nodes.append((create_time, msg))
    if not message_nodes: return None
    message_nodes.sort(key=lambda x: x[0]) # Sort by timestamp
    processed_messages = []
    for msg_index, (create_time, msg) in enumerate(message_nodes):
        role = msg["author"]["role"]
        display_role = "User" if role == "user" else "ChatGPT"
        timestamp_str, dt_obj = format_timestamp(create_time)
        full_content = "".join(p for p in msg["content"]["parts"] if isinstance(p, str)).strip()
        processed_messages.append({
            "role": display_role, "timestamp": timestamp_str, "content": full_content,
            "datetime_obj": dt_obj, "index": msg_index, "word_count": len(full_content.split())
        })
    return processed_messages