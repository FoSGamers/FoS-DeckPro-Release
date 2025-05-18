# app.py (Main Flask Application - Definitive Version with Fixes & Debugging)
import os
import json
import traceback
import io
from datetime import datetime, timedelta
from flask import ( Flask, render_template, request, jsonify, session,
                    send_file, flash, redirect, url_for )
from werkzeug.utils import secure_filename
from flask_session import Session # Import Flask-Session

# Import service layer and helpers
from services.export_service import generate_export_files, create_zip_bundle
# Import helpers used directly by routes AND ensure extract function is available
from utils.helpers import ( format_timestamp, get_display_title,
                            DEFAULT_SPLIT_VALUE, extract_messages_from_chat )

app = Flask(__name__)
print("[APP DEBUG] Flask app initialized.")

# --- Session Configuration (Server-Side) ---
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'local-dev-secret-must-be-changed-final-check')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session' # Ensure this directory exists and is writable
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=4)
# app.config['SESSION_COOKIE_SECURE'] = True # Use only with HTTPS
# app.config['SESSION_COOKIE_HTTPONLY'] = True
# app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
print(f"[APP DEBUG] Session type configured for: {app.config['SESSION_TYPE']}")
print(f"[APP DEBUG] Session file dir set to: {os.path.abspath(app.config['SESSION_FILE_DIR'])}")

# Initialize the session extension AFTER setting config
server_session = Session()
server_session.init_app(app)
print("[APP DEBUG] Flask-Session initialized.")
# --- End Session Configuration ---

# --- Session Data Management ---
def get_session_chats():
    print("[APP DEBUG] Attempting get_session_chats()")
    data = session.get('chat_data', None) # Default to None to distinguish from empty list
    if data is None:
        print("[APP DEBUG] 'chat_data' key NOT FOUND in session.")
        return []
    elif not isinstance(data, list):
        print(f"[APP DEBUG] WARNING: 'chat_data' in session is TYPE {type(data)}, not list! Clearing session.")
        session.clear() # Clear corrupted session
        return []
    else:
        print(f"[APP DEBUG] Retrieved 'chat_data'. Length: {len(data)}.")
        return data

def get_session_chat_dt_map():
     raw_map = session.get('chat_datetime_map_iso', {}); dt_map = {}
     # print(f"[APP DEBUG] Retrieved 'chat_datetime_map_iso'. Items: {len(raw_map)}") # Verbose
     for k, v_iso in raw_map.items():
         try: dt_map[int(k)] = datetime.fromisoformat(v_iso) if v_iso else None
         except: dt_map[int(k)] = None
     return dt_map

def set_session_chats(data_to_store):
    print(f"[APP DEBUG] Attempting set_session_chats(). Incoming data length: {len(data_to_store)}")
    session.clear() # Clear previous data first
    session['chat_data'] = data_to_store # Store the main list
    dt_map_iso = {} # Store datetimes as strings
    for i, chat in enumerate(data_to_store):
        ts = chat.get("update_time", chat.get("create_time")); _, dt = format_timestamp(ts)
        dt_map_iso[str(i)] = dt.isoformat() if dt else None
    session['chat_datetime_map_iso'] = dt_map_iso;
    session.modified = True # ** Explicitly mark session as modified **
    print(f"[APP DEBUG] SET session complete. Keys in session: {list(session.keys())}. 'chat_data' length check: {len(session.get('chat_data',[]))}")


# --- Routes ---
@app.route('/', methods=['GET', 'POST'])
def index():
    # --- POST Request Logic (File Upload) ---
    if request.method == 'POST':
        print("[APP DEBUG] POST request received for /")
        if 'file' not in request.files or not request.files['file'].filename:
            flash('No file selected.', 'error'); return redirect(request.url)
        file = request.files['file']
        if file and file.filename.lower().endswith('.json'):
            fname = secure_filename(file.filename) # Secure filename early
            try:
                raw = file.read().decode('utf-8'); data = json.loads(raw);
                if not isinstance(data, list): raise ValueError("JSON root not list.");
                print(f"[APP DEBUG] File '{fname}' parsed successfully. Length: {len(data)}. Calling set_session_chats...")
                set_session_chats(data); # Store in session
                flash(f'Loaded "{fname}" ({len(data)} convos).', 'success')
            except Exception as e:
                flash(f'Error processing file "{fname}": {e}', 'error');
                print(f"Upload Error: {traceback.format_exc()}")
            print("[APP DEBUG] POST request finished. Redirecting to GET /")
            # Redirect ensures subsequent refresh doesn't re-post form
            return redirect(url_for('index'))
        else:
            flash('Invalid file type (Requires .json).', 'error');
            return redirect(request.url)

    # --- GET Request Logic (Display Page) ---
    print("[APP DEBUG] GET request received for /")
    all_chats_data = get_session_chats() # Retrieve data using careful helper

    chats_for_display = []
    has_data_flag = False # Default to False

    # Define filter variables *before* the main processing block
    search_term = request.args.get('search', '').lower()
    date_on = request.args.get('date_filter') == 'on'
    start_str = request.args.get('start_date', '')
    end_str = request.args.get('end_date', '')
    start_dt, end_dt = None, None # Initialize date objects

    if all_chats_data: # Only proceed if session retrieval was successful
        print(f"[APP DEBUG] Data found in session (length {len(all_chats_data)}). Processing list...")
        try:
            # Parse dates only if date_on is true *initially*
            if date_on:
                try:
                    start_dt=datetime.strptime(start_str,'%Y-%m-%d').date()
                    end_dt=(datetime.strptime(end_str,'%Y-%m-%d')+timedelta(days=1)).date()
                    print(f"[APP DEBUG] Date filter active: {start_dt} to {end_dt}")
                except ValueError:
                    date_on = False # Turn off filter if format is bad
                    if start_str or end_str: # Flash only if user provided input
                         flash('Invalid date format ignored.', 'warning')
                    print("[APP DEBUG] Date filter disabled due to invalid format.")

            dt_map = get_session_chat_dt_map()
            print("[APP DEBUG] Starting chat processing loop...")
            processed_count = 0
            for i, chat in enumerate(all_chats_data):
                # Check for processing errors within the loop
                try:
                    title=get_display_title(chat,i);
                except Exception as title_err:
                    print(f"[APP DEBUG] ERROR getting title for index {i}: {title_err}")
                    # Decide whether to skip or use a default error title
                    title = f"Error processing title for chat {i+1}"
                    # continue # Option: skip chats with bad titles

                # Apply filters
                if search_term and search_term not in title.lower(): continue

                # Check date filter *after* potential disabling and title generation
                if date_on:
                    try:
                        chat_dt=dt_map.get(i);
                        # Check for valid date object before comparing
                        if not chat_dt or not isinstance(chat_dt, datetime) or not (start_dt <= chat_dt.date() < end_dt): continue
                    except Exception as date_err:
                        print(f"[APP DEBUG] ERROR checking date for index {i}, title '{title}': {date_err}")
                        continue # Skip if date check errors out

                # If passes all filters
                chats_for_display.append({'original_index': i, 'title': title})
                processed_count += 1

            print(f"[APP DEBUG] Finished chat processing loop. {processed_count} chats passed filters.")
            # Only set has_data_flag if we started with data AND the loop ran ok
            has_data_flag = True

        except Exception as e_filter_loop:
            print(f"ERROR processing chat list in GET: {e_filter_loop}")
            traceback.print_exc()
            flash("Error displaying chat list.", "error")
            has_data_flag = False; chats_for_display = []

    else: # all_chats_data was empty or invalid from session
        print("[APP DEBUG] No valid chat data found in session for GET request.")

    # Define filter values for template rendering *after* potential modification (like date_on being disabled)
    def_start=(datetime.now()-timedelta(days=30)).strftime('%Y-%m-%d'); def_end=datetime.now().strftime('%Y-%m-%d')
    filter_vals = {'search':search_term, 'date_filter':date_on, 'start_date':start_str or def_start, 'end_date':end_str or def_end}

    print(f"[APP DEBUG] Rendering template. has_data = {has_data_flag}, chats to display = {len(chats_for_display)}")
    return render_template('index.html', chats=chats_for_display, filter_values=filter_vals, has_data=has_data_flag)


# --- /preview and /export routes remain unchanged from previous versions ---
# (Make sure they are present in your actual file)
@app.route('/preview')
def preview():
    idx=request.args.get('index',type=int); chats=get_session_chats();
    if idx is None or not (0 <= idx < len(chats)): return jsonify({"error": "Invalid index"}), 400
    try:
        msgs = extract_messages_from_chat(chats[idx], get_display_title(chats[idx], idx));
        if not msgs: return jsonify({"preview": "(No valid messages found)"})
        limit=25; lines=[f"--- Preview: {get_display_title(chats[idx], idx)} ---\n"]
        for i,m in enumerate(msgs):
            if i>=limit: lines.append(f"\n... ({len(msgs)-limit} more)"); break
            ts,_ = format_timestamp(m['datetime_obj'].timestamp()) if m.get('datetime_obj') else ("No Ts", None)
            lines.append(f"{m.get('role','?')}[{ts}]:\n"+"\n".join([f"  {ln}" for ln in m.get('content','').splitlines()])+"\n")
        return jsonify({"preview": "\n".join(lines)})
    except Exception as e: print(f"Preview Error: {traceback.format_exc()}"); return jsonify({"error": f"Preview gen error: {e}"}), 500

@app.route('/export', methods=['POST'])
def export():
    chats=get_session_chats();
    if not chats: flash("No data loaded.", "error"); return redirect(url_for('index'))
    try:
        indices=request.form.getlist('selected_chats',type=int);
        if not indices: flash("No chats selected.", "warning"); return redirect(url_for('index'))
        fmts={fmt:f'export_{fmt}' in request.form for fmt in ['txt','md','html','db','sqlite']}
        if not any(fmts.values()): flash("No format selected.","warning"); return redirect(url_for('index')+'#export-options')
        try: sval=int(request.form.get('split_value',DEFAULT_SPLIT_VALUE)); sval=max(1, sval)
        except: sval=DEFAULT_SPLIT_VALUE
        opts={ # Gather all options
            'split_mode':request.form.get('split_mode','None'),'split_value':sval,
            'folder_mode':request.form.get('folder_mode','Default'),
            'anonymize':'anonymize' in request.form,'leet_speak':'leet_speak' in request.form,
            'use_chatid_filename':'use_chatid_filename' in request.form,
            'html_embed_css':'html_embed_css' in request.form,
            'is_merge':'merge_selected' in request.form
        }
        file_data = generate_export_files(chats, indices, fmts, opts) # Call service
        if not file_data: flash("No files generated.","error"); return redirect(url_for('index'))
        if len(file_data)==1:
            fname,fdata=file_data[0]; buf=io.BytesIO(fdata);
            resp=send_file(buf, as_attachment=True, download_name=os.path.basename(fname), mimetype='application/octet-stream')
        else:
            zip_buf=create_zip_bundle(file_data);
            if not zip_buf: raise Exception("ZIP creation failed.")
            zip_fname=f"ChatGPT_Export_{datetime.now():%Y%m%d_%H%M%S}.zip";
            resp=send_file(zip_buf, as_attachment=True, download_name=zip_fname, mimetype='application/zip')
        resp.headers.update({"Cache-Control":"no-cache","Pragma":"no-cache","Expires":"0"})
        flash(f'Exporting {len(file_data)} file(s)... Download starting.', 'success')
        return resp
    except ValueError as ve: flash(f"Input Error: {ve}", "error"); print(f"Export ValueError: {ve}"); return redirect(url_for('index'))
    except Exception as e: flash(f"Export failed: {e}", "error"); print(f"Export Error: {traceback.format_exc()}"); return redirect(url_for('index'))


# --- Ensure session directory exists on startup ---
def ensure_session_dir():
    session_dir = app.config.get('SESSION_FILE_DIR', '.flask_session')
    if not os.path.exists(session_dir):
        try: os.makedirs(session_dir); print(f"[APP SETUP] Created session directory: {session_dir}")
        except OSError as e: print(f"[APP SETUP] Error creating session dir '{session_dir}': {e}. Please create it manually.")

# --- Run ---
if __name__ == '__main__':
    ensure_session_dir() # Call function to check/create dir
    print("\n--- Enhance! Modular Exporter (Local - Debugging) ---");
    print("Access: http://127.0.0.1:5000"); print("--- CTRL+C to stop ---")
    app.run(debug=True, port=5000)