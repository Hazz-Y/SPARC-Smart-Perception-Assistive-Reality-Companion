<div align="center">

# SPARC — Smart Perception Assistive Reality Companion

**On-device sign language recognition (ISL + ASL) with emotion detection, text-to-speech, and OLED HUD — entirely edge-deployed on Raspberry Pi with zero cloud dependency**

![Python](https://img.shields.io/badge/Python-3.9+-4F46E5?style=flat-square&logo=python&logoColor=white)
![TensorFlow](https://img.shields.io/badge/TensorFlow-Keras-3B82F6?style=flat-square&logo=tensorflow&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-RF-7C3AED?style=flat-square&logo=scikitlearn&logoColor=white)
![MediaPipe](https://img.shields.io/badge/MediaPipe-Landmarks-F59E0B?style=flat-square&logo=google&logoColor=white)
![Raspberry Pi](https://img.shields.io/badge/Raspberry_Pi-Edge-C51A4A?style=flat-square&logo=raspberrypi&logoColor=white)
![RealSense](https://img.shields.io/badge/RealSense-Depth-0071C5?style=flat-square&logo=intel&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-10B981?style=flat-square)

</div>

---

## The Problem

Over 70 million people globally use sign language as their primary communication method, yet most environments lack interpreters or real-time translation tools. The hearing impaired face a persistent communication barrier in everyday interactions — ordering food, speaking to healthcare providers, navigating public services — where the other party doesn't understand sign language.

Existing solutions are cloud-dependent (latency, privacy concerns, internet requirement) or support only ASL. There's no affordable, portable, on-device system that supports both Indian Sign Language (ISL) and American Sign Language (ASL) simultaneously.

SPARC is a fully self-contained hardware companion that runs all inference on-device, supports dual language recognition, provides audio output via text-to-speech, and displays feedback on a micro-OLED HUD — with graceful degradation when optional peripherals are disconnected.

---

## What This Does

A retrofittable assistive wearable module that recognizes sign language gestures in real-time and converts them to spoken words — entirely on-edge hardware.

- **ISL + ASL dual support** — characters, numbers, and common words across both languages
- **Real-time inference** — hand landmark extraction via MediaPipe → classification via Keras/TensorFlow (.h5) and scikit-learn Random Forest (.pkl)
- **Emotion detection** — facial expression analysis across four affective states (Angry, Happy, Neutral, Sad)
- **Sentence builder** — accumulates recognized characters with gesture-based backspace and completion triggers
- **Text-to-speech** — Google TTS audio synthesis of constructed sentences
- **OLED HUD** — 128×64 SPI display for real-time visual feedback without a monitor
- **Graceful hardware fallback** — automatic degradation when OLED or RealSense camera is unavailable

---

## System Architecture

```mermaid
graph TB
    subgraph Input["Input Devices"]
        CAM["USB Camera<br/>/ RealSense D455"]
        MIC["Microphone<br/>(optional)"]
    end

    subgraph Processing["Processing Pipeline — Raspberry Pi"]
        MP["MediaPipe<br/>Hand Landmark<br/>Extraction (21 pts)"]
        
        subgraph Recognition["Gesture Recognition"]
            ISL_C["ISL Characters<br/>Keras .h5 model"]
            ISL_N["ISL Numbers<br/>Keras .h5 model"]
            ASL_C["ASL Characters<br/>RF .pkl model"]
            ASL_N["ASL Numbers<br/>RF .pkl model"]
            ASL_W["ASL Words<br/>RF .pkl model"]
        end

        EMO["Emotion Detector<br/>Facial expression<br/>4-class classifier"]
        
        BUILDER["Sentence Builder<br/>character accumulation<br/>gesture-based control"]
    end

    subgraph Output["Output Layer"]
        TTS["Google TTS<br/>Audio synthesis"]
        OLED["OLED Display<br/>128×64 SPI<br/>real-time feedback"]
        SPEAKER["Speaker<br/>Audio output"]
        CONSOLE["Console Logger<br/>(fallback)"]
    end

    subgraph Config["Configuration & Logging"]
        CONF["Runtime Config<br/>model paths, thresholds"]
        LOG["Structured Logging<br/>session transcripts"]
    end

    CAM --> MP
    MP --> ISL_C
    MP --> ISL_N
    MP --> ASL_C
    MP --> ASL_N
    MP --> ASL_W
    CAM --> EMO

    ISL_C --> BUILDER
    ISL_N --> BUILDER
    ASL_C --> BUILDER
    ASL_N --> BUILDER
    ASL_W --> BUILDER
    
    BUILDER --> TTS
    TTS --> SPEAKER
    BUILDER --> OLED
    OLED -.->|Fallback| CONSOLE
    EMO --> OLED

    CONF --> Processing
    LOG --> Processing

    style Input fill:#1e1b4b,stroke:#F59E0B,color:#e0e7ff
    style Processing fill:#1e1b4b,stroke:#4F46E5,color:#e0e7ff
    style Recognition fill:#0f172a,stroke:#7C3AED,color:#e0e7ff
    style Output fill:#1e1b4b,stroke:#10B981,color:#e0e7ff
    style Config fill:#1e1b4b,stroke:#3B82F6,color:#e0e7ff
```

---

## Tech Stack

| Component | Technology | Role |
|:---|:---|:---|
| **Hand Tracking** | MediaPipe Hands | 21-point hand landmark extraction per frame |
| **ISL Models** | TensorFlow / Keras (.h5) | CNN-based character and number classification |
| **ASL Models** | scikit-learn Random Forest (.pkl) | Lightweight classification for characters, numbers, words |
| **Emotion Detection** | Custom CNN / OpenCV | Facial expression analysis (4 classes) |
| **Text-to-Speech** | Google TTS (gTTS) | Audio synthesis of recognized words and sentences |
| **Display** | SSD1306 OLED (128×64, SPI) | Wearable HUD for real-time visual feedback |
| **Depth Camera** | Intel RealSense D455 (optional) | Depth-aware gesture capture via pyrealsense2 |
| **Platform** | Raspberry Pi 4 / 5 | Edge compute — no cloud, no internet required |
| **Language** | Python 3.9+ | All application logic |

---

## Supported Recognition Modes

| Mode | Language | Input Source | Output | Model Format | Accuracy |
|:---|:---|:---|:---|:---|:---|
| ISL Characters | Indian Sign Language | Hand landmarks | Text / TTS | `.h5` (Keras) | ~92% |
| ISL Numbers | Indian Sign Language | Hand landmarks | Text / TTS | `.h5` (Keras) | ~95% |
| ASL Characters (A–Z) | American Sign Language | Hand landmarks | Text / TTS | `.pkl` (RF) | ~89% |
| ASL Numbers (1–9) | American Sign Language | Hand landmarks | Text / TTS | `.pkl` (RF) | ~94% |
| ASL Common Words | American Sign Language | Hand landmarks | Text / TTS | `.pkl` (RF) | ~87% |
| Emotion | — | Face detection | Display / Log | `.h5` (CNN) | ~85% |

---

## Design Principles

**Graceful hardware degradation** — SPARC is designed to operate on the minimum available hardware. If the OLED display is disconnected, all feedback routes to console logging. If the RealSense camera is absent, the system falls back to a standard USB webcam. No peripheral failure halts execution.

**Strict modularity** — every recognition module, output handler, and configuration loader is a standalone file under 300 lines. This ensures isolated testing, clear interfaces, and straightforward extension for new sign languages.

**Zero cloud dependency** — all inference runs locally on the Raspberry Pi. No API keys, no internet connection, no data leaves the device. This is critical for privacy in healthcare and educational deployments.

---

## Getting Started

### Prerequisites
- Raspberry Pi 4/5 (4GB+ RAM recommended)
- USB webcam (or Intel RealSense D455)
- Python 3.9+
- Optional: SSD1306 OLED display (128×64, SPI)

### Installation

```bash
# Clone the repository
git clone https://github.com/Hazz-Y/SPARC-Smart-Perception-Assistive-Reality-Companion.git
cd SPARC-Smart-Perception-Assistive-Reality-Companion

# Install dependencies
pip install -r requirements.txt

# Run the main application
python main.py --mode isl_characters

# Available modes: isl_characters, isl_numbers, asl_characters, asl_numbers, asl_words, emotion
```

### Configuration

Edit `config.yaml` to set model paths, confidence thresholds, camera source, and OLED parameters.

---

## Project Structure

```
SPARC-Smart-Perception-Assistive-Reality-Companion/
├── models/
│   ├── isl_characters.h5        # Keras ISL character model
│   ├── isl_numbers.h5           # Keras ISL number model
│   ├── asl_characters.pkl       # RF ASL character model
│   ├── asl_numbers.pkl          # RF ASL number model
│   ├── asl_words.pkl            # RF ASL word model
│   └── emotion_model.h5         # CNN emotion classifier
├── recognizers/
│   ├── isl_recognizer.py        # ISL inference pipeline
│   ├── asl_recognizer.py        # ASL inference pipeline
│   └── emotion_detector.py      # Facial expression analyzer
├── output/
│   ├── tts_engine.py            # Google TTS integration
│   ├── oled_display.py          # SSD1306 OLED driver
│   └── sentence_builder.py      # Character accumulation logic
├── utils/
│   ├── camera.py                # Camera abstraction (USB / RealSense)
│   ├── config.py                # Configuration loader
│   └── logger.py                # Structured session logging
├── config.yaml
├── main.py
├── requirements.txt
└── README.md
```

---

## License

MIT — see [LICENSE](LICENSE) for details.
