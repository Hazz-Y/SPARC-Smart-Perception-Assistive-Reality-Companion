import os
import cv2
import random
from ultralytics import YOLO
from gtts import gTTS
import time
import signal
import sys

# Global variables
detected_objects_history = []
running = True

# Signal handler for graceful shutdown
def signal_handler(sig, frame):
    global running
    print("\nShutting down gracefully...")
    running = False
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Load lightweight YOLO model
print("Loading YOLO model...")
model = YOLO('yolov8n.pt')  # nano version - smallest and fastest
print("YOLO model loaded successfully!")

# Initialize camera
print("Initializing camera...")
cam = cv2.VideoCapture(0)
if not cam.isOpened():
    print("Could not open camera.")
    exit(1)

# Generate varied announcement sentences
def generate_announcement(objects):
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
        # For 3 or more objects
        first_part = ", ".join(objects[:-1])
        last_object = objects[-1]
        templates = [
            f"I can see {first_part}, and a {last_object}.",
            f"There are {first_part}, and a {last_object} in the image.",
            f"I detect {first_part}, and a {last_object}.",
            f"I can make out {first_part}, and a {last_object} here."
        ]
    
    return random.choice(templates)

# Function to announce objects
def announce_objects():
    global detected_objects_history
    
    if not detected_objects_history:
        announcement = "No objects detected yet."
    else:
        # Get unique objects from history
        unique_objects = list(dict.fromkeys(detected_objects_history))
        announcement = generate_announcement(unique_objects)
    
    print(f"Announcing: {announcement}")
    
    try:
        tts = gTTS(text=announcement, lang='en')
        filename = '/tmp/tts_output.mp3'
        tts.save(filename)
        os.system(f'mpg123 "{filename}" > /dev/null 2>&1')
        os.remove(filename)
        print("Announcement completed!")
    except Exception as e:
        print(f"TTS error: {e}")

# Main continuous loop
print("Starting continuous object detection...")
print("Press Ctrl+C to stop")
print("Announcing every 5 seconds...")

last_announcement_time = time.time()

try:
    while running:
        # Capture image from camera
        ret, frame = cam.read()
        if not ret:
            print("Could not read frame from camera.")
            time.sleep(1)
            continue
        
        # Save image
        image_path = '/home/pi/SPARC/camera_snapshot.jpg'
        cv2.imwrite(image_path, frame)
        
        # Run YOLO detection
        results = model(image_path)
        
        # Extract detected objects
        current_objects = []
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    if confidence > 0.5:  # Only high confidence detections
                        class_name = model.names[class_id]
                        current_objects.append(class_name)
        
        # Add to history
        detected_objects_history.extend(current_objects)
        
        # Print current detection
        if current_objects:
            unique_current = list(dict.fromkeys(current_objects))
            print(f"Current detection: {unique_current}")
        else:
            print("No objects detected in current frame")
        
        # Announce every 5 seconds
        current_time = time.time()
        if current_time - last_announcement_time >= 5.0:
            announce_objects()
            last_announcement_time = current_time
        
        # Small delay to prevent excessive CPU usage
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\nStopping...")
finally:
    cam.release()
    print("Camera released. Goodbye!")