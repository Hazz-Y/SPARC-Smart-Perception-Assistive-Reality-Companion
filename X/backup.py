#!/usr/bin/python
# -*- coding:utf-8 -*-
#
# SPARC System - AI Assistant with Object Detection and Sign Language Translation
# 
# Required dependencies:
# - speech_recognition (pip install SpeechRecognition)
# - pygame (pip install pygame) 
# - pyaudio (pip install pyaudio)
# - All other existing dependencies
#

import os
import sys
import time
import joblib
import cv2
import pandas as pd
import numpy as np
from cvzone.HandTrackingModule import HandDetector
import math
from gtts import gTTS
import string
import random
import re
import logging
import traceback
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO
import signal
import pyrealsense2 as rs
import speech_recognition as sr
import threading
import pygame

# OLED Display Setup
picdir = '/home/pi/SPARC/pic'
libdir = '/home/pi/SPARC/lib'
if os.path.exists(libdir):
    sys.path.append(libdir)

try:
    from waveshare_OLED import OLED_1in32
    OLED_AVAILABLE = True
except ImportError:
    print("OLED library not found. Display functionality will be disabled.")
    OLED_AVAILABLE = False

logging.basicConfig(level=logging.INFO)

class SPARCSystem:
    def __init__(self):
        # Initialize OLED display
        self.disp = None
        self.font_small = None
        self.font_medium = None
        self.font_large = None
        self.setup_display()
        
        # Initialize gesture recognition components
        self.setup_gesture_recognition()
        
        # Initialize object detection components
        self.setup_object_detection()
        
        # Initialize Intel RealSense camera
        self.setup_realsense_camera()
        
        # Variables for sentence building (gesture recognition)
        self.sentence = ""
        self.no_hand_frames = 0
        self.backspace_frame_counter = 0
        self.mode_switch_time = None
        self.last_recognition_time = None
        self.out_of_frame_frames = 0
        self.current_mode = 'character'
        self.confidence_threshold = 0.40
        self.frame_skip = 2
        self.frame_count = 0
        
        # Object detection variables
        self.detected_objects_history = []
        self.running = True
        
        # Voice input setup
        self.setup_voice_input()
        
        # Signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
    
    def signal_handler(self, sig, frame):
        """Handle graceful shutdown"""
        self.running = False
        self.cleanup()
        sys.exit(0)
    
    def setup_display(self):
        """Initialize the OLED display"""
        if not OLED_AVAILABLE:
            return
        try:
            self.disp = OLED_1in32.OLED_1in32()
            logging.info("1.32inch OLED initialized")
            self.disp.Init()
            self.disp.clear()
            # Setup fonts with fallback options
            try:
                self.font_small = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 12)
                self.font_medium = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 14)
                self.font_large = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 16)
                logging.info("Loaded custom fonts from Font.ttc")
            except:
                try:
                    self.font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
                    self.font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
                    self.font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
                    logging.info("Loaded system DejaVu fonts")
                except:
                    self.font_small = ImageFont.load_default()
                    self.font_medium = ImageFont.load_default()
                    self.font_large = ImageFont.load_default()
                    logging.info("Using default PIL font")
        except Exception as e:
            logging.error(f"Failed to initialize OLED: {e}")
            self.disp = None
    
    def setup_gesture_recognition(self):
        """Initialize gesture recognition models and camera"""
        model_paths = {
            'character': '/home/pi/gesture-to-audio/models/characters/RFC_MODEL_3_A_Z_modes.pkl',
            'numbers': '/home/pi/gesture-to-audio/models/numbers/RFC_MODEL_2_0_9_modes.pkl',
            'words': '/home/pi/gesture-to-audio/models/words/set1/RFC_MODEL_WORDS_SET_1.pkl'
        }
        self.models = {mode: joblib.load(path) for mode, path in model_paths.items()}
        self.detector = HandDetector(staticMode=False, maxHands=1, modelComplexity=0, detectionCon=0.7, minTrackCon=0.5)
        self.num_landmarks = 21
        self.label_maps = {
            'character': {
                0: 'A', 1: 'B', 2: 'back_space', 3: 'C', 4: 'D', 5: 'E', 6: 'F', 7: 'G', 8: 'H', 9: 'I', 10: 'J',
                11: 'K', 12: 'L', 13: 'M', 14: 'N', 15: 'numbers', 16: 'O', 17: 'P', 18: 'Q', 19: 'R', 20: 'S',
                21: 'T', 22: 'U', 23: 'V', 24: 'W', 25: 'words', 26: 'X', 27: 'Y', 28: 'Z'
            },
            'numbers': {
                0: '0', 1: '1', 2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8', 9: '9', 10: 'back_space', 
                11: 'character', 12: 'words'
            },
            'words': {
                0: 'back_space', 1: 'character', 2: 'Hello-Hi-Bye', 3: 'Help', 4: 'How', 5: 'I-Love-You', 6: 'Nice',
                7: 'No', 8: 'numbers', 9: 'Please', 10: 'Sorry', 11: 'Thankyou', 12: 'What-is-your-name', 13: 'Who', 
                14: 'Yes'
            }
        }
    
    def setup_object_detection(self):
        """Initialize YOLO model for object detection"""
        self.yolo_model = YOLO('yolov8n.pt')  # nano version - smallest and fastest
    
    def setup_voice_input(self):
        """Initialize speech recognition"""
        try:
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            # Adjust for ambient noise
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Voice input initialized successfully!")
        except Exception as e:
            print(f"Voice input setup failed: {e}")
            self.recognizer = None
            self.microphone = None
    
    def play_ping_sound(self):
        """Play a ping sound to indicate input time"""
        try:
            # Create a simple beep sound
            os.system('echo -e "\a"')
        except:
            pass
    
    def get_voice_input(self, timeout=5):
        """Get voice input with timeout, also handles keyboard input"""
        print(f"Listening for voice input or keyboard input (timeout: {timeout}s)...")
        print("You can speak or press '1' for object detection, '2' for gesture recognition")
        
        # Use a simple approach: just use regular input for now
        # This will work reliably for keyboard input
        try:
            keyboard_input = input().strip().lower()
            if keyboard_input:
                print(f"Keyboard input captured: '{keyboard_input}'")
                return keyboard_input
        except:
            pass
        
        # If no keyboard input, return empty string
        print("No input detected")
        return ""
    
    def setup_realsense_camera(self):
        """Initialize Intel RealSense D455 camera"""
        try:
            # Configure RealSense pipeline
            self.pipeline = rs.pipeline()
            config = rs.config()
            
            # Enable RGB stream
            config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
            
            # Start streaming
            self.pipeline.start(config)
            self.realsense_available = True
        except Exception as e:
            self.realsense_available = False
            # Try to find a working camera
            self.cap = None
            available_devices = [0, 1, 2, 10, 11, 12, 20, 21, 22, 23, 24, 25]  # Common camera device numbers
            
            for device_num in available_devices:
                try:
                    self.cap = cv2.VideoCapture(device_num)
                    if self.cap.isOpened():
                        # Test if we can read a frame
                        ret, frame = self.cap.read()
                        if ret and frame is not None:
                            break
                        else:
                            self.cap.release()
                            self.cap = None
                    else:
                        self.cap.release()
                        self.cap = None
                except Exception as e:
                    if self.cap:
                        self.cap.release()
                        self.cap = None
            
            if self.cap is None:
                # Don't exit, just disable camera features
                self.camera_available = False
            else:
                self.camera_available = True
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.cap.set(cv2.CAP_PROP_FPS, 15)
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    def get_camera_frame(self):
        """Get frame from RealSense or fallback camera"""
        if self.realsense_available:
            try:
                frames = self.pipeline.wait_for_frames()
                color_frame = frames.get_color_frame()
                if color_frame:
                    frame = np.asanyarray(color_frame.get_data())
                    return True, frame
                return False, None
            except Exception as e:
                return False, None
        elif hasattr(self, 'camera_available') and self.camera_available and self.cap:
            return self.cap.read()
        else:
            return False, None
    
    def show_startup_message(self):
        """Display startup message on OLED"""
        if not self.disp:
            return
        try:
            image = Image.new('L', (self.disp.width, self.disp.height), 0)
            draw = ImageDraw.Draw(image)
            startup_lines = [
                "SPARC:The",
                "Future of",
                "Communication",
            ]
            # Use larger font for better visibility
            font = self.font_large if self.font_large else self.font_medium
            line_height = 18
            total_height = len(startup_lines) * line_height
            start_y = (self.disp.height - total_height) // 2
            for i, line in enumerate(startup_lines):
                try:
                    bbox = draw.textbbox((0, 0), line, font=font)
                    text_width = bbox[2] - bbox[0]
                except AttributeError:
                    text_width, _ = draw.textsize(line, font=font)
                x_pos = (self.disp.width - text_width) // 2
                y_pos = start_y + (i * line_height)
                # Draw text with bold effect (draw multiple times slightly offset)
                draw.text((x_pos, y_pos), line, font=font, fill=255)
                draw.text((x_pos+1, y_pos), line, font=font, fill=255)
                draw.text((x_pos, y_pos+1), line, font=font, fill=255)
            self.disp.ShowImage(self.disp.getbuffer(image))
            time.sleep(3)  # Show for longer
        except Exception as e:
            logging.error(f"Error showing startup message: {e}")
    
    def show_welcome_display(self, message):
        """Display welcome message on OLED"""
        if not self.disp:
            return
        try:
            image = Image.new('L', (self.disp.width, self.disp.height), 0)
            draw = ImageDraw.Draw(image)
            
            # Use large font for better visibility
            font = self.font_large if self.font_large else self.font_medium
            
            # Split message into 3 lines as requested
            welcome_lines = [
                "Hello. I",
                "am SPARC",
                "Initializing...."
            ]
            
            # Center the text vertically
            line_height = 16
            total_height = len(welcome_lines) * line_height
            start_y = max(2, (self.disp.height - total_height) // 2)
            
            for i, line in enumerate(welcome_lines):
                try:
                    bbox = draw.textbbox((0, 0), line, font=font)
                    text_width = bbox[2] - bbox[0]
                except AttributeError:
                    text_width, _ = draw.textsize(line, font=font)
                x_pos = (self.disp.width - text_width) // 2
                y_pos = start_y + (i * line_height)
                # Draw text with bold effect (draw multiple times slightly offset)
                draw.text((x_pos, y_pos), line, font=font, fill=255)
                draw.text((x_pos+1, y_pos), line, font=font, fill=255)
                draw.text((x_pos, y_pos+1), line, font=font, fill=255)
                draw.text((x_pos+1, y_pos+1), line, font=font, fill=255)
            
            self.disp.ShowImage(self.disp.getbuffer(image))
            time.sleep(4)  # Show longer for better readability
        except Exception as e:
            logging.error(f"Error showing welcome display: {e}")
            import traceback
            traceback.print_exc()
    
    def show_simple_display(self, text):
        """Display simple text on OLED for testing"""
        if not self.disp:
            return
        try:
            image = Image.new('L', (self.disp.width, self.disp.height), 0)
            draw = ImageDraw.Draw(image)
            
            font = self.font_small if self.font_small else self.font_medium
            
            # Simple single line display
            draw.text((5, 40), text, font=font, fill=255)
            
            self.disp.ShowImage(self.disp.getbuffer(image))
            time.sleep(2)
        except Exception as e:
            logging.error(f"Error showing simple display: {e}")
    
    def update_display(self, sentence, current_gesture=""):
        """Update OLED display with text"""
        if not self.disp:
            return
        try:
            image = Image.new('L', (self.disp.width, self.disp.height), 0)
            draw = ImageDraw.Draw(image)
            words = sentence.split() if sentence else []
            lines = []
            current_line = ""
            max_width = self.disp.width - 4
            # Use larger font for better visibility
            font = self.font_large if self.font_large else self.font_medium
            for word in words:
                test_line = current_line + " " + word if current_line else word
                try:
                    bbox = draw.textbbox((0, 0), test_line, font=font)
                    test_width = bbox[2] - bbox[0]
                except AttributeError:
                    test_width, _ = draw.textsize(test_line, font=font)
                if test_width <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)
            max_lines = 3  # Fewer lines due to larger font
            if len(lines) > max_lines:
                lines = lines[-max_lines:]
            if current_gesture and current_gesture != "No Gesture Detected":
                gesture_line = f">> {current_gesture}"
                lines.append(gesture_line)
            line_height = 18  # Increased for larger font
            start_y = 2
            for i, line in enumerate(lines):
                y_pos = start_y + (i * line_height)
                if y_pos < self.disp.height - line_height:
                    # Simulate bold by drawing text multiple times with slight offsets
                    for dx, dy in [(0,0), (1,0), (0,1), (1,1)]:
                        draw.text((2+dx, y_pos+dy), line, font=font, fill=255)
            draw.rectangle([(0, 0), (self.disp.width-1, self.disp.height-1)], outline=255, fill=None)
            self.disp.ShowImage(self.disp.getbuffer(image))
        except Exception as e:
            logging.error(f"Error updating display: {e}")
            import traceback
            traceback.print_exc()
    
    def announce_message(self, message):
        """Convert text to speech and play it"""
        try:
            folder = '/tmp/audio'
            os.makedirs(folder, exist_ok=True)
            filename = ''.join(random.choice(string.ascii_lowercase) for _ in range(8)) + '.mp3'
            file_path = os.path.join(folder, filename)
            tts = gTTS(text=message, lang='en')
            tts.save(file_path)
            os.system(f'mpg123 "{file_path}" > /dev/null 2>&1')
            os.remove(file_path)
        except Exception as e:
            print(f"Audio playback error: {e}")
    
    def welcome_message(self):
        """Display and announce welcome message"""
        welcome_announcement = "Hello I am SPARC, what can I do for you?"
        welcome_display = "Hello. I\nam SPARC\nInitializing...."
        
        # Show on OLED first
        self.show_welcome_display(welcome_display)
        
        # Announce and show on terminal
        print(f"Announcing: {welcome_announcement}")
        self.announce_message(welcome_announcement)
        print("Welcome message completed!")
    
    def get_user_input(self):
        """Get user input from voice or keyboard"""
        print("Waiting for user input...")
        user_input = self.get_voice_input(timeout=5)
        print(f"Received input: '{user_input}'")
        
        # Check for object detection keywords
        object_keywords = [
            'hey sparc what you can see', 'what you can see', 'you can see', 
            'see', 'object detection', 'detect objects', 'what do you see', '1'
        ]
        
        # Check for sign language translation keywords
        sign_language_keywords = [
            'can you translate the sign language for me', 'translate sign language', 
            'sign language', 'gesture', 'hand gesture', 'translate gesture', 
            'sign translation', 'hand gesture', '2'
        ]
        
        print(f"Checking object keywords: {object_keywords}")
        print(f"Checking gesture keywords: {sign_language_keywords}")
        
        if any(keyword in user_input for keyword in object_keywords):
            print("Matched object detection keywords")
            return 'object_detection'
        elif any(keyword in user_input for keyword in sign_language_keywords):
            print("Matched gesture recognition keywords")
            return 'gesture_recognition'
        else:
            print("No keywords matched - invalid input")
            return 'invalid'
    
    def handle_invalid_input(self):
        """Handle invalid user input with sorry messages"""
        sorry_messages = [
            "Sorry, currently this task is out of my range.",
            "I'm not able to help with that right now.",
            "That's beyond my current capabilities.",
            "I can't assist with that task at the moment.",
            "Sorry, I don't understand that request.",
            "That's not something I can do right now."
        ]
        sorry_message = random.choice(sorry_messages)
        self.announce_message(sorry_message)
    
    def generate_announcement(self, objects):
        """Generate varied announcement sentences for detected objects"""
        if not objects:
            return "I don't see any clear objects in the image."
        
        if len(objects) == 1:
            templates = [
                f"I can see a {objects[0]} in the image.",
                f"There's a {objects[0]} visible.",
                f"I detect a {objects[0]} here.",
                f"I can make out a {objects[0]} in the picture."
            ]
        elif len(objects) == 2:
            templates = [
                f"I can see a {objects[0]} and a {objects[1]}.",
                f"There are a {objects[0]} and a {objects[1]} in the image.",
                f"I detect a {objects[0]} along with a {objects[1]}.",
                f"I can make out a {objects[0]} and a {objects[1]} here."
            ]
        else:
            first_part = ", ".join(objects[:-1])
            last_object = objects[-1]
            templates = [
                f"I can see {first_part}, and a {last_object}.",
                f"There are {first_part}, and a {last_object} in the image.",
                f"I detect {first_part}, and a {last_object}.",
                f"I can make out {first_part}, and a {last_object} here."
            ]
        
        return random.choice(templates)
    
    def run_object_detection(self):
        """Run object detection for 15 seconds"""
        print("Starting object detection for 15 seconds...")
        
        # Check if camera is available
        if not hasattr(self, 'camera_available') or not self.camera_available:
            error_message = "Sorry, no camera is available for object detection. Please check your camera connection."
            print(f"Error: {error_message}")
            self.announce_message(error_message)
            return
        
        # Run detection for 15 seconds
        detection_start_time = time.time()
        detection_duration = 15.0  # 15 seconds
        
        try:
            while self.running and (time.time() - detection_start_time) < detection_duration:
                # Get frame from camera
                ret, frame = self.get_camera_frame()
                if not ret:
                    time.sleep(1)
                    continue
                
                # Run YOLO detection
                results = self.yolo_model(frame)
                
                # Extract detected objects and draw bounding boxes
                current_objects = []
                for result in results:
                    boxes = result.boxes
                    if boxes is not None:
                        for box in boxes:
                            class_id = int(box.cls[0])
                            confidence = float(box.conf[0])
                            if confidence > 0.5:  # Only high confidence detections
                                class_name = self.yolo_model.names[class_id]
                                current_objects.append(class_name)
                                
                                # Draw bounding box
                                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                                cv2.putText(frame, f"{class_name}: {confidence:.2f}", 
                                          (int(x1), int(y1)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                # Add to history
                self.detected_objects_history.extend(current_objects)
                
                # Display current detection info
                if current_objects:
                    unique_current = list(dict.fromkeys(current_objects))
                    cv2.putText(frame, f"Detected: {', '.join(unique_current)}", 
                              (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                else:
                    cv2.putText(frame, "No objects detected", 
                              (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                # Show frame
                cv2.imshow("SPARC Object Detection", frame)
                
                # Check for quit
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    cv2.destroyAllWindows()
                    return
            
            # After 15 seconds, announce results
            cv2.destroyAllWindows()
            print("15 seconds completed. Announcing results...")
            if self.detected_objects_history:
                unique_objects = list(dict.fromkeys(self.detected_objects_history))
                announcement = self.generate_announcement(unique_objects)
                print(f"Announcing: {announcement}")
                self.announce_message(announcement)
            else:
                no_objects_msg = "I don't see any objects in the current view."
                print(f"Announcing: {no_objects_msg}")
                self.announce_message(no_objects_msg)
            
            # Reset history for next session
            self.detected_objects_history = []
            
        except KeyboardInterrupt:
            cv2.destroyAllWindows()
            self.detected_objects_history = []
            return
    
    def calculate_angle(self, A, B, C):
        """Calculate angle between three points"""
        BA = (A[0] - B[0], A[1] - B[1])
        BC = (C[0] - B[0], C[1] - B[1])
        magnitude_BA = math.sqrt(BA[0] ** 2 + BA[1] ** 2)
        magnitude_BC = math.sqrt(BC[0] ** 2 + BC[1] ** 2)
        if magnitude_BA == 0 or magnitude_BC == 0:
            return 0.0
        cosine_angle = (BA[0] * BC[0] + BA[1] * BC[1]) / (magnitude_BA * magnitude_BC)
        cosine_angle = max(-1.0, min(1.0, cosine_angle))
        angle = math.degrees(math.acos(cosine_angle))
        return angle
    
    def calculate_features(self, coords):
        """Calculate distance features from coordinates"""
        distances = []
        for i in range(len(coords)):
            for j in range(i + 1, len(coords)):
                distance = np.linalg.norm(np.array(coords[i]) - np.array(coords[j]))
                distances.append(distance)
        return distances
    
    def replace_multiple_spaces_with_single(self, sentence):
        """Clean up multiple spaces in sentence"""
        return re.sub(r'\s+', ' ', sentence).strip()
    
    def process_gesture_recognition(self, left_hand_coords, right_hand_coords):
        """Process gesture recognition from hand coordinates"""
        left_hand_angles = [self.calculate_angle(left_hand_coords[i - 1], left_hand_coords[i], left_hand_coords[i + 1])
                            if left_hand_coords[0] != (0, 0) else 0.0
                            for i in range(1, self.num_landmarks - 1)]
        right_hand_angles = [self.calculate_angle(right_hand_coords[i - 1], right_hand_coords[i], right_hand_coords[i + 1])
                             if right_hand_coords[0] != (0, 0) else 0.0
                             for i in range(1, self.num_landmarks - 1)]
        angles = left_hand_angles + right_hand_angles
        combined_coords = left_hand_coords + right_hand_coords
        features = self.calculate_features(combined_coords) + angles
        features_df = pd.DataFrame([features])
        current_time = time.time()
        if self.mode_switch_time and (current_time - self.mode_switch_time < 1.5):
            return "Waiting..."
        elif self.last_recognition_time and (current_time - self.last_recognition_time < 1.5):
            return "Waiting..."
        best_prediction = None
        best_prob = 0
        best_label = "No Gesture Detected"
        best_mode = None
        for mode, clf in self.models.items():
            label_map = self.label_maps[mode]
            probabilities = clf.predict_proba(features_df)
            max_prob = np.max(probabilities)
            if max_prob >= self.confidence_threshold and max_prob > best_prob:
                prediction = clf.predict(features_df)
                predicted_label = label_map.get(prediction[0], 'Unknown')
                best_prob = max_prob
                best_label = predicted_label
                best_mode = mode
        predicted_gesture = best_label
        if predicted_gesture != 'No Gesture Detected':
            if predicted_gesture == 'back_space':
                self.backspace_frame_counter += 1
                if self.backspace_frame_counter == 1:
                    if best_mode == 'words':
                        words = self.sentence.strip().split(' ')
                        if words:
                            self.sentence = ' '.join(words[:-1]) + ' '
                    else:
                        if self.sentence:
                            self.sentence = self.sentence[:-1]
                    print(f"Backspace applied. Current sentence: {self.sentence}")
                elif self.backspace_frame_counter > 1:
                    self.backspace_frame_counter = 0
            else:
                self.backspace_frame_counter = 0
                if predicted_gesture not in ['back_space', 'character', 'numbers', 'words']:
                    self.sentence += predicted_gesture
                    print(f"Added '{predicted_gesture}'. Current sentence: {self.sentence}")
                    self.last_recognition_time = current_time
        return predicted_gesture
    
    def run_gesture_recognition(self):
        """Run sign language translation until sentence is completed"""
        print("Starting gesture recognition mode...")
        
        # Check if camera is available (use same logic as object detection)
        if not hasattr(self, 'camera_available') or not self.camera_available:
            error_message = "Sorry, no camera is available for sign language translation. Please check your camera connection."
            print(f"Error: {error_message}")
            self.announce_message(error_message)
            return
        
        # Use the same camera as object detection
        if self.realsense_available:
            # Use RealSense camera
            cap = None
        else:
            # Use the same fallback camera as object detection
            cap = self.cap
        
        try:
            while self.running:
                # Get frame from camera (same method as object detection)
                ret, img = self.get_camera_frame()
                if not ret:
                    time.sleep(1)
                    continue
                self.frame_count += 1
                if self.frame_count % self.frame_skip != 0:
                    continue
                hands, img = self.detector.findHands(img, draw=True)
                left_hand_coords = [(0, 0)] * self.num_landmarks
                right_hand_coords = [(0, 0)] * self.num_landmarks
                current_gesture = "No Gesture Detected"
                if hands:
                    self.no_hand_frames = 0
                    self.out_of_frame_frames = 0
                    for hand in hands:
                        lmList = hand["lmList"]
                        handType = hand["type"]
                        if handType == "Left":
                            left_hand_coords = [(lm[0], lm[1]) for lm in lmList]
                        elif handType == "Right":
                            right_hand_coords = [(lm[0], lm[1]) for lm in lmList]
                    current_gesture = self.process_gesture_recognition(left_hand_coords, right_hand_coords)
                else:
                    self.no_hand_frames += 1
                    self.out_of_frame_frames += 1
                    if self.no_hand_frames >= 5 and self.current_mode in ['character', 'numbers']:
                        self.sentence += ' '
                        self.no_hand_frames = 0
                    self.sentence = self.replace_multiple_spaces_with_single(self.sentence)
                    if self.out_of_frame_frames >= 45:
                        if self.sentence.strip():
                            final_sentence = ' '.join(self.sentence.split())
                            print(f"Gesture sentence completed: {final_sentence}")
                            print(f"Announcing: {final_sentence}")
                            self.announce_message(final_sentence)
                            self.sentence = ""
                            self.update_display("Sentence completed!", "Ready for new input")
                            time.sleep(2)
                            # Return after sentence is completed and announced
                            cv2.destroyAllWindows()
                            return
                        self.out_of_frame_frames = 0
                cv2.putText(img, f"Gesture: {current_gesture}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                display_sentence = self.sentence if len(self.sentence) <= 50 else self.sentence[-47:] + "..."
                cv2.putText(img, f"Sentence: {display_sentence}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
                cv2.putText(img, f"Mode: {self.current_mode}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                hand_status = f"Hands Detected: {len(hands)}" if hands else "No Hands Detected"
                cv2.putText(img, hand_status, (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
                cv2.imshow("Hand Gesture Recognition - Camera Feed", img)
                self.update_display(self.sentence, current_gesture)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        except KeyboardInterrupt:
            if self.sentence.strip():
                final_sentence = ' '.join(self.sentence.split())
                print(f"Gesture sentence completed: {final_sentence}")
                print(f"Announcing: {final_sentence}")
                self.announce_message(final_sentence)
                self.update_display(final_sentence, "Final Output")
                time.sleep(3)
        finally:
            cv2.destroyAllWindows()
            # Don't release camera as it's shared with object detection
            self.sentence = ""  # Reset sentence
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if hasattr(self, 'pipeline') and self.realsense_available:
                self.pipeline.stop()
            if hasattr(self, 'cap') and hasattr(self, 'camera_available') and self.camera_available:
                self.cap.release()
            if self.disp:
                self.disp.clear()
                self.disp.module_exit()
        except:
            pass
    
    def run(self):
        """Main SPARC system loop"""
        print("SPARC System Starting...")
        
        # Show startup message first
        self.show_startup_message()
        self.welcome_message()
        
        print("System ready! Starting main loop...")
        
        while self.running:
            try:
                # Play ping sound and wait for input
                print("Playing ping sound...")
                self.play_ping_sound()
                time.sleep(0.5)
                
                # Get user input with 5 second timeout
                print("Waiting for user input (5 seconds)...")
                user_choice = self.get_user_input()
                
                if user_choice == 'object_detection':
                    print("User selected: Object Detection")
                    self.run_object_detection()
                    
                    # After object detection, play ping and wait for next input
                    print("Object detection completed. Playing ping...")
                    self.play_ping_sound()
                    time.sleep(0.5)
                    print("Waiting for next input (5 seconds)...")
                    next_input = self.get_voice_input(timeout=5)
                    
                    if any(keyword in next_input for keyword in ['hand gesture', 'gesture', 'sign language', 'translate gesture', '2']):
                        print("User selected: Gesture Recognition")
                        self.run_gesture_recognition()
                    elif any(keyword in next_input for keyword in ['what you can see', 'see', 'object detection', 'detect objects', '1']):
                        print("User selected: Object Detection again")
                        continue  # Run object detection again
                    else:
                        # No input or invalid input, continue with object detection
                        print("No valid input, continuing with object detection...")
                        continue
                        
                elif user_choice == 'gesture_recognition':
                    print("User selected: Gesture Recognition")
                    self.run_gesture_recognition()
                    
                    # After gesture recognition, play ping and wait for next input
                    print("Gesture recognition completed. Playing ping...")
                    self.play_ping_sound()
                    time.sleep(0.5)
                    print("Waiting for next input (5 seconds)...")
                    next_input = self.get_voice_input(timeout=5)
                    
                    if any(keyword in next_input for keyword in ['what you can see', 'see', 'object detection', 'detect objects', '1']):
                        print("User selected: Object Detection")
                        self.run_object_detection()
                    elif any(keyword in next_input for keyword in ['hand gesture', 'gesture', 'sign language', 'translate gesture', '2']):
                        print("User selected: Gesture Recognition again")
                        continue  # Run gesture recognition again
                    else:
                        # No input or invalid input, continue with gesture recognition
                        print("No valid input, continuing with gesture recognition...")
                        continue
                        
                else:  # invalid input
                    print("Invalid input received")
                    sorry_messages = [
                        "Sorry, currently this task is out of my range.",
                        "I'm not able to help with that right now.",
                        "That's beyond my current capabilities.",
                        "I can't assist with that task at the moment.",
                        "Sorry, I don't understand that request.",
                        "That's not something I can do right now."
                    ]
                    sorry_message = random.choice(sorry_messages)
                    print(f"Announcing: {sorry_message}")
                    self.announce_message(sorry_message)
                    
                    # Play ping and wait for next input
                    print("Playing ping...")
                    self.play_ping_sound()
                    time.sleep(0.5)
                    print("Waiting for next input (5 seconds)...")
                    continue
                    
            except KeyboardInterrupt:
                print("\nShutdown requested by user (Ctrl+C)")
                break
            except Exception as e:
                print(f"An error occurred: {e}")
                traceback.print_exc()
        
        print("Shutting down SPARC system...")
        self.cleanup()
        print("SPARC system stopped.")

if __name__ == "__main__":
    sparc_system = SPARCSystem()
    sparc_system.run()
