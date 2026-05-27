"""
SPARC Configuration Settings
Centralizes all paths, model locations, and runtime constants.
"""
from pathlib import Path

# Base directories
# settings.py is in SPARC/config/settings.py
# Base dir is the repo root, 3 levels up
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ASSETS_DIR = BASE_DIR
# Assuming pic is in the repo root or assets dir
PIC_DIR = BASE_DIR / 'pic'
LIB_DIR = BASE_DIR / 'lib'

# Model paths
GESTURE_MODELS = {
    'asl_character': BASE_DIR / 'RFC_MODEL_3_A_Z_modes.pkl',
    'asl_numbers': BASE_DIR / 'RFC_MODEL_2_0_9_modes.pkl',
    'words': BASE_DIR / 'RFC_MODEL_WORDS_SET_1.pkl',
    'isl': BASE_DIR / 'Indian-Sign-Language-Detection/model.h5',
}
YOLO_WEIGHTS = BASE_DIR / 'weights' / 'yolov8n.pt'

# Video settings
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FRAME_FPS = 30

# Gesture settings
GESTURE_CONFIDENCE = 0.40

# Audio settings
TTS_LANG = 'en'
AUDIO_TMP = '/tmp/audio'

# OLED font file (match Gesture.py)
FONT_FILE = PIC_DIR / 'Font.ttc'

# Object detection
# --- timings ---
OBJECT_DET_DURATION_S = 30  # run detection for 30 seconds

# --- depth options ---
ENABLE_DEPTH = True           # try to enable RealSense depth if available
DEPTH_ALIGN_TO_COLOR = True   # align depth to color stream
DEPTH_SAMPLE_BOX = 7          # odd kernel size for center-ROI median (e.g., 5/7/9)
DEPTH_CLIP_MIN_M = 0.15        # clip too-near noise
DEPTH_CLIP_MAX_M = 6.0         # D455 typical useful range (tweakable)

# Depth colorization
DEPTH_COLOR_MAP = "JET"        # one of: "JET", "TURBO", "INFERNO", "MAGMA"
DEPTH_NORM_MODE = "auto"       # "auto" (min-max per frame) or "fixed"
DEPTH_NORM_FIXED_MAX_M = 5.0   # used when NORM_MODE == "fixed"

# OLED tuning (approximate backup.py look/feel)
OLED_LINE_HEIGHT_LARGE = 18
OLED_LINE_HEIGHT_MED = 14
OLED_MARGIN_X = 0
OLED_MARGIN_Y = 0
OLED_BOLD_OFFSETS = [(0,0),(1,0),(0,1),(1,1)]
OLED_USE_BORDER = True
OLED_FONT_PREF_SIZES = {"small": 12, "medium": 14, "large": 16}

# --- voice & prompts ---
WHAT_NEXT_VARIANTS = [
    "Now what can I do?",
    "What would you like me to do next?",
    "How can I help you now?",
    "What’s next?",
    "Ready for the next task. What should I do?"
]

APOLOGY_VARIANTS = [
    "Sorry, this function is not in scope right now.",
    "I’m sorry, I can’t do that yet.",
    "That’s beyond my capabilities at the moment.",
    "Apologies, I don’t support that request."
]

# --- input phrases ---
# Gesture mode: matches any phrase containing "gesture"
GESTURE_PHRASES = [
    "gesture"  # Simple keyword matching - any phrase with "gesture" will match
]

# Mode switching phrases
CHARACTER_MODE_PHRASES = [
    "character"  # Matches any phrase containing "character"
]

NUMBER_MODE_PHRASES = [
    "number", "numbers"  # Matches any phrase containing "number" or "numbers"
]

WORD_MODE_PHRASES = [
    "word", "words"  # Matches any phrase containing "word" or "words"
]

# --- keyboard shortcuts ---
KEY_GESTURE = ("1", "sign", "gesture")
KEY_QUIT = ("q", "quit", "exit")
KEY_CHARACTER_MODE = ("c", "character")
KEY_NUMBER_MODE = ("n", "number", "numbers")
KEY_WORD_MODE = ("w", "word", "words")

# --- Microphone preferences ---
# Mic preference tuning
MIC_PREFER_NAMES = [
    "bluez_input", "headset", "handsfree", "hfp", "hsp",
    "earbuds", "earbud", "airpods", "buds", "oneplus", "boat", "sony", "jbl"
]
MIC_EXCLUDE_NAMES = [
    "monitor", "hdmi", "null", "swr", "pipewire", "jack", "output", "playback"
]

# SpeechRecognition tuning
SR_ADJUST_DURATION_S = 0.6
SR_PHRASE_TIME_LIMIT_S = 7
SR_LISTEN_TIMEOUT_S = 7
SR_ENERGY_FLOOR = 120
SR_DYNAMIC_ENERGY = True

# Verbose diagnostics
VOICE_DEBUG = True

# Persisted config path (used by config_io)
from pathlib import Path
CONFIG_HOME = Path(__file__).resolve().parent  # not used directly, kept for reference

# Mic: default pin (can be overridden by config_io + env)
DEFAULT_BT_MIC_NAME = "bluez_input.98_34_8C_90_06_22.0"
# If you want broader match, you can also keep "bluez_input" in MIC_PREFER_NAMES.

# OLED defaults (these are fallbacks; final values will load from config_io)
OLED_DEFAULT_ROTATION = 0       # degrees
OLED_DEFAULT_SCAN_DIR = "auto"  # driver default unless overridden
OLED_DEFAULT_OFFSET_X = 0
OLED_DEFAULT_OFFSET_Y = 0

