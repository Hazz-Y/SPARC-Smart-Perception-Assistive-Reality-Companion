import sys, termios, tty, time
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from SPARC.services.display import DisplayService

HELP = """\
Display Calibration:
  Arrows: move (offset_x/offset_y)
  r: rotate 0/90/180/270
  b: toggle border
  + / - : line height large ++ / --
  s: save & exit
  q: quit without save
"""

def getch():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == '\x1b':
            ch += sys.stdin.read(2)
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

def main():
    try:
        disp = DisplayService()
        print(HELP)
        while True:
            disp.show_three_lines_bold("SPARC: The", "Future of", "Communication", hold_s=0)
            ch = getch()
            if ch == '\x1b[A':   # up
                disp.offset_y -= 1
            elif ch == '\x1b[B': # down
                disp.offset_y += 1
            elif ch == '\x1b[C': # right
                disp.offset_x += 1
            elif ch == '\x1b[D': # left
                disp.offset_x -= 1
            elif ch in ('r','R'):
                disp.rotation = {0:90, 90:180, 180:270, 270:0}[disp.rotation]
            elif ch == 'b':
                disp.use_border = not disp.use_border
            elif ch == '+':
                disp.line_h_large += 1
            elif ch == '-':
                disp.line_h_large = max(10, disp.line_h_large - 1)
            elif ch in ('s','S'):
                disp.save_calibration()
                print("Saved. Exiting.")
                break
            elif ch in ('q','Q'):
                print("Quit without saving.")
                break
            time.sleep(0.05)
    except Exception as e:
        print(f"Calibration failed: {e}")
        print("OLED may not be available.")

if __name__ == "__main__":
    main()
