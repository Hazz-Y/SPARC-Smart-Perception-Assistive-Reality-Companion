# SPARC - Smart Perception Assistive Reality Companion

Real-time sign language recognition and multimodal communication for edge-deployed assistive hardware.

![Python](https://img.shields.io/badge/python-3.9+-blue.svg?style=flat-square) ![License](https://img.shields.io/badge/license-MIT-green.svg?style=flat-square) ![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi-red.svg?style=flat-square) ![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg?style=flat-square) ![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-orange.svg?style=flat-square)

> SPARC addresses the communication barrier for the hearing impaired by providing an entirely on-device hardware companion. By combining embedded computer vision with machine learning models, the system operates without cloud dependency or external processing. Native support for both Indian Sign Language (ISL) and American Sign Language (ASL) ensures broader communicative accessibility.

## Key Capabilities

**ISL Recognition** | Real-time classification of Indian Sign Language numbers and characters using a Keras/TensorFlow model.
**ASL Recognition** | Identification of American Sign Language characters, numbers, and common words via scikit-learn random forests.
**Emotion Detection** | Facial expression analysis categorizing four distinct affective states (Angry, Happy, Neutral, Sad).
**Text-to-Speech** | Audio synthesis of recognized gestures or constructed sentences via Google TTS.
**OLED Interface** | Visual feedback system optimized for a 128×64 SPI display.
**RealSense Compatibility** | Extended depth-camera integration with `pyrealsense2` for advanced hardware deployments.
**Graceful Hardware Fallback** | Automatic operational degradation when optional peripherals are disconnected.
**Sentence Builder** | Accumulation of recognized characters with gesture-based backspace and completion triggers.

## System Architecture

```text
+-------------------------------------------------------------+
|                       Hardware Layer                        |
|   [Camera]       [OLED Display]      [Mic]     [Speakers]   |
+-------|----------------|---------------|-----------|--------+
        |                |               |           |
+-------v----------------v---------------v-----------v--------+
|                      Processing Layer                       |
|   [Gesture       [Emotion      [Voice       [TTS Engine]    |
|   Recognizer]    Detector]      Input]                      |
+------------------------^---------------------------^--------+
                         |                           |
+------------------------v---------------------------v--------+
|             Configuration & Logging Backbone                |
+-------------------------------------------------------------+
```

The system employs a strict modular architecture, maintaining separation of concerns across service layers and recognition modules. Individual components are restricted to under 300 lines of code, ensuring high maintainability and isolated testing.

A core principle of SPARC is graceful hardware degradation. If the OLED display or specialized RealSense camera is unavailable, the software automatically falls back to console logging and standard USB webcams without halting execution.

## Supported Modes

Mode | Language | Input | Output | Model Format
---|---|---|---|---
ISL Characters | ISL | Hand Landmarks | Text / TTS | `.h5`
ISL Numbers | ISL | Hand Landmarks | Text / TTS | `.h5`
ASL Characters (A-Z) | ASL | Hand Landmarks | Text / TTS | `.pkl`
ASL Numbers (1-9) | ASL | Hand Landmarks | Text / TTS | `.pkl`
ASL Words | ASL | Hand Landmarks | Text / TTS | `.pkl`
Emotion Detection | Universal | Facial Image | Text / UI | `.h5`

## Hardware Requirements

**Required**
- Raspberry Pi 5 (or any other capable onboard PC)
- USB webcam
- Speakers

**Optional / Extended Compatibility**
- Waveshare 1.51" OLED (128×64, SPI)
- Bluetooth/USB microphone
- Intel RealSense depth camera

Note: SPARC operates fully without optional components.

## Software Stack

Library | Role
---|---
`opencv-python` | Computer vision and image acquisition
`cvzone` / `MediaPipe` | Hand tracking and facial landmark extraction
`tensorflow` / `Keras` | Deep learning model inference (ISL, Emotion)
`scikit-learn` / `joblib` | Machine learning model inference (ASL)
`gTTS` | Text-to-speech generation
`pygame` | Audio file playback
`SpeechRecognition` | Voice input processing
`pyaudio` | Audio stream capture
`Pillow` | Image manipulation for OLED output
`pyrealsense2` | RealSense camera support (optional)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Hazz-Y/SPARC-Smart-Perception-Assistive-Reality-Companion.git
cd SPARC-Smart-Perception-Assistive-Reality-Companion
```

2. Create and activate a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install system and Python dependencies:
```bash
sudo apt-get update
sudo apt-get install -y mpg123 libportaudio2 python3-pip python3-venv
pip install -r requirements.txt
```

4. Place model files in their required directories:
```bash
# ISL Model
# /home/pi/SPARC/Indian-Sign-Language-Detection/model.h5

# ASL Models
# /home/pi/SPARC/RFC_MODEL_2_0_9_modes.pkl
# /home/pi/SPARC/RFC_MODEL_3_A_Z_modes.pkl
# /home/pi/gesture-to-audio/models/words/set1/RFC_MODEL_WORDS_SET_1.pkl

# Emotion Model
# /home/pi/SPARC/Face_Recognition/model.h5
# /home/pi/SPARC/Face_Recognition/src/haarcascade_frontalface_default.xml
```

5. Calibrate OLED display (Optional):
```bash
python calibrate_display_interactive.py
```

6. Verify installation:
```bash
ENV=CI python main.py
```

## Usage

Start SPARC:
```bash
cd /home/pi/SPARC
source .venv/bin/activate
python main.py
```

Key | Action
---|---
`1` / `ISL` | Select Indian Sign Language mode
`2` / `ASL` | Select American Sign Language mode
`1` / `gesture` | Enter gesture recognition mode
`n` / `number` | Switch to number mode
`c` / `character` | Switch to character mode
`w` / `word` | Switch to word mode
`q` / `quit` | Exit SPARC

Ensure the camera frames the user's upper body and hands clearly. Recognized gestures accumulate to build sentences. A specific backspace gesture removes the last recognized character, while a completion gesture finalizes the sentence and triggers the TTS output.

## Model Details

**ISL Model**
- Format: `Keras` / `TensorFlow` (`.h5`)
- Input Specification: 21 hand landmarks
- Output Classes: 35 (Letters A-Z, Numbers 1-9)
- File Location: `/home/pi/SPARC/Indian-Sign-Language-Detection/model.h5`

**ASL Models**
- Format: `joblib` (`.pkl`)
- Input Specification: Hand landmarks
- Output Classes: 26 (Characters), 9 (Numbers), dynamic (Words)
- File Locations:
  - Numbers: `/home/pi/SPARC/RFC_MODEL_2_0_9_modes.pkl`
  - Characters: `/home/pi/SPARC/RFC_MODEL_3_A_Z_modes.pkl`
  - Words: `/home/pi/gesture-to-audio/models/words/set1/RFC_MODEL_WORDS_SET_1.pkl`

**Emotion Model**
- Format: `Keras` / `TensorFlow` (`.h5`)
- Input Specification: 48x48 grayscale face images
- Output Classes: 4 (Angry, Happy, Neutral, Sad)
- File Location: `/home/pi/SPARC/Face_Recognition/model.h5`
- Haar Cascade: `/home/pi/SPARC/Face_Recognition/src/haarcascade_frontalface_default.xml`

## Configuration Reference

Parameter | Type | Default | Description
---|---|---|---
`frame_width` | Integer | N/A | Camera capture resolution width.
`frame_height` | Integer | N/A | Camera capture resolution height.
`fps` | Integer | N/A | Target camera frames per second.
`confidence_threshold` | Float | N/A | Minimum probability score required for valid gesture recognition.
`tts_language` | String | N/A | ISO language code for Google TTS output.
`oled_font_sizes` | Integer/Dict | N/A | Pixel sizes for OLED text rendering.
`debug` | Boolean | N/A | Flag to enable verbose logging output.

## Troubleshooting

**Camera not detected**
Check USB camera connection, verify `sudo usermod -a -G video $USER`, and try an alternate USB port.

**OLED SPI issues**
Enable SPI via `sudo raspi-config` -> Interface Options -> SPI, check wiring, and run `python calibrate_display_interactive.py`.

**TTS audio failing**
Install `mpg123` via `sudo apt-get install mpg123`, check audio output with `aplay -l`, and test via `speaker-test -t wav`.

**Missing model files**
Verify model paths in `config/settings.py` match physical locations and confirm correct file formats (`.h5` vs `.pkl`).

**RealSense fallback**
Install the Intel RealSense SDK and verify detection via `rs-enumerate-devices`. The system will automatically fall back to USB webcam if unconfigured.

**PyAudio microphone issues**
Test PyAudio with `python -c "import pyaudio; print('OK')"`, verify permissions, and specify the preferred microphone in `config/settings.py`.

## Roadmap

- [x] ISL support
- [x] ASL support
- [x] Emotion detection
- [x] OLED display
- [x] TTS
- [x] Hardware fallback
- [ ] Continuous gesture streaming
- [ ] Bluetooth HID output
- [ ] Web dashboard
- [ ] LLM-assisted sentence correction
- [ ] Multilingual TTS

## Contributors

- `@Hazz-Y` (Harsh Yadav) - [GitHub Profile](https://github.com/Hazz-Y)

## License

This project is licensed under the [MIT License](LICENSE).
