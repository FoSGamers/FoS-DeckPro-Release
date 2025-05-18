# services/export_service.py (FIXED SyntaxError in size splitting loop - Revision 4 - COMPLETE)
import os
import io
import zipfile
import traceback
import json # To format queue messages
from datetime import datetime

# Import helpers and ALL specific exporter classes + the base class
from utils.helpers import (
    sanitize_filename, get_display_title, extract_messages_from_chat,
    SMART_FOLDER_KEYWORDS, SMART_FOLDER_OTHER, DEFAULT_SPLIT_VALUE
)
# Import base first, then specific implementations
from exporters.base_exporter import BaseExporter
from exporters.txt_exporter import TxtExporter
from exporters.md_exporter import MdExporter
from exporters.html_exporter import HtmlExporter
from exporters.csv_exporter import CsvExporter
from exporters.sqlite_exporter import SqliteExporter

# --- Build the Exporter Map ---
# Create instances of each concrete exporter class
EXPORTER_MAP = {
    'txt': TxtExporter(),
    'md': MdExporter(),
    'html': HtmlExporter(),
    'csv': CsvExporter(),  # This handles the '.csv' output
    'sqlite': SqliteExporter(),
}
# Map the 'db' key used in the form/HTML to the CsvExporter instance
# This ensures the checkbox name="export_db" correctly triggers CSV export logic
EXPORTER_MAP['db'] = EXPORTER_MAP['csv']

print(f"[SERVICE] Initialized exporters for formats: {list(EXPORTER_MAP.keys())}")

def get_exporter_instance(format_key):
    """Gets an instance of the requested exporter based on format key (e.g., 'txt', 'md', 'db')."""
    # Use lowercase key for lookup consistency
    return EXPORTER_MAP.get(format_key.lower())

def _determine_output_subdir(chat_title, folder_mode):
    """Determines the relative subdirectory path for smart folders within the zip."""
    if folder_mode != 'Smart':
        return "" # Empty path means files go into the root of the zip

    # Find first matching keyword, default to OTHER if no match
    matched_folder = next(
        (folder_name for keyword, folder_name in SMART_FOLDER_KEYWORDS.items()
         if keyword.lower() in chat_title.lower()),
        SMART_FOLDER_OTHER # Default folder if no keywords match
    )
    return matched_folder # Return just the subfolder name

# --- Helper to publish progress via queue ---
def _publish_progress(queue, message, type="progress", percent=None):
    """Puts a JSON-formatted progress message into the provided queue."""
    if not queue: return # No queue provided, can't publish
    try:
        payload = {"type": type, "message": message}
        # Ensure percentage is within valid range if provided
        if percent is not None:
            payload["percent"] = max(0, min(100, int(percent))) # Clamp 0-100
        # Put the JSON string representation into the queue
        queue.put(json.dumps(payload))
    except Exception as e:
        # Log error if queuing fails, but don't stop the export
        print(f"[SERVICE ERROR] Failed to queue progress message: {e}")


# --- Main Export Function (Accepts progress_queue) ---
def generate_export_files(all_chats_data, selected_indices, formats, options, progress_queue=None):
    """
    Main service function to generate export file data, reporting progress via queue.
    Orchestrates merging, splitting, and calls individual exporters.
    """
    all_generated_files = [] # List to hold tuples of (filename_in_zip, file_content_bytes)
    is_merge = options.get('is_merge', False)
    active_fmts = {f for f,a in formats.items() if a} # Set of active format keys (e.g., {'txt', 'md', 'db'})
    total_proc = len(selected_indices) # Total number of chats selected
    proc_count = 0 # Counter for processed chats

    if not active_fmts:
        raise ValueError("No export formats selected.")

    _publish_progress(progress_queue, "Export process starting...", percent=0)
    print("-" * 30) # Terminal separator

    if is_merge:
        # --- Merge Logic ---
        _publish_progress(progress_queue, f"Starting MERGE for {total_proc} chats...")
        print(f"[EXPORT SVC] Starting MERGE...")
        if len(selected_indices) <= 1: raise ValueError("Select >= 2 chats to merge.")
        options['split_mode'] = 'None'; _publish_progress(progress_queue, "Splitting disabled for merge.")

        merged_msgs = []; first_title = "Merged_Chats"
        for i, idx in enumerate(selected_indices):
            proc_count=i+1; percent = int((proc_count / total_proc) * 50) # Reading phase is ~50%
            if not(0 <= idx < len(all_chats_data)):
                _publish_progress(progress_queue, f"Skipping invalid index {idx}", "warning")
                print(f"[WARN] Invalid merge index {idx} skipped.")
                continue
            cdata=all_chats_data[idx]; title=get_display_title(cdata,idx); cid=cdata.get("conversation_id",f"idx_{idx}")
            _publish_progress(progress_queue, f"({proc_count}/{total_proc}) Reading: {title[:40]}...", percent=percent)
            print(f"[MERGE {proc_count}/{total_proc}] Reading: '{title}'")
            if i == 0: first_title = sanitize_filename(title) # Use first valid title as base hint

            # Extract messages for this chat
            msgs = extract_messages_from_chat(cdata, title); # Use helper
            if msgs:
                # Add context needed by exporters (like SQLite) directly to message dicts
                for m in msgs: m.update({'chat_id':cid,'chat_title':title})
                merged_msgs.extend(msgs)
            else: _publish_progress(progress_queue, f"No messages extracted from '{title}'", "warning")

        if not merged_msgs: raise ValueError("No messages found to merge.");
        _publish_progress(progress_queue, f"Sorting {len(merged_msgs)} messages...", percent=55)
        print(f"[MERGE] Sorting {len(merged_msgs)} messages...")
        merged_msgs.sort(key=lambda m: m.get('datetime_obj', datetime.min)) # Sort by actual datetime object
        mrg_base = sanitize_filename(f"Merged_{len(selected_indices)}_{datetime.now():%Y%m%d_%H%M}");
        # Update options dict with context specific to the merged file (used by exporters like SQLite)
        options.update({'chat_id':"MERGED",'chat_title':mrg_base})
        _publish_progress(progress_queue, f"Generating outputs (Base: {mrg_base})...", percent=60)
        print(f"[MERGE] Generating merged outputs (Base: {mrg_base})...")

        fmt_count = len(active_fmts)
        for i, fmt in enumerate(active_fmts):
            percent = 60 + int(((i+1) / fmt_count) * 40); # Generation phase is remaining ~40%
            exp = get_exporter_instance(fmt);
            if not exp: _publish_progress(progress_queue, f"No exporter for '{fmt}'", "warning"); continue
            _publish_progress(progress_queue, f"Generating merged: {fmt.upper()}", percent=percent)
            print(f"  - Generating merged: {fmt.upper()}")
            try:
                # Check if exporter has special method (like SQLite), otherwise use standard part gen
                # generate_single_file should return bytes, generate_part_content returns string
                if hasattr(exp, 'generate_single_file'):
                    file_bytes = exp.generate_single_file(merged_msgs, mrg_base, options) # Should return bytes
                else:
                    content_str = exp.generate_part_content(merged_msgs, mrg_base, options) # Returns string
                    file_bytes = content_str.encode('utf-8') if content_str else None # Encode string result

                if file_bytes:
                    # Use the correct extension from the exporter instance
                    all_generated_files.append((f"{mrg_base}.{exp.get_extension()}", file_bytes)) # Add (filename, bytes)
                else: _publish_progress(progress_queue, f"No content for merged {fmt.upper()}", "warning")
            except Exception as e:
                _publish_progress(progress_queue, f"ERROR merging {fmt}: {e}", "error");
                print(f"  - ERROR generating merged {fmt}: {e}"); traceback.print_exc()

    else: # --- Regular Export Logic ---
        _publish_progress(progress_queue, f"Starting REGULAR export for {total_proc} chats...")
        print(f"[EXPORT SVC] Starting REGULAR export...")
        split=options.get('split_mode','None'); sval=options.get('split_value',DEFAULT_SPLIT_VALUE); ssize=split=='Size'; scount=split=='Count'; max_sz=sval*1024*1024 if ssize else float('inf'); max_ct=sval if scount else float('inf')

        for i, idx in enumerate(selected_indices):
            proc_count=i+1; percent = int((proc_count / total_proc) * 100) # Overall percentage
            if not(0 <= idx < len(all_chats_data)): _publish_progress(progress_queue, f"Skipping invalid index {idx}", "warning"); continue
            cdata=all_chats_data[idx]; title=get_display_title(cdata,idx); cid=cdata.get("conversation_id",f"idx_{idx}");
            _publish_progress(progress_queue, f"({proc_count}/{total_proc}) Processing: {title[:40]}...", percent=percent)
            print(f"[EXPORT {proc_count}/{total_proc}] Processing: '{title}' (ID: {cid})")
            msgs = extract_messages_from_chat(cdata, title) # Use helper
            if not msgs: _publish_progress(progress_queue, f"No messages extracted for '{title}', skipping.", "warning"); print(f"  - WARN: No messages extracted."); continue

            base_fn=cid if options.get('use_chatid_filename') else sanitize_filename(title);
            sub_dir=_determine_output_subdir(title,options.get('folder_mode','Default'));
            # Update options dict with context specific to this chat
            options.update({'chat_id':cid,'chat_title':title})

            for fmt in active_fmts:
                exp = get_exporter_instance(fmt);
                if not exp: _publish_progress(progress_queue, f"No exporter for '{fmt}' in '{title}'", "warning"); continue
                _publish_progress(progress_queue, f"({proc_count}/{total_proc}) Generating {fmt.upper()} for '{title[:25]}...'")
                print(f"  - Generating: {fmt.upper()}...")
                try:
                    # Handle SQLite separately
                    if fmt == 'sqlite' and hasattr(exp, 'generate_single_file'):
                         fbytes=exp.generate_single_file(msgs, base_fn, options); # Should return bytes
                         if fbytes: all_generated_files.append((os.path.join(sub_dir,f"{base_fn}.sqlite"), fbytes))
                         else: _publish_progress(progress_queue, f"No SQLite content for '{title}'", "warning")
                         continue # SQLite done for this chat

                    # Splitting logic for text-based formats
                    start=0; pnum=1;
                    # Estimate if splitting is needed for this chat/format
                    hint=(scount and len(msgs)>max_ct)or(ssize and sum(len(m.get('content','').encode('utf-8','ignore')) for m in msgs) > max_sz * 0.8)
                    while start < len(msgs):
                        end=len(msgs); pmsgs=[]; pbytes_est=0 # Estimated size for this part

                        # Determine which messages go into this specific part
                        if scount:
                             end = min(start + int(max_ct), len(msgs)) # Use int() for safety
                             pmsgs = msgs[start:end]
                        elif ssize:
                            # *** CORRECTED Size Splitting Logic ***
                            i_idx = start # Local index for this inner loop
                            while i_idx < len(msgs):
                                est = len(msgs[i_idx].get('content','').encode('utf-8','ignore')) + 150
                                # Check size *before* adding the message
                                if i_idx > start and pbytes_est + est > max_sz:
                                    break # Stop before adding this message
                                # If it fits (or it's the first message), add its estimated size
                                pbytes_est += est
                                # *** FIX: Increment index *after* checks ***
                                i_idx += 1
                            # *** END FIX ***
                            end = i_idx # Index 'i_idx' is now the first message that *didn't* fit
                            pmsgs = msgs[start:end] # Select messages up to, but not including, end
                            # Handle edge case: first message itself is too large, or only one msg left
                            if start == end and start < len(msgs):
                                _publish_progress(progress_queue, f"Single msg index {start} might exceed size limit", "info")
                                pmsgs = [msgs[start]]; end = start + 1 # Take just the one and advance
                            # *** End Corrected Size Splitting Logic ***
                        else: # No splitting enabled
                             pmsgs = msgs[start:end]

                        if not pmsgs: break # Safety check if slice somehow results in empty list

                        # Determine filename for this part, adding suffix if needed
                        needs_suffix=(split!='None')and(hint or pnum>1)
                        part_suffix=f"_part{pnum}" if needs_suffix else ""
                        pbase=f"{base_fn}{part_suffix}"
                        # Use the correct extension from the exporter instance
                        fname_zip = os.path.join(sub_dir, f"{pbase}.{exp.get_extension()}")
                        _publish_progress(progress_queue, f"    Generating part: {os.path.basename(fname_zip)} ({len(pmsgs)} msgs)"); print(f"    - Gen part: {os.path.basename(fname_zip)}")

                        # Generate content using the specific exporter for this part
                        # BaseExporter's generate_part_content returns string
                        # SQLiteExporter overrides it to return bytes
                        content_result=exp.generate_part_content(pmsgs, pbase, options);

                        # Check type of result and encode if necessary
                        if isinstance(content_result, bytes): fbytes_part = content_result # SQLite already returns bytes
                        elif isinstance(content_result, str): fbytes_part = content_result.encode('utf-8')
                        else: fbytes_part = None # Skip if unexpected type

                        # Add generated content (as bytes) to the list if valid
                        if fbytes_part: all_generated_files.append((fname_zip, fbytes_part))
                        else: _publish_progress(progress_queue, f"No content for {fmt} part {pnum} in '{title}'", "warning")
                        start=end; pnum+=1 # Move to next part's start index
                except Exception as e:
                    _publish_progress(progress_queue, f"ERROR exporting {fmt} for '{title}': {e}", "error");
                    print(f"    - ERROR exporting {fmt}: {e}"); traceback.print_exc()
    _publish_progress(progress_queue, f"Finished. Generated {len(all_generated_files)} files.", percent=100); print(f"[EXPORT SVC] Finished. Generated {len(all_generated_files)} files."); print("-" * 30)
    return all_generated_files

def create_zip_bundle(file_list):
    # Creates a zip file in memory from a list of (filename, bytes_content).
    if not file_list: return None
    try:
        print(f"[ZIP SVC] Creating ZIP ({len(file_list)} parts)..."); buf=io.BytesIO();
        # Use allowZip64=True for potentially very large exports > 4GB
        with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
            for fn,fdata in file_list:
                # Clean filename, ensure relative path within zip
                cfname=os.path.normpath(fn).replace('\\','/').lstrip('/')
                if cfname: # Avoid adding empty filenames
                    # print(f"  - Adding to ZIP: {cfname} ({len(fdata)} bytes)") # Verbose
                    zf.writestr(cfname, fdata)
        buf.seek(0); print("[ZIP SVC] ZIP created."); return buf
    except Exception as e: print(f"ZIP Error: {e}\n{traceback.format_exc()}"); return None