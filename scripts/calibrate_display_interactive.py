#!/usr/bin/env python3
"""
Interactive OLED Display Calibration
Use arrow keys to adjust alignment, 's' to save, 'q' to quit
"""
import os
import sys
import time

# Fix Qt platform plugin issues
os.environ['QT_QPA_PLATFORM'] = 'xcb'
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = ''

# Add SPARC to path
sys.path.insert(0, '/home/pi')

from SPARC.services.display import DisplayService

def main():
    print("OLED Display Calibration")
    print("========================")
    print("Use arrow keys to adjust alignment:")
    print("  ↑/↓ = adjust offset_y")
    print("  ←/→ = adjust offset_x")
    print("  r/R = rotate (0→90→180→270→0)")
    print("  s/S = save current settings")
    print("  q/Q = quit without saving")
    print("  c/C = center (reset offsets)")
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
    
    try:
        import tty, termios
        old_settings = termios.tcgetattr(sys.stdin)
        tty.setraw(sys.stdin.fileno())
        
        while True:
            ch = sys.stdin.read(1)
            
            if ch in ('q', 'Q'):
                break
            elif ch in ('s', 'S'):
                display.save_calibration()
                print("\n✓ Settings saved!")
                break
            elif ch in ('c', 'C'):
                display.offset_x = 0
                display.offset_y = 0
                print(f"\n✓ Centered: X={display.offset_x}, Y={display.offset_y}")
            elif ch == '\x1b':  # Arrow key sequence start
                ch2 = sys.stdin.read(1)
                if ch2 == '[':
                    ch3 = sys.stdin.read(1)
                    if ch3 == 'A':  # Up arrow
                        display.offset_y -= 1
                        print(f"\n↑ Y={display.offset_y}")
                    elif ch3 == 'B':  # Down arrow
                        display.offset_y += 1
                        print(f"\n↓ Y={display.offset_y}")
                    elif ch3 == 'C':  # Right arrow
                        display.offset_x += 1
                        print(f"\n→ X={display.offset_x}")
                    elif ch3 == 'D':  # Left arrow
                        display.offset_x -= 1
                        print(f"\n← X={display.offset_x}")
            elif ch in ('r', 'R'):
                rotations = [0, 90, 180, 270]
                current_idx = rotations.index(display.rotation)
                next_idx = (current_idx + 1) % len(rotations)
                display.rotation = rotations[next_idx]
                print(f"\n↻ Rotation={display.rotation}°")
            
            # Update display with new settings
            display.show_centered_lines_bold(test_lines, large=True, border=True, hold_s=0)
            
    except ImportError:
        print("Terminal control not available. Using simple input mode.")
        print("Enter commands: x+1, x-1, y+1, y-1, r, s, q")
        
        while True:
            cmd = input("Command: ").strip().lower()
            
            if cmd == 'q':
                break
            elif cmd == 's':
                display.save_calibration()
                print("✓ Settings saved!")
                break
            elif cmd == 'x+1':
                display.offset_x += 1
                print(f"X={display.offset_x}")
            elif cmd == 'x-1':
                display.offset_x -= 1
                print(f"X={display.offset_x}")
            elif cmd == 'y+1':
                display.offset_y += 1
                print(f"Y={display.offset_y}")
            elif cmd == 'y-1':
                display.offset_y -= 1
                print(f"Y={display.offset_y}")
            elif cmd == 'r':
                rotations = [0, 90, 180, 270]
                current_idx = rotations.index(display.rotation)
                next_idx = (current_idx + 1) % len(rotations)
                display.rotation = rotations[next_idx]
                print(f"Rotation={display.rotation}°")
            elif cmd == 'c':
                display.offset_x = 0
                display.offset_y = 0
                print(f"Centered: X={display.offset_x}, Y={display.offset_y}")
            
            display.show_centered_lines_bold(test_lines, large=True, border=True, hold_s=0)
    
    finally:
        try:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        except:
            pass
        
        display.clear()
        display.close()
        print("\nCalibration complete.")

if __name__ == '__main__':
    main()

