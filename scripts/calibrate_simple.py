#!/usr/bin/env python3
"""
Simple OLED Display Calibration
Adjust alignment with simple commands
"""
import os
import sys

# Fix Qt platform plugin issues
os.environ['QT_QPA_PLATFORM'] = 'xcb'
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = ''

# Add SPARC to path
sys.path.insert(0, '/home/pi')

from SPARC.services.display import DisplayService

def main():
    print("OLED Display Calibration")
    print("========================")
    print("Commands:")
    print("  x+1, x-1 = adjust horizontal offset")
    print("  y+1, y-1 = adjust vertical offset") 
    print("  r = rotate (0→90→180→270→0)")
    print("  c = center (reset offsets)")
    print("  s = save settings")
    print("  q = quit")
    print()
    
    display = DisplayService()
    
    # Show current settings
    print(f"Current settings:")
    print(f"  Rotation: {display.rotation}°")
    print(f"  Offset X: {display.offset_x}")
    print(f"  Offset Y: {display.offset_y}")
    print()
    
    # Test pattern
    test_lines = ["CALIBRATION", "TEST PATTERN", "ADJUST ME"]
    display.show_centered_lines_bold(test_lines, large=True, border=True, hold_s=0)
    print("Test pattern displayed. Adjust alignment now.")
    print()
    
    while True:
        try:
            cmd = input("Command (x+1/x-1/y+1/y-1/r/c/s/q): ").strip().lower()
            
            if cmd == 'q':
                break
            elif cmd == 's':
                display.save_calibration()
                print("✓ Settings saved!")
                break
            elif cmd == 'x+1':
                display.offset_x += 1
                print(f"→ X={display.offset_x}")
            elif cmd == 'x-1':
                display.offset_x -= 1
                print(f"← X={display.offset_x}")
            elif cmd == 'y+1':
                display.offset_y += 1
                print(f"↓ Y={display.offset_y}")
            elif cmd == 'y-1':
                display.offset_y -= 1
                print(f"↑ Y={display.offset_y}")
            elif cmd == 'r':
                rotations = [0, 90, 180, 270]
                current_idx = rotations.index(display.rotation)
                next_idx = (current_idx + 1) % len(rotations)
                display.rotation = rotations[next_idx]
                print(f"↻ Rotation={display.rotation}°")
            elif cmd == 'c':
                display.offset_x = 0
                display.offset_y = 0
                print(f"✓ Centered: X={display.offset_x}, Y={display.offset_y}")
            else:
                print("Invalid command. Try: x+1, x-1, y+1, y-1, r, c, s, q")
                continue
            
            # Update display with new settings
            display.show_centered_lines_bold(test_lines, large=True, border=True, hold_s=0)
            
        except KeyboardInterrupt:
            print("\nInterrupted. Exiting...")
            break
        except EOFError:
            print("\nEOF. Exiting...")
            break
    
    display.clear()
    display.close()
    print("Calibration complete.")

if __name__ == '__main__':
    main()

