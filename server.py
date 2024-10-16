import asyncio
import websockets
import base64
import os
import cv2
import numpy as np
import logging
import wave

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

frame_count = 0
audio_count = 0

# Audio settings (matching client settings)
CHANNELS = 1
RATE = 44100
CHUNK = 1024
FORMAT = 'int16'

async def receive_data(websocket, path):
    global frame_count, audio_count
    
    # Create directories for frames and audio
    os.makedirs('received_frames', exist_ok=True)
    os.makedirs('received_audio', exist_ok=True)
    
    # Open a wave file for audio
    wf = wave.open(f'received_audio/audio_{audio_count}.wav', 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(2)  # 2 bytes for 'int16'
    wf.setframerate(RATE)
    
    try:
        while True:
            message = await websocket.recv()
            
            if message.startswith("VIDEO:"):
                # Process video frame
                img_data = base64.b64decode(message[6:])
                nparr = np.frombuffer(img_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if frame is not None:
                    frame_count += 1
                    filename = f'received_frames/frame_{frame_count:04d}.jpg'
                    cv2.imwrite(filename, frame)
                    logging.info(f"Frame {frame_count} received and saved as '{filename}'")
                else:
                    logging.error("Failed to decode image")
            
            elif message.startswith("AUDIO:"):
                # Process audio data
                audio_data = base64.b64decode(message[6:])
                audio_array = np.frombuffer(audio_data, dtype=np.int16)
                wf.writeframes(audio_array.tobytes())
                logging.info(f"Audio chunk received and saved")
            
            else:
                logging.warning(f"Received unknown data type")
            
            await websocket.send("ACK")  # Send acknowledgment
    
    except websockets.exceptions.ConnectionClosedOK:
        logging.info("Connection closed normally")
    except Exception as e:
        logging.error(f"An error occurred: {e}", exc_info=True)
    finally:
        wf.close()
        audio_count += 1
        logging.info(f"Audio file closed: received_audio/audio_{audio_count}.wav")

async def main():
    server = await websockets.serve(receive_data, "0.0.0.0", 8765, max_size=None)
    logging.info("Server is listening on ws://0.0.0.0:8765")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())