# Intel RealSense D455 Setup Guide for SPARC

## Overview
Your SPARC AI Assistant now supports both USB webcam and Intel RealSense D455 cameras with automatic detection and fallback.

## Current Status
- ✅ **USB Webcam**: Working (Logitech C270 detected)
- ⏳ **RealSense D455**: Ready for integration (not currently connected)

## When You Get Your RealSense D455

### 1. Hardware Connection
- Connect RealSense D455 via **USB 3.0** port (blue connector)
- Ensure good power supply (RealSense requires more power than regular webcams)
- Use a powered USB hub if needed

### 2. Software Installation
The Python bindings are already installed, but you may need system libraries:

```bash
# Install RealSense system libraries (if needed)
sudo apt-get update
sudo apt-get install -y librealsense2-utils librealsense2-dev

# Or download from Intel's repository for latest version
wget -qO- https://librealsense.intel.com/Debian/apt-repo/conf/librealsense.pgp | sudo apt-key add -
echo 'deb https://librealsense.intel.com/Debian/apt-repo focal main' | sudo tee /etc/apt/sources.list.d/librealsense.list
sudo apt-get update
sudo apt-get install -y librealsense2-utils librealsense2-dev
```

### 3. Test Your RealSense D455
```bash
cd /home/pi/SPARC
source /home/pi/spectov/bin/activate
python test_realsense.py
```

### 4. Run SPARC with RealSense
```bash
cd /home/pi/SPARC
source /home/pi/spectov/bin/activate
python main.py
```

## Features

### Automatic Camera Detection
- **Priority**: RealSense D455 (if connected)
- **Fallback**: USB Webcam (if RealSense not available)
- **Display**: Shows camera type on startup

### RealSense D455 Advantages
- **Higher Resolution**: 640x480 @ 30fps
- **Depth Sensing**: Access to depth information
- **Better Quality**: Superior image quality
- **Stereo Vision**: Dual camera setup for better accuracy

### Current Features (Both Cameras)
- ✅ Object Detection with YOLO
- ✅ Hand Gesture Recognition
- ✅ Voice Commands
- ✅ Keyboard Input (1, 2, 3)
- ✅ OLED Display
- ✅ Text-to-Speech

### Future Enhancements (RealSense Only)
- 🔮 Distance measurement
- 🔮 3D object detection
- 🔮 Depth-based gesture recognition
- 🔮 Spatial awareness

## Troubleshooting

### RealSense Not Detected
1. Check USB connection (must be USB 3.0)
2. Verify power supply
3. Run: `lsusb | grep Intel`
4. Check firmware: `rs-fw-update -l`

### Permission Issues
```bash
sudo usermod -a -G video $USER
sudo usermod -a -G plugdev $USER
# Logout and login again
```

### Performance Issues
- Use powered USB hub
- Close other camera applications
- Check CPU temperature

## Usage Examples

### With RealSense D455
```bash
python main.py
# Output: "Camera Type: REALSENSE"
# Output: "RealSense D455 - Depth sensing enabled!"
```

### With USB Webcam (Fallback)
```bash
python main.py
# Output: "Camera Type: WEBCAM"
```

## Next Steps
1. Connect your RealSense D455
2. Run the test script
3. Enjoy enhanced SPARC capabilities!

---
*SPARC AI Assistant - The Future of Communication*

