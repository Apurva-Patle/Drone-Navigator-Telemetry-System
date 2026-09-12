import cv2
from ultralytics import YOLO


# -----------------------------
# Configuration
# -----------------------------

CONF_THRESHOLD = 0.6

TARGET_CLASSES = {
    "person",
    "bicycle",
    "car",
    "motorcycle",
    "bus",
    "truck"
}

# Simulated distance parameters
KNOWN_OBJECT_HEIGHT = 1.7
FOCAL_LENGTH = 600


# -----------------------------
# Main Application
# -----------------------------

def main():

    print("Loading YOLOv8 model...")

    model = YOLO("yolov8n.pt")

    print("YOLOv8 model loaded successfully.")

    # Open webcam
    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("Error: Could not open camera.")
        return

    print("Camera started.")
    print("Press 'q' to exit.")

    previous_time = cv2.getTickCount()

    while True:

        # -----------------------------
        # Capture frame
        # -----------------------------

        success, frame = camera.read()

        if not success:
            print("Error: Could not read frame.")
            break

        height, width, _ = frame.shape

        # -----------------------------
        # Calculate FPS
        # -----------------------------

        current_time = cv2.getTickCount()

        fps = cv2.getTickFrequency() / (
            current_time - previous_time
        )

        previous_time = current_time

        # -----------------------------
        # Target Lock Zone
        # Middle 20% of screen
        # -----------------------------

        left_limit = int(width * 0.4)
        right_limit = int(width * 0.6)

        frame_center = width // 2

        # Draw target zone
        cv2.line(
            frame,
            (left_limit, 0),
            (left_limit, height),
            (255, 255, 0),
            1
        )

        cv2.line(
            frame,
            (right_limit, 0),
            (right_limit, height),
            (255, 255, 0),
            1
        )

        # -----------------------------
        # YOLO Detection
        # -----------------------------

        results = model(
            frame,
            imgsz=416,
            verbose=False
        )

        detections = []

        # -----------------------------
        # Process detections
        # -----------------------------

        for box in results[0].boxes:

            confidence = float(box.conf[0])

            # Ignore low-confidence detections
            if confidence < CONF_THRESHOLD:
                continue

            class_id = int(box.cls[0])

            object_name = results[0].names[class_id]

            # Only consider target objects
            if object_name not in TARGET_CLASSES:
                continue

            # Bounding box coordinates
            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0]
            )

            # Object center
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2

            # Bounding box height
            box_height = y2 - y1

            # -----------------------------
            # Simulated Distance
            # -----------------------------

            if box_height > 0:

                distance = (
                    KNOWN_OBJECT_HEIGHT * FOCAL_LENGTH
                ) / box_height

            else:

                distance = 0

            # Check target zone
            inside_target_zone = (
                left_limit < center_x < right_limit
            )

            # Store detection
            detections.append({
                "confidence": confidence,
                "object_name": object_name,
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "center_x": center_x,
                "center_y": center_y,
                "box_height": box_height,
                "distance": distance,
                "inside_zone": inside_target_zone
            })

        # -----------------------------
        # Select Best Target
        # -----------------------------

        best_target = None
        best_distance_from_center = float("inf")

        for detection in detections:

            if detection["inside_zone"]:

                center_distance = abs(
                    detection["center_x"] - frame_center
                )

                if center_distance < best_distance_from_center:

                    best_distance_from_center = center_distance

                    best_target = detection

        # -----------------------------
        # Draw Detections
        # -----------------------------

        for detection in detections:

            x1 = detection["x1"]
            y1 = detection["y1"]
            x2 = detection["x2"]
            y2 = detection["y2"]

            object_name = detection["object_name"]
            confidence = detection["confidence"]
            distance = detection["distance"]

            # Target status
            if detection is best_target:

                status = "TARGET LOCKED"
                color = (0, 0, 255)

            else:

                status = "Scanning"
                color = (0, 255, 0)

            # Draw bounding box
            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                color,
                2
            )

            # Draw object center
            cv2.circle(
                frame,
                (
                    detection["center_x"],
                    detection["center_y"]
                ),
                4,
                color,
                -1
            )

            # Display object information
            label = (
                f"{object_name} "
                f"{confidence:.2f} - "
                f"{status}"
            )

            cv2.putText(
                frame,
                label,
                (x1, max(y1 - 30, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2
            )

            # Display simulated distance
            distance_text = f"Distance: {distance:.1f} m"

            cv2.putText(
                frame,
                distance_text,
                (x1, max(y1 - 10, 40)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2
            )

        # -----------------------------
        # Drone HUD
        # -----------------------------

        cv2.putText(
            frame,
            "DRONE NAVIGATOR",
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"FPS: {fps:.1f}",
            (20, 65),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            "TARGET ZONE",
            (left_limit + 5, height - 15),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 0),
            1
        )

        # -----------------------------
        # Display
        # -----------------------------

        cv2.imshow(
            "Drone Navigator - Real-Time Detection",
            frame
        )

        # Press Q to exit
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    # -----------------------------
    # Shutdown
    # -----------------------------

    camera.release()
    cv2.destroyAllWindows()

    print("Camera stopped.")
    print("Drone Navigator stopped.")


# -----------------------------
# Program Entry Point
# -----------------------------

if __name__ == "__main__":
    main()