"""
Core validation and application loop logic.
"""
import cv2
import time
import mediapipe as mp
from collections import deque
from . import config
from .visualizer import Visualizer
from . import gestures

class GestureRecognizerApp:
    def __init__(self):
        self.visualizer = Visualizer()
        
        # Initialize MediaPipe
        self.holistic = mp.solutions.holistic.Holistic(
            min_detection_confidence=config.MP_MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=config.MP_MIN_TRACKING_CONFIDENCE
        )
        
        # State
        self.buffer_start_time = None
        self.buffer_active = True
        self.gesture_detected = None
        self.gesture_stable_time = 0
        self.current_word = None
        self.current_confidence = 0
        self.head_history = deque(maxlen=10)
        
    def run(self):
        """Main application loop"""
        print("="*70)
        print("GESTURE-BASED SIGN LANGUAGE RECOGNITION (OPTIMIZED)")
        print("="*70)
        
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.WEBCAM_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.WEBCAM_HEIGHT)
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret: break
                
                # Flip and process
                frame = cv2.flip(frame, 1)
                image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image_rgb.flags.writeable = False
                results = self.holistic.process(image_rgb)
                image_rgb.flags.writeable = True
                
                # Draw landmarks
                frame = self.visualizer.draw_landmarks(frame, results)
                
                # Logic
                self._process_frame_logic(results)
                
                # UI
                buffer_remaining = 0
                if self.buffer_active and self.buffer_start_time:
                    elapsed = time.time() - self.buffer_start_time
                    buffer_remaining = max(0, config.BUFFER_TIME - elapsed)
                
                frame = self.visualizer.draw_ui(
                    frame, self.buffer_active, buffer_remaining,
                    self.current_word, self.current_confidence,
                    self.gesture_detected, self.gesture_stable_time,
                    self.current_confidence # TODO: Pass gesture specific conf if needed
                )
                
                cv2.imshow('ISL Recognition', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
                time.sleep(0.01) # Small sleep to reduce CPU usage
                
        except KeyboardInterrupt:
            print("Stopping...")
        finally:
            cap.release()
            cv2.destroyAllWindows()
            self.holistic.close()

    def _process_frame_logic(self, results):
        current_time = time.time()
        
        # Buffer Logic
        if self.buffer_active:
            if self.buffer_start_time is None:
                self.buffer_start_time = current_time
            
            elapsed = current_time - self.buffer_start_time
            if elapsed >= config.BUFFER_TIME:
                self.buffer_active = False
                self.buffer_start_time = None
                print("[BUFFER] Complete! Starting recognition...")
            return

        # Recognition Logic
        detected_gesture, confidence = self._detect_gesture(results)
        
        if detected_gesture and confidence > 40.0:
            if self.gesture_detected == detected_gesture:
                self.gesture_stable_time += 0.03 # Approx frame time
                
                required_time = config.GESTURE_STABLE_DURATION
                if detected_gesture == "namaste": required_time = config.GESTURE_STABLE_DURATION_NAMASTE
                elif detected_gesture == "water": required_time = config.GESTURE_STABLE_DURATION_WATER
                
                if self.gesture_stable_time >= required_time:
                    self._confirm_gesture(detected_gesture, confidence)
            else:
                self.gesture_detected = detected_gesture
                self.gesture_stable_time = 0
        else:
            self.gesture_detected = None
            self.gesture_stable_time = 0

    def _detect_gesture(self, results):
        """Hierarchical gesture detection"""
        # 1. Head Gestures (Highest Priority)
        g, c = gestures.detect_head_gesture(results, self.head_history)
        if g: return g, c
        
        # 2. Pose/Body Gestures
        detected, confidence = gestures.detect_namaste_gesture(results)
        if detected: return "namaste", confidence
        
        detected, confidence = gestures.detect_hands_intersection(results)
        if detected: return "hands_intersect", confidence
            
        detected, confidence = gestures.detect_india_gesture(results)
        if detected: return "india", confidence
            
        detected, confidence = gestures.detect_sibling_gesture(results)
        if detected: return "sibling", confidence
             
        # 3. Hand Gestures
        detected, confidence = gestures.detect_doctor_gesture(results)
        if detected: return "doctor", confidence
            
        detected, confidence = gestures.detect_female_gesture(results)
        if detected: return "female", confidence
            
        detected, confidence = gestures.detect_male_gesture(results)
        if detected: return "male", confidence
            
        detected, confidence = gestures.detect_thank_you_gesture(results)
        if detected: return "thank_you", confidence
            
        detected, confidence = gestures.detect_water_gesture(results)
        if detected: return "water", confidence
            
        detected, confidence = gestures.detect_cheek_gesture(results)
        if detected: return "index_on_cheek", confidence
            
        detected, confidence = gestures.detect_both_palms_forward(results)
        if detected: return "both_palms", confidence
            
        # 4. Simple Signs
        g, c = gestures.detect_simple_hand_signs(results)
        if g: return g, c
        
        return None, 0.0

    def _confirm_gesture(self, gesture, confidence):
        word = config.GESTURE_MAP.get(gesture)
        if word and word != self.current_word:
            self.current_word = word
            self.current_confidence = confidence
            print(f"[RECOGNIZED] {word} ({confidence:.1f}%)")
            
            # Reset
            self.buffer_active = True
            self.buffer_start_time = time.time()
            self.gesture_detected = None
            self.gesture_stable_time = 0
