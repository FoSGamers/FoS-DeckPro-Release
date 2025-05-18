import asyncio
import websockets

async def chat():
    uri = "ws://127.0.0.1:8001/ws"
    async with websockets.connect(uri) as websocket:
        print("\nConnected to chatbot! Type '!help' or 'exit' to quit.")
        while True:
            message = input("You: ")
            if message.lower() == "exit":
                break
            await websocket.send(message)
            response = await websocket.recv()
            print(f"Bot: {response}")

if __name__ == "__main__":
    asyncio.run(chat())
