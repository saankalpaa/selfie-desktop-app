import cv2

#Load a pre-trained Haar Cascade classifier to perform face detection .
face_classifier = cv2.CascadeClassifier(cv2.data.haarcascades +'haarcascade_frontalface_default.xml')

#Open your camera --- make sure there aren't more than one face as this will trigger multiple detections. The code can handle this, but for your project this will cause an issue.  
face_cap = cv2.VideoCapture(0)

#Exit the program if the camera cannot be opened. 
if not face_cap.isOpened():
    exit()

def draw_quadrants_and_center_box(frame):
    height, width = frame.shape[:2]
    center_coords_x = width // 2
    center_coords_y = height // 2
    
    # define center box size (let's assign 20% of the screen to the width and 40% to height such that we can have the face detector bounding box exactly inside the center rectangle)
    center_box_width = int(width * 0.2) 
    center_box_height = int(height * 0.4)
    
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

#Keep looping until 'q' is pressed to quit. 
while True:
    #Read a frame from the camera.
    im_ret, im_frame = face_cap.read()

    #If im_ret returns an error.
    if not im_ret:
        print("Error reading from camera.")
        break

    # draw quadrants and center box in the frame for making it easier to visualize where the face of the person is in
    im_frame = draw_quadrants_and_center_box(im_frame)
    
    #Perform grayscale conversion for better detection accuracy.
    gray_frame = cv2.cvtColor(im_frame, cv2.COLOR_BGR2GRAY)

    #Use the face detector on the gray scale or gray_frame.
    faces = face_classifier.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=10, minSize=(30, 30))

    #For each face that you detect, draw a bounding box. 
    for (x, y, w, h) in faces:      
        cv2.rectangle(im_frame, (x, y), (x + w, y + h), (255, 0, 0), 3)

        #On the console print out the coordinates of the face. 
        print(f"Face found at: x-coord={x}, y-coord={y}, width={w}, height={h}")

    #Display the frame with the bounding boxes around the face.
    cv2.imshow('Face Detector Example', im_frame)

    #Exit the program when the 'q' key is pressed. 
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

#Perform clean up. 
face_cap.release()
cv2.destroyAllWindows()