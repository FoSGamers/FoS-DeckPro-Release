# File: modules/chatbot_plus/main.py

import json
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn

app = FastAPI()
COMMANDS_FILE = "modules/chatbot_plus/commands.json"

def load_commands():
    if not os.path.exists(COMMANDS_FILE):
        return []
    with open(COMMANDS_FILE, "r") as f:
        return json.load(f)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            commands = load_commands()
            response = None
            for cmd in commands:
                if data.lower().strip() == cmd["command"].lower():
                    response = cmd["response"]
                    break
            if response:
                await websocket.send_text(response)
            else:
                await websocket.send_text(f"Unknown command: {data}")
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Launching FastAPI server on http://127.0.0.1:8001 ...")
    uvicorn.run("modules.chatbot_plus.main:app", host="127.0.0.1", port=8001, reload=False)
