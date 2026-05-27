"""
SPARC Main Entry Point
Handles input loop, OLED, TTS, gestures, and graceful shutdown.
Supports keyboard input for mode switching and gesture recognition.
"""
import os
import sys

# Fix Qt platform plugin issues on Raspberry Pi
os.environ['QT_QPA_PLATFORM'] = 'xcb'
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = ''
import logging
import select
import time
import re
import signal, contextlib
from SPARC.config.settings import (
    GESTURE_PHRASES, KEY_GESTURE, KEY_QUIT,
    CHARACTER_MODE_PHRASES, NUMBER_MODE_PHRASES, WORD_MODE_PHRASES,
    KEY_CHARACTER_MODE, KEY_NUMBER_MODE, KEY_WORD_MODE,
    WHAT_NEXT_VARIANTS, APOLOGY_VARIANTS
)
from SPARC.config import settings
from SPARC.services.logger import setup_logging
from SPARC.services.display import DisplayService
from SPARC.services.audio import AudioService
# TEMPORARILY DISABLED - RealSense (using USB webcam instead)
# from SPARC.cameras.realsense_manager import RealSenseManager
# TEMPORARILY DISABLED - Object Detection
# from SPARC.vision.object_detection import ObjectDetector
from SPARC.gestures.gesture_recognizer import GestureRecognizer

def _normalize_text(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def get_keyboard_choice(timeout_s=5) -> str:
    print(f"[Input] Type 1 (gesture), n (number mode), c (character mode), w (word mode), q (quit)")
    print("> ", end="", flush=True)
    r,_,_ = select.select([sys.stdin], [], [], timeout_s)
    if r:
        return sys.stdin.readline().strip().lower()
    return ""

def get_language_mode(display, audio) -> str:
    """
    Prompt user to select language mode (ISL or ASL)
    Returns: 'ISL' or 'ASL'
    """
    while True:
        print("\n[LANGUAGE MODE SELECTION]")
        print("Select language mode:")
        print("  1 = ISL (Indian Sign Language)")
        print("  2 = ASL (American Sign Language)")
        print("> ", end="", flush=True)
        choice = sys.stdin.readline().strip().lower()
        
        if choice == "1" or choice == "isl":
            display.show_centered_lines_bold(["ISL Mode", "Selected"], large=True, border=True, hold_s=2)
            audio.say("ISL mode selected")
            return "ISL"
        elif choice == "2" or choice == "asl":
            display.show_centered_lines_bold(["ASL Mode", "Selected"], large=True, border=True, hold_s=2)
            audio.say("ASL mode selected")
            return "ASL"
        else:
            print(f"Invalid choice: '{choice}'. Please enter 1 for ISL or 2 for ASL.")

def intent_from_text(text: str) -> str:
    """
    Parse voice or keyboard input to determine intent.
    Returns: "quit", "gesture", "character_mode", "number_mode", "word_mode", or "unknown"
    """
    t = _normalize_text(text)
    if not t: return ""
    
    # Quit command
    if t in KEY_QUIT: 
        return "quit"
    
    # Mode switching (check these first before gesture)
    if any(p in t for p in CHARACTER_MODE_PHRASES) or t in KEY_CHARACTER_MODE:
        return "character_mode"
    if any(p in t for p in NUMBER_MODE_PHRASES) or t in KEY_NUMBER_MODE:
        return "number_mode"
    if any(p in t for p in WORD_MODE_PHRASES) or t in KEY_WORD_MODE:
        return "word_mode"
    
    # Gesture mode - matches any phrase containing "gesture" keyword
    if any(p in t for p in GESTURE_PHRASES) or t in KEY_GESTURE:
        return "gesture"
    
    return "unknown"

@contextlib.contextmanager
def _defer_sigint():
    original = signal.getsignal(signal.SIGINT)
    try:
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        yield
    finally:
        signal.signal(signal.SIGINT, original)

def main():
    setup_logging()
    logger = logging.getLogger('SPARC')
    display = DisplayService()
    # Use persisted OLED calibration (do not override here)
    audio = AudioService()
    # TEMPORARILY DISABLED - RealSense (using USB webcam instead)
    # cam = RealSenseManager()
    cam = None  # Gesture recognizer will use USB webcam via cv2.VideoCapture
    # TEMPORARILY DISABLED - Object Detection
    # detector = ObjectDetector()
    detector = None
    
    # Select language mode (ISL or ASL)
    language_mode = get_language_mode(display, audio)
    logger.info(f"Selected language mode: {language_mode}")
    
    gest = GestureRecognizer(display_service=display, audio_service=audio, language_mode=language_mode)

    # OLED-only welcome (centered, bold)
    display.show_centered_lines_bold(["SPARC:The", "Future of", "Communication"], large=True, border=True, hold_s=2)
    # OLED+audio greeting (centered, bold)
    display.show_centered_lines_bold(["Hello. I", "am SPARC", "Initializing...."], large=True, border=True, hold_s=2)
    audio.say("Hello, I am SPARC. What can I do for you?")

    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        display.clear()
        display.close()
        # TEMPORARILY DISABLED - RealSense
        # if cam:
        #     cam.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal

    running = True
    try:
        while running:
            print("\n[INPUT] Type a command:")
            print("        1=gesture | n=number mode | c=character mode | w=word mode | q=quit")
            # No OLED prompt while waiting
            key = get_keyboard_choice(timeout_s=5)
            choice = intent_from_text(key) if key else ""
            
            if choice == "quit":
                running = False
                break
            elif choice == "gesture":
                # Open gesture recognition mode
                final_sentence = gest.run_until_sentence(cam)
                if final_sentence:
                    with _defer_sigint():
                        audio.say(final_sentence)
                        time.sleep(0.2)
                with _defer_sigint():
                    audio.say_random(WHAT_NEXT_VARIANTS)
                    time.sleep(0.2)
            elif choice == "character_mode":
                # Switch to character mode within gesture recognizer
                gest.current_mode = 'characters'
                display.show_centered_lines_bold(["Switched to", "CHARACTER", "mode"], large=True, border=True, hold_s=2)
                audio.say("Switched to character mode")
                print(f"[MODE] Switched to CHARACTER mode")
            elif choice == "number_mode":
                # Switch to number mode within gesture recognizer
                gest.current_mode = 'numbers'
                display.show_centered_lines_bold(["Switched to", "NUMBER", "mode"], large=True, border=True, hold_s=2)
                audio.say("Switched to number mode")
                print(f"[MODE] Switched to NUMBER mode")
            elif choice == "word_mode":
                # Switch to word mode using the new ISL Recognition App
                print(f"[MODE] Switching to WORD mode (New Implementation)")
                try:
                    # Clear display before starting new app
                    display.clear()
                    
                    # Import and run the new ISL Recognition App
                    from SPARC.isl_recognition.core import GestureRecognizerApp
                    word_app = GestureRecognizerApp()
                    word_app.run()
                    
                    # After returning from the app, refresh the main menu display
                    display.show_centered_lines_bold(["SPARC", "Main Menu"], large=True, border=True, hold_s=2)
                except Exception as e:
                    logger.error(f"Failed to run Word Mode app: {e}")
                    print(f"Error running Word Mode: {e}")
            elif choice == "unknown" and key:
                with _defer_sigint():
                    audio.say_random(APOLOGY_VARIANTS)
                    time.sleep(0.2)
                with _defer_sigint():
                    audio.say_random(WHAT_NEXT_VARIANTS)
                    time.sleep(0.2)
            # else: no input, loop continues quietly
    except KeyboardInterrupt:
        logger.info("Received KeyboardInterrupt, shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        logger.info("Cleaning up resources...")
        try:
            display.clear()
            display.close()
        except Exception as e:
            logger.warning(f"Error cleaning up display: {e}")
        # TEMPORARILY DISABLED - RealSense
        # try:
        #     if cam:
        #         cam.stop()
        # except Exception as e:
        #     logger.warning(f"Error stopping camera: {e}")
        logger.info("SPARC shutdown complete.")

if __name__ == '__main__':
    main()

