import asyncio
import websockets
import json
import os

async def connect_to_chatbot():
    uri = "ws://127.0.0.1:8001/ws"
    print("Connecting to chatbot server...")
    
    try:
    async with websockets.connect(uri) as websocket:
            print("Connected! Type your messages (or 'quit' to exit)")
            print("Available commands will be loaded from commands.json")
            
            # Load and display available commands
            commands_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "commands.json")
            if os.path.exists(commands_file):
                with open(commands_file, "r") as f:
                    commands = json.load(f)
                    print("\nAvailable commands:")
                    for cmd in commands:
                        print(f"- {cmd['command']}")
                    print()
            
        while True:
            message = input("You: ")
                if message.lower() == 'quit':
                break
                    
            await websocket.send(message)
            response = await websocket.recv()
            print(f"Bot: {response}")
                
    except ConnectionRefusedError:
        print("Error: Could not connect to the chatbot server. Make sure it's running!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(connect_to_chatbot())
