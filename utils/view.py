from datetime import datetime
import subprocess
import platform
import cv2
import os

def draw_quadrants_and_center_box(frame):
    height, width = frame.shape[:2]
    center_coords_x = width // 2
    center_coords_y = height // 2
    
    # define center box size (let's assign 30% of the screen to the width and 45% to height such that we can have the face detector bounding box exactly inside the center rectangle)
    center_box_width = int(width * 0.3) 
    center_box_height = int(height * 0.45)
    
    # draw a vertical center line
    cv2.line(frame, (center_coords_x, 0), (center_coords_x, height), (255, 255, 255), 2)
    
    # draw a horizontal center line
    cv2.line(frame, (0, center_coords_y), (width, center_coords_y), (255, 255, 255), 2)
    
    # draw the center box
    top_left = (center_coords_x - center_box_width // 2, center_coords_y - center_box_height // 2)
    bottom_right = (center_coords_x + center_box_width // 2, center_coords_y + center_box_height // 2)
    cv2.rectangle(frame, top_left, bottom_right, (0, 255, 0), 2)
    
    # let's add labels to each quadrant and also teh center box
    font = cv2.FONT_HERSHEY_COMPLEX
    cv2.putText(frame, 'TL', (20, 30), font, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, 'TR', (center_coords_x + 20, 30), font, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, 'BL', (20, height - 20), font, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, 'BR', (center_coords_x + 20, height - 20), font, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, 'CENTER', (center_coords_x - 40, center_coords_y), font, 0.7, (0, 255, 0), 2)
    
    return frame

def get_current_postion_where_the_face_lies(face_center_x_pos, face_center_y_pos, frame_w, frame_h):
    cx, cy = frame_w // 2, frame_h // 2
    
    #Get the center zone width and height
    center_w = int(frame_w * 0.3)
    center_h = int(frame_h * 0.45)
    
    if (cx - center_w // 2) < face_center_x_pos < (cx + center_w // 2) and (cy - center_h // 2) < face_center_y_pos < (cy + center_h // 2):
        return "center"
    if face_center_x_pos < cx and face_center_y_pos < cy:
        return "top-left"
    if face_center_x_pos >= cx and face_center_y_pos < cy:
        return "top-right"
    if face_center_x_pos < cx and face_center_y_pos >= cy:
        return "bottom-left"
    
    return "bottom-right"

def is_face_fully_in_target(x, y, w, h, target, frame_w, frame_h):
    cx, cy = frame_w // 2, frame_h // 2
    
    #Get the center zone width and height
    center_w = int(frame_w * 0.3)
    center_h = int(frame_h * 0.45)
    
    # Get the coordinates of the center zone
    center_left = cx - center_w // 2
    center_right = cx + center_w // 2
    center_top = cy - center_h // 2
    center_bottom = cy + center_h // 2

    #Get the face coordinates
    face_left = x
    face_right = x + w
    face_top = y
    face_bottom = y + h

    if target == "center":
        return (face_left >= center_left and face_right <= center_right and
                face_top >= center_top and face_bottom <= center_bottom)
    if target == "top-left":
        return face_right <= cx and face_bottom <= cy
    if target == "top-right":
        return face_left >= cx and face_bottom <= cy
    if target == "bottom-left":
        return face_right <= cx and face_top >= cy
    if target == "bottom-right":
        return face_left >= cx and face_top >= cy
    
    return False

def save_image(frame):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"images/selfie_{ts}.jpg"
    
    cv2.imwrite(filename, frame)
    
    try:
        system = platform.system()
        if system == "Windows":
            os.startfile(filename)
        elif system == "Darwin": 
            subprocess.run(["open", filename])
        else: 
            subprocess.run(["xdg-open", filename])
    except Exception as e:
        print(f"Image saved but couldn't open it automatically: {e}")
    
    return filename

def check_if_user_is_facing_the_camera(gray, x, y, w, h, eye_classifier):
    """Check if user is facing the camera and if not return where is he facing towards left or right"""
    try:
        roi = gray[y:y+h, x:x+w]
    except Exception:
        return False, "no_eyes_detected"
    
    eyes = eye_classifier.detectMultiScale(roi, scaleFactor=1.1, minNeighbors=5, minSize=(10, 10))
    
    if len(eyes) < 2:
        return False, "no_eyes_detected"
    
    # Take two biggest eyes
    eyes = sorted(eyes, key=lambda e: e[2]*e[3], reverse=True)[:2]
    
    # Get y coordinates of the eyes (vertical position)
    y_pos = [e[1] + e[3]//2 for e in eyes]
    
    # Check if eyes are roughly horizontal (not tilted)
    eyes_horizontal = abs(y_pos[0] - y_pos[1]) < (h * 0.18)
    
    if not eyes_horizontal:
        return False, "no_eyes_detected"
    
    # Check horizontal alignment - calculate center of both eyes
    eye_centers_x = [(e[0] + e[2]//2) for e in eyes]
    avg_eye_center_x = sum(eye_centers_x) / len(eye_centers_x)
    
    # Calculate face center
    face_center_x = w / 2
    
    # Calculate offset as percentage of face width
    offset = (avg_eye_center_x - face_center_x) / w
    
    # Define threshold for "centered" (e.g., within 15% of center)
    CENTER_THRESHOLD = 0.15
    
    if abs(offset) <= CENTER_THRESHOLD:
        # User is facing the camera
        return True, "center"
    elif offset < -CENTER_THRESHOLD:
        # Eyes are on the left side of face ROI
        return False, "rotate_left"
    else:
        # Eyes are on the right side of face ROI
        return False, "rotate_right"