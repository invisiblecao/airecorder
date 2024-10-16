import os
import torch
import numpy as np
import speech_recognition as sr
from datetime import datetime, timedelta
from collections import deque
from transformers import pipeline

class WhisperTranscriber:
    def __init__(self):
        self.transcription = []
        self.data_queue = deque()
        self.phrase_time = None
        self.recorder = sr.Recognizer()
        # Change the model to "large"
        self.audio_model = pipeline("automatic-speech-recognition", model="openai/whisper-large-v2")
        self.record_timeout = 5
        self.phrase_timeout = 3

    def initialize_microphone(self):
        mic_name = os.getenv("MIC_NAME")
        if mic_name:
            for index, name in enumerate(sr.Microphone.list_microphone_names()):
                if name == mic_name:
                    return sr.Microphone(device_index=index, sample_rate=16000)
        print(f"No microphone found with the name \"{mic_name}\". Using the default local microphone.")
        return sr.Microphone(sample_rate=16000)

    def record_callback(self, _, audio: sr.AudioData) -> None:
        data = audio.get_raw_data()
        self.data_queue.append(data)

    def start_transcription(self):
        source = self.initialize_microphone()
        with source:
            self.recorder.adjust_for_ambient_noise(source)
        self.recorder.listen_in_background(source, self.record_callback, phrase_time_limit=self.record_timeout)
        print("Model loaded.\n")

    def process_audio(self):
        try:
            now = datetime.utcnow()
            if self.data_queue:
                phrase_complete = False
                if self.phrase_time and now - self.phrase_time > timedelta(seconds=self.phrase_timeout):
                    phrase_complete = True
                self.phrase_time = now
                
                audio_data = b''.join(self.data_queue)
                self.data_queue.clear()
                
                audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
                # You might need to adjust the chunk size for the large model
                result = self.audio_model(audio_np, chunk_length_s=30, stride_length_s=5)
                text = result['text'].strip()

                if phrase_complete:
                    self.transcription.append(text)
                else:
                    self.transcription[-1] = text

                os.system('cls' if os.name == 'nt' else 'clear')
                for line in self.transcription:
                    print(line)
                print('', end='', flush=True)
            else:
                return self.transcription
        except KeyboardInterrupt:
            pass

        print("\n\nTranscription:")
        for line in self.transcription:
            print(line)
        return self.transcription
