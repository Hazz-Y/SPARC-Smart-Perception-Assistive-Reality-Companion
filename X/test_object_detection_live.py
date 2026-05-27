#!/usr/bin/python
# -*- coding:utf-8 -*-

"""
Test object detection with live feed and bounding boxes
"""

import cv2
import time
from main import CameraManager
from ultralytics import YOLO

def test_object_detection_live():
    """Test object detection with live feed"""
    print("Testing object detection with live feed...")
    
    # Initialize camera manager
    camera_manager = CameraManager()
    
    if not camera_manager.camera_type:
        print("❌ No camera detected!")
        return False
    
    print(f"✅ Camera detected: {camera_manager.camera_type.upper()}")
    
    # Initialize YOLO
    try:
        print("Loading YOLO model...")
        yolo_model = YOLO('yolov8n.pt')
        print("✅ YOLO model loaded!")
    except Exception as e:
        print(f"❌ Failed to load YOLO: {e}")
        return False
    
    print("Starting object detection with live feed...")
    print("Press 'q' to quit")
    
    try:
        frame_count = 0
        while True:
            # Capture image from camera
            ret, frame = camera_manager.read_frame()
            if not ret:
                print("Could not read frame from camera.")
                time.sleep(1)
                continue
            
            frame_count += 1
            
            # Run YOLO detection on the frame
            results = yolo_model(frame)
            
            # Extract detected objects and draw bounding boxes
            current_objects = []
            annotated_frame = frame.copy()
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        class_id = int(box.cls[0])
                        confidence = float(box.conf[0])
                        if confidence > 0.5:  # Only high confidence detections
                            class_name = yolo_model.names[class_id]
                            current_objects.append(class_name)
                            
                            # Get bounding box coordinates
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                            
                            # Draw bounding box
                            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                            
                            # Draw label with confidence
                            label = f"{class_name}: {confidence:.2f}"
                            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
                            cv2.rectangle(annotated_frame, (x1, y1 - label_size[1] - 10), 
                                        (x1 + label_size[0], y1), (0, 255, 0), -1)
                            cv2.putText(annotated_frame, label, (x1, y1 - 5), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
            
            # Add overlay information
            height, width = annotated_frame.shape[:2]
            cv2.putText(annotated_frame, f"Objects: {len(current_objects)}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(annotated_frame, f"Frames: {frame_count}", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            cv2.putText(annotated_frame, "Press 'q' to quit", 
                       (10, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Display the annotated frame
            cv2.imshow('SPARC Object Detection Test - Live Feed', annotated_frame)
            
            # Print detection info
            if current_objects:
                unique_objects = list(dict.fromkeys(current_objects))
                print(f"Frame {frame_count}: Detected {unique_objects}")
            
            # Check for key press
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:  # 'q' or ESC
                break
            
    except KeyboardInterrupt:
        print("Object detection stopped by user.")
    finally:
        cv2.destroyAllWindows()
        camera_manager.release()
    
    print(f"✅ Object detection test completed! Total frames: {frame_count}")
    return True

if __name__ == "__main__":
    print("=" * 50)
    print("SPARC Object Detection - Live Feed Test")
    print("=" * 50)
    
    success = test_object_detection_live()
    if success:
        print("\n🎉 Object detection with live feed is working!")
        print("You can now run the full SPARC system with: python main.py")
    else:
        print("\n❌ Object detection test failed.")
    
    print("=" * 50)
