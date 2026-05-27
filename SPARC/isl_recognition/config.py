"""
Configuration constants for the ISL Recognition System.
"""

# Webcam Settings
WEBCAM_WIDTH = 1280
WEBCAM_HEIGHT = 720
FPS_TARGET = 30

# Buffer and Stability Settings
BUFFER_TIME = 4.0  # seconds
GESTURE_STABLE_DURATION = 0.3  # seconds
GESTURE_STABLE_DURATION_NAMASTE = 0.4
GESTURE_STABLE_DURATION_WATER = 0.8
GESTURE_STABLE_DURATION_DEFAULT = 0.3

# MediaPipe Settings
MP_MIN_DETECTION_CONFIDENCE = 0.5
MP_MIN_TRACKING_CONFIDENCE = 0.5

# Gesture Mappings
GESTURE_MAP = {
    "namaste": "Namaste",
    "hands_intersect": "Home",
    "india": "I am Indian",
    "female": "Female",
    "male": "Male",
    "thank_you": "Thank you",
    "sibling": "Sibling",
    "doctor": "Doctor",
    "water": "i want water",
    "both_thumbs_up": "are you okay ?",
    "one_thumb_up": "Okay",
    "thumbs_down": "not agree",
    "palm_up": "Hello",
    "index_on_cheek": "Blind",
    "both_palms": "Big",
    "head_nod": "Yes",
    "head_rotate": "No"
}

# Gesture Display Names (for UI)
GESTURE_DISPLAY_NAMES = {
    "namaste": "Prayer Hands (Namaste)",
    "hands_intersect": "Hands Intersect (Blue + Green)",
    "india": "Blue Thumb Above Eyebrows + Hand Above Shoulder",
    "female": "Blue Hand Touching Nose",
    "male": "Blue Hand Touching Lips",
    "thank_you": "Blue Hand Touching Chin",
    "sibling": "Middle Finger Touch Same Shoulder",
    "doctor": "Blue Hand Touching Shoulder Width",
    "water": "Green Hand Inside Mouth",
    "both_thumbs_up": "Both Thumbs Up",
    "one_thumb_up": "One Thumb Up",
    "thumbs_down": "Thumbs Down",
    "palm_up": "Palm Up",
    "index_on_cheek": "Index on Right Cheek",
    "both_palms": "Both Palms Forward",
    "head_nod": "Head Nod",
    "head_rotate": "Head Rotate"
}

# Colors (BGR Format)
COLOR_ORANGE = (0, 165, 255)
COLOR_WHITE = (255, 255, 255)
COLOR_GREEN = (0, 255, 0)
COLOR_BLUE = (255, 0, 0)
COLOR_CYAN = (0, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_GRAY = (200, 200, 200)
COLOR_LIGHT_GRAY = (180, 180, 180)
