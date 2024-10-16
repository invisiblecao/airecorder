import cv2
import dlib
import os
class FaceProcessor:
    def __init__(self):
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(os.getenv("SHAPE_PREDICTOR_PATH", "/home/kepan/airecorder/test2/models/shape_predictor_68_face_landmarks.dat"))

    def detect_faces(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.detector(gray)
        return faces

    def extract_features(self, frame, face):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        landmarks = self.predictor(gray, face)
        return landmarks

    def recognize_and_track_faces(self, frame):
        faces = self.detect_faces(frame)
        labels = []
        emotions = []  # Placeholder for emotions logic
        for face in faces:
            landmarks = self.extract_features(frame, face)
            # Add your face recognition logic here
            labels.append("Person")  # Replace with actual label
            emotions.append("Neutral")  # Replace with actual emotion detection
        return faces, labels, emotions

    def draw_face_boxes_with_descriptions(self, frame, face_locations, labels, descriptions):
        for (i, rect) in enumerate(face_locations):
            (x, y, w, h) = (rect.left(), rect.top(), rect.width(), rect.height())
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, f"{labels[i]}: {descriptions[i]}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        return frame