# File: modules/chatbot_plus/app.py

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import json
import os

app = FastAPI()
COMMANDS_PATH = os.path.join(os.path.dirname(__file__), "commands.json")

def load_commands():
    if not os.path.exists(COMMANDS_PATH):
        return []
    with open(COMMANDS_PATH, "r") as f:
        return json.load(f)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    commands = load_commands()
    while True:
        try:
            data = await websocket.receive_text()
            normalized = data.strip().lower()
            response = next((cmd["response"] for cmd in commands if cmd["command"].lower() == normalized), None)

            if normalized == "!help":
                cmd_list = sorted(set(cmd["command"] for cmd in commands))
                await websocket.send_text("Available commands:\n" + "\n".join(f"- {cmd}" for cmd in cmd_list))
            elif response:
                await websocket.send_text(response)
            else:
                await websocket.send_text(f"Unknown command: {data}")
        except WebSocketDisconnect:
            break
