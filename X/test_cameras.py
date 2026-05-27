#!/usr/bin/python
# -*- coding:utf-8 -*-

"""
Test script to find working camera devices
"""

import cv2
import os
import glob

def test_camera_device(device_num):
    """Test a specific camera device"""
    try:
        print(f"Testing /dev/video{device_num}...")
        cap = cv2.VideoCapture(device_num)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                print(f"✅ /dev/video{device_num} - Working! Frame shape: {frame.shape}")
                cap.release()
                return True
            else:
                print(f"❌ /dev/video{device_num} - Opens but can't read frames")
        else:
            print(f"❌ /dev/video{device_num} - Cannot open")
        cap.release()
    except Exception as e:
        print(f"❌ /dev/video{device_num} - Error: {e}")
    return False

def main():
    print("=" * 50)
    print("Camera Device Test")
    print("=" * 50)
    
    # Find all video devices
    video_devices = glob.glob('/dev/video*')
    print(f"Found video devices: {video_devices}")
    
    working_cameras = []
    
    # Test each device
    for device_path in sorted(video_devices):
        device_num = device_path.split('/dev/video')[1]
        if test_camera_device(int(device_num)):
            working_cameras.append(int(device_num))
    
    print("\n" + "=" * 50)
    print("Results:")
    if working_cameras:
        print(f"✅ Working cameras: {working_cameras}")
        print(f"Recommended device: /dev/video{working_cameras[0]}")
    else:
        print("❌ No working cameras found")
        print("\nTroubleshooting:")
        print("1. Check camera connections")
        print("2. Try: sudo usermod -a -G video $USER")
        print("3. Reboot and try again")
        print("4. Check if cameras are being used by other processes")
    
    print("=" * 50)

if __name__ == "__main__":
    main()
