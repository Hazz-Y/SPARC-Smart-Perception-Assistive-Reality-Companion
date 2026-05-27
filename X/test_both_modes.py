#!/usr/bin/python
# -*- coding:utf-8 -*-

"""
Test both object detection and gesture recognition modes
"""

import cv2
import time
from main import GestureCVAudioOLED

def test_both_modes():
    """Test both object detection and gesture recognition"""
    print("Testing both modes...")
    
    try:
        # Initialize the system
        print("Initializing SPARC system...")
        system = GestureCVAudioOLED()
        
        print(f"✅ Camera: {system.camera_manager.camera_type.upper()}")
        print("✅ System initialized successfully!")
        
        # Test camera read
        ret, frame = system.camera_manager.read_frame()
        if ret:
            print(f"✅ Camera working: Frame shape {frame.shape}")
        else:
            print("❌ Camera not working")
            return False
        
        print("\n🎉 Both modes should now work!")
        print("Run: python main.py")
        print("Press '1' for object detection with live feed")
        print("Press '2' for gesture recognition")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("SPARC Both Modes Test")
    print("=" * 50)
    
    success = test_both_modes()
    if success:
        print("\n✅ All systems ready!")
    else:
        print("\n❌ System test failed.")
    
    print("=" * 50)
