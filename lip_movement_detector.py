import dlib
import numpy as np
import cv2
from keras.models import load_model
from sklearn.preprocessing import MinMaxScaler

class LipMovementDetector:
    def __init__(self, shape_predictor_path, model_path):
        self.detector = dlib.get_frontal_face_detector()
        self.shape_predictor = dlib.shape_predictor(shape_predictor_path)
        self.model = load_model(model_path, compile=False)

    def detect_lip_movement(self, frame, face_locations):
        speaking_persons = []
        
        for (x, y, w, h) in face_locations:
            rect = dlib.rectangle(int(x), int(y), int(x + w), int(y + h))
            shape = self.shape_predictor(frame, rect)
            
            lip_points = []
            for i in range(48, 68):
                lip_points.append((shape.part(i).x, shape.part(i).y))
            
            lip_distance = self.calculate_lip_distance(lip_points)
            
            lip_sequence = np.array([lip_distance]).reshape(-1, 1)
            scaler = MinMaxScaler()
            lip_sequence = scaler.fit_transform(lip_sequence).reshape(1, -1, 1)
            
            prediction = self.model.predict(lip_sequence)
            speaking_persons.append(np.argmax(prediction) == 1)
        
        return speaking_persons
    
    @staticmethod
    def calculate_lip_distance(lip_points):
        A = np.linalg.norm(np.array(lip_points[2]) - np.array(lip_points[9]))
        B = np.linalg.norm(np.array(lip_points[4]) - np.array(lip_points[7]))
        C = np.linalg.norm(np.array(lip_points[0]) - np.array(lip_points[6]))
        return (A + B + C) / 3
