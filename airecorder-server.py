
CHATBOT_WS_PORT     = 50004

AIRECORDER_WS_PORT  = 50101
# AIRECORDER_WS_PORT  = 50103  # for airecorder2

ws_chatbot = None

import asyncio
import websockets
import json
import base64
import numpy as np
import torch
import os
import uuid
import scipy.io.wavfile
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, WhisperTokenizer, pipeline
from scipy.signal import resample
import warnings
import traceback

# Suppress warnings (optional)
warnings.filterwarnings("ignore")

# Device selection
device = "cuda" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16
print(f"Using device: {device}")

# Load Whisper model
model_id = "openai/whisper-large-v3-turbo"

model = AutoModelForSpeechSeq2Seq.from_pretrained(
    model_id,
    torch_dtype=torch_dtype,
    low_cpu_mem_usage=True,
    use_safetensors=True,
).to(device)

processor = AutoProcessor.from_pretrained(model_id)

# Initialize tokenizer with language="en"
tokenizer = WhisperTokenizer.from_pretrained(model_id, language="en")

# Initialize pipeline with max_new_tokens=25
pipe = pipeline(
    "automatic-speech-recognition",
    model=model,
    tokenizer=tokenizer,
    feature_extractor=processor.feature_extractor,
    torch_dtype=torch_dtype,
    device=device,
    max_new_tokens=25,
)

# Global variables
client_sample_rate = 44100  # The sample rate of the incoming audio data
target_sample_rate = 16000  # The sample rate expected by the model


async def process_audio_data(websocket, audio_data, user_state):
    try:
        # Decode the base64 audio data
        decoded_audio = base64.b64decode(audio_data)
        audio_np = np.frombuffer(decoded_audio, dtype=np.float32)

        # Accumulate audio data
        user_state['audio_buffer'].extend(audio_np)

        # If accumulated audio data is sufficient, process it
        if len(user_state['audio_buffer']) >= client_sample_rate * user_state['buffer_duration']:
            audio_segment = np.array(user_state['audio_buffer'], dtype=np.float32)
            user_state['audio_buffer'] = []  # Reset buffer

            # Resample audio to 16,000 Hz
            num_samples = int(len(audio_segment) * target_sample_rate / client_sample_rate)
            audio_resampled = resample(audio_segment, num_samples).astype(np.float32)

            # Write audio data to a temporary WAV file
            filename = f"{uuid.uuid4().hex}.wav"
            scipy.io.wavfile.write(filename, target_sample_rate, audio_resampled)

            # Transcribe the audio file
            result = pipe(
                filename,
                generate_kwargs={"language": "english"}
            )

            # Remove the temporary file
            os.remove(filename)

            transcription = result["text"].strip()

            if transcription:
                print(f"Sending transcription: {transcription}")
                await websocket.send(json.dumps({"type": "transcription", "data": transcription}))
            else:
                print("No transcription available.")

    except Exception as e:
        print(f"Error processing audio data: {e}")
        traceback.print_exc()

###
import websockets
from websockets.exceptions import ConnectionClosedError

###

async def process_video_data(websocket, video_data):

    # Process video data here
    # try:
    print(f"Received video frame: {len(video_data)} bytes")
                
    # Send the decoded data to the ChatBot server
    global ws_chatbot
    await ws_chatbot.send(json.dumps({
        'request_type': 'infer-image',
        'engine':       'internvl',
        'model':        'internvl:8b',
        'prompt':       '''Briefly describe the emotion and body gesture of the people in the image in the following format (ID=from left to right, the first person use A, the second one use B and so on):
            (ID)'s emotion: (emotion) 
            (ID)'s gesture: (gesture)
        ''',
        'image':        video_data,
    }))
    
    # print("Data sent to WebSocket service.")
    # Optionally receive a response
    response = await ws_chatbot.recv()
    print(f"Received response from WebSocket: {response}")    
    
    # response_json = json.loads(response)
    # print(response_json['response'])
    
    await websocket.send(json.dumps({
        "type": "transcription",
        "data": response,
    }))
        
    # except Exception as e:
    #     print(f"Error processing video data: {e}")
        

###

async def handle_client(websocket, path):
    print("Client connected")

    # Initialize per-client state
    user_state = {
        'audio_buffer': [],
        'buffer_duration': 2,  # Adjust the buffer duration (in seconds) as needed
    }

    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                if data['type'] == 'audio':
                    await process_audio_data(websocket, data['data'], user_state)
                elif data['type'] == 'video':
                    await process_video_data(websocket, data['data'])
                else:
                    print(f"Unknown data type: {data['type']}")
            except json.JSONDecodeError as e:
                print(f"Failed to decode JSON: {e}")
    except websockets.exceptions.ConnectionClosed as e:
        print(f"Client disconnected: {e}")
    except Exception as e:
        print(f"Error in handle_client: {e}")

###

async def main():
    
    print(f"Connecting to chatserver at ws://127.0.0.1:{CHATBOT_WS_PORT}...")
    global ws_chatbot
    ws_chatbot = await websockets.connect(f'ws://127.0.0.1:{CHATBOT_WS_PORT}')
    print('chatserver is connected')

    server = await websockets.serve(handle_client, "0.0.0.0", AIRECORDER_WS_PORT)
    print(f"Server is listening on port {AIRECORDER_WS_PORT}")
        
    await server.wait_closed()

###

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Error: {e}")