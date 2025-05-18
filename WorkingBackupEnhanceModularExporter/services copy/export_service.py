# services/export_service.py
import os
import io
import zipfile
import traceback
from datetime import datetime

# Import helpers and ALL specific exporter classes + the base class
from utils.helpers import (
    sanitize_filename, get_display_title, extract_messages_from_chat,
    SMART_FOLDER_KEYWORDS, SMART_FOLDER_OTHER, DEFAULT_SPLIT_VALUE
)
from exporters.base_exporter import BaseExporter
from exporters.txt_exporter import TxtExporter
from exporters.md_exporter import MdExporter
from exporters.html_exporter import HtmlExporter
from exporters.csv_exporter import CsvExporter
from exporters.sqlite_exporter import SqliteExporter

# --- Build the Exporter Map ---
# Create instances of each exporter class we want to use
EXPORTER_MAP = {
    'txt': TxtExporter(),
    'md': MdExporter(),
    'html': HtmlExporter(),
    'csv': CsvExporter(),  # Maps 'db' form value to CSV exporter logic (uses csv extension)
    'sqlite': SqliteExporter(),
}
# Map the 'db' key used in the form/HTML to the CsvExporter instance as well
EXPORTER_MAP['db'] = EXPORTER_MAP['csv']

print(f"Initialized exporters for formats: {list(EXPORTER_MAP.keys())}")

def get_exporter_instance(format_key):
    """Gets an instance of the requested exporter based on format key (e.g., 'txt', 'md')."""
    return EXPORTER_MAP.get(format_key.lower()) # Use lowercase key

def _determine_output_subdir(chat_title, folder_mode):
    """Determines the relative subdirectory path for smart folders."""
    if folder_mode != 'Smart':
        return "" # Empty path means root of zip/output

    # Find first matching keyword, default to OTHER
    matched_folder = next(
        (folder_name for keyword, folder_name in SMART_FOLDER_KEYWORDS.items()
         if keyword.lower() in chat_title.lower()),
        SMART_FOLDER_OTHER
    )
    return matched_folder

def generate_export_files(all_chats_data, selected_indices, formats, options):
    """
    Main service function to generate export file data.

    Args:
        all_chats_data (list): The full list of chat dictionaries from JSON.
        selected_indices (list): List of integer indices to export.
        formats (dict): Dict like {'txt': True, 'md': False, ...}.
        options (dict): Dict containing export settings.

    Returns:
        list: A list of tuples: [(filename_in_zip, file_content_bytes), ...].
              Returns empty list or raises exception on critical error.
    """
    all_generated_files = [] # Holds (filename, bytes) tuples for zipping
    is_merge = options.get('is_merge', False)

    active_formats = {fmt_key for fmt_key, active in formats.items() if active}
    if not active_formats:
        raise ValueError("No export formats selected.")

    if is_merge:
        # --- Merge Logic ---
        if len(selected_indices) <= 1:
             raise ValueError("Select at least two chats to merge.")
        options['split_mode'] = 'None' # Force no splitting for merge

        merged_messages = []
        first_title_base = "Merged_Chats"
        for i, index in enumerate(selected_indices):
             if 0 <= index < len(all_chats_data):
                 chat_data = all_chats_data[index]
                 chat_title = get_display_title(chat_data, index)
                 if i == 0: first_title_base = sanitize_filename(chat_title) # Use first chat title as base hint
                 chat_id = chat_data.get("conversation_id", f"index_{index}")

                 messages = extract_messages_from_chat(chat_data, chat_title) # Use helper
                 if messages:
                     # Add context directly to message dicts for exporters to use
                     for msg in messages:
                          msg['chat_id'] = chat_id
                          msg['chat_title'] = chat_title
                     merged_messages.extend(messages)
             else: print(f"Warning: Invalid index {index} skipped during merge.")

        if not merged_messages:
             raise ValueError("No valid messages found in the selected chats to merge.")

        # Sort all merged messages by datetime object
        merged_messages.sort(key=lambda m: m.get('datetime_obj', datetime.min))

        merge_filename_base = sanitize_filename(f"Merged_{len(selected_indices)}_Chats_{datetime.now().strftime('%Y%m%d_%H%M')}")

        # Pass necessary context for specific exporters (like SQLite)
        options['chat_id'] = "MERGED" # Use a generic ID for the merged context
        options['chat_title'] = merge_filename_base # Use the generated filename as the overall title

        for fmt_key in active_formats:
             exporter = get_exporter_instance(fmt_key) # Get instance using the map
             if not exporter:
                 print(f"Warning: No exporter found for format key '{fmt_key}'")
                 continue

             print(f"Generating merged file for format: {fmt_key}")
             try:
                 # SQLite handles its own file generation as bytes
                 if fmt_key == 'sqlite' and hasattr(exporter, 'generate_single_file'):
                     file_bytes = exporter.generate_single_file(merged_messages, merge_filename_base, options)
                 else: # Other formats generate content string first
                     content_string = exporter.generate_part_content(merged_messages, merge_filename_base, options)
                     file_bytes = content_string.encode('utf-8') if content_string else None

                 if file_bytes:
                      filename = f"{merge_filename_base}.{exporter.get_extension()}"
                      all_generated_files.append((filename, file_bytes))
             except Exception as e:
                 print(f"Error generating merged {fmt_key} for {merge_filename_base}: {e}")
                 traceback.print_exc() # Print full traceback for debugging

    else:
        # --- Regular Export Logic ---
        split_mode = options.get('split_mode', 'None')
        split_value = options.get('split_value', DEFAULT_SPLIT_VALUE)
        split_by_size = split_mode == 'Size'
        split_by_count = split_mode == 'Count'
        max_size_bytes = split_value * 1024 * 1024 if split_by_size else float('inf')
        max_messages_per_part = split_value if split_by_count else float('inf')

        for index in selected_indices:
            if not (0 <= index < len(all_chats_data)):
                print(f"Warning: Invalid index {index} skipped.")
                continue

            chat_data = all_chats_data[index]
            chat_title = get_display_title(chat_data, index)
            chat_id = chat_data.get("conversation_id", f"index_{index}")

            messages = extract_messages_from_chat(chat_data, chat_title) # Use helper
            if not messages:
                print(f"Warning: No messages extracted for '{chat_title}', skipping.")
                continue

            base_filename = chat_id if options.get('use_chatid_filename') else sanitize_filename(chat_title)
            output_subdir = _determine_output_subdir(chat_title, options.get('folder_mode', 'Default'))

            # Pass chat-specific context needed by exporters
            options['chat_id'] = chat_id
            options['chat_title'] = chat_title

            for fmt_key in active_formats:
                exporter = get_exporter_instance(fmt_key)
                if not exporter:
                    print(f"Warning: No exporter found for format key '{fmt_key}'")
                    continue

                print(f"Generating {fmt_key} for: {os.path.join(output_subdir, base_filename)}")
                try:
                     # SQLite generates one file per chat
                     if fmt_key == 'sqlite' and hasattr(exporter, 'generate_single_file'):
                         file_bytes = exporter.generate_single_file(messages, base_filename, options)
                         if file_bytes:
                              filename_in_zip = os.path.join(output_subdir, f"{base_filename}.{exporter.get_extension()}")
                              all_generated_files.append((filename_in_zip, file_bytes))
                         continue # Move to next format for this chat

                     # --- Splitting Logic for other formats ---
                     file_part = 1
                     message_idx_start = 0
                     # Heuristic: Does this chat likely need *any* splitting?
                     needs_any_split_heuristic = (split_by_count and len(messages) > max_messages_per_part) or \
                                                (split_by_size and sum(len(m['content'].encode('utf-8','ignore')) for m in messages) > max_size_bytes * 0.8)

                     while message_idx_start < len(messages):
                         message_idx_end = len(messages) # Default: take all remaining
                         part_messages = []
                         current_part_size_bytes = 0 # Used only for size splitting check

                         # Determine messages for this part based on split mode
                         if split_by_count:
                             message_idx_end = min(message_idx_start + max_messages_per_part, len(messages))
                             part_messages = messages[message_idx_start:message_idx_end]
                         elif split_by_size:
                             # Iterate message by message until size limit is reached
                             temp_idx = message_idx_start
                             while temp_idx < len(messages):
                                  # Estimate size increase (crude) - includes message + potential formatting overhead
                                  msg_size_est = len(messages[temp_idx]['content'].encode('utf-8','ignore')) + 150 # Add overhead guess
                                  # Only break if the part already has messages AND adding the next one exceeds limit
                                  if temp_idx > message_idx_start and current_part_size_bytes + msg_size_est > max_size_bytes:
                                       break # Stop before adding this message
                                  current_part_size_bytes += msg_size_est
                                  temp_idx += 1
                             message_idx_end = temp_idx
                             # Ensure at least one message is included per part, even if it exceeds limit
                             part_messages = messages[message_idx_start:message_idx_end] if message_idx_start != message_idx_end else [messages[message_idx_start]]
                             message_idx_end = message_idx_start + len(part_messages) # Adjust end index based on actual messages taken
                         else: # No splitting
                             part_messages = messages[message_idx_start:message_idx_end]

                         if not part_messages: break # Safety check

                         # Determine filename for this part
                         # Add suffix if splitting is enabled AND (it's likely needed OR it's not the first part)
                         needs_part_suffix = (split_mode != 'None') and (needs_any_split_heuristic or file_part > 1)
                         part_suffix = f"_part{file_part}" if needs_part_suffix else ""
                         part_filename_base = f"{base_filename}{part_suffix}"
                         filename_in_zip = os.path.join(output_subdir, f"{part_filename_base}.{exporter.get_extension()}")

                         # Generate content for this part using the exporter
                         content_string = exporter.generate_part_content(part_messages, part_filename_base, options)
                         if content_string:
                              all_generated_files.append((filename_in_zip, content_string.encode('utf-8')))

                         message_idx_start = message_idx_end # Move start index for next part
                         file_part += 1

                except Exception as e:
                     print(f"Error generating {fmt_key} for {base_filename}: {e}")
                     traceback.print_exc()

    return all_generated_files


def create_zip_bundle(file_data_list):
    """Creates a zip file in memory."""
    if not file_data_list: return None
    try:
        zip_buffer = io.BytesIO()
        # Use allowZip64=True for potentially very large exports
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as zipf:
            for filename, file_bytes in file_data_list:
                # Ensure filename is relative path within zip, handle potential windows paths
                clean_filename = os.path.normpath(filename).replace('\\', '/').lstrip('/')
                if not clean_filename: continue # Skip empty names after cleaning
                print(f"Adding to zip: {clean_filename}")
                zipf.writestr(clean_filename, file_bytes)

        zip_buffer.seek(0) # Rewind buffer to the beginning
        return zip_buffer
    except Exception as e:
        print(f"Error creating zip file: {e}\n{traceback.format_exc()}")
        return None