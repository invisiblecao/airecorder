import cv2
import dlib
import numpy as np
from tensorflow.keras.models import load_model

class LipMovementNet:
    def __init__(self):
        pass

    def process_video(self, video_path, shape_predictor, model):
        cap = cv2.VideoCapture(video_path)
        detector = dlib.get_frontal_face_detector()
        
        speaking_frames = []
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = detector(gray)
            
            for face in faces:
                shape = shape_predictor(gray, face)
                mouth_points = shape.parts()[48:68]  # Mouth landmarks
                
                mouth_array = np.array([(p.x, p.y) for p in mouth_points])
                x, y, w, h = cv2.boundingRect(mouth_array)
                mouth_roi = gray[y:y+h, x:x+w]
                
                mouth_roi = cv2.resize(mouth_roi, (100, 50))  # Adjust size as needed
                mouth_roi = mouth_roi.astype('float32') / 255.0
                mouth_roi = np.expand_dims(mouth_roi, axis=-1)
                mouth_roi = np.expand_dims(mouth_roi, axis=0)
                
                prediction = model.predict(mouth_roi)
                is_speaking = prediction[0][1] > 0.5  # Assuming binary classification
                
                speaking_frames.append(is_speaking)
                
                # Visualize the result (optional)
                color = (0, 255, 0) if is_speaking else (0, 0, 255)
                cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            
            cv2.imshow('Lip Movement Detection', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        
        return speaking_frames

def main(video_path, shape_predictor_path, model_path):
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(shape_predictor_path)
    model = load_model(model_path)
    
    lip_movement_net = LipMovementNet()
    speaking_frames = lip_movement_net.process_video(video_path, predictor, model)
    
    print(f"Speaking detected in {sum(speaking_frames)} out of {len(speaking_frames)} frames")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Lip Movement Detection')
    parser.add_argument('-v', '--video', required=True, help='Path to input video file')
    parser.add_argument('-p', '--predictor', required=True, help='Path to shape predictor file')
    parser.add_argument('-m', '--model', required=True, help='Path to pre-trained model file')
    args = parser.parse_args()
    
    main(args.video, args.predictor, args.model)