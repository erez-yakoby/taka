# Taka - Face Recognition & Tracking System

## Project Overview

Real-time face recognition system that connects to an IP camera stream, detects faces, identifies known individuals, and sends pan/tilt tracking angles to an Arduino UNO R4 WiFi over UDP.

## Architecture

- **`src/face_detect.py`** — Main script. Streams video from an IP camera, detects faces every 30 frames, overlays name labels with confidence percentages. Green box = known face, red box = unknown. Computes pan/tilt angles for the best unknown face and sends them to the Arduino via UDP.
- **`src/enroll_face.py`** — Enrollment script. Captures multiple face shots from the camera stream and saves their encodings to `known_faces/`. Press `c` to capture, `s` to save.
- **`src/known_faces/`** — Directory of `.pkl` files, one per person, storing name + list of face encodings.

## Key Constants (`face_detect.py`)

| Constant | Value | Description |
|----------|-------|-------------|
| `DETECT_EVERY` | 30 | Process every Nth frame |
| `H_FOV` | 60 | Camera horizontal field of view (degrees) |
| `KNOWN_FACE_THRESHOLD` | 0.50 | Max face distance to consider a match (50%+ confidence) |
| `ARDUINO_IP` | 192.168.10.100 | Arduino UNO R4 WiFi IP |
| `ARDUINO_PORT` | 5005 | UDP port for angle data |

## Dependencies

- `face_recognition` (wraps dlib)
- `opencv-python` (cv2)
- `numpy`
- Python 3.11+

## Usage

```bash
# Enroll a new face (capture multiple shots, press 'c' per shot, 's' to save)
python src/enroll_face.py --name "Erez" --url http://192.168.10.5:8080/video

# Run face detection + tracking
python src/face_detect.py http://192.168.10.5:8080/video
```

Default camera URL: `http://192.168.10.5:8080/video`

## How It Works

1. **Multi-encoding enrollment**: Multiple face encodings per person are stored as pickle files. More photos = more stable recognition. Press `c` multiple times during enrollment for different angles/expressions.
2. **Detection**: Runs on every 30th frame (`DETECT_EVERY = 30`) to reduce CPU load. Frames are downscaled to 50% before detection.
3. **Matching**: For each detected face, computes the average face distance across all stored encodings per person. The person with the lowest average distance below `KNOWN_FACE_THRESHOLD` (0.50) is a match. Confidence = `(1 - distance) * 100`.
4. **Tracking**: The most confident unknown face's pan/tilt angles (relative to camera center) are computed from the bounding box position and camera FOV, then sent as `"+12.3,-5.7\n"` via UDP to the Arduino.
5. **Hardware**: Arduino UNO R4 WiFi listens on UDP port 5005 for pan/tilt angle commands.
