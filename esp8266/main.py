# main.py
# ESP8266 Servo Controller - Face Tracking System
# Based on Gabriel Baziramwabo's ESP8266 MQTT implementation

import time
import network
import machine
import ubinascii
import ujson as json
from machine import Pin, PWM
from umqtt.simple import MQTTClient

# CONFIGURATION - EDIT THESE VALUES
WIFI_SSID = "RCA"
WIFI_PASS = "password123"

MQTT_BROKER = "157.173.101.159"
MQTT_PORT = 1883

TEAM_ID = "BACK-BENCHERS"
TOPIC_MOVEMENT = f"vision/{TEAM_ID}/movement"
TOPIC_HEARTBEAT = f"vision/{TEAM_ID}/heartbeat"

# Servo configuration
SERVO_PIN = 4  # D2 (GPIO4) - same as LED in Gabriel's example
SERVO_MIN_DUTY = 40   # ~0 degrees (adjust for your servo)
SERVO_MAX_DUTY = 115  # ~180 degrees (adjust for your servo)
SERVO_CENTER_DUTY = 77  # ~90 degrees
SERVO_FREQ = 50  # 50Hz for standard servos

# Movement parameters
MOVE_STEP = 3  # Degrees to move per command
MOVE_DELAY_MS = 50  # Delay between movements (reduce jitter)
SMOOTHING_ENABLED = True

# Generate unique client ID
CLIENT_ID = b"esp8266_" + ubinascii.hexlify(machine.unique_id())

# Global variables
current_angle = 90  # Start at center
target_angle = 90
last_move_time = 0
mqtt_client = None

# Servo Setup
servo = PWM(Pin(SERVO_PIN), freq=SERVO_FREQ)

def angle_to_duty(angle):
    """Convert angle (0-180) to PWM duty cycle"""
    angle = max(0, min(180, angle))
    duty = SERVO_MIN_DUTY + (angle / 180.0) * (SERVO_MAX_DUTY - SERVO_MIN_DUTY)
    return int(duty)

def set_servo_angle(angle):
    """Set servo to specific angle"""
    global current_angle
    duty = angle_to_duty(angle)
    servo.duty(duty)
    current_angle = angle

# Network Functions
def wifi_connect():
    """Connect to Wi-Fi"""
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    
    if not sta.isconnected():
        print(f"Connecting to WiFi: {WIFI_SSID}")
        sta.connect(WIFI_SSID, WIFI_PASS)
        
        start = time.ticks_ms()
        while not sta.isconnected():
            if time.ticks_diff(time.ticks_ms(), start) > 20000:
                raise RuntimeError("Wi-Fi connection timeout")
            time.sleep(0.3)
    
    print(f"✓ Wi-Fi connected: {sta.ifconfig()[0]}")

# MQTT Functions
def mqtt_callback(topic, msg):
    """Handle incoming MQTT messages"""
    global target_angle
    
    try:
        if topic == TOPIC_MOVEMENT.encode():
            data = json.loads(msg)
            status = data.get("status", "NO_FACE")
            confidence = data.get("confidence", 0.0)
            
            print(f"← {status} (conf: {confidence:.2f})")
            
            # Update target angle based on status
            if status == "MOVE_LEFT":
                target_angle = max(0, target_angle - MOVE_STEP)
                print(f"  Target: {target_angle}°")
                
            elif status == "MOVE_RIGHT":
                target_angle = min(180, target_angle + MOVE_STEP)
                print(f"  Target: {target_angle}°")
                
            elif status == "CENTERED":
                # Face is centered, hold position
                pass
                
            elif status == "NO_FACE":
                # Return to center when no face
                target_angle = 90
                print("  Return to center")
    
    except Exception as e:
        print(f"Error in callback: {e}")

def mqtt_connect():
    """Connect to MQTT broker"""
    global mqtt_client
    
    client = MQTTClient(
        client_id=CLIENT_ID,
        server=MQTT_BROKER,
        port=MQTT_PORT,
        keepalive=60
    )
    
    # Set Last Will (device goes offline)
    status_topic = f"iot/status/{CLIENT_ID.decode()}"
    client.set_last_will(status_topic.encode(), b"offline", retain=True)
    
    client.connect()
    
    # Publish online status
    client.publish(status_topic.encode(), b"online", retain=True)
    
    print(f"✓ MQTT connected as: {CLIENT_ID.decode()}")
    print(f"✓ Subscribed to: {TOPIC_MOVEMENT}")
    
    return client

# Smooth Movement Function
def smooth_move_to_target():
    """Gradually move servo to target angle (reduces jitter)"""
    global current_angle, last_move_time
    
    current_time = time.ticks_ms()
    
    # Check if enough time has passed
    if time.ticks_diff(current_time, last_move_time) < MOVE_DELAY_MS:
        return
    
    if current_angle != target_angle:
        # Move one step toward target
        if current_angle < target_angle:
            current_angle = min(current_angle + 1, target_angle)
        else:
            current_angle = max(current_angle - 1, target_angle)
        
        set_servo_angle(current_angle)
        last_move_time = current_time

# Boot Sequence
print("=" * 50)
print("ESP8266 Face-Tracking Servo Controller")
print(f"Team ID: {TEAM_ID}")
print("=" * 50)

# Initialize servo to center
print("Initializing servo to center position...")
set_servo_angle(90)
time.sleep(1)

# Connect to Wi-Fi
wifi_connect()

# Connect to MQTT
mqtt_client = mqtt_connect()
mqtt_client.set_callback(mqtt_callback)
mqtt_client.subscribe(TOPIC_MOVEMENT.encode())

print("\n✓ System ready - Waiting for face tracking data...")
print("Current angle:", current_angle)
print()

# Main Loop
last_heartbeat = time.ticks_ms()
HEARTBEAT_INTERVAL = 30000  # 30 seconds

try:
    while True:
        # Check for incoming MQTT messages
        mqtt_client.check_msg()
        
        # Smooth movement
        if SMOOTHING_ENABLED:
            smooth_move_to_target()
        else:
            if current_angle != target_angle:
                set_servo_angle(target_angle)
        
        # Send heartbeat
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_heartbeat) >= HEARTBEAT_INTERVAL:
            heartbeat = {
                "node": "esp8266",
                "status": "ONLINE",
                "angle": current_angle,
                "timestamp": time.time()
            }
            mqtt_client.publish(
                TOPIC_HEARTBEAT.encode(),
                json.dumps(heartbeat)
            )
            last_heartbeat = current_time
        
        time.sleep_ms(10)

except KeyboardInterrupt:
    print("\n✓ Shutting down...")

except Exception as e:
    print(f"\n✗ Error in main loop: {e}")
    time.sleep(5)
    machine.reset()

finally:
    # Cleanup
    try:
        mqtt_client.disconnect()
    except:
        pass
    
    # Return servo to center
    set_servo_angle(90)
    print("✓ Servo returned to center")
    print("✓ Cleanup complete")