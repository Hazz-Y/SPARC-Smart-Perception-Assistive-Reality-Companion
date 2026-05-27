"""
Visualization and UI drawing module.
"""
import cv2
import mediapipe as mp
import numpy as np
from . import config

class Visualizer:
    def __init__(self):
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_holistic = mp.solutions.holistic
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Pre-define drawing specs to avoid recreation every frame
        self.face_landmark_spec = self.mp_drawing.DrawingSpec(color=(255, 255, 0), thickness=1, circle_radius=1)
        self.face_connection_spec = self.mp_drawing.DrawingSpec(color=(255, 255, 0), thickness=1)
        
        self.left_hand_spec = self.mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2, circle_radius=2)
        self.left_hand_conn_spec = self.mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2)
        
        self.right_hand_spec = self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2)
        self.right_hand_conn_spec = self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2)
        
        self.pose_style = self.mp_drawing_styles.get_default_pose_landmarks_style()

    def draw_landmarks(self, image, results):
        """Draw MediaPipe landmarks on image"""
        # Draw pose landmarks
        self.mp_drawing.draw_landmarks(
            image, results.pose_landmarks, self.mp_holistic.POSE_CONNECTIONS,
            landmark_drawing_spec=self.pose_style)
        
        # Draw face landmarks (for cheek detection)
        # Only draw contours if face landmarks exist to save processing
        if results.face_landmarks:
            self.mp_drawing.draw_landmarks(
                image, results.face_landmarks, self.mp_holistic.FACEMESH_CONTOURS,
                landmark_drawing_spec=self.face_landmark_spec,
                connection_drawing_spec=self.face_connection_spec)
        
        # Draw left hand landmarks - BLUE color
        if results.left_hand_landmarks:
            self.mp_drawing.draw_landmarks(
                image, results.left_hand_landmarks, self.mp_holistic.HAND_CONNECTIONS,
                landmark_drawing_spec=self.left_hand_spec,
                connection_drawing_spec=self.left_hand_conn_spec)
        
        # Draw right hand landmarks - GREEN color
        if results.right_hand_landmarks:
            self.mp_drawing.draw_landmarks(
                image, results.right_hand_landmarks, self.mp_holistic.HAND_CONNECTIONS,
                landmark_drawing_spec=self.right_hand_spec,
                connection_drawing_spec=self.right_hand_conn_spec)
        
        return image

    def draw_ui(self, image, buffer_active, buffer_remaining, current_word, confidence, 
                gesture_detected, gesture_stable_time, gesture_confidence=0):
        """Draw prediction information on image - Beautiful and organized interface"""
        h, w = image.shape[:2]
        
        # Create overlay for transparency
        overlay = image.copy()
        cv2.rectangle(overlay, (0, 0), (w, 85), (20, 20, 40), -1)  # Header
        cv2.rectangle(overlay, (0, 85), (w, 220), (10, 10, 20), -1)  # Info area
        cv2.addWeighted(overlay, 0.75, image, 0.25, 0, image)
        
        self._draw_title(image)
        self._draw_status(image, buffer_active, buffer_remaining)
        
        if gesture_detected and not buffer_active:
            self._draw_gesture_info(image, gesture_detected, gesture_confidence, gesture_stable_time)
            
        if current_word and confidence > 0:
            self._draw_prediction(image, current_word, confidence)
            
        return image

    def _draw_title(self, image):
        # Draw shadow first
        cv2.putText(image, "INDIAN SIGN LANGUAGE", (12, 37), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, config.COLOR_BLACK, 4)
        
        # Draw colored words
        words = ["INDIAN", "SIGN", "LANGUAGE"]
        colors = [config.COLOR_ORANGE, config.COLOR_WHITE, config.COLOR_GREEN]
        
        current_x = 10
        y_pos = 35
        
        for word, color in zip(words, colors):
            (text_width, _), _ = cv2.getTextSize(word, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 3)
            cv2.putText(image, word, (current_x, y_pos), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 3)
            current_x += text_width + 15
            
        # Subtitle
        cv2.putText(image, "Real-Time Gesture Recognition System", (10, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, config.COLOR_GRAY, 1)

    def _draw_status(self, image, buffer_active, buffer_remaining):
        # Buffer and Status text
        h = image.shape[0]
        bottom_y = h - 15
        
        if buffer_active:
            cv2.putText(image, "Status:", (10, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.6, config.COLOR_GRAY, 1)
            cv2.putText(image, "Preparing...", (10, 125), cv2.FONT_HERSHEY_SIMPLEX, 0.7, config.COLOR_CYAN, 2)
            
            buffer_text = f"Buffer: {buffer_remaining:.1f}s"
            cv2.putText(image, buffer_text, (10, bottom_y), cv2.FONT_HERSHEY_SIMPLEX, 0.45, config.COLOR_GRAY, 1)
        else:
            cv2.putText(image, "Status:", (10, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.6, config.COLOR_GRAY, 1)
            cv2.putText(image, "ACTIVE", (10, 125), cv2.FONT_HERSHEY_SIMPLEX, 0.7, config.COLOR_GREEN, 2)

    def _draw_gesture_info(self, image, gesture_detected, gesture_confidence, gesture_stable_time):
        gesture_name = config.GESTURE_DISPLAY_NAMES.get(gesture_detected, gesture_detected)
        
        # Stability bar
        h = image.shape[0]
        bottom_y = h - 15
        
        required_stability = config.GESTURE_STABLE_DURATION
        if gesture_detected == "namaste":
            required_stability = config.GESTURE_STABLE_DURATION_NAMASTE
        elif gesture_detected == "water":
            required_stability = config.GESTURE_STABLE_DURATION_WATER
            
        stability = min(gesture_stable_time / required_stability, 1.0)
        stability_pct = int(stability * 100)
        
        cv2.putText(image, f"Stability: {stability_pct}%", (10, bottom_y), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, config.COLOR_GRAY, 1)
        
        # Detailed Info
        info_y = 105
        cv2.putText(image, "Detecting:", (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, config.COLOR_LIGHT_GRAY, 1)
        cv2.putText(image, gesture_name, (10, info_y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.65, config.COLOR_CYAN, 2)
        
        if gesture_confidence > 0:
            conf_y = info_y + 45
            cv2.putText(image, "Confidence:", (10, conf_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, config.COLOR_LIGHT_GRAY, 1)
            cv2.putText(image, f"{gesture_confidence:.1f}%", (10, conf_y + 18), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, config.COLOR_ORANGE, 2)

    def _draw_prediction(self, image, current_word, confidence):
        pred_y = 150
        cv2.putText(image, "RECOGNIZED:", (10, pred_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, config.COLOR_LIGHT_GRAY, 1)
        
        word_y = pred_y + 25
        # Shadow
        cv2.putText(image, current_word, (12, word_y + 2), cv2.FONT_HERSHEY_SIMPLEX, 1.0, config.COLOR_BLACK, 4)
        
        # Color based on confidence
        if confidence >= 80.0:
            text_color = config.COLOR_GREEN
        elif confidence >= 60.0:
            text_color = config.COLOR_CYAN
        else:
            text_color = config.COLOR_ORANGE
            
        cv2.putText(image, current_word, (10, word_y), cv2.FONT_HERSHEY_SIMPLEX, 1.0, text_color, 2)
        
        # Final confidence
        conf_y = word_y + 30
        cv2.putText(image, "Confidence:", (10, conf_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, config.COLOR_LIGHT_GRAY, 1)
        cv2.putText(image, f"{confidence:.1f}%", (10, conf_y + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.65, text_color, 2)
