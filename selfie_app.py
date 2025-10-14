import time
import cv2

from constant import EDGE_THRESHOLD, GUIDANCE_INTERVAL, INITIAL_FACE_DETECTION_WAIT_TIME, REQUIRED_STABLE_FRAMES
from utils.view import draw_quadrants_and_center_box, get_current_postion_where_the_face_lies, is_face_fully_in_target, save_image
from utils.speech import get_guidance_for_user, get_target_position, speak

def main():
    target_position = get_target_position()
    
    #Load a pre-trained Haar Cascade classifier to perform face detection
    face_classifier = cv2.CascadeClassifier(cv2.data.haarcascades +'haarcascade_frontalface_default.xml')

    #Open your camera --- make sure there aren't more than one face as this will trigger multiple detections. The code can handle this, but for your project this will cause an issue.  
    face_cap = cv2.VideoCapture(0)
    
    if not face_cap.isOpened():
        print("Couldn't open the camera")
        speak("Sorry, Couldn't open camera at the moment. Please try again later!")
        return
    
    frame_width = int(face_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(face_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    cv2.namedWindow('Selfie App', cv2.WINDOW_NORMAL)
    cv2.setWindowProperty('Selfie App', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    has_image_been_captured = False
    last_guidance_time = time.time() - GUIDANCE_INTERVAL
    
    last_detected_quad_coords_of_user= None #if user has been seen or their face has been detected previously in the same session store that so that guidance is given based on this memory
    user_last_detected_time=0 #tracks the time when users face was last detected
    
    offscreen_last_command = "initial" #to know what should be the next command to give to the user should be given based on the last guidance
    
    has_countdown_started = False
    last_countdown_value = None
    
    frames_in_target = 0
    
    initial_face_detection = False
    initial_face_detection_start = time.time()
    
    #Keep looping until 'q' is pressed to quit or an image has been captured
    while True:
        #Read a frame from the camera.
        im_ret, im_frame = face_cap.read()

        #If im_ret returns an error.
        if not im_ret:
            print("Error reading from camera.")
            break

        # make sure the image is not mirrored to avoid confusion in directions
        im_frame = cv2.flip(im_frame, 1)
        

        # draw quadrants and center box in the frame for making it easier to visualize where the face of the person is in
        im_frame = draw_quadrants_and_center_box(im_frame)
        
        #maintain a copy of frame so that when image is saved it is saved without the bounding boxes and quadrants
        copy_of_frame = im_frame.copy()
        
        #Perform grayscale conversion for better detection accuracy.
        gray_frame = cv2.cvtColor(im_frame, cv2.COLOR_BGR2GRAY)

        #Use the face detector on the gray scale or gray_frame.
        faces = face_classifier.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=10, minSize=(30, 30))

        # keep track of current time
        current_time = time.time()
        
        # give 5 seconds for initial detection before giving guidance
        if not initial_face_detection:
            if len(faces) > 0:
                # face detected
                initial_face_detection = True
                user_last_detected_time = current_time
            elif (current_time - initial_face_detection_start) >= INITIAL_FACE_DETECTION_WAIT_TIME:
                # face wasn't detected proceed with the guidance
                initial_face_detection = True
            else:
                cv2.imshow('Selfie App', im_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                continue 

        if len(faces) > 0 and not has_image_been_captured:   
            #choose the largest face
            faces = sorted(faces, key=lambda f: f[2]*f[3], reverse=True)
            
            x, y, w, h = faces[0]
            
            #Only draw a bounding box to one face that is the largest face detected
            cv2.rectangle(im_frame, (x, y), (x + w, y + h), (255, 0, 0), 3)
            
            #Draw a circular dot on the center of the face
            face_center_x_pos = x + w // 2
            face_center_y_pos = y + h // 2
            
            cv2.circle(im_frame, (face_center_x_pos, face_center_y_pos), 5, (0, 0, 255), -1)
            
            current_quadrant = get_current_postion_where_the_face_lies(face_center_x_pos, face_center_y_pos, frame_width, frame_height)
            fully_in_target = is_face_fully_in_target(x, y, w, h, target_position, frame_width, frame_height)
            
            print(f"Face in: {current_quadrant}, Target: {target_position}, Fully inside: {fully_in_target}")
            
            last_detected_quad_coords_of_user = (x, y, w, h)
            offscreen_last_command= "initial"


            if not fully_in_target:
                    #if the user is not in the target position guide them towards the target position
                    has_countdown_started = False
                    frames_in_target = 0

                    if current_time - last_guidance_time >= GUIDANCE_INTERVAL:
                        guidance = get_guidance_for_user(current_quadrant, target_position)
                        speak(guidance)
                        
                        last_guidance_time = current_time
                        
            else:
                    # face is in the target position and also facing the camera
                    frames_in_target += 1
                    
                    # when first entering stable zone
                    if frames_in_target == 1 and not has_countdown_started:
                        speak("Hold still")
                        has_countdown_started = True
                        
                    remaining_frames = max(REQUIRED_STABLE_FRAMES - frames_in_target, 0)
                    countdown = int((remaining_frames / max(REQUIRED_STABLE_FRAMES, 1)) * 3) + 1
                    countdown = min(max(countdown, 1), 3)
                    
                    if countdown != last_countdown_value and current_time - last_guidance_time >= 0.9:
                        speak(str(countdown))
                        
                        last_countdown_value = countdown
                        last_guidance_time = current_time
                    
                    cv2.putText(im_frame, f"Hold still... {countdown}", 
                               (frame_width // 2 - 150, 50),
                               cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
                               
                    
                    if frames_in_target >= REQUIRED_STABLE_FRAMES:
                        speak("Perfect! Smile!")
                        
                        time.sleep(0.5)
                        
                        filename = save_image(copy_of_frame)
                        
                        speak("Picture has been clicked and saved")
                        print(f"[INFO] Image saved: {filename}")
                        
                        has_image_been_captured = True
                        
                        # short delay then quit loop
                        time.sleep(1)
                        break
                    
        else:
            # If face isn't detected or the image has been captured already
            
            frames_in_target = 0
            has_countdown_started = False
            last_countdown_value = None    
                    
            time_since_last_face_was_detected = current_time - user_last_detected_time if user_last_detected_time else None
            
            if current_time - last_guidance_time >= GUIDANCE_INTERVAL and not has_image_been_captured:
                if last_detected_quad_coords_of_user and time_since_last_face_was_detected is not None and time_since_last_face_was_detected <= GUIDANCE_INTERVAL:
                    lx, ly, lw, lh = last_detected_quad_coords_of_user
                    
                    towards_left = lx < (frame_width * EDGE_THRESHOLD)
                    towards_right = (lx + lw) > (frame_width * (1 - EDGE_THRESHOLD))
                    towards_top = ly < (frame_height * EDGE_THRESHOLD)
                    towards_bottom = (ly + lh) > (frame_height * (1 - EDGE_THRESHOLD))

                    if towards_left:
                        speak("Take one side-step to your right")
                    elif towards_right:
                        speak("Take one side-step to your left")
                    elif towards_top:
                        speak("Take one step backwards without turning around")
                    elif towards_bottom:
                        speak("Take one step forward")
                    else:
                        fx = lx + lw // 2
                        fy = ly + lh // 2
                        last_q = get_current_postion_where_the_face_lies(fx, fy, frame_width, frame_height)
                        guidance = get_guidance_for_user(last_q, target_position)
                        speak("I lost your face ", guidance)
                        
                    last_guidance_time = current_time
                    
                else:
                    #Users face hasn't been detected once in this session so just follow a pattern
                    if offscreen_last_command == "initial":
                        speak("I cannot see your face. Please try slightly turning your head towards the sound.")
                        offscreen_last_command = "rotate_head"
                    elif offscreen_last_command == "rotate_head":
                        speak("Please take two steps back without turning around.")
                        offscreen_last_command = "step_back"
                    elif offscreen_last_command == "step_back":
                        speak("Perfect. Now take two side-steps towards your left side.")
                        offscreen_last_command = "move_left"
                        
                    elif offscreen_last_command == "move_left":
                        speak("Okay. Now take four side-steps towards your right side.")
                        offscreen_last_command = "move_right"
                        
                    elif offscreen_last_command == "move_closer":
                        speak("Now take one more step backward without turning around.")
                        offscreen_last_command = "final_adjust"
                    else:
                        speak("Please adjust your position slowly; I’ll keep guiding you.")
                        offscreen_last_command = "initial"
                    last_guidance_time = current_time
                    
        cv2.imshow('Selfie App', im_frame)

        # Exit on 'q' key
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        
    # Cleanup
    face_cap.release()
    cv2.destroyAllWindows()
    
    if not has_image_been_captured:
        speak("Session ended!")
    else:
        speak("Goodbye!")
        
if __name__ == "__main__":
    main()
