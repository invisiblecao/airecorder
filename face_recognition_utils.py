import cv2
import face_recognition
import numpy as np
from deepface import DeepFace

known_face_encodings = []
known_face_labels = []
next_label_id = 1

def recognize_and_track_faces(frame):
    global known_face_encodings, known_face_labels, next_label_id
    
    # Resize frame for faster processing
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
    
    face_locations = face_recognition.face_locations(rgb_small_frame, model="cnn")
    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
    
    labels = []
    emotions = []
    
    for face_encoding in face_encodings:
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        name = "Unknown"
        
        if True in matches:
            first_match_index = matches.index(True)
            name = known_face_labels[first_match_index]
        else:
            name = f"Person {next_label_id}"
            next_label_id += 1
            known_face_encodings.append(face_encoding)
            known_face_labels.append(name)
        
        labels.append(name)
    
    # Scale back up face locations
    face_locations = [(top * 4, right * 4, bottom * 4, left * 4) for (top, right, bottom, left) in face_locations]
    
    # Perform emotion analysis
    for (top, right, bottom, left) in face_locations:
        face_image = frame[top:bottom, left:right]
        try:
            emotion_result = DeepFace.analyze(face_image, actions=['emotion'], enforce_detection=False)
            emotions.append(emotion_result[0]['dominant_emotion'])
        except:
            emotions.append("unknown")
    
    return face_locations, labels, emotions

def draw_face_boxes_with_descriptions(frame, face_locations, labels, face_descriptions):
    for (top, right, bottom, left), label, description in zip(face_locations, labels, face_descriptions):
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        
        y = top - 15 if top - 15 > 15 else top + 15
        cv2.putText(frame, f"{label}: {description}", (left, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    return frame