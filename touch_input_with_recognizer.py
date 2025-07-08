import time
import xml.etree.ElementTree as ET
from pathlib import Path

import cv2
import numpy as np
from pynput.keyboard import Controller

import recognizer as recognizer_module


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

DRAW_WINDOW_SIZE= 1000

TEMPLATE_DIR= Path("letter_templates")
RECOGNITION_THRESHOLD= 0.74
MIN_POINTS_PER_LETTER= 12
SKIP_FRAMES_AFTER_PRESS= 2
FAIL_TEXT_DURATION_SECONDS= 2.5

keyboard_controller = Controller()

def read_template(xml_path: Path):
    root = ET.parse(xml_path).getroot()
    tmpl_name = root.attrib.get("Name", xml_path.stem).strip().lower()
    tmpl_points = [
        (float(pt.attrib["X"]), float(pt.attrib["Y"]))
        for pt in root.iter("Point")
    ]
    return tmpl_name, tmpl_points


def build_gesture_recognizer(window_h: int):
    recognizer = recognizer_module.DollarRecognizer(window_h= window_h)
    TEMPLATE_DIR.mkdir(exist_ok= True)

    for xml_file in TEMPLATE_DIR.glob("*.xml"):
        name, points = read_template(xml_file)
        recognizer.add_template(name, points)

    print("Buchstaben geladen:", len(recognizer.templates))
    return recognizer


def show_letters(recognizer):
    tmpl_by_name = {}
    for tmpl in recognizer.templates:
        if tmpl.name not in tmpl_by_name:
            tmpl_by_name[tmpl.name] = tmpl.raw_points

    sorted_names = sorted(tmpl_by_name.keys())

    COLS= 4
    CELL_SIZE= 200

    total = len(sorted_names)
    rows_needed = (total + COLS - 1) // COLS
    img_h = rows_needed * CELL_SIZE
    img_w = COLS * CELL_SIZE

    canvas = np.full((img_h, img_w, 3), 255, np.uint8)

    for idx, name in enumerate(sorted_names):
        row, col = divmod(idx, COLS)
        pts = tmpl_by_name[name]

        xs, ys = zip(*pts)
        w = max(xs) - min(xs) or 1
        h = max(ys) - min(ys) or 1
        scale = (CELL_SIZE - 2 * 20) / max(w, h)

        draw_pts = []
        cen_x = min(xs) + w / 2
        cen_y = min(ys) + h / 2
        for x_val, y_val in pts:
            new_x = int((x_val - cen_x) * scale + (col * CELL_SIZE + CELL_SIZE / 2))
            new_y = int((-(y_val - cen_y)) * scale + (row * CELL_SIZE + CELL_SIZE / 2))
            draw_pts.append((new_x, new_y))

        cv2.polylines(canvas, [np.array(draw_pts, np.int32)], False, (0, 0, 0), 6)
        cv2.putText(canvas,
                    name.upper(),
                    (col * CELL_SIZE + 8, row * CELL_SIZE + 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (0, 0, 200),
                    2)

    cv2.namedWindow("LettersWindow", cv2.WINDOW_NORMAL)
    cv2.imshow("LettersWindow", canvas)
    cv2.resizeWindow("LettersWindow", 800, 800)


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
    camera_capture.set(cv2.CAP_PROP_FRAME_WIDTH,  FRAME_WIDTH)
    camera_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    camera_capture.set(cv2.CAP_PROP_FPS,          TARGET_FPS)
    time.sleep(2)

    crop_top_bottom = int(FRAME_HEIGHT * 0.1)
    crop_left_right = int(FRAME_WIDTH  * 0.1)

    roi_width  = FRAME_WIDTH  - 2 * crop_left_right
    roi_height = FRAME_HEIGHT - 2 * crop_top_bottom

    scale_x = DRAW_WINDOW_SIZE / roi_width
    scale_y = DRAW_WINDOW_SIZE / roi_height

    background_float = calibrate_background(
        camera_capture, CALIBRATION_SECONDS, crop_top_bottom, crop_left_right
    )
    background_uint8 = cv2.convertScaleAbs(background_float)

    recognizer = build_gesture_recognizer(DRAW_WINDOW_SIZE)
    show_letters(recognizer)

    smoothed_x = smoothed_y = None
    presence_frames = absence_frames = 0
    finger_currently_down = False
    finger_down_start_time = 0.0
    frames_since_down = 0

    stroke_points = []
    draw_points = []
    spelled_chars = []

    last_letter = ""
    last_score = 0.0
    last_letter_time = 0.0

    fail_guess = ""
    fail_score = 0.0
    last_fail_time = 0.0

    try:
        while True:
            ok, frame = camera_capture.read()
            if not ok:
                continue
            frame = cv2.flip(frame, 1)
            now = time.time()

            roi = frame[crop_top_bottom:-crop_top_bottom,
                             crop_left_right:-crop_left_right]
            gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

            diff = cv2.subtract(background_uint8, gray_roi)
            _, finger_mask = cv2.threshold(diff, DARK_DIFF_THRESHOLD, 255, cv2.THRESH_BINARY)

            contours, _ = cv2.findContours(finger_mask, cv2.RETR_EXTERNAL,
                                           cv2.CHAIN_APPROX_SIMPLE)

            finger_contour = None
            for contour in contours:
                area = cv2.contourArea(contour)
                if not (MIN_CONTOUR_AREA <= area <= MAX_CONTOUR_AREA):
                    continue
                x, y, w, h = cv2.boundingRect(contour)
                if diff[y:y + h, x:x + w].mean() < MEAN_DARKNESS_MINIMUM:
                    continue
                finger_contour = contour
                break

            finger_present = finger_contour is not None

            if not finger_present:
                cv2.accumulateWeighted(gray_roi.astype(np.float32),
                                       background_float, 0.02)
                background_uint8 = cv2.convertScaleAbs(background_float)

            presence_frames = presence_frames + 1 if finger_present else 0
            absence_frames  = absence_frames  + 1 if not finger_present else 0

            if (finger_present and not finger_currently_down and
                    presence_frames >= PRESENCE_FRAMES_REQUIRED):
                finger_currently_down = True
                frames_since_down = 0
                finger_down_start_time = now
                stroke_points.clear()
                draw_points.clear()

            if finger_currently_down and absence_frames >= ABSENCE_FRAMES_REQUIRED:
                finger_currently_down = False
                down_time = now - finger_down_start_time

                if down_time <= TAP_DURATION_MAX_SECONDS:
                    time.sleep(TAP_RESET_SECONDS)
                else:
                    if len(stroke_points) >= MIN_POINTS_PER_LETTER:
                        res = recognizer.recognize(stroke_points)
                        if res.score >= RECOGNITION_THRESHOLD:
                            key = res.name.lower()
                            spelled_chars.append(key)
                            keyboard_controller.press(key)
                            keyboard_controller.release(key)

                            last_letter = key
                            last_score = res.score
                            last_letter_time = now
                        else:
                            fail_guess = res.name
                            fail_score = res.score
                            last_fail_time = now
                stroke_points.clear()
                draw_points.clear()

            if finger_present:
                x, y, w, h = cv2.boundingRect(finger_contour)
                cx, cy = x + w / 2, y + h / 2

                smoothed_x = (cx if smoothed_x is None
                              else SMOOTHING_ALPHA * cx +
                                   (1 - SMOOTHING_ALPHA) * smoothed_x)
                smoothed_y = (cy if smoothed_y is None
                              else SMOOTHING_ALPHA * cy +
                                   (1 - SMOOTHING_ALPHA) * smoothed_y)

                scaled_x = int(np.clip(smoothed_x * scale_x, 0, DRAW_WINDOW_SIZE))
                scaled_y = int(np.clip(smoothed_y * scale_y, 0, DRAW_WINDOW_SIZE))
                last_coords = (scaled_x, scaled_y)

                cv2.circle(roi, (int(smoothed_x), int(smoothed_y)), 6, (0, 255, 0), -1)

                if finger_currently_down:
                    frames_since_down += 1
                    if frames_since_down > SKIP_FRAMES_AFTER_PRESS:
                        stroke_points.append(last_coords)
                        draw_points.append((int(smoothed_x), int(smoothed_y)))

            if len(draw_points) >= 2:
                cv2.polylines(roi, [np.array(draw_points, np.int32)],
                              False, (255, 0, 0), 2)

            spelled_word = "".join(spelled_chars).upper()
            cv2.putText(roi,
                        f"Spelled word: {spelled_word}",
                        (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (255, 255, 255),
                        2)

            if now - last_fail_time < FAIL_TEXT_DURATION_SECONDS:
                cv2.putText(
                    roi,
                    f"No valid letter (best guess: {fail_guess.upper()} "
                    f"{fail_score * 100:.0f}%)",
                    (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.74,
                    (0, 20, 255),
                    2,
                )
            elif last_letter and now - last_letter_time < 2:
                cv2.putText(
                    roi,
                    f"Letter: {last_letter.upper()} "
                    f"({last_score * 100:.0f}% certainty)",
                    (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (255, 200, 0),
                    2,
                )

            cv2.imshow(
                "touch_input_with_recognizer.py | ESC to exit",
                cv2.resize(roi, (DRAW_WINDOW_SIZE, DRAW_WINDOW_SIZE)),
            )
            if cv2.waitKey(1) & 0xFF == 27: #27=esc
                break

    finally:
        camera_capture.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
