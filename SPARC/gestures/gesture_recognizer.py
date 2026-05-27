"""
Gesture Recognizer for SPARC
Recognizes hand gestures, builds sentences, updates OLED if provided.
"""
import logging
import os
import time
import cv2
import numpy as np
import random
import string
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
from cvzone.HandTrackingModule import HandDetector
from SPARC.core.model_handler import ModelHandler
from SPARC.utils.geometry import pre_process_landmark, replace_multiple_spaces_with_single
from SPARC.emotions.emotion_detector import EmotionDetector

# Emotion to emoji mapping
EMOTION_EMOJI_MAP = {
    'Angry': '😡',
    'Happy': '😄',
    'Neutral': '😐',
    'Sad': '😢',
    'No Face': ''
}

class GestureRecognizer:
    def __init__(self, display_service=None, audio_service=None, language_mode='ISL'):
        """
        Initialize GestureRecognizer
        """
        self.logger = logging.getLogger('GestureRecognizer')
        self.display = display_service
        self.audio = audio_service
        self.language_mode = language_mode.upper()
        
        # Initialize Model Handler
        self.model_handler = ModelHandler(self.language_mode)
        
        # Hand Detector
        self.detector = HandDetector(staticMode=False, maxHands=2, modelComplexity=0, detectionCon=0.7, minTrackCon=0.5)
        self.num_landmarks = 21
        
        self.sentence = ""
        self.no_hand_frames = 0
        self.backspace_frame_counter = 0
        self.mode_switch_time = None
        self.last_recognition_time = None
        self.out_of_frame_frames = 0
        self.current_mode = 'numbers' # Default mode
        self.confidence_threshold = 0.40
        
        # Define number and character sets for filtering
        self.numbers_set = set(['1', '2', '3', '4', '5', '6', '7', '8', '9'])
        self.characters_set = set(string.ascii_uppercase)
        
        self.frame_count = 0
        self.cap = None
        
        # Timing
        self.last_gesture_detection_time = 0
        self.last_sentence_update_time = 0
        self.detection_interval = 1.0
        self.sentence_update_interval = 1.0
        
        self.current_gesture = "No Gesture Detected"
        self.display_sentence = ""
        
        # Initialize emotion detector
        try:
            from SPARC.emotions.emotion_detector import EmotionDetector
            self.emotion_detector = EmotionDetector()
            self.logger.info("Emotion detector initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize emotion detector: {e}")
            self.emotion_detector = None
            
        self.stored_emotion = "Neutral"
        self.last_emotion_update_time = 0
        self.emotion_update_interval = 1.0
        
        self.pending_gesture = None
        self.last_detection_added_time = 0
        self.min_detection_interval = 1.0

    def update_display(self, sentence, current_gesture=""):
        if not self.display:
            return
        lines = []
        
        clean_sentence = replace_multiple_spaces_with_single(sentence)
        words = clean_sentence.split()
        
        # Measure text width logic
        font = getattr(self.display, 'font_large', None) or getattr(self.display, 'font_medium', None)
        if not font: font = ImageFont.load_default()
        
        temp_img = Image.new('1', (self.display.width, self.display.height), 255)
        temp_draw = ImageDraw.Draw(temp_img)
        
        def measure_text(text):
            try:
                bbox = temp_draw.textbbox((0, 0), text, font=font)
                return bbox[2] - bbox[0]
            except AttributeError:
                w, _ = font.getsize(text)
                return w
            except:
                return len(text) * 8
                
        def break_long_word(word, max_w):
            if not word: return []
            chunks = []
            current_chunk = ""
            for char in word:
                test_chunk = current_chunk + char
                if measure_text(test_chunk) <= max_w:
                    current_chunk = test_chunk
                else:
                    if current_chunk: chunks.append(current_chunk)
                    current_chunk = char if measure_text(char) <= max_w else ""
            if current_chunk: chunks.append(current_chunk)
            return chunks if chunks else [word]

        max_width = self.display.width - 8
        current_line = ""
        
        for word in words:
            word_width = measure_text(word)
            if word_width > max_width:
                word_chunks = break_long_word(word, max_width)
                for chunk in word_chunks:
                    if current_line:
                        lines.append(current_line)
                        current_line = ""
                    lines.append(chunk)
                continue
            
            test_line = current_line + " " + word if current_line else word
            if measure_text(test_line) <= max_width:
                current_line = test_line
            else:
                if current_line: lines.append(current_line)
                current_line = word
        
        if current_line: lines.append(current_line)
        
        max_sentence_lines = 3
        if len(lines) > max_sentence_lines:
            lines = lines[-max_sentence_lines:]
            
        mode_line = f"{self.language_mode} Mode: {self.current_mode.upper()}"
        mode_width = measure_text(mode_line)
        if mode_width > max_width:
           truncated = mode_line
           while measure_text(truncated + "...") > max_width and len(truncated) > 5:
               truncated = truncated[:-1]
           mode_line = truncated + "..." if len(truncated) < len(mode_line) else mode_line
           
        gesture_line = None
        if current_gesture and current_gesture != "No Gesture Detected":
            gesture_line = f">> {current_gesture}"
            gesture_width = measure_text(gesture_line)
            if gesture_width > max_width:
                truncated = gesture_line
                while measure_text(truncated + "...") > max_width and len(truncated) > 5:
                    truncated = truncated[:-1]
                gesture_line = truncated + "..." if len(truncated) < len(gesture_line) else gesture_line

        if gesture_line:
            if len(lines) > 1: lines = lines[-1:]
            lines.append(mode_line)
            lines.append(gesture_line)
        else:
            if len(lines) > 2: lines = lines[-2:]
            lines.append(mode_line)

        self.display.show_lines(lines, large=True, border=True)

    def display_array_characters(self):
        """Display current sentence with emotion emoji using display_pic2.py config"""
        if not self.display or not self.display.oled:
            self.logger.warning("Display not available for array display")
            return
        
        try:
            width, height = self.display.width, self.display.height
            emoji = EMOTION_EMOJI_MAP.get(self.stored_emotion, '')
            lines = []
            words = self.display_sentence.split() if self.display_sentence else []
            current_line = ""
            emoji_space = 40 if emoji else 0  
            max_width = width - 8 - emoji_space  
            
            font = getattr(self.display, 'font_large', None) or getattr(self.display, 'font_medium', None)
            if not font: font = ImageFont.load_default()
            
            temp_img = Image.new('1', (width, height), 255)
            temp_draw = ImageDraw.Draw(temp_img)
            
            def measure_text(text):
                try:
                    bbox = temp_draw.textbbox((0, 0), text, font=font)
                    return bbox[2] - bbox[0]
                except AttributeError:
                    w, _ = font.getsize(text)
                    return w
                except:
                   return len(text) * 8
            
            def break_long_word(word, max_w):
                if not word: return []
                chunks = []
                current_chunk = ""
                for char in word:
                    test_chunk = current_chunk + char
                    if measure_text(test_chunk) <= max_w:
                        current_chunk = test_chunk
                    else:
                        if current_chunk: chunks.append(current_chunk)
                        current_chunk = char if measure_text(char) <= max_w else ""
                if current_chunk: chunks.append(current_chunk)
                return chunks if chunks else [word]

            for word in words:
                word_width = measure_text(word)
                if word_width > max_width:
                    word_chunks = break_long_word(word, max_width)
                    for chunk in word_chunks:
                        if current_line:
                            lines.append(current_line)
                            current_line = ""
                        lines.append(chunk)
                    continue
                
                test_line = current_line + " " + word if current_line else word
                if measure_text(test_line) <= max_width:
                    current_line = test_line
                else:
                    if current_line: lines.append(current_line)
                    current_line = word
            
            if current_line: lines.append(current_line)
            
            if len(lines) > 3: lines = lines[-3:]
            
            info_image = Image.new('1', (width, height), 255) 
            draw_array = ImageDraw.Draw(info_image)
            
            array_font = getattr(self.display, 'font_large', None)
            if not array_font:        
                # Fallback
                picdir = '/home/pi/OLED_Module_Code/OLED_Module_Code/RaspberryPi/python/pic'
                try:
                    font_path = os.path.join(picdir, 'Font.ttc')
                    if os.path.exists(font_path):
                        array_font = ImageFont.truetype(font_path, 16)
                    else:
                        array_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
                except:
                     array_font = ImageFont.load_default()

            emoji_font = None
            emoji_font_paths = [
                "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
                "/usr/share/fonts/truetype/noto/NotoEmoji-Regular.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            ]
            for font_path in emoji_font_paths:
                try:
                    if os.path.exists(font_path):
                        emoji_font = ImageFont.truetype(font_path, 32)
                        break
                except: continue
            if emoji_font is None: emoji_font = ImageFont.load_default()
            
            emoji_size = 32
            line_height = getattr(self.display, 'line_h_large', 18)
            total_height = line_height * len(lines) if lines else line_height
            start_y = max(0, (height - total_height) // 2)
            
            if emoji and emoji_font:
                emoji_x = 4
                emoji_y = start_y + (total_height - emoji_size) // 2
                try:
                     draw_array.text((emoji_x, emoji_y), emoji, font=emoji_font, fill=0)
                except: pass
            
            text_start_x = (emoji_size + 8) if emoji else 0
            
            for i, line in enumerate(lines):
                y_pos = start_y + (i * line_height)
                
                try:
                    bbox = draw_array.textbbox((0, 0), line, font=array_font)
                    text_width = bbox[2] - bbox[0]
                except: text_width = len(line) * 8
                
                available_width = width - text_start_x - 4 if emoji else width - 8
                
                if text_width > available_width:
                     # Simple truncation logic same as before (omitted for brevity, assume simple truncate)
                     # Actually better to replicate fully for robustness
                     truncated = line
                     while True:
                         try:
                            bbox = draw_array.textbbox((0, 0), truncated + "...", font=array_font)
                            test_w = bbox[2] - bbox[0]
                         except: test_w = len(truncated + "...") * 8
                         if test_w <= available_width or len(truncated) <= 3: break
                         truncated = truncated[:-1]
                     line = truncated + "..." if len(truncated) < len(line) else line
                     try:
                        bbox = draw_array.textbbox((0, 0), line, font=array_font)
                        text_width = bbox[2] - bbox[0]
                     except: text_width = len(line) * 8

                if emoji:
                    x_pos = text_start_x
                    if text_width < available_width:
                        x_pos = text_start_x + (available_width - text_width) // 2
                else:
                    x_pos = max(0, (width - text_width) // 2)
                    
                x_pos = max(0, min(x_pos, width - text_width - 4))
                
                try:
                    for dx, dy in [(0, 0), (1, 0), (0, 1), (1, 1)]:
                        draw_array.text((x_pos + dx, y_pos + dy), line, font=array_font, fill=0)
                except Exception as e:
                     self.logger.warning(f"Error drawing text: {e}")

            # Transformations
            info_image = info_image.transpose(Image.FLIP_LEFT_RIGHT)
            info_image = info_image.transpose(Image.FLIP_TOP_BOTTOM)
            info_image = info_image.transpose(Image.ROTATE_180)
            
            self.display.oled.ShowImage(self.display.oled.getbuffer(info_image))
            time.sleep(5)
            self.update_display(self.display_sentence, self.current_gesture)
            
        except Exception as e:
            self.logger.error(f"Error displaying array characters: {e}")
            try: self.update_display(self.display_sentence, self.current_gesture)
            except: pass

    def announce_sentence(self, sentence):
        try:
            folder = '/tmp/audio'
            os.makedirs(folder, exist_ok=True)
            filename = ''.join(random.choice(string.ascii_lowercase) for _ in range(8)) + '.mp3'
            file_path = os.path.join(folder, filename)
            tts = gTTS(text=sentence, lang='en')
            tts.save(file_path)
            os.system(f'mpg123 "{file_path}" > /dev/null 2>&1')
            os.remove(file_path)
        except Exception as e:
            self.logger.error(f"Audio playback error: {e}")

    def process_gesture_recognition(self, left_hand_coords, right_hand_coords):
        """
        Process gesture recognition using ModelHandler.
        """
        best_label = "No Gesture Detected"
        best_prob = 0
        
        # Words Mode removed

        for hand_coords in [left_hand_coords, right_hand_coords]:
            if hand_coords and hand_coords[0] != (0, 0):
                preprocessed = pre_process_landmark([[c[0], c[1]] for c in hand_coords])
                
                if self.language_mode == 'ISL':
                    label, prob = self.model_handler.predict_isl(preprocessed)
                    if prob >= self.confidence_threshold and prob > best_prob:
                            # Filter
                            if self.current_mode == 'numbers' and label in self.numbers_set:
                                best_prob = prob
                                best_label = label
                            elif self.current_mode == 'characters' and label in self.characters_set:
                                best_prob = prob
                                best_label = label
                                
                elif self.language_mode == 'ASL':
                        if self.current_mode == 'numbers':
                            label, prob = self.model_handler.predict_asl_numbers(preprocessed)
                            if prob >= self.confidence_threshold and prob > best_prob:
                                best_prob = prob
                                best_label = label
                        elif self.current_mode == 'characters':
                            label, prob = self.model_handler.predict_asl_characters(preprocessed)
                            if prob >= self.confidence_threshold and prob > best_prob:
                                best_prob = prob
                                best_label = label
                                 
        predicted_gesture = best_label
        if predicted_gesture != 'No Gesture Detected':
            if predicted_gesture != 'back_space':
                self.backspace_frame_counter = 0
            self.last_recognition_time = time.time()
            
        return predicted_gesture

    # Copy of run_until_sentence (mostly unchanged logic, just reference self.process_gesture_recognition)
    def run_until_sentence(self, camera=None, window_name="SPARC Gesture") -> str:
        self.logger.info("Gesture recognition with OLED display and audio announcement started.")
        if camera is None:
            self.cap = cv2.VideoCapture(0)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        else:
            self.cap = camera
            
        self.sentence = ""
        self.display_sentence = ""
        self.current_gesture = "No Gesture Detected"
        self.pending_gesture = None
        self.no_hand_frames = 0
        self.out_of_frame_frames = 0
        self.last_gesture_detection_time = time.time()
        self.last_sentence_update_time = time.time()
        self.last_emotion_update_time = time.time()
        
        try:
            while True:
                if camera is None:
                    success, img = self.cap.read()
                else:
                    success, img = self.cap.get_frame()
                if not success or img is None: continue
                
                hands, img = self.detector.findHands(img, draw=True)
                current_time = time.time()
                
                if current_time - self.last_gesture_detection_time >= self.detection_interval:
                    left_hand_coords = [(0, 0)] * self.num_landmarks
                    right_hand_coords = [(0, 0)] * self.num_landmarks
                    
                    if hands:
                        self.no_hand_frames = 0
                        self.out_of_frame_frames = 0
                        for hand in hands:
                            lmList = hand["lmList"]
                            handType = hand["type"]
                            if handType == "Left": left_hand_coords = [(lm[0], lm[1]) for lm in lmList]
                            elif handType == "Right": right_hand_coords = [(lm[0], lm[1]) for lm in lmList]
                            
                        detected_gesture = self.process_gesture_recognition(left_hand_coords, right_hand_coords)
                        self.current_gesture = detected_gesture
                        if detected_gesture != "No Gesture Detected":
                            self.pending_gesture = detected_gesture
                    else:
                        self.no_hand_frames += 1
                        self.out_of_frame_frames += 1
                        self.current_gesture = "No Gesture Detected"
                        self.pending_gesture = None
                        
                        if self.out_of_frame_frames >= 45 and self.sentence.strip():
                            final_sentence = ' '.join(self.sentence.split())
                            self.announce_sentence(final_sentence)
                            self.update_display("Sentence completed!", "Ready for new input")
                            time.sleep(2)
                            cv2.destroyAllWindows()
                            if camera is None and self.cap: self.cap.release()
                            return final_sentence
                            
                    self.last_gesture_detection_time = current_time

                if current_time - self.last_sentence_update_time >= self.sentence_update_interval:
                    self.display_sentence = self.sentence
                    self.last_sentence_update_time = current_time

                if self.emotion_detector and current_time - self.last_emotion_update_time >= self.emotion_update_interval:
                     try:
                        det = self.emotion_detector.detect_emotion(img)
                        det = det.replace('?', '').strip()
                        if det != "No Face": self.stored_emotion = det
                     except: pass
                     self.last_emotion_update_time = current_time

                # Display Logic (OpenCV)
                mode_display = f"{self.language_mode} Mode: {self.current_mode.upper()}"
                cv2.putText(img, mode_display, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                cv2.putText(img, f"Gesture: {self.current_gesture}", (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # ... (Rest of OpenCV display logic roughly same) ...
                cv2.imshow(window_name, img)
                self.update_display(self.display_sentence, self.current_gesture)
                
                key = cv2.waitKey(10) & 0xFF
                if key != 255:
                    if key == ord('q') or key == ord('Q'):
                        return self.sentence
                    elif key == ord('n') or key == ord('N'): self.current_mode = 'numbers'
                    elif key == ord('c') or key == ord('C'): self.current_mode = 'characters'

                    elif key == ord('x') or key == ord('X'):
                        # Clear all
                        self.sentence = ""
                        self.display_sentence = ""
                        self.last_sentence_update_time = current_time
                    elif key == ord('s') or key == ord('S'):
                        # Backspace
                        if self.sentence:
                            self.sentence = self.sentence[:-1]
                            self.display_sentence = self.sentence
                            self.last_sentence_update_time = current_time
                    elif key == ord('a') or key == ord('A'):
                        # Announce
                        if self.sentence.strip():
                            final_sentence = ' '.join(self.sentence.split())
                            self.display_array_characters()
                            self.announce_sentence(final_sentence)
                            self.sentence = ""
                            self.display_sentence = ""
                            self.last_sentence_update_time = current_time
                    elif key == 13: # Enter
                        if self.pending_gesture and self.pending_gesture != "No Gesture Detected":
                             if current_time - self.last_detection_added_time >= self.min_detection_interval:
                                 if self.pending_gesture == 'back_space': self.sentence = self.sentence[:-1]
                                 else:

                                     self.sentence += self.pending_gesture
                                 self.last_detection_added_time = current_time
        finally:
             cv2.destroyAllWindows()
             if camera is None and self.cap: self.cap.release()
        return ""
