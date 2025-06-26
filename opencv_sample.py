import cv2
import sys

video_id = 2

if len(sys.argv) > 1:
    video_id = int(sys.argv[1])


# Create a video capture object for the webcam
cap = cv2.VideoCapture(video_id)

while True:
    # Capture a frame from the webcam
    ret, frame = cap.read()

    # Convert the frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Display the frame
    cv2.imshow('frame', frame)

    # Wait for a key press and check if it's the 'q' key
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the video capture object and close all windows
cap.release()
cv2.destroyAllWindows()
