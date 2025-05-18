#!/bin/bash

# Script to install and run the Scryfall Image URL Fetcher web app on macOS, optimized for VS Code

set -e  # Exit on error

echo "🚀 Starting Scryfall Web App installation..."

# 1. Check and install Homebrew
if ! command -v brew &> /dev/null; then
    echo "📦 Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    # Add Homebrew to PATH
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc
    eval "$(/opt/homebrew/bin/brew shellenv)"
else
    echo "✅ Homebrew already installed"
fi

# 2. Install Python 3.10
echo "🐍 Installing Python 3.10..."
brew install python@3.10 || true  # Ignore if already installed

# 3. Install VS Code CLI (if not installed)
if ! command -v code &> /dev/null; then
    echo "📝 Installing VS Code CLI..."
    brew install --cask visual-studio-code || true
fi

# 4. Create project directory
PROJECT_DIR="$HOME/scryfall_web_app"
echo "📁 Creating project directory at $PROJECT_DIR..."
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# 5. Install Python dependencies
echo "📦 Installing Python dependencies..."
/opt/homebrew/bin/pip3.10 install flask pandas aiohttp || true  # Ignore if already installed

# 6. Create file structure
echo "🗂 Setting up file structure..."
mkdir -p templates static/css data/uploads data/output .vscode

# 7. Write app.py
cat > app.py << 'EOF'
import os
import pandas as pd
import aiohttp
import asyncio
import sqlite3
from flask import Flask, request, render_template, send_file
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

app = Flask(__name__)
UPLOAD_FOLDER = "data/uploads"
OUTPUT_FOLDER = "data/output"
DB_FILE = "scryfall.db"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100MB max file size

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        license_key TEXT UNIQUE,
        tier TEXT,
        cards_processed_today INTEGER,
        last_reset DATE
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS processing_history (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        filename TEXT,
        cards_processed INTEGER,
        errors INTEGER,
        timestamp DATETIME
    )""")
    conn.commit()
    conn.close()

# Scryfall API call
async def fetch_image_url(session, scryfall_id, language):
    if pd.isna(scryfall_id):
        return None, "Missing Scryfall ID"
    language = language.lower().strip() if language else "en"
    base_url = "https://api.scryfall.com/cards"
    try:
        async with session.get(f"{base_url}/{scryfall_id}/{language}") as response:
            if response.status == 200:
                data = await response.json()
                return data.get("image_uris", {}).get("normal"), "Success"
        async with session.get(f"{base_url}/{scryfall_id}") as response:
            if response.status == 200:
                data = await response.json()
                return data.get("image_uris", {}).get("normal"), "Success (Fallback)"
    except Exception as e:
        return None, str(e)
    finally:
        await asyncio.sleep(0.1)  # Scryfall rate limit

# Process CSV file
async def process_csv(file_path, license_key):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Check subscription limits
    c.execute("SELECT tier, cards_processed_today, last_reset FROM users WHERE license_key = ?", (license_key,))
    user = c.fetchone()
    if not user:
        return None, "Invalid license key"
    
    tier, cards_processed_today, last_reset = user
    today = datetime.now().date()
    if last_reset != str(today):
        cards_processed_today = 0
        c.execute("UPDATE users SET cards_processed_today = 0, last_reset = ? WHERE license_key = ?", (today, license_key))
    
    limits = {"free": 50, "basic": 1000, "pro": 10000, "enterprise": 1000000}
    if cards_processed_today >= limits.get(tier, 50):
        return None, f"Daily limit reached for {tier} tier"
    
    # Read CSV in chunks
    chunk_size = 10000
    output_file = os.path.join(OUTPUT_FOLDER, f"processed_{secure_filename(os.path.basename(file_path))}")
    errors = 0
    
    async with aiohttp.ClientSession() as session:
        for chunk in pd.read_csv(file_path, chunksize=chunk_size):
            chunk["scryfall image url"] = None
            chunk["status"] = None
            tasks = [fetch_image_url(session, row["Scryfall ID"], row.get("Language", "en")) 
                     for _, row in chunk.iterrows()]
            results = await asyncio.gather(*tasks)
            
            for i, (url, status) in enumerate(results):
                chunk.iloc[i, chunk.columns.get_loc("scryfall image url")] = url
                chunk.iloc[i, chunk.columns.get_loc("status")] = status
                if status != "Success" and status != "Success (Fallback)":
                    errors += 1
            
            # Append to output file
            chunk.to_csv(output_file, mode="a", index=False, header=not os.path.exists(output_file))
            
            # Update user limits
            cards_processed_today += len(chunk)
            if cards_processed_today > limits.get(tier, 50):
                break
            c.execute("UPDATE users SET cards_processed_today = ? WHERE license_key = ?", 
                      (cards_processed_today, license_key))
    
    # Log processing history
    c.execute("INSERT INTO processing_history (user_id, filename, cards_processed, errors, timestamp) VALUES (?, ?, ?, ?, ?)",
              (1, os.path.basename(file_path), cards_processed_today, errors, datetime.now()))
    conn.commit()
    conn.close()
    
    return output_file, None

@app.route("/", methods=["GET", "POST"])
def index():
    error = None
    output_file = None
    if request.method == "POST":
        license_key = request.form.get("license_key")
        if "file" not in request.files:
            error = "No file uploaded"
        else:
            file = request.files["file"]
            if file.filename == "":
                error = "No file selected"
            elif file and file.filename.endswith(".csv"):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(file_path)
                output_file, error = asyncio.run(process_csv(file_path, license_key))
    
    return render_template("index.html", error=error, output_file=output_file)

@app.route("/download/<filename>")
def download(filename):
    return send_file(os.path.join(OUTPUT_FOLDER, filename), as_attachment=True)

if __name__ == "__main__":
    init_db()
    # Temporary: Add a test user
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT OR IGNORE INTO users (license_key, tier, cards_processed_today, last_reset) VALUES (?, ?, 0, ?)",
                 ("test-key-123", "free", str(datetime.now().date())))
    conn.commit()
    conn.close()
    app.run(debug=True, host="0.0.0.0", port=5000)
EOF

# 8. Write templates/index.html
cat > templates/index.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Scryfall Image URL Fetcher</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <div class="container mt-5">
        <h1>Scryfall Image URL Fetcher</h1>
        <p>Upload a CSV file with <code>Scryfall ID</code> and optional <code>Language</code> columns.</p>
        
        <form method="post" enctype="multipart/form-data">
            <div class="mb-3">
                <label for="license_key" class="form-label">License Key</label>
                <input type="text" class="form-control" id="license_key" name="license_key" required>
            </div>
            <div class="mb-3">
                <label for="file" class="form-label">Select CSV File</label>
                <input type="file" class="form-control" id="file" name="file" accept=".csv" required>
            </div>
            <button type="submit" class="btn btn-primary">Upload and Process</button>
        </form>

        {% if error %}
            <div class="alert alert-danger mt-3">{{ error }}</div>
        {% endif %}
        {% if output_file %}
            <div class="alert alert-success mt-3">
                Processing complete! <a href="/download/{{ output_file | basename }}" class="btn btn-success">Download</a>
            </div>
        {% endif %}
    </div>
</body>
</html>
EOF

# 9. Write static/css/style.css
cat > static/css/style.css << 'EOF'
body {
    background-color: #f8f9fa;
}
.container {
    max-width: 800px;
}
EOF

# 10. Write .vscode/settings.json
cat > .vscode/settings.json << 'EOF'
{
    "python.pythonPath": "/opt/homebrew/bin/python3.10",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true
}
EOF

# 11. Write .vscode/launch.json for debugging
cat > .vscode/launch.json << 'EOF'
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Run Flask App",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/app.py",
            "args": [],
            "env": {
                "FLASK_APP": "app.py",
                "FLASK_ENV": "development"
            },
            "jinja": true
        }
    ]
}
EOF

# 12. Create sample CSV
cat > data/uploads/sample.csv << 'EOF'
Scryfall ID,Language
a3fb7228-e76b-4e96-a40e-20b5fed75685,ja
c1d109bc-ffd8-428f-8d7d-3f8d7e64802d,en
EOF

# 13. Open project in VS Code
echo "📝 Opening project in VS Code..."
code .

# 14. Instructions for user
echo "✅ Installation complete!"
echo "📂 Project opened in VS Code at $PROJECT_DIR"
echo "📝 To run the app:"
echo "   1. In VS Code, open the terminal (View > Terminal)"
echo "   2. Run: /opt/homebrew/bin/python3.10 app.py"
echo "   3. Or use the 'Run Flask App' debug configuration (Run > Start Debugging)"
echo "🌐 Access the app at http://localhost:5000"
echo "🔑 Use license key: test-key-123 (Free Tier, 50 cards/day)"
echo "📄 Test with sample.csv in data/uploads"
echo "🛑 To stop the server, press Ctrl+C in the terminal or stop the debugger"