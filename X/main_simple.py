#!/usr/bin/python
# -*- coding:utf-8 -*-
#
# SPARC System - Simplified version for testing
# Works with USB camera and OLED display

import os
import sys
import time
import cv2
import numpy as np
import logging
import traceback
from PIL import Image, ImageDraw, ImageFont
import signal

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
        
        # Initialize camera
        self.setup_camera()
        
        # Variables
        self.running = True
        
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
            print("OLED library not available - display functionality disabled")
            return
        try:
            print("Initializing OLED display...")
            self.disp = OLED_1in32.OLED_1in32()
            print("1.32inch OLED object created")
            self.disp.Init()
            print("OLED display initialized")
            self.disp.clear()
            print("OLED display cleared")
            
            # Setup fonts with fallback options
            try:
                self.font_small = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 12)
                self.font_medium = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 14)
                self.font_large = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 16)
                print("Loaded custom fonts from Font.ttc")
            except Exception as e:
                print(f"Failed to load custom fonts: {e}")
                try:
                    self.font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
                    self.font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
                    self.font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
                    print("Loaded system DejaVu fonts")
                except Exception as e2:
                    print(f"Failed to load system fonts: {e2}")
                    self.font_small = ImageFont.load_default()
                    self.font_medium = ImageFont.load_default()
                    self.font_large = ImageFont.load_default()
                    print("Using default PIL font")
            
            print("OLED display setup completed successfully")
        except Exception as e:
            print(f"Failed to initialize OLED: {e}")
            import traceback
            traceback.print_exc()
            self.disp = None
    
    def setup_camera(self):
        """Initialize USB camera"""
        self.camera_available = False
        self.cap = None
        
        print("Trying to find USB camera...")
        available_devices = [0, 1, 2, 10, 11, 12, 20, 21, 22, 23, 24, 25, 19, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35]
        
        for device_num in available_devices:
            try:
                print(f"Trying camera device {device_num}...")
                self.cap = cv2.VideoCapture(device_num)
                if self.cap.isOpened():
                    # Test if we can read a frame
                    ret, frame = self.cap.read()
                    if ret and frame is not None:
                        print(f"Successfully opened camera device {device_num}")
                        self.camera_available = True
                        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                        self.cap.set(cv2.CAP_PROP_FPS, 15)
                        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                        print("USB camera initialized successfully")
                        return
                    else:
                        print(f"Camera device {device_num} opened but couldn't read frame")
                        self.cap.release()
                        self.cap = None
                else:
                    print(f"Could not open camera device {device_num}")
                    if self.cap:
                        self.cap.release()
                        self.cap = None
            except Exception as e:
                print(f"Error testing camera device {device_num}: {e}")
                if self.cap:
                    self.cap.release()
                    self.cap = None
        
        # If we get here, no camera was found
        print("No working camera found - camera features will be disabled")
        self.camera_available = False
    
    def get_camera_frame(self):
        """Get frame from camera"""
        if self.camera_available and self.cap:
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
            line_height = 16
            total_height = len(startup_lines) * line_height
            start_y = (self.disp.height - total_height) // 2
            for i, line in enumerate(startup_lines):
                try:
                    bbox = draw.textbbox((0, 0), line, font=self.font_medium)
                    text_width = bbox[2] - bbox[0]
                except AttributeError:
                    text_width, _ = draw.textsize(line, font=self.font_medium)
                x_pos = (self.disp.width - text_width) // 2
                y_pos = start_y + (i * line_height)
                draw.text((x_pos, y_pos), line, font=self.font_medium, fill=255)
            self.disp.ShowImage(self.disp.getbuffer(image))
            time.sleep(3)
        except Exception as e:
            logging.error(f"Error showing startup message: {e}")
    
    def show_welcome_display(self):
        """Display welcome message on OLED"""
        if not self.disp:
            return
        try:
            image = Image.new('L', (self.disp.width, self.disp.height), 0)
            draw = ImageDraw.Draw(image)
            
            welcome_lines = [
                "Hello. I",
                "am SPARC",
                "Initializing...."
            ]
            
            line_height = 16
            total_height = len(welcome_lines) * line_height
            start_y = max(2, (self.disp.height - total_height) // 2)
            
            for i, line in enumerate(welcome_lines):
                try:
                    bbox = draw.textbbox((0, 0), line, font=self.font_large)
                    text_width = bbox[2] - bbox[0]
                except AttributeError:
                    text_width, _ = draw.textsize(line, font=self.font_large)
                x_pos = (self.disp.width - text_width) // 2
                y_pos = start_y + (i * line_height)
                draw.text((x_pos, y_pos), line, font=self.font_large, fill=255)
            
            self.disp.ShowImage(self.disp.getbuffer(image))
            time.sleep(4)
        except Exception as e:
            logging.error(f"Error showing welcome display: {e}")
    
    def test_camera(self):
        """Test camera functionality"""
        if not self.camera_available:
            print("No camera available for testing")
            return
        
        print("Testing camera for 10 seconds...")
        start_time = time.time()
        
        try:
            while self.running and (time.time() - start_time) < 10:
                ret, frame = self.get_camera_frame()
                if ret:
                    cv2.putText(frame, "SPARC Camera Test", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.putText(frame, f"Time: {int(time.time() - start_time)}s", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                    cv2.imshow("SPARC Camera Test", frame)
                    
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                else:
                    print("Failed to read frame from camera")
                    time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            cv2.destroyAllWindows()
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.cap and self.camera_available:
                print("Releasing camera...")
                self.cap.release()
                print("Camera released successfully")
            
            if self.disp:
                print("Clearing OLED display...")
                self.disp.clear()
                self.disp.module_exit()
                print("OLED display cleaned up successfully")
                
        except Exception as e:
            print(f"Error during cleanup: {e}")
    
    def run(self):
        """Main SPARC system loop"""
        print("SPARC System Starting...")
        
        # Show startup message first
        self.show_startup_message()
        self.show_welcome_display()
        
        print("System ready!")
        print(f"Camera available: {self.camera_available}")
        print(f"OLED available: {self.disp is not None}")
        
        if self.camera_available:
            print("Testing camera...")
            self.test_camera()
        else:
            print("No camera available - skipping camera test")
        
        print("SPARC system test completed.")

if __name__ == "__main__":
    sparc_system = SPARCSystem()
    sparc_system.run()

