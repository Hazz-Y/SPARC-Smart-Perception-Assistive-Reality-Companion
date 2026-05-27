"""
Emotion Detector for SPARC
Detects emotions from faces in video frames using a pre-trained CNN model.
"""
import logging
import os
import cv2
import numpy as np
from tensorflow import keras
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Flatten, Conv2D, MaxPooling2D

# Paths for emotion detection model and cascade
EMOTION_MODEL_PATH = '/home/pi/SPARC/Face_Recognition/model.h5'
CASCADE_PATH = '/home/pi/SPARC/Face_Recognition/src/haarcascade_frontalface_default.xml'

# Emotion labels (alphabetical order as per model)
EMOTION_DICT = {0: "Angry", 1: "Disgusted", 2: "Fearful", 3: "Happy", 4: "Neutral", 5: "Sad", 6: "Surprised"}

# Allowed emotions (only these 4 will be detected)
ALLOWED_EMOTIONS = {0: "Angry", 3: "Happy", 4: "Neutral", 5: "Sad"}

# Neutral bias threshold - if Neutral score is within this ratio of max score, choose Neutral
NEUTRAL_BIAS_THRESHOLD = 0.75  # If Neutral is at least 75% of max score, prefer Neutral

class EmotionDetector:
    def __init__(self):
        self.logger = logging.getLogger('EmotionDetector')
        self.model = None
        self.face_cascade = None
        self.current_emotion = "No Face"
        self._init_model()
        self._init_cascade()
        
    def _init_model(self):
        """Load the emotion detection model"""
        try:
            if os.path.exists(EMOTION_MODEL_PATH):
                # Try loading as full model first
                try:
                    self.model = keras.models.load_model(EMOTION_MODEL_PATH)
                    self.logger.info(f"Loaded emotion model from {EMOTION_MODEL_PATH}")
                except:
                    # If that fails, build the model architecture and load weights
                    self.model = Sequential()
                    self.model.add(Conv2D(32, kernel_size=(3, 3), activation='relu', input_shape=(48,48,1)))
                    self.model.add(Conv2D(64, kernel_size=(3, 3), activation='relu'))
                    self.model.add(MaxPooling2D(pool_size=(2, 2)))
                    self.model.add(Dropout(0.25))
                    self.model.add(Conv2D(128, kernel_size=(3, 3), activation='relu'))
                    self.model.add(MaxPooling2D(pool_size=(2, 2)))
                    self.model.add(Conv2D(128, kernel_size=(3, 3), activation='relu'))
                    self.model.add(MaxPooling2D(pool_size=(2, 2)))
                    self.model.add(Dropout(0.25))
                    self.model.add(Flatten())
                    self.model.add(Dense(1024, activation='relu'))
                    self.model.add(Dropout(0.5))
                    self.model.add(Dense(7, activation='softmax'))
                    
                    self.model.load_weights(EMOTION_MODEL_PATH)
                    self.logger.info(f"Loaded emotion model weights from {EMOTION_MODEL_PATH}")
            else:
                self.logger.warning(f"Emotion model not found at {EMOTION_MODEL_PATH}")
        except Exception as e:
            self.logger.error(f"Failed to load emotion model: {e}")
            self.model = None
    
    def _init_cascade(self):
        """Load the face detection cascade"""
        try:
            # Prevents openCL usage and unnecessary logging messages
            cv2.ocl.setUseOpenCL(False)
            
            if os.path.exists(CASCADE_PATH):
                self.face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
                self.logger.info(f"Loaded face cascade from {CASCADE_PATH}")
            else:
                self.logger.warning(f"Face cascade not found at {CASCADE_PATH}")
        except Exception as e:
            self.logger.error(f"Failed to load face cascade: {e}")
            self.face_cascade = None
    
    def detect_emotion(self, frame):
        """
        Detect emotion from a video frame.
        
        Args:
            frame: OpenCV frame (BGR format)
            
        Returns:
            str: Detected emotion or "No Face" if no face detected
        """
        if self.model is None or self.face_cascade is None:
            return "No Face"
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.3, 
                minNeighbors=5
            )
            
            if len(faces) == 0:
                self.current_emotion = "No Face"
                return "No Face"
            
            # Use the first detected face
            (x, y, w, h) = faces[0]
            
            # Extract face region
            roi_gray = gray[y:y + h, x:x + w]
            
            # Resize to 48x48 (model input size)
            cropped_img = cv2.resize(roi_gray, (48, 48))
            
            # Prepare for model prediction
            cropped_img = np.expand_dims(np.expand_dims(cropped_img, -1), 0)
            
            # Predict emotion
            prediction = self.model.predict(cropped_img, verbose=0)
            prediction = prediction[0]  # Get the first (and only) prediction array
            
            # Filter to only allowed emotions
            allowed_predictions = {}
            for idx, emotion_name in ALLOWED_EMOTIONS.items():
                allowed_predictions[idx] = prediction[idx]
            
            # Get max score among allowed emotions
            if not allowed_predictions:
                # Fallback to Neutral if something goes wrong
                emotion = "Neutral"
                self.current_emotion = emotion
                return emotion
            
            max_allowed_score = max(allowed_predictions.values())
            neutral_score = prediction[4]  # Neutral is at index 4
            
            # Apply Neutral bias: if Neutral is within threshold of max allowed, prefer Neutral
            if neutral_score >= max_allowed_score * NEUTRAL_BIAS_THRESHOLD:
                # Prefer Neutral if it's close enough to the max allowed emotion
                emotion = "Neutral"
            else:
                # Otherwise, get the emotion with highest score among allowed ones
                maxindex = max(allowed_predictions, key=allowed_predictions.get)
                emotion = ALLOWED_EMOTIONS.get(maxindex, "Neutral")
            
            self.current_emotion = emotion
            return emotion
            
        except Exception as e:
            self.logger.error(f"Error detecting emotion: {e}")
            return "No Face"
    
    def get_current_emotion(self):
        """Get the last detected emotion"""
        return self.current_emotion

