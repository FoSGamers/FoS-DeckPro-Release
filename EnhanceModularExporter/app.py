# app.py (Main Flask Application - Definitive Version with Fixes & Debugging)
import os
import json
import traceback
import io
import time # Keep time import if needed anywhere
import uuid
import threading
# Need Queue and queue for checking Empty exception
from queue import Queue, Empty as QueueEmpty
from datetime import datetime, timedelta
from flask import ( Flask, render_template, request, jsonify, session,
                    send_file, flash, redirect, url_for, Response )
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
# IMPORTANT: CHANGE THIS IN A REAL DEPLOYMENT! Load from env var is best practice.
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'local-dev-secret-must-be-changed-final-final-v2')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session' # Ensure this directory exists and is writable
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=4) # Adjust as needed
app.config["SSE_REDIS_URL"] = None # Disable Redis requirement for simple local test
# Optional security settings (uncomment if/when using HTTPS)
# app.config['SESSION_COOKIE_SECURE'] = True
# app.config['SESSION_COOKIE_HTTPONLY'] = True
# app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
print(f"[APP DEBUG] Session type: {app.config['SESSION_TYPE']}")
print(f"[APP DEBUG] Session dir: {os.path.abspath(app.config['SESSION_FILE_DIR'])}")

# Initialize the session extension AFTER setting config
server_session = Session()
server_session.init_app(app)
# Register the sse blueprint AFTER Session init
# Import sse here to avoid circular dependency if it needed app context
from flask_sse import sse
app.register_blueprint(sse, url_prefix='/stream')
print("[APP DEBUG] Flask-Session and Flask-SSE initialized.")
# --- End Session Configuration ---

# --- Global Storage (Local Dev Only - Not suitable for production) ---
export_jobs = {} # Stores job status and result {job_id: {"status": "...", "result_...": ...}}
export_queues = {} # Stores queues for SSE {job_id: Queue()}
jobs_lock = threading.Lock() # Protect access to shared job dictionaries

# --- Session Data Management ---
def get_session_chats():
    # print("[APP DEBUG] Attempting get_session_chats()") # Verbose
    data = session.get('chat_data', None) # Default to None to distinguish from empty list
    if data is None:
        # print("[APP DEBUG] 'chat_data' key NOT FOUND in session.")
        return []
    elif not isinstance(data, list):
        print(f"[APP WARN] Session 'chat_data' is TYPE {type(data)}, not list! Clearing session.")
        session.clear() # Clear corrupted session
        return []
    else:
        # print(f"[APP DEBUG] Retrieved 'chat_data'. Length: {len(data)}.")
        return data

def get_session_chat_dt_map():
     raw_map = session.get('chat_datetime_map_iso', {}); dt_map = {}
     # print(f"[APP DEBUG] Retrieved 'chat_datetime_map_iso'. Items: {len(raw_map)}") # Can be verbose
     for k, v_iso in raw_map.items():
         try: dt_map[int(k)] = datetime.fromisoformat(v_iso) if v_iso else None
         except: dt_map[int(k)] = None # Handle potential errors during conversion
     return dt_map

def set_session_chats(data_to_store):
    print(f"[APP DEBUG] set_session_chats() called. Len(data)={len(data_to_store)}")
    session.clear(); session['chat_data'] = data_to_store; dt_map_iso = {}
    for i, chat in enumerate(data_to_store):
        ts = chat.get("update_time", chat.get("create_time")); _, dt = format_timestamp(ts)
        dt_map_iso[str(i)] = dt.isoformat() if dt else None
    session['chat_datetime_map_iso'] = dt_map_iso; session.modified = True # Explicitly mark modified
    print(f"[APP DEBUG] set_session_chats() finished. Session keys: {list(session.keys())}")


# --- Background Export Worker ---
# (This function remains the same as in the previous response with SSE)
def run_export_background(job_id, all_chats_data, selected_indices, formats, options):
    """Function executed in a background thread."""
    print(f"[WORKER {job_id}] Starting background export...")
    progress_queue = export_queues.get(job_id)
    if not progress_queue: print(f"[WORKER {job_id}] ERROR: Queue not found!"); return

    def update_progress(message, type="progress", percent=None):
        try:
            payload = {"type": type, "message": message}
            if percent is not None: payload["percent"] = max(0, min(100, int(percent)))
            progress_queue.put(json.dumps(payload))
        except Exception as q_err: print(f"[WORKER {job_id}] ERROR queuing message: {q_err}")

    try:
        update_progress("Starting export process...", percent=0)
        file_data_list = generate_export_files(all_chats_data, selected_indices, formats, options, progress_queue) # Pass queue

        if not file_data_list: raise ValueError("Export service returned no files.")

        is_single_file = len(file_data_list) == 1; result_filename = None; mime_type = 'application/octet-stream'
        if is_single_file:
            result_filename = os.path.basename(file_data_list[0][0]); zip_buffer = io.BytesIO(file_data_list[0][1])
            update_progress(f"Prepared single file: {result_filename}", percent=95)
        else:
            result_filename = f"ChatGPT_Export_{datetime.now():%Y%m%d_%H%M%S}.zip"; update_progress(f"Creating ZIP: {result_filename}...", percent=95)
            zip_buffer = create_zip_bundle(file_data_list);
            if not zip_buffer: raise Exception("ZIP bundle creation failed.")
            mime_type = 'application/zip'; update_progress("ZIP archive created.", percent=98)

        result_data_bytes = zip_buffer.getvalue()
        with jobs_lock: export_jobs[job_id] = {"status": "complete", "result_filename": result_filename, "result_data": result_data_bytes, "mime_type": mime_type }
        update_progress(f"Export complete! Ready for download.", type="complete", percent=100); print(f"[WORKER {job_id}] Export successful.")
    except Exception as e:
        error_message = f"Export failed: {e}"; print(f"[WORKER {job_id}] ERROR: {error_message}"); traceback.print_exc();
        update_progress(error_message, type="error", percent=100)
        with jobs_lock: export_jobs[job_id] = {"status": "error", "message": error_message}
    finally:
        update_progress("Background task finished.", type="final");
        with jobs_lock: export_queues.pop(job_id, None); print(f"[WORKER {job_id}] Background thread finished.")


# --- Routes ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        print("[APP DEBUG] POST / received")
        if 'file' not in request.files or not request.files['file'].filename: flash('No file selected.', 'error'); return redirect(request.url)
        file = request.files['file']
        if file and file.filename.lower().endswith('.json'):
            fname = secure_filename(file.filename) # Secure filename early
            try:
                raw = file.read().decode('utf-8'); data = json.loads(raw);
                if not isinstance(data, list): raise ValueError("JSON root not list.");
                # *** CORRECTED SYNTAX: Set session and flash AFTER validation ***
                set_session_chats(data);
                flash(f'Loaded "{fname}" ({len(data)} convos).', 'success')
            except Exception as e: flash(f'Error processing file "{fname}": {e}', 'error'); print(f"Upload Error: {traceback.format_exc()}")
            return redirect(url_for('index')) # Redirect to GET after POST
        else: flash('Invalid file type (Requires .json).', 'error'); return redirect(request.url)

    # --- GET Request Logic ---
    print("[APP DEBUG] GET / received")
    all_chats_data = get_session_chats() # Retrieve data

    chats_for_display = []; has_data_flag = False
    # *** CORRECTED: Define filter vars BEFORE the 'if all_chats_data' block ***
    search_term=request.args.get('search','').lower(); date_on=request.args.get('date_filter')=='on'; start_str=request.args.get('start_date',''); end_str=request.args.get('end_date','')
    start_dt, end_dt = None, None # Initialize date objects

    if all_chats_data:
        print(f"[APP DEBUG] GET / - Data found (len {len(all_chats_data)}). Processing...")
        try:
            # Parse dates only if date_on is true *initially*
            if date_on:
                try:
                    start_dt=datetime.strptime(start_str,'%Y-%m-%d').date()
                    end_dt=(datetime.strptime(end_str,'%Y-%m-%d')+timedelta(days=1)).date()
                except ValueError:
                    date_on = False # Disable if format bad
                    if start_str or end_str: flash('Invalid date format ignored.', 'warning')

            dt_map = get_session_chat_dt_map()
            for i, chat in enumerate(all_chats_data):
                title=get_display_title(chat,i); # Use helper
                if search_term and search_term not in title.lower(): continue
                # Check date filter *after* potential disabling
                if date_on:
                    chat_dt=dt_map.get(i);
                    # Ensure chat_dt is a valid datetime object before comparing dates
                    if not chat_dt or not isinstance(chat_dt, datetime) or not (start_dt <= chat_dt.date() < end_dt):
                        continue
                chats_for_display.append({'original_index': i, 'title': title})
            has_data_flag = True # Set flag only if processing succeeds
            print(f"[APP DEBUG] GET / - Processing finished. Chats displayed: {len(chats_for_display)}")
        except Exception as e_filter: print(f"ERROR filtering list: {e_filter}"); traceback.print_exc(); flash("Error filtering chats.", "error"); has_data_flag = False; chats_for_display = []
    else: print("[APP DEBUG] GET / - No data in session.")

    # Set default filter values for rendering the form
    def_start=(datetime.now()-timedelta(days=30)).strftime('%Y-%m-%d'); def_end=datetime.now().strftime('%Y-%m-%d')
    filter_vals = {'search':search_term, 'date_filter':date_on, 'start_date':start_str or def_start, 'end_date':end_str or def_end}
    return render_template('index.html', chats=chats_for_display, filter_values=filter_vals, has_data=has_data_flag)


@app.route('/preview')
def preview():
    # (Preview logic remains unchanged)
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

# Route to START the export (now returns Job ID)
@app.route('/start-export', methods=['POST'])
def start_export():
    """Starts the export process in a background thread."""
    print("[APP ROUTE] Received POST /start-export")
    chats=get_session_chats();
    if not chats: return jsonify({"error": "No chat data loaded."}), 400
    try:
        payload = request.get_json();
        if not payload: return jsonify({"error": "Missing JSON payload."}), 400
        indices=payload.get('selected_indices', []); formats=payload.get('formats', {}); options=payload.get('options', {})
        if not indices: return jsonify({"error": "No chats selected."}), 400
        if not formats or not any(formats.values()): return jsonify({"error": "No formats selected."}), 400

        job_id = str(uuid.uuid4()); print(f"[APP ROUTE] Starting job ID: {job_id}")
        progress_queue = Queue();
        with jobs_lock: export_queues[job_id] = progress_queue; export_jobs[job_id] = {"status": "queued"}
        export_thread = threading.Thread(target=run_export_background,args=(job_id, chats, indices, formats, options),daemon=True); export_thread.start()
        print(f"[APP ROUTE] Background thread started for job {job_id}")
        return jsonify({"status": "Export started", "job_id": job_id}), 202
    except Exception as e: print(f"[APP ROUTE] Error starting export: {e}"); traceback.print_exc(); return jsonify({"error": f"Failed start: {e}"}), 500

# Route for SSE Progress Stream
@app.route('/export-progress/<job_id>')
def export_progress(job_id):
    """Streams progress updates using Server-Sent Events."""
    print(f"[SSE ROUTE] Client connected for job ID: {job_id}")
    def generate():
        q = export_queues.get(job_id)
        if not q: print(f"[SSE ROUTE] Job {job_id} queue missing."); yield f"data: {json.dumps({'type':'error','message':'Job not found.'})}\n\n"; return
        last_keepalive = time.time()
        while True:
            try:
                message_json = q.get(timeout=10); yield f"data: {message_json}\n\n"; message_data = json.loads(message_json)
                if message_data.get("type") in ["complete", "error", "final"]: print(f"[SSE {job_id}] Final msg. Closing."); break
                last_keepalive = time.time()
            except QueueEmpty: # Correct exception import needed: from queue import Empty as QueueEmpty
                with jobs_lock: job_status = export_jobs.get(job_id, {}).get("status")
                if job_status not in ["running", "queued", None]: print(f"[SSE {job_id}] Job ended ({job_status}). Closing."); break
                elif time.time() - last_keepalive > 25: yield ": keepalive\n\n"; last_keepalive = time.time()
            except Exception as e: print(f"[SSE {job_id}] Error: {e}"); traceback.print_exc(); break
        print(f"[SSE {job_id}] Generator finished.")
    return Response(generate(), mimetype='text/event-stream')

# Route to Download the Result
@app.route('/download/<job_id>')
def download_result(job_id):
    """Serves the generated export file for download."""
    print(f"[DOWNLOAD] Request for job: {job_id}")
    job_info = None # Initialize
    with jobs_lock: job_info = export_jobs.get(job_id) # Get info safely

    if not job_info: flash("Job not found or expired.", "error"); return redirect(url_for('index'))
    if job_info["status"] == "complete":
        result_data = job_info.get("result_data")
        if not result_data: flash("Result data missing.", "error"); return redirect(url_for('index'))
        print(f"[DOWNLOAD] Serving file: {job_info['result_filename']}")
        buffer = io.BytesIO(result_data);
        response = send_file(buffer, as_attachment=True, download_name=job_info["result_filename"], mimetype=job_info["mime_type"])
        response.headers.update({"Cache-Control":"no-cache","Pragma":"no-cache","Expires":"0"})
        # Consider removing job data after download starts to save memory
        # with jobs_lock: export_jobs.pop(job_id, None)
        return response
    elif job_info["status"] == "error":
        flash(f"Job {job_id} failed: {job_info.get('message', 'Unknown')}", "error");
        with jobs_lock: export_jobs.pop(job_id, None) # Clean up failed job
        return redirect(url_for('index'))
    else: flash(f"Job {job_id} status: {job_info['status']}.", "warning"); return redirect(url_for('index'))

# --- Ensure session directory exists ---
def ensure_session_dir():
    sdir = app.config.get('SESSION_FILE_DIR','.flask_session');
    if not os.path.exists(sdir):
        try: os.makedirs(sdir); print(f"[SETUP] Created session dir: {sdir}")
        except OSError as e: print(f"[ERROR] Cannot create session dir '{sdir}': {e}")
if __name__ == '__main__':
    ensure_session_dir();
    print("\n--- Enhance! Modular Exporter (Local - SSE FINAL FIX 3) ---");
    print("Access: http://127.0.0.1:5000"); print("--- CTRL+C to stop ---");
    # Use threaded=True for development server to handle background task and SSE
    app.run(debug=True, port=5000, threaded=True)