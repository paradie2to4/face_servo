#!/usr/bin/env python3
"""
PC Vision Node - Face Detection and Tracking
Detects faces, determines movement, and publishes to MQTT
"""

import cv2
import time
import json
import paho.mqtt.client as mqtt
from datetime import datetime


# CONFIGURATION - CHANGE THESE VALUES
TEAM_ID = "BACK-BENCHERS"
MQTT_BROKER = "157.173.101.159"
MQTT_PORT = 1883
MQTT_TOPIC = f"vision/{TEAM_ID}/movement"
MQTT_HEARTBEAT = f"vision/{TEAM_ID}/heartbeat"

# Face detection parameters
FACE_MARGIN = 50  # Pixels from center to consider "centered"
CONFIDENCE_THRESHOLD = 0.7
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# MQTT Setup
mqtt_client = mqtt.Client(client_id=f"vision_pc_{TEAM_ID}")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✓ Connected to MQTT broker at {MQTT_BROKER}")
        # Publish heartbeat
        heartbeat = {
            "node": "pc",
            "status": "ONLINE",
            "timestamp": int(time.time())
        }
        client.publish(MQTT_HEARTBEAT, json.dumps(heartbeat), retain=True)
    else:
        print(f"✗ Connection failed with code {rc}")

def on_disconnect(client, userdata, rc):
    print("✗ Disconnected from MQTT broker")

mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect

print(f"Connecting to MQTT broker: {MQTT_BROKER}:{MQTT_PORT}")
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()

# Face Detection Setup
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Camera Setup
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

if not cap.isOpened():
    print("✗ Error: Could not open camera")
    exit(1)

print("✓ Camera initialized")
print(f"✓ Publishing to topic: {MQTT_TOPIC}")
print(f"✓ Team ID: {TEAM_ID}")
print("\nPress 'q' to quit\n")


# Movement Detection Function
def determine_movement(face_center_x, frame_center_x, width):
    """
    Determines movement based on face position
    Returns: (status, confidence)
    """
    offset = face_center_x - frame_center_x
    
    # Calculate confidence based on distance from center
    confidence = min(abs(offset) / (FRAME_WIDTH / 2), 1.0)
    
    if abs(offset) < FACE_MARGIN:
        return "CENTERED", confidence
    elif offset < -FACE_MARGIN:
        return "MOVE_RIGHT", confidence  # Face is on left, servo moves right
    elif offset > FACE_MARGIN:
        return "MOVE_LEFT", confidence   # Face is on right, servo moves left
    else:
        return "CENTERED", confidence

# Main Loop
last_status = None
last_publish_time = 0
PUBLISH_INTERVAL = 0.1  # Publish every 100ms

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("✗ Failed to grab frame")
            break
        
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(50, 50)
        )
        
        frame_center_x = FRAME_WIDTH // 2
        frame_center_y = FRAME_HEIGHT // 2
        
        # Draw center line
        cv2.line(frame, (frame_center_x, 0), (frame_center_x, FRAME_HEIGHT), (0, 255, 0), 2)
        cv2.line(frame, (frame_center_x - FACE_MARGIN, 0), 
                 (frame_center_x - FACE_MARGIN, FRAME_HEIGHT), (0, 255, 255), 1)
        cv2.line(frame, (frame_center_x + FACE_MARGIN, 0), 
                 (frame_center_x + FACE_MARGIN, FRAME_HEIGHT), (0, 255, 255), 1)
        
        current_time = time.time()
        
        if len(faces) > 0:
            # Use the largest face (closest to camera)
            largest_face = max(faces, key=lambda rect: rect[2] * rect[3])
            (x, y, w, h) = largest_face
            
            # Calculate face center
            face_center_x = x + w // 2
            face_center_y = y + h // 2
            
            # Determine movement
            status, confidence = determine_movement(face_center_x, frame_center_x, w)
            
            # Draw rectangle around face
            color = (0, 255, 0) if status == "CENTERED" else (0, 0, 255)
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            
            # Draw face center point
            cv2.circle(frame, (face_center_x, face_center_y), 5, (255, 0, 0), -1)
            
            # Display status
            cv2.putText(frame, f"Status: {status}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            cv2.putText(frame, f"Confidence: {confidence:.2f}", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Publish to MQTT (throttled)
            if current_time - last_publish_time >= PUBLISH_INTERVAL:
                if status != last_status or status != "CENTERED":
                    message = {
                        "status": status,
                        "confidence": round(confidence, 2),
                        "timestamp": int(current_time),
                        "face_position": {
                            "x": int(face_center_x),
                            "y": int(face_center_y)
                        }
                    }
                    
                    mqtt_client.publish(MQTT_TOPIC, json.dumps(message), qos=1)
                    print(f"→ {status} (confidence: {confidence:.2f})")
                    
                    last_status = status
                    last_publish_time = current_time
        
        else:
            # No face detected
            cv2.putText(frame, "Status: NO_FACE", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Publish NO_FACE status
            if current_time - last_publish_time >= PUBLISH_INTERVAL:
                if last_status != "NO_FACE":
                    message = {
                        "status": "NO_FACE",
                        "confidence": 0.0,
                        "timestamp": int(current_time)
                    }
                    
                    mqtt_client.publish(MQTT_TOPIC, json.dumps(message), qos=1)
                    print("→ NO_FACE")
                    
                    last_status = "NO_FACE"
                    last_publish_time = current_time
        
        # Display the frame
        cv2.imshow('Face Tracking - Press Q to quit', frame)
        
        # Check for quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    print("\n\n✓ Shutting down gracefully...")

finally:
    # Cleanup
    heartbeat = {
        "node": "pc",
        "status": "OFFLINE",
        "timestamp": int(time.time())
    }
    mqtt_client.publish(MQTT_HEARTBEAT, json.dumps(heartbeat), retain=True)
    
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    cap.release()
    cv2.destroyAllWindows()
    print("✓ Cleanup complete")