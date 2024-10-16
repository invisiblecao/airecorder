import asyncio
import websockets
import base64
import os

frame_count = 0

async def receive_frame(websocket, path):
    global frame_count
    try:
        while True:
            # Receive one frame
            message = await websocket.recv()
            
            # Decode the base64 string
            img_data = base64.b64decode(message)
            
            # Create a directory to store frames if it doesn't exist
            os.makedirs('received_frames', exist_ok=True)
            
            # Save the image with a sequential name
            frame_count += 1
            filename = f'received_frames/frame_{frame_count:04d}.jpg'
            with open(filename, 'wb') as f:
                f.write(img_data)
            
            print(f"Frame received and saved as '{filename}'")
            
    except websockets.exceptions.ConnectionClosedOK:
        print("Connection closed")

start_server = websockets.serve(receive_frame, "localhost", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
print("Server is listening on ws://localhost:8765")
asyncio.get_event_loop().run_forever()
