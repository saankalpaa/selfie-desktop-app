import platform
import subprocess
import speech_recognition as sr
from constant import MAX_ATTEMPTS_TO_GET_A_TARGET_POSITION, VALID_POSITIONS

recognizer = sr.Recognizer()
microphone = sr.Microphone()

system = platform.system()

with microphone as source:
    recognizer.adjust_for_ambient_noise(source, duration=1.5)


def speak(text: str):
    """This supports both windows and macOs"""
    print('[APP]: ', text)
    
    try:
        if system == "Darwin":
            # for macOs we use macOs "say" command
            subprocess.run(['say', text], check=True)
        elif system == "Windows":
            # for windows we use pyttsx3 engine
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty('rate', 150)
            engine.say(text)
            engine.runAndWait() 
    except Exception as e:
        print("TTS Error", e)
              

def listen_for_command():
    with microphone as source:
        print("[LISTENING...]")
        
        try:
            audio = recognizer.listen(source, timeout=3, phrase_time_limit=8)
            print("[PROCESSING]")
            command = recognizer.recognize_google(audio).lower()
            print(f"[USER]: {command}")
            return command
        except sr.WaitTimeoutError:
            print("[No speech detected]")
            return None
        except sr.UnknownValueError:
            print("[COULD NOT UNDERSTAND]")
            return None
        except sr.RequestError as e:
            print(f"[ERROR]: {e}")
            return None


def get_target_position():
    # Ask user for the target postion
    speak("Welcome to the selfie app!")
    speak("Where would you like your face to appear?")
    speak("Your options are: top left, top right, bottom left, bottom right, or center.")
    
    attempts = 0
    
    while attempts < MAX_ATTEMPTS_TO_GET_A_TARGET_POSITION:
        cmd = listen_for_command()
    
        if cmd is None:
            speak("I didn't catch that. Please try again.")
            attempts += 1
            continue
    
        for pos in VALID_POSITIONS:
            if pos in cmd:
                speak(f"Got it! {pos} has been set as the position.")
                return pos.replace(" ", "-")
    
        speak("I didn't understand that position. Please choose from: top left, top right, bottom left, bottom right, or center.")
    
        attempts += 1
    
    speak("Too many attempts. Setting the position as center by default!")
    
    return "center"

def get_guidance_for_user(current_position, target_position):
    # Guidance mapping based on where the user is currently and where the user needs to go towards
    mapping = {
        "top-left": (-1, -1),
        "top-right": (1, -1),
        "bottom-left": (-1, 1),
        "bottom-right": (1, 1),
        "center": (0, 0)
    }
    cx, cy = mapping.get(current_position, (0,0))
    tx, ty = mapping.get(target_position, (0,0))
    dx = tx - cx
    dy = ty - cy
    parts = []
    if dy < 0:
        parts.append("one step forward")
    elif dy > 0:
        parts.append("one step back without turning around")
    if dx < 0:
        parts.append("one side-step to your left")
    elif dx > 0:
        parts.append("one side-step to your right")
    if not parts:
        # in case of current position and target position is same but the face is not fully inside the position/quadrant. so just try to move a user to take them out of this edge case. this is not the perfect solution but it just does the job of taking user out of this weird position
        if current_position == "top-left":
            return "Take one side-step to your left and one step forward"
        elif current_position == "top-right":
            return "Take one side-step to your right and one step forward"
        elif current_position == "bottom-right":
            return "Take one side-step to your right and one step back without turning around"
        elif current_position == "bottom-left":
            return "Take one side-step to your left and one step back without turning around"
        else:
            return "Take one side-step to your right"
    return "Take " + " and ".join(parts)