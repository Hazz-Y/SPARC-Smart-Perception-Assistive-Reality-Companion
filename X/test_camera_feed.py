#!/usr/bin/python
# -*- coding:utf-8 -*-

"""
Simple test script for camera feed functionality
Tests both webcam and RealSense without OLED dependencies
"""

import cv2
import numpy as np
import pyrealsense2 as rs
import sys
import time

class SimpleCameraManager:
    def __init__(self):
        self.camera_type = None
        self.cap = None
        self.pipeline = None
        self.config = None
        self.detect_camera()
    
    def detect_camera(self):
        """Detect available camera type"""
        # Try RealSense first
        try:
            ctx = rs.context()
            devices = ctx.query_devices()
            if len(devices) > 0:
                print("RealSense D455 detected!")
                self.camera_type = "realsense"
                self.setup_realsense()
                if self.camera_type == "realsense":
                    return
                else:
                    print("RealSense setup failed, trying webcam...")
        except Exception as e:
            print(f"RealSense not available: {e}")
        
        # Fallback to USB webcam
        try:
            self.cap = cv2.VideoCapture(0)
            if self.cap.isOpened():
                # Test if we can actually read a frame
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    self.camera_type = "webcam"
                    print("USB Webcam detected and working!")
                    return
                else:
                    print("Webcam detected but cannot read frames")
                    self.cap.release()
        except Exception as e:
            print(f"Webcam not available: {e}")
        
        print("No working camera detected!")
        self.camera_type = None
    
    def setup_realsense(self):
        """Setup RealSense D455"""
        try:
            self.pipeline = rs.pipeline()
            self.config = rs.config()
            
            # Configure streams
            self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
            self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
            
            # Start streaming
            self.pipeline.start(self.config)
            print("RealSense D455 initialized successfully!")
            
        except Exception as e:
            print(f"Failed to setup RealSense: {e}")
            self.camera_type = None
    
    def read_frame(self):
        """Read frame from appropriate camera"""
        if self.camera_type == "realsense":
            return self.read_realsense_frame()
        elif self.camera_type == "webcam":
            return self.read_webcam_frame()
        else:
            return False, None
    
    def read_realsense_frame(self):
        """Read frame from RealSense"""
        try:
            frames = self.pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()
            if not color_frame:
                return False, None
            
            # Convert to numpy array
            color_image = np.asanyarray(color_frame.get_data())
            return True, color_image
            
        except Exception as e:
            print(f"Error reading RealSense frame: {e}")
            return False, None
    
    def read_webcam_frame(self):
        """Read frame from USB webcam"""
        try:
            ret, frame = self.cap.read()
            return ret, frame
        except Exception as e:
            print(f"Error reading webcam frame: {e}")
            return False, None
    
    def get_depth_frame(self):
        """Get depth frame (RealSense only)"""
        if self.camera_type != "realsense":
            return None
        
        try:
            frames = self.pipeline.wait_for_frames()
            depth_frame = frames.get_depth_frame()
            if depth_frame:
                return np.asanyarray(depth_frame.get_data())
        except Exception as e:
            print(f"Error reading depth frame: {e}")
        return None
    
    def release(self):
        """Release camera resources"""
        if self.camera_type == "realsense" and self.pipeline:
            self.pipeline.stop()
        elif self.camera_type == "webcam" and self.cap:
            self.cap.release()

def test_camera_feed():
    """Test camera feed functionality"""
    print("=" * 50)
    print("SPARC Camera Feed Test")
    print("=" * 50)
    
    # Initialize camera
    camera_manager = SimpleCameraManager()
    
    if not camera_manager.camera_type:
        print("❌ No camera detected!")
        return False
    
    print(f"✅ Camera detected: {camera_manager.camera_type.upper()}")
    print("Starting camera feed...")
    print("Press 'q' to quit, '1'=Object Detection, '2'=Gesture Recognition")
    
    try:
        while True:
            # Read frame from camera
            ret, frame = camera_manager.read_frame()
            if not ret:
                print("Could not read frame from camera.")
                time.sleep(1)
                continue
            
            # Add overlay information
            height, width = frame.shape[:2]
            
            # Camera type info
            cv2.putText(frame, f"Camera: {camera_manager.camera_type.upper()}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Instructions
            cv2.putText(frame, "Press 'q' to quit, '1'=Objects, '2'=Signs", 
                       (10, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Add depth info if RealSense
            if camera_manager.camera_type == "realsense":
                depth_frame = camera_manager.get_depth_frame()
                if depth_frame is not None:
                    center_y, center_x = depth_frame.shape[0] // 2, depth_frame.shape[1] // 2
                    depth_value = depth_frame[center_y, center_x]
                    cv2.putText(frame, f"Depth: {depth_value}mm", 
                               (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            # Display frame
            cv2.imshow('SPARC Camera Feed Test', frame)
            
            # Check for key press
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('1'):
                print("Object Detection mode would start here...")
            elif key == ord('2'):
                print("Gesture Recognition mode would start here...")
            
    except KeyboardInterrupt:
        print("Camera feed stopped by user.")
    finally:
        cv2.destroyAllWindows()
        camera_manager.release()
    
    print("✅ Camera feed test completed successfully!")
    return True

if __name__ == "__main__":
    success = test_camera_feed()
    if success:
        print("\n🎉 Camera integration is working correctly!")
        print("You can now run the full SPARC system with: python main.py")
    else:
        print("\n❌ Camera test failed. Please check your camera connection.")
    
    print("=" * 50)
