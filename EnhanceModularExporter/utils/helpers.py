# utils/helpers.py (COMPLETE AND VERIFIED - Revision 3)
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
        # Check range (allow ~15 years future buffer)
        if ts_float < 0 or ts_float > time.time() + 473040000: # Approx 15 years
             return "Invalid Timestamp Range", None
        # Create naive datetime object in local timezone
        dt_obj = datetime.fromtimestamp(ts_float)
        return dt_obj.strftime('%Y-%m-%d %H:%M:%S'), dt_obj
    except (ValueError, TypeError, OSError) as e:
        # Use print for debugging locally, consider logging for production
        # print(f"[HELPER WARN] Timestamp format error for {unix_ts}: {e}")
        return "Invalid Timestamp Format", None

def get_display_title(chat_data, index):
    """Gets a display title for a chat, handling untitled chats."""
    raw_title = chat_data.get("title")
    title = str(raw_title).strip() if raw_title else ""
    if not title:
        try:
            mapping = chat_data.get("mapping", {})
            if mapping:
                # Find the node with the earliest timestamp as a proxy for the start
                root_node_id = min(mapping, key=lambda k: mapping.get(k, {}).get("message", {}).get("create_time", float('inf')), default=None)
                current_node_data = mapping.get(root_node_id) if root_node_id else None
                msg_count = 0
                while current_node_data and msg_count < 5: # Limit search depth
                    msg = current_node_data.get("message")
                    if msg and msg.get("author",{}).get("role") == "user":
                        content = msg.get("content",{}).get("parts",[])
                        if content and isinstance(content[0], str):
                            title = f"Untitled: {content[0][:60].strip()}..."
                            break # Found first user message
                    # Traverse children (try finding the child node - assumes linear most times)
                    children = current_node_data.get("children", [])
                    next_node_id = children[0] if children else None
                    current_node_data = mapping.get(next_node_id) if next_node_id else None
                    msg_count += 1
        except Exception as e:
             # print(f"[HELPER WARN] Error generating fallback title: {e}")
             pass # Ignore errors during fallback title generation
        # If still no title, use conversation ID or index
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
                # print(f"[HELPER WARN] Regex error during anonymization: {re_err}")
                pass # Continue even if one pattern fails
    if leet_speak:
        try:
            new_content = [LEET_MAP[c] if c in LEET_MAP and random.random() < 0.3 else c for c in content]
            content = "".join(new_content)
        except Exception as leet_err:
             # print(f"[HELPER WARN] Error applying leet speak: {leet_err}")
             pass # Continue if leet speak fails
    return content

def extract_messages_from_chat(chat_data, chat_title):
    """
    Extracts and sorts messages from a single chat_data object.
    Returns list of message dictionaries or None on critical failure.
    """
    messages = []
    mapping = chat_data.get("mapping")
    if not isinstance(mapping, dict):
        # print(f"[HELPER WARN] Chat '{chat_title}' has invalid/missing 'mapping'. Skipping.")
        return None # Cannot proceed without mapping

    message_nodes = []
    # Iterate through all nodes in the mapping
    for node_id, node_data in mapping.items():
        # Basic structure validation for the node itself
        if not isinstance(node_data, dict):
            continue # Skip this node if structure is wrong

        # Get the message dictionary within the node
        msg = node_data.get("message")
        if not isinstance(msg, dict):
            continue # Skip if message structure is wrong

        # Now safely access keys within the 'msg' dictionary
        author = msg.get("author")
        content = msg.get("content")
        create_time = msg.get("create_time")

        # Check required fields and types rigorously
        if (isinstance(author, dict) and author.get("role") in ["user", "assistant"] and
            isinstance(content, dict) and content.get("content_type") == "text" and
            # Check if 'parts' exists AND is a list
            "parts" in content and isinstance(content.get("parts"), list) and
            create_time is not None):
             # Ensure all 'parts' are strings before adding
             parts_list = content.get("parts", []) # Get parts list safely
             if isinstance(parts_list, list):
                 valid_parts = [p for p in parts_list if isinstance(p, str)]
                 # Only add if all original parts were valid strings
                 if len(valid_parts) == len(parts_list):
                     message_nodes.append((create_time, msg))

    # After checking all nodes
    if not message_nodes:
        return None # Return None if absolutely no valid messages were found

    # Sort the collected valid message nodes by their timestamp
    message_nodes.sort(key=lambda x: x[0])

    # Process sorted nodes into the final message list format
    processed_messages = []
    for msg_index, (create_time, msg_dict) in enumerate(message_nodes): # Use the msg_dict from the tuple
        role = msg_dict.get("author", {}).get("role") # Safely access role
        if not role: continue # Skip if role is missing somehow

        display_role = "User" if role == "user" else "ChatGPT"
        timestamp_str, dt_obj = format_timestamp(create_time)

        # Join only string parts, handle potential errors gracefully
        try:
            parts_list = msg_dict.get("content", {}).get("parts", [])
            if isinstance(parts_list, list):
                full_content = "".join(p for p in parts_list if isinstance(p, str)).strip()
            else:
                full_content = "[Error: Invalid content parts structure]"
        except Exception as join_err:
            full_content = "[Error processing content]"

        processed_messages.append({
            "role": display_role,
            "timestamp": timestamp_str,
            "content": full_content,
            "datetime_obj": dt_obj,
            "index": msg_index,
            "word_count": len(full_content.split())
        })
    return processed_messages