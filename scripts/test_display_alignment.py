#!/usr/bin/env python3
"""
Simple OLED alignment tester
Run this to test different alignment settings
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from services.display import DisplayService
from config_io import load_config, save_config
import time

def test_alignment(offset_x=0, offset_y=0, rotation=0, line_height=18):
    """Test specific alignment settings"""
    print(f"Testing: offset_x={offset_x}, offset_y={offset_y}, rotation={rotation}, line_height={line_height}")
    
    # Load current config
    config = load_config()
    
    # Update display settings
    config["display"]["offset_x"] = offset_x
    config["display"]["offset_y"] = offset_y
    config["display"]["rotation"] = rotation
    config["display"]["line_height_large"] = line_height
    
    # Save config
    save_config(config)
    
    # Create display service with new settings
    disp = DisplayService()
    
    # Show test pattern
    disp.show_three_lines_bold("SPARC: The", "Future of", "Communication", hold_s=2)
    
    # Clean up
    disp.clear()
    disp.close()

def main():
    print("OLED Alignment Tester")
    print("This will test different alignment settings and show them on the OLED")
    print("Press Ctrl+C to stop between tests")
    
    # Test different common misalignment scenarios
    test_cases = [
        # (offset_x, offset_y, rotation, line_height)
        (0, 0, 0, 18),      # Default
        (2, 0, 0, 18),      # Move right
        (-2, 0, 0, 18),     # Move left
        (0, 2, 0, 18),      # Move down
        (0, -2, 0, 18),     # Move up
        (0, 0, 90, 18),     # Rotate 90
        (0, 0, 180, 18),   # Rotate 180
        (0, 0, 270, 18),   # Rotate 270
        (0, 0, 0, 16),     # Smaller line height
        (0, 0, 0, 20),     # Larger line height
    ]
    
    for i, (ox, oy, rot, lh) in enumerate(test_cases):
        try:
            print(f"\nTest {i+1}/{len(test_cases)}:")
            test_alignment(ox, oy, rot, lh)
            input("Press Enter to continue to next test (or Ctrl+C to stop)...")
        except KeyboardInterrupt:
            print("\nStopped by user")
            break
        except Exception as e:
            print(f"Error in test {i+1}: {e}")
            continue
    
    print("\nAll tests completed!")
    print("If you found a good alignment, you can manually set it in the config file:")
    print("~/.config/sparc/config.json")

if __name__ == "__main__":
    main()

