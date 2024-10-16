import asyncio
import websockets
import base64
import numpy as np
import whisper
import torch

# Load Whisper model
model = whisper.load_model("medium")

async def process_audio(websocket, path):
    print("Client connected")
    buffer = b""
    
    try:
        async for message in websocket:
            if message.startswith("AUDIO:"):
                # Decode base64 audio data
                audio_data = base64.b64decode(message[6:])
                buffer += audio_data

                # Process audio when buffer reaches a certain size (e.g., 2 seconds of audio)
                if len(buffer) >= 32000:  # 16000 samples/sec * 2 seconds * 2 bytes/sample
                    audio_array = np.frombuffer(buffer, dtype=np.int16).astype(np.float32) / 32768.0
                    
                    # Transcribe audio
                    result = model.transcribe(audio_array, language="en")
                    transcript = result["text"].strip()

                    if transcript:
                        print(f"Transcript: {transcript}")
                        await websocket.send(f"TRANSCRIPT:{transcript}")

                    # Clear buffer
                    buffer = b""

    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")

async def main():
    server = await websockets.serve(process_audio, "0.0.0.0", 8760)
    print("WebSocket server started on ws://0.0.0.0:8760")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
