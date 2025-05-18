#!/usr/bin/env python3
import os, shutil
from pathlib import Path
from datetime import datetime

ROOT = Path.cwd()
BACKUP = ROOT / f"backup_fosbot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

FILES = {
    # Root files
    ".env": """COMMAND_PREFIX=!
WS_HOST=localhost
WS_PORT=8000
LOG_LEVEL=DEBUG
""",

    "requirements.txt": """fastapi
uvicorn[standard]
python-dotenv
""",

    "README.md": """# FoSBot
Run this app locally with:

1. source venv/bin/activate
2. pip install -r requirements.txt
3. uvicorn app.main:app --reload
""",

    # App files
    "app/__init__.py": "",

    "app/main.py": '''from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

app = FastAPI()
app.mount("/", StaticFiles(directory="static", html=True), name="static")

@app.get("/api/ping")
async def ping():
    return {"message": "pong"}

@app.get("/whatnot_extension.zip")
async def get_extension():
    zip_path = Path("whatnot_extension.zip")
    if zip_path.exists():
        return FileResponse(zip_path, media_type="application/zip", filename="whatnot_extension.zip")
    return {"error": "ZIP not found"}
''',
    # Static UI
    "static/index.html": """<!DOCTYPE html>
<html>
<head><title>FoSBot Dashboard</title></head>
<body>
  <h1>FoSBot Dashboard</h1>
  <input id='chat-input' placeholder='Type a message...'>
  <div id='chat-output'></div>
  <script src='main.js'></script>
</body>
</html>
""",

    "static/main.js": """const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (e) => {
  const out = document.getElementById('chat-output');
  out.innerHTML += `<p>${e.data}</p>`;
};
document.getElementById('chat-input').addEventListener('keypress', (e) => {
  if (e.key === 'Enter') {
    ws.send(e.target.value);
    e.target.value = '';
  }
});
""",

    # WebSocket stub (optional)
    "app/routers/__init__.py": "",

    "app/routers/websocket_router.py": '''from fastapi import APIRouter, WebSocket

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
        except:
            break
'''
}
