import os
import sys
import pickle
import argparse

os.environ["OPENCV_LOG_LEVEL"] = "SILENT"
os.environ["QT_LOGGING_RULES"] = "*.debug=false"

import cv2  # noqa: E402
import face_recognition  # noqa: E402

KNOWN_FACES_DIR = os.path.join(os.path.dirname(__file__), "known_faces")


def main():
    parser = argparse.ArgumentParser(description="Enroll a face from IP camera")
    parser.add_argument("--name", required=True, help="Name of the person")
    parser.add_argument("--url", default="http://192.168.10.5:8080/video", help="IP camera URL")
    args = parser.parse_args()

    os.makedirs(KNOWN_FACES_DIR, exist_ok=True)

    cap = cv2.VideoCapture(args.url)
    if not cap.isOpened():
        print(f"Error: cannot open stream {args.url}")
        sys.exit(1)

    print(f"Stream opened for '{args.name}'.")
    print("  'c' = capture a shot  |  's' = save & quit  |  'q' = cancel")

    captured_encodings = []

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        status = f"Captures: {len(captured_encodings)} | 'c'=capture 's'=save 'q'=cancel"
        cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow("Enroll Face", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord("c"):
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            locations = face_recognition.face_locations(rgb_frame)

            if len(locations) == 0:
                print("No face detected. Try again.")
                continue
            if len(locations) > 1:
                print(f"Multiple faces detected ({len(locations)}). Make sure only one face is visible.")
                continue

            encoding = face_recognition.face_encodings(rgb_frame, locations)[0]
            captured_encodings.append(encoding)
            print(f"  Captured #{len(captured_encodings)} for '{args.name}'")

        if key == ord("s"):
            if not captured_encodings:
                print("No captures yet. Press 'c' to capture first.")
                continue

            filename = args.name.lower().replace(" ", "_") + ".pkl"
            filepath = os.path.join(KNOWN_FACES_DIR, filename)

            with open(filepath, "wb") as f:
                pickle.dump({"name": args.name, "encodings": captured_encodings}, f)

            print(f"Saved {len(captured_encodings)} encoding(s) for '{args.name}' to {filepath}")
            break

        if key == ord("q"):
            print("Cancelled.")
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
