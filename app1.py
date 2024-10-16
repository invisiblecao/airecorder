import os
import warnings
import asyncio
import websockets
import json
import base64
import cv2
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from collections import defaultdict
from deepface import DeepFace  # For face recognition
from internvl2_processor import process_frame_with_internvl  # Import the new InternVL2 processing file

warnings.filterwarnings("ignore")
os.environ['CUDA_LAUNCH_BLOCKING'] = '1'

# FastAPI setup
app = FastAPI()

# Initialize DeepFace for face recognition
face_processor = DeepFace

person_data = defaultdict(lambda: {"emotion": "", "recognition": ""})
templates = Jinja2Templates(directory="templates")


# Process video frame using InternVL2 and DeepFace
async def process_video_frame(frame_data):
    try:
        # Use the function from internvl2_processor.py to process the frame with InternVL2
        description = process_frame_with_internvl(frame_data)
        
        # Perform face recognition using DeepFace
        try:
            # Decode the base64 frame to a numpy array for DeepFace
            header, encoded = frame_data.split(',', 1)
            decoded_frame = base64.b64decode(encoded)
            np_frame = np.frombuffer(decoded_frame, dtype=np.uint8)
            frame = cv2.imdecode(np_frame, cv2.IMREAD_COLOR)
            
            # Analyze the frame using DeepFace
            face_recognition_result = face_processor.analyze(frame, actions=['recognition'])
        except Exception as e:
            face_recognition_result = f"Error recognizing face: {e}"

        return description, face_recognition_result

    except Exception as e:
        print(f"Error processing video frame: {e}")
        return None, None


# WebSocket handler
async def handle_client(websocket, path):
    print("Client connected")
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                if data['type'] == 'video':
                    description, recognition = await process_video_frame(data['data'])
                    if description:
                        response = {
                            "type": "analysis",
                            "description": description,
                            "recognition": recognition
                        }
                        await websocket.send(json.dumps(response))
                else:
                    print(f"Unknown data type: {data['type']}")
            except json.JSONDecodeError as e:
                print(f"Failed to decode JSON: {e}")
    except websockets.exceptions.ConnectionClosed as e:
        print(f"Client disconnected: {e}")
    except Exception as e:
        print(f"Error in handle_client: {e}")


# Web endpoint for FastAPI
@app.get('/')
def index(request: Request):
    return templates.TemplateResponse('index.html', {"request": request})


@app.post('/process_image')
async def handle_image_request(request: Request):
    data = await request.json()
    image_data = base64.b64decode(data['image'])
    image = Image.open(BytesIO(image_data)).convert('RGB')
    result = face_processor.analyze(np.array(image), actions=['recognition'])
    return JSONResponse(content={"result": result})


# WebSocket server
async def main():
    websocket_server = await websockets.serve(handle_client, "0.0.0.0", 50101)
    print("WebSocket server is listening on port 50101")
    await websocket_server.wait_closed()


if __name__ == "__main__":
    import uvicorn

    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Error: {e}")