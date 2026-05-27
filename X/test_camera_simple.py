#!/usr/bin/python
# -*- coding:utf-8 -*-

"""
Simple camera test without display dependencies
"""

import cv2
import time

def test_camera():
    """Test camera functionality"""
    print("Testing camera on /dev/video4...")
    
    cap = cv2.VideoCapture(4)
    if not cap.isOpened():
        print("❌ Cannot open camera")
        return False
    
    print("✅ Camera opened successfully")
    
    # Test reading frames
    for i in range(5):
        ret, frame = cap.read()
        if ret:
            print(f"✅ Frame {i+1}: {frame.shape}")
        else:
            print(f"❌ Failed to read frame {i+1}")
            cap.release()
            return False
    
    cap.release()
    print("✅ Camera test completed successfully!")
    return True

if __name__ == "__main__":
    test_camera()
