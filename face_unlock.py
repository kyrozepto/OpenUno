import cv2
import serial
import time

# --- Configuration ---
ARDUINO_PORT = 'COM4'  # Arduino's Serial Port (as specified)
BAUD_RATE = 9600
CASCADE_PATH = 'haarcascade_frontalface_default.xml' # Path to the Haar Cascade XML file
UNLOCK_COOLDOWN = 5 # Seconds to wait before sending another unlock command
FRAME_WIDTH = 640 # Webcam frame width
FRAME_HEIGHT = 480 # Webcam frame height

# --- Global Variables ---
last_unlock_time = 0
arduino = None

def initialize_serial():
    """Initializes serial connection to Arduino."""
    global arduino
    try:
        print(f"Attempting to connect to Arduino on {ARDUINO_PORT} at {BAUD_RATE} baud...")
        arduino = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
        time.sleep(2) # Wait for Arduino to reset and connection to establish
        if arduino.is_open:
            print(f"Successfully connected to Arduino on {ARDUINO_PORT}")
            # Optional: Read any initial messages from Arduino
            # for _ in range(3): # Try to read a few lines
            #     if arduino.in_waiting > 0:
            #         initial_message = arduino.readline().decode('utf-8', errors='ignore').strip()
            #         print(f"Arduino initial: {initial_message}")
            #     else:
            #         break
            return True
        else:
            print(f"Failed to open serial port {ARDUINO_PORT}, though object was created.")
            return False
    except serial.SerialException as e:
        print(f"Error: Could not connect to Arduino on {ARDUINO_PORT}. {e}")
        print("Please check:")
        print("1. Arduino is connected to the PC.")
        print(f"2. {ARDUINO_PORT} is the correct port (check Device Manager).")
        print("3. No other program (like Arduino Serial Monitor) is using the port.")
        return False
    except Exception as e_gen:
        print(f"An unexpected error occurred during serial initialization: {e_gen}")
        return False


def send_unlock_command():
    """Sends the unlock command 'U' to Arduino."""
    global arduino, last_unlock_time
    current_time = time.time()
    if arduino and arduino.is_open:
        if (current_time - last_unlock_time) > UNLOCK_COOLDOWN:
            try:
                arduino.write(b'U') # Send 'U' as bytes
                print(f"Sent 'U' (Unlock) command to Arduino at {time.strftime('%H:%M:%S')}.")
                last_unlock_time = current_time
                # Optional: Read response from Arduino
                # time.sleep(0.1) # Give Arduino a moment to respond
                # if arduino.in_waiting > 0:
                #    response = arduino.readline().decode('utf-8', errors='ignore').strip()
                #    if response:
                #        print(f"Arduino says: {response}")
            except Exception as e:
                print(f"Error sending command to Arduino: {e}")
        else:
            # This message can be spammy, so only print if debugging
            # print("Unlock command in cooldown.")
            pass
    else:
        print("Arduino not connected or port not open. Cannot send command.")

def main():
    global last_unlock_time

    if not initialize_serial():
        input("Press Enter to exit...") # Keep console open to see error
        return

    # Load the Haar Cascade for face detection
    face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
    if face_cascade.empty():
        print(f"Error: Could not load Haar Cascade classifier from {CASCADE_PATH}")
        print("Ensure the file exists in the same directory as the script,")
        print("or the path is correct, and OpenCV is installed correctly.")
        if arduino and arduino.is_open:
            arduino.close()
        input("Press Enter to exit...")
        return

    # Initialize webcam
    cap = cv2.VideoCapture(0) # 0 is usually the default webcam
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        if arduino and arduino.is_open:
            arduino.close()
        input("Press Enter to exit...")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    print("Starting face detection. A window with webcam feed should appear.")
    print("Press 'q' in the webcam window to quit.")

    face_detected_previously = False

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Can't receive frame (stream end?). Exiting ...")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Performance: Use a slightly larger scaleFactor and minNeighbors if CPU is high
        # minSize can be increased if you only want to detect larger/closer faces
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))

        current_face_detected = len(faces) > 0

        if current_face_detected:
            if not face_detected_previously:
                print(f"Face detected! ({len(faces)} faces found)")
            send_unlock_command() # Send unlock if face is detected

            # Draw rectangles around detected faces (for visual feedback)
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2) # Blue rectangle
        # else:
        #     if face_detected_previously:
        #         print("Face no longer detected.") # Optional: log when face is lost

        face_detected_previously = current_face_detected

        # Display the resulting frame
        cv2.imshow('Face Detection - Door Unlock System (Press q to quit)', frame)

        # Check for 'q' key press to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Exiting by user request ('q' pressed)...")
            break

    # Release resources
    cap.release()
    cv2.destroyAllWindows()
    if arduino and arduino.is_open:
        arduino.close()
        print("Arduino connection closed.")
    print("Script finished.")

if __name__ == '__main__':
    main()