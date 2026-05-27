#!/usr/bin/python
# -*- coding:utf-8 -*-

"""
Test the fixed camera feed functionality
"""

import cv2
import time
from main import CameraManager

def test_camera_feed():
    """Test camera feed with the fixed CameraManager"""
    print("Testing fixed camera feed...")
    
    # Initialize camera manager
    camera_manager = CameraManager()
    
    if not camera_manager.camera_type:
        print("❌ No camera detected!")
        return False
    
    print(f"✅ Camera detected: {camera_manager.camera_type.upper()}")
    print("Starting camera feed test...")
    print("Press 'q' to quit")
    
    try:
        frame_count = 0
        while True:
            # Read frame from camera
            ret, frame = camera_manager.read_frame()
            if not ret:
                print("Could not read frame from camera.")
                time.sleep(1)
                continue
            
            frame_count += 1
            
            # Add overlay information
            height, width = frame.shape[:2]
            
            # Camera type info
            cv2.putText(frame, f"Camera: {camera_manager.camera_type.upper()}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Frame count
            cv2.putText(frame, f"Frames: {frame_count}", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            # Instructions
            cv2.putText(frame, "Press 'q' to quit", 
                       (10, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Display frame
            cv2.imshow('SPARC Camera Feed Test - Fixed', frame)
            
            # Check for key press
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            
            # Print status every 30 frames
            if frame_count % 30 == 0:
                print(f"✅ Camera feed working! Frames: {frame_count}")
            
    except KeyboardInterrupt:
        print("Camera feed stopped by user.")
    finally:
        cv2.destroyAllWindows()
        camera_manager.release()
    
    print(f"✅ Camera feed test completed! Total frames: {frame_count}")
    return True

if __name__ == "__main__":
    print("=" * 50)
    print("SPARC Camera Feed Test - Fixed Version")
    print("=" * 50)
    
    success = test_camera_feed()
    if success:
        print("\n🎉 Camera feed is working correctly!")
        print("You can now run the full SPARC system with: python main.py")
    else:
        print("\n❌ Camera feed test failed.")
    
    print("=" * 50)
