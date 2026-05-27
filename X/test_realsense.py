#!/usr/bin/python
# -*- coding:utf-8 -*-

"""
Test script for RealSense D455 integration
Run this script to test if your RealSense D455 is properly detected
"""

import pyrealsense2 as rs
import numpy as np
import cv2
import sys

def test_realsense():
    """Test RealSense D455 detection and basic functionality"""
    print("Testing Intel RealSense D455...")
    
    try:
        # Create context and query devices
        ctx = rs.context()
        devices = ctx.query_devices()
        
        if len(devices) == 0:
            print("❌ No RealSense devices found!")
            print("Please make sure your RealSense D455 is connected via USB 3.0")
            return False
        
        print(f"✅ Found {len(devices)} RealSense device(s)")
        
        # Get device info
        for i, device in enumerate(devices):
            print(f"Device {i}: {device.get_info(rs.camera_info.name)}")
            print(f"  Serial: {device.get_info(rs.camera_info.serial_number)}")
            print(f"  Firmware: {device.get_info(rs.camera_info.firmware_version)}")
        
        # Test pipeline creation
        pipeline = rs.pipeline()
        config = rs.config()
        
        # Configure RGB stream only (disable depth and IR)
        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        config.disable_stream(rs.stream.depth)
        config.disable_stream(rs.stream.infrared)
        config.disable_stream(rs.stream.infrared2)
        
        print("✅ Pipeline configuration successful")
        
        # Start streaming
        pipeline.start(config)
        print("✅ RealSense D455 streaming started!")
        
        # Capture a few frames to test
        print("Capturing RGB test frames...")
        for i in range(5):
            frames = pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()
            
            if color_frame:
                print(f"  Frame {i+1}: RGB {color_frame.get_width()}x{color_frame.get_height()}")
            else:
                print(f"  Frame {i+1}: Failed to capture RGB")
        
        # Stop streaming
        pipeline.stop()
        print("✅ RealSense D455 test completed successfully!")
        print("\n🎉 Your RealSense D455 is ready to use with SPARC!")
        return True
        
    except Exception as e:
        print(f"❌ RealSense test failed: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure RealSense D455 is connected via USB 3.0")
        print("2. Check if the device is recognized: lsusb | grep Intel")
        print("3. Try running: sudo apt-get install librealsense2-utils")
        print("4. Check USB power - RealSense needs good power supply")
        return False

def test_webcam_fallback():
    """Test webcam fallback"""
    print("\nTesting webcam fallback...")
    try:
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print(f"✅ Webcam working: {frame.shape[1]}x{frame.shape[0]}")
                cap.release()
                return True
        cap.release()
        print("❌ Webcam not working")
        return False
    except Exception as e:
        print(f"❌ Webcam test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("SPARC RealSense D455 Integration Test")
    print("=" * 50)
    
    realsense_ok = test_realsense()
    webcam_ok = test_webcam_fallback()
    
    print("\n" + "=" * 50)
    print("Test Results:")
    print(f"RealSense D455: {'✅ Working' if realsense_ok else '❌ Not detected'}")
    print(f"USB Webcam: {'✅ Working' if webcam_ok else '❌ Not working'}")
    
    if realsense_ok:
        print("\n🚀 You can now use your RealSense D455 with SPARC!")
        print("Run: python main.py")
    elif webcam_ok:
        print("\n📷 SPARC will use your USB webcam as fallback")
        print("Run: python main.py")
    else:
        print("\n⚠️  No cameras detected. Please check your connections.")
    
    print("=" * 50)

