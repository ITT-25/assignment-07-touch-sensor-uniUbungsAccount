import cv2
import numpy as np
import socket
import json
import time

FRAME_WIDTH= 640
FRAME_HEIGHT= 480
TARGET_FPS= 30

CALIBRATION_SECONDS= 3

DARK_DIFF_THRESHOLD= 25
MEAN_DARKNESS_MINIMUM= 20
MIN_CONTOUR_AREA= 800
MAX_CONTOUR_AREA= 5000

PRESENCE_FRAMES_REQUIRED= 2
ABSENCE_FRAMES_REQUIRED= 2
TAP_DURATION_MAX_SECONDS= 0.35
TAP_RESET_SECONDS= 0.04
TAP_TEXT_DURATION_SECONDS= 1.0

SMOOTHING_ALPHA= 0.5

FITTS_WINDOW_SIZE= 800

UDP_IP_ADDRESS= "127.0.0.1"
UDP_PORT_NUMBER= 5700


def calibrate_background(capture, seconds, top_crop, left_crop):
    print("Kalibriere, Bitte nicht anfassen!")
    background_frames = []
    calibration_start = time.time()

    while time.time() - calibration_start < seconds:
        ok, frame = capture.read()
        if not ok:
            continue
        region_of_interest = frame[top_crop:-top_crop, left_crop:-left_crop]
        gray_roi = cv2.cvtColor(region_of_interest, cv2.COLOR_BGR2GRAY)
        background_frames.append(gray_roi.astype(np.float32))

        cv2.imshow("Kalibriere...", region_of_interest)

    cv2.destroyWindow("Kalibriere...")
    return np.mean(background_frames, axis=0).astype(np.float32)


def main() -> None:
    camera_capture = cv2.VideoCapture(0)
    camera_capture.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    camera_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    camera_capture.set(cv2.CAP_PROP_FPS, TARGET_FPS)
    time.sleep(2)

    crop_top_bottom = int(FRAME_HEIGHT * 0.1)
    crop_left_right = int(FRAME_WIDTH * 0.1)
    roi_width = FRAME_WIDTH - 2 * crop_left_right
    roi_height = FRAME_HEIGHT - 2 * crop_top_bottom
    scale_x = FITTS_WINDOW_SIZE / roi_width
    scale_y = FITTS_WINDOW_SIZE / roi_height

    background_float = calibrate_background(
        camera_capture, CALIBRATION_SECONDS, crop_top_bottom, crop_left_right
    )
    background_uint8 = cv2.convertScaleAbs(background_float)

    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    smoothed_x = smoothed_y = None
    presence_frames = absence_frames = 0
    finger_currently_down = False
    finger_down_start_time = 0.0

    last_tap_time= -1.0
    last_tap_coordinates = (0, 0)

    try:
        while True:
            ok, frame = camera_capture.read()
            if not ok:
                continue
            now = time.time()

            roi = frame[crop_top_bottom:-crop_top_bottom,
                        crop_left_right:-crop_left_right]
            gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

            darkness_difference = cv2.subtract(background_uint8, gray_roi)
            _, finger_mask = cv2.threshold(
                darkness_difference,
                DARK_DIFF_THRESHOLD,
                255,
                cv2.THRESH_BINARY
            )

            finger_contour = None
            contours, _ = cv2.findContours(
                finger_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            for contour in contours:
                area = cv2.contourArea(contour)
                if not (MIN_CONTOUR_AREA <= area <= MAX_CONTOUR_AREA):
                    continue
                x, y, w, h = cv2.boundingRect(contour)
                if darkness_difference[y:y + h, x:x + w].mean(
                ) < MEAN_DARKNESS_MINIMUM:
                    continue
                finger_contour = contour
                break

            finger_present = finger_contour is not None

            if not finger_present:
                cv2.accumulateWeighted(
                    gray_roi.astype(np.float32),
                    background_float,
                    0.02
                )
                background_uint8 = cv2.convertScaleAbs(background_float)

            presence_frames = presence_frames + 1 if finger_present else 0
            absence_frames = absence_frames  + 1 if not finger_present else 0

            if (finger_present and
                    not finger_currently_down and
                    presence_frames >= PRESENCE_FRAMES_REQUIRED):
                finger_currently_down = True
                finger_down_start_time = now

            if (finger_currently_down and
                    absence_frames >= ABSENCE_FRAMES_REQUIRED):
                finger_currently_down = False
                if now - finger_down_start_time <= TAP_DURATION_MAX_SECONDS:
                    for value in (1, 0):
                        udp_socket.sendto(
                            json.dumps({"tap": value}).encode(),
                            (UDP_IP_ADDRESS, UDP_PORT_NUMBER)
                        )
                        if value == 1:
                            time.sleep(TAP_RESET_SECONDS)
                    last_tap_time        = now
                    last_tap_coordinates = last_sent_coordinates

            if finger_present:
                x, y, w, h = cv2.boundingRect(finger_contour)
                centre_x, centre_y = x + w / 2, y + h / 2

                if smoothed_x is None:
                    smoothed_x, smoothed_y = centre_x, centre_y
                else:
                    smoothed_x = (
                        SMOOTHING_ALPHA * centre_x +
                        (1 - SMOOTHING_ALPHA) * smoothed_x
                    )
                    smoothed_y = (
                        SMOOTHING_ALPHA * centre_y +
                        (1 - SMOOTHING_ALPHA) * smoothed_y
                    )

                scaled_x = int(max(
                    0, min(FITTS_WINDOW_SIZE, smoothed_x * scale_x)
                ))
                scaled_y = int(max(
                    0, min(FITTS_WINDOW_SIZE, smoothed_y * scale_y)
                ))
                last_sent_coordinates = (scaled_x, scaled_y)

                udp_socket.sendto(
                    json.dumps({"movement": {
                        "x": scaled_x, "y": scaled_y
                    }}).encode(),
                    (UDP_IP_ADDRESS, UDP_PORT_NUMBER)
                )

                cv2.circle(
                    roi,
                    (int(smoothed_x), int(smoothed_y)),
                    6,
                    (0, 255, 0),
                    -1
                )

            if now - last_tap_time < TAP_TEXT_DURATION_SECONDS:
                cv2.putText(
                    roi,
                    f"Tap ({last_tap_coordinates[0]}, {last_tap_coordinates[1]})",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (0, 0, 255),
                    2,
                    cv2.LINE_AA
                )

            cv2.imshow(
                "touch_input.py | ESC to exit | Thick Pencil or TV-Remote works best | Tap briefly to click",
                cv2.resize(roi, (FRAME_WIDTH, FRAME_HEIGHT))
            )
            if cv2.waitKey(1) & 0xFF == 27: #27=esc
                break

    finally:
        camera_capture.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
