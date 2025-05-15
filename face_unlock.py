import cv2
import serial
import time
import datetime  # For timestamp logging
import os  # For logging to file

# --- Configuration ---
ARDUINO_PORT = 'COM4'  # Arduino's Serial Port (as specified)
BAUD_RATE = 9600
CASCADE_PATH = 'haarcascade_frontalface_default.xml' # Path to the Haar Cascade XML file
FRAME_WIDTH = 640 # Webcam frame width
FRAME_HEIGHT = 480 # Webcam frame height
LOG_TO_FILE = True  # Enable logging to file
LOG_FILE_PATH = "face_unlock_log.txt"  # Log file path
FACE_TIMEOUT = 5.0  # Time in seconds before system reactivates after face disappears

# --- Global Variables ---
arduino = None
log_entries = []  # Store log entries
last_face_detection_time = 0
system_active = True  # Tracks if the security system is active

def log_message(message, console_only=False):
    """Logs a message with timestamp to console and optionally to log file."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    
    if LOG_TO_FILE and not console_only:
        log_entries.append(log_entry)

def save_logs():
    """Saves accumulated logs to file."""
    if LOG_TO_FILE and log_entries:
        try:
            with open(LOG_FILE_PATH, "a") as f:
                f.write("\n".join(log_entries) + "\n")
            log_message(f"Logs saved to {LOG_FILE_PATH}", console_only=True)
            log_entries.clear()
        except Exception as e:
            print(f"Error saving logs: {e}")

def initialize_serial():
    """Initializes serial connection to Arduino."""
    global arduino
    try:
        log_message(f"Attempting to connect to Arduino on {ARDUINO_PORT} at {BAUD_RATE} baud...")
        arduino = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
        time.sleep(2) # Wait for Arduino to reset and connection to establish
        if arduino.is_open:
            log_message(f"Successfully connected to Arduino on {ARDUINO_PORT}")
            
            # Read initial messages from Arduino
            start_time = time.time()
            while time.time() - start_time < 3:  # Try for 3 seconds
                if arduino.in_waiting > 0:
                    initial_message = arduino.readline().decode('utf-8', errors='ignore').strip()
                    if initial_message:
                        log_message(f"Arduino says: {initial_message}")
                time.sleep(0.1)
                
            return True
        else:
            log_message(f"Failed to open serial port {ARDUINO_PORT}, though object was created.")
            return False
    except serial.SerialException as e:
        log_message(f"Error: Could not connect to Arduino on {ARDUINO_PORT}. {e}")
        log_message("Please check:")
        log_message("1. Arduino is connected to the PC.")
        log_message(f"2. {ARDUINO_PORT} is the correct port (check Device Manager).")
        log_message("3. No other program (like Arduino Serial Monitor) is using the port.")
        return False
    except Exception as e_gen:
        log_message(f"An unexpected error occurred during serial initialization: {e_gen}")
        return False

def send_command_to_arduino(command):
    """Sends a command to Arduino: 'D' for deactivate, 'A' for activate."""
    global arduino
    if arduino and arduino.is_open:
        try:
            arduino.write(command.encode())
            log_message(f"Sent '{command}' command to Arduino")
            
            # Read response from Arduino
            time.sleep(0.5)
            responses = []
            while arduino.in_waiting > 0:
                response = arduino.readline().decode('utf-8', errors='ignore').strip()
                if response:
                    responses.append(response)
            
            if responses:
                log_message(f"Arduino responded: {'; '.join(responses)}")
        except Exception as e:
            log_message(f"Error sending command to Arduino: {e}")
    else:
        log_message("Arduino not connected or port not open. Cannot send command.")

def main():
    global last_face_detection_time, system_active

    log_message("Face Detection Security System Starting")
    log_message(f"Configuration: Frame size={FRAME_WIDTH}x{FRAME_HEIGHT}, Face timeout={FACE_TIMEOUT}s")
    
    if not initialize_serial():
        log_message("Failed to initialize serial connection")
        save_logs()
        input("Press Enter to exit...")
        return

    face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
    if face_cascade.empty():
        log_message(f"Error: Could not load Haar Cascade classifier from {CASCADE_PATH}")
        log_message("Ensure the file exists in the same directory as the script.")
        if arduino and arduino.is_open:
            arduino.close()
        save_logs()
        input("Press Enter to exit...")
        return

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        log_message("Error: Could not open webcam.")
        if arduino and arduino.is_open:
            arduino.close()
        save_logs()
        input("Press Enter to exit...")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    log_message("Starting face detection system")
    log_message("Press 'q' in the webcam window to quit")

    face_detected_previously = False
    last_log_save = time.time()
    frames_processed = 0
    start_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            log_message("Error: Can't receive frame. Exiting ...")
            break

        frames_processed += 1
        current_time = time.time()
        elapsed = current_time - start_time

        # Performance logging
        if elapsed >= 5.0:
            fps = frames_processed / elapsed
            log_message(f"Performance: {fps:.1f} FPS", console_only=True)
            frames_processed = 0
            start_time = current_time

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))

        current_face_detected = len(faces) > 0

        if current_face_detected:
            last_face_detection_time = current_time
            if system_active:
                log_message("Face detected - Deactivating security system")
                send_command_to_arduino('D')  # Deactivate
                system_active = False

            # Draw rectangles around detected faces
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)  # Green rectangle
                cv2.putText(frame, 'System Deactivated', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        else:
            # Check if we've exceeded the face timeout
            if not system_active and (current_time - last_face_detection_time) >= FACE_TIMEOUT:
                if not system_active:
                    log_message("No face detected for 5 seconds - Reactivating security system")
                    send_command_to_arduino('A')  # Activate
                    system_active = True

        # Add status overlay
        status_text = "System: " + ("DEACTIVATED" if not system_active else "ACTIVE")
        cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, 
                    (0, 255, 0) if not system_active else (0, 0, 255), 2)

        # Add timeout countdown when face is lost
        if not current_face_detected and not system_active:
            time_since_face = current_time - last_face_detection_time
            if time_since_face < FACE_TIMEOUT:
                countdown = f"Reactivating in: {FACE_TIMEOUT - time_since_face:.1f}s"
                cv2.putText(frame, countdown, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # Add timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, timestamp, (FRAME_WIDTH - 230, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow('Face Detection Security System (Press q to quit)', frame)

        # Save logs periodically
        if current_time - last_log_save > 10.0:
            save_logs()
            last_log_save = current_time

        if cv2.waitKey(1) & 0xFF == ord('q'):
            log_message("Exiting by user request ('q' pressed)")
            break

    cap.release()
    cv2.destroyAllWindows()
    if arduino and arduino.is_open:
        arduino.close()
        log_message("Arduino connection closed")
    
    save_logs()
    log_message("Script finished")

if __name__ == '__main__':
    main()