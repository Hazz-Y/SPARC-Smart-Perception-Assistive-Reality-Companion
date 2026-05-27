#!/usr/bin/env python3
"""
SPARC RealSense D455 - Object Detection with Distance Measurement
Uses both RGB and depth sensors simultaneously
"""

import cv2
import numpy as np
import pyrealsense2 as rs
from ultralytics import YOLO
import time
import os

class RealSenseObjectDetection:
    def __init__(self):
        """Initialize RealSense D455 with both RGB and depth sensors"""
        self.pipeline = None
        self.config = None
        self.yolo_model = None
        self.depth_scale = None
        
        # Initialize YOLO model
        self.setup_yolo()
        
        # Initialize RealSense
        self.setup_realsense()
    
    def setup_yolo(self):
        """Load YOLO model for object detection"""
        try:
            print("Loading YOLO model...")
            self.yolo_model = YOLO('yolov8n.pt')
            print("✅ YOLO model loaded successfully!")
        except Exception as e:
            print(f"❌ Failed to load YOLO model: {e}")
            self.yolo_model = None
    
    def setup_realsense(self):
        """Setup RealSense D455 with both RGB and depth streams"""
        try:
            print("Setting up RealSense D455...")
            
            # Try RealSense SDK first
            try:
                # Create pipeline and config
                self.pipeline = rs.pipeline()
                self.config = rs.config()
                
                # Get available devices
                ctx = rs.context()
                devices = ctx.query_devices()
                if len(devices) == 0:
                    print("❌ No RealSense devices found")
                    return False
                
                device = devices[0]
                print(f"✅ Using RealSense device: {device.get_info(rs.camera_info.name)}")
                
                # Configure both RGB and depth streams
                self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
                self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
                
                # Start streaming
                self.pipeline.start(self.config)
                
                # Test if we can get frames
                frames = self.pipeline.wait_for_frames(timeout_ms=5000)
                color_frame = frames.get_color_frame()
                depth_frame = frames.get_depth_frame()
                
                if color_frame and depth_frame:
                    print("✅ RealSense D455 SDK initialized successfully!")
                    print("✅ RGB and depth sensors active via SDK")
                    return True
                else:
                    print("❌ Failed to get frames from RealSense SDK")
                    self.pipeline.stop()
                    self.pipeline = None
                    
            except Exception as e:
                print(f"❌ RealSense SDK failed: {e}")
                if self.pipeline:
                    try:
                        self.pipeline.stop()
                    except:
                        pass
                    self.pipeline = None
            
            # Fallback: Use RealSense as USB camera for RGB
            print("🔄 Trying RealSense as USB camera...")
            for device_num in [0, 1, 2, 3, 4, 5, 6]:
                try:
                    print(f"Trying RealSense as USB camera on /dev/video{device_num}...")
                    self.cap = cv2.VideoCapture(device_num)
                    if self.cap.isOpened():
                        ret, frame = self.cap.read()
                        if ret and frame is not None:
                            height, width = frame.shape[:2]
                            if width >= 320 and height >= 240:
                                print(f"✅ RealSense D455 working as USB camera on /dev/video{device_num}!")
                                print(f"✅ Resolution: {width}x{height}")
                                print("⚠️  Note: Using RGB only (depth not available via USB)")
                                return True
                            else:
                                self.cap.release()
                        else:
                            self.cap.release()
                    else:
                        self.cap.release()
                except Exception as e:
                    print(f"RealSense USB camera test failed on /dev/video{device_num}: {e}")
                    if hasattr(self, 'cap'):
                        self.cap.release()
            
            print("❌ Could not initialize RealSense in any mode")
            return False
                
        except Exception as e:
            print(f"❌ Failed to setup RealSense: {e}")
            return False
    
    def get_distance_at_point(self, depth_frame, x, y):
        """Get distance at specific pixel coordinates"""
        try:
            # Get depth value at the point
            depth_value = depth_frame.get_distance(x, y)
            
            # Convert to millimeters
            distance_mm = depth_value * 1000
            
            return distance_mm
        except Exception as e:
            print(f"Error getting distance: {e}")
            return 0.0
    
    def draw_detection_with_distance(self, frame, depth_frame, results):
        """Draw bounding boxes with distance measurements"""
        annotated_frame = frame.copy()
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    # Get bounding box coordinates
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                    confidence = box.conf[0].cpu().numpy()
                    class_id = int(box.cls[0].cpu().numpy())
                    class_name = self.yolo_model.names[class_id]
                    
                    # Calculate center point for distance measurement
                    center_x = (x1 + x2) // 2
                    center_y = (y1 + y2) // 2
                    
                    # Get distance at center point
                    distance = self.get_distance_at_point(depth_frame, center_x, center_y)
                    
                    # Draw bounding box
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
                    # Prepare label with distance
                    if distance > 0:
                        label = f"{class_name}: {confidence:.2f} | {distance:.1f}mm"
                    else:
                        label = f"{class_name}: {confidence:.2f} | No depth"
                    
                    # Draw label background
                    label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                    cv2.rectangle(annotated_frame, (x1, y1 - label_size[1] - 10), 
                                (x1 + label_size[0], y1), (0, 255, 0), -1)
                    
                    # Draw label text
                    cv2.putText(annotated_frame, label, (x1, y1 - 5), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
                    
                    # Draw center point
                    cv2.circle(annotated_frame, (center_x, center_y), 5, (255, 0, 0), -1)
                    
                    # Draw distance line
                    cv2.line(annotated_frame, (center_x, center_y), (center_x, center_y - 20), (255, 0, 0), 2)
        
        return annotated_frame
    
    def draw_detection_without_distance(self, frame, results):
        """Draw bounding boxes without distance measurements (for USB mode)"""
        annotated_frame = frame.copy()
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    # Get bounding box coordinates
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                    confidence = box.conf[0].cpu().numpy()
                    class_id = int(box.cls[0].cpu().numpy())
                    class_name = self.yolo_model.names[class_id]
                    
                    # Draw bounding box
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
                    # Prepare label without distance
                    label = f"{class_name}: {confidence:.2f} (No depth)"
                    
                    # Draw label background
                    label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                    cv2.rectangle(annotated_frame, (x1, y1 - label_size[1] - 10), 
                                (x1 + label_size[0], y1), (0, 255, 0), -1)
                    
                    # Draw label text
                    cv2.putText(annotated_frame, label, (x1, y1 - 5), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
        return annotated_frame
    
    def run_detection(self):
        """Main detection loop with RGB and depth"""
        if not self.yolo_model:
            print("❌ YOLO model not initialized")
            return
        
        if not hasattr(self, 'pipeline') and not hasattr(self, 'cap'):
            print("❌ RealSense not initialized")
            return
        
        print("🚀 Starting object detection with distance measurement...")
        print("Press 'q' to quit, 's' to save current frame")
        
        frame_count = 0
        start_time = time.time()
        use_sdk = hasattr(self, 'pipeline') and self.pipeline is not None
        
        try:
            while True:
                if use_sdk:
                    # Use RealSense SDK
                    frames = self.pipeline.wait_for_frames()
                    color_frame = frames.get_color_frame()
                    depth_frame = frames.get_depth_frame()
                    
                    if not color_frame or not depth_frame:
                        continue
                    
                    # Convert to numpy arrays
                    color_image = np.asanyarray(color_frame.get_data())
                    depth_image = np.asanyarray(depth_frame.get_data())
                    
                    # Run YOLO detection
                    results = self.yolo_model(color_image, conf=0.5)
                    
                    # Draw detections with distance
                    annotated_frame = self.draw_detection_with_distance(color_image, depth_frame, results)
                    
                    # Create depth visualization
                    depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)
                    
                else:
                    # Use USB camera (RGB only)
                    ret, color_image = self.cap.read()
                    if not ret:
                        continue
                    
                    # Run YOLO detection
                    results = self.yolo_model(color_image, conf=0.5)
                    
                    # Draw detections without distance (depth not available)
                    annotated_frame = self.draw_detection_without_distance(color_image, results)
                    
                    # Create placeholder depth visualization
                    depth_colormap = np.zeros((color_image.shape[0], color_image.shape[1], 3), dtype=np.uint8)
                    cv2.putText(depth_colormap, "Depth not available via USB", (50, 240), 
                              cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                
                # Add frame info
                frame_count += 1
                elapsed_time = time.time() - start_time
                fps = frame_count / elapsed_time if elapsed_time > 0 else 0
                
                # Add info overlay
                mode_text = "SDK Mode" if use_sdk else "USB Mode (RGB only)"
                object_count = len(results[0].boxes) if results[0].boxes is not None else 0
                info_text = f"{mode_text} | FPS: {fps:.1f} | Objects: {object_count}"
                cv2.putText(annotated_frame, info_text, (10, 30), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                # Display frames
                cv2.imshow('SPARC - Object Detection with Distance', annotated_frame)
                cv2.imshow('SPARC - Depth Map', depth_colormap)
                
                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("🛑 Quitting...")
                    break
                elif key == ord('s'):
                    # Save current frame
                    timestamp = int(time.time())
                    cv2.imwrite(f'/home/pi/SPARC/detection_{timestamp}.jpg', annotated_frame)
                    cv2.imwrite(f'/home/pi/SPARC/depth_{timestamp}.jpg', depth_colormap)
                    print(f"💾 Saved frames: detection_{timestamp}.jpg, depth_{timestamp}.jpg")
                
        except KeyboardInterrupt:
            print("🛑 Interrupted by user")
        except Exception as e:
            print(f"❌ Error during detection: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        print("🧹 Cleaning up...")
        if hasattr(self, 'pipeline') and self.pipeline:
            try:
                self.pipeline.stop()
            except:
                pass
        if hasattr(self, 'cap') and self.cap:
            try:
                self.cap.release()
            except:
                pass
        cv2.destroyAllWindows()
        print("✅ Cleanup completed")

def main():
    """Main function"""
    print("=" * 60)
    print("SPARC RealSense D455 - Object Detection with Distance")
    print("=" * 60)
    
    # Create detection instance
    detector = RealSenseObjectDetection()
    
    # Run detection
    detector.run_detection()

if __name__ == "__main__":
    main()
