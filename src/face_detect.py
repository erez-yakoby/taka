import os
import sys
import pickle
import glob
import socket

os.environ["OPENCV_LOG_LEVEL"] = "SILENT"
os.environ["QT_LOGGING_RULES"] = "*.debug=false"

import numpy as np  # noqa: E402
import cv2  # noqa: E402
import face_recognition  # noqa: E402

DETECT_EVERY = 30
H_FOV = 60  # horizontal field of view in degrees (typical phone camera)
KNOWN_FACE_THRESHOLD = 0.50  # max face distance to consider a match (50%+ confidence)
ARDUINO_IP = "10.89.194.68"  # Arduino UNO R4 WiFi IP
ARDUINO_PORT = 5005
KNOWN_FACES_DIR = os.path.join(os.path.dirname(__file__), "known_faces")


def load_known_faces():
    """Load known faces grouped by person.

    Returns list of (name, encodings_array) tuples.
    Supports both old format (single "encoding") and new format (multiple "encodings").
    """
    known_people = []
    for path in glob.glob(os.path.join(KNOWN_FACES_DIR, "*.pkl")):
        with open(path, "rb") as f:
            data = pickle.load(f)
        if "encodings" in data:
            encodings = np.array(data["encodings"])
        else:
            encodings = np.array([data["encoding"]])
        known_people.append((data["name"], encodings))
        print(f"  Loaded: {data['name']} ({len(encodings)} encoding(s))")
    return known_people


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else "http://192.168.10.5:8080/video"
    print(f"Connecting to: {url}")

    print("Loading known faces...")
    known_people = load_known_faces()
    if not known_people:
        print("  No known faces found. All faces will show as Unknown.")
        print("  Run enroll_face.py to add known faces.")

    cap = cv2.VideoCapture(url)
    if not cap.isOpened():
        print(f"Error: cannot open stream {url}")
        sys.exit(1)

    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print(f"UDP target: {ARDUINO_IP}:{ARDUINO_PORT}")
    print("Stream opened. Press 'q' to quit.")

    frame_count = 0
    last_results = []  # list of (top, right, bottom, left, name, is_known)

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        frame_count += 1
        if frame_count % DETECT_EVERY == 0:
            small = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            rgb_small = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

            locations = face_recognition.face_locations(rgb_small)
            encodings = face_recognition.face_encodings(rgb_small, locations)

            last_results = []
            for (top, right, bottom, left), encoding in zip(locations, encodings):
                # Scale back up (we resized to 0.5)
                top, right, bottom, left = top * 2, right * 2, bottom * 2, left * 2

                name = "Unknown"
                is_known = False
                confidence = 0.0
                best_dist = 1.0
                if known_people:
                    best_name = None
                    for person_name, person_encodings in known_people:
                        distances = face_recognition.face_distance(person_encodings, encoding)
                        avg_dist = distances.mean()
                        if avg_dist < best_dist:
                            best_dist = avg_dist
                            best_name = person_name
                    if best_dist <= KNOWN_FACE_THRESHOLD:
                        name = best_name
                        is_known = True
                        confidence = (1 - best_dist) * 100

                last_results.append((top, right, bottom, left, name, is_known, confidence, best_dist))

        # Find the best (lowest distance) unknown face
        unknowns = [(i, r) for i, r in enumerate(last_results) if not r[5]]
        best_unknown_idx = None
        if unknowns:
            best_unknown_idx = min(unknowns, key=lambda x: x[1][7])[0]

        frame_h, frame_w = frame.shape[:2]
        v_fov = H_FOV * (frame_h / frame_w)

        for i, (top, right, bottom, left, name, is_known, confidence, best_dist) in enumerate(last_results):
            color = (0, 255, 0) if is_known else (0, 0, 255)
            label = f"{name} ({confidence:.0f}%)" if is_known else name
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.putText(frame, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            if i == best_unknown_idx:
                face_cx = (left + right) / 2
                face_cy = (top + bottom) / 2
                pan = (face_cx - frame_w / 2) / (frame_w / 2) * (H_FOV / 2)
                tilt = (face_cy - frame_h / 2) / (frame_h / 2) * (v_fov / 2)
                angle_text = f"pan:{pan:+.0f} tilt:{tilt:+.0f}"
                cv2.putText(frame, angle_text, (left, bottom + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                udp_sock.sendto(f"{pan:+.1f},{tilt:+.1f}\n".encode(), (ARDUINO_IP, ARDUINO_PORT))

        cv2.imshow("Face Recognition", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    udp_sock.close()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
