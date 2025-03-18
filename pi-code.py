# Importing required libraries
from pubnub.pubnub import PubNub, SubscribeListener, SubscribeCallback, PNStatusCategory
from pubnub.pnconfiguration import PNConfiguration
from pubnub.exceptions import PubNubException
import RPi.GPIO as GPIO
import time
import threading
import json

# PubNub Configuration
pnconf = PNConfiguration()
pnconf.publish_key = 'pub-c-85ba3694-4855-4861-a14b-fdfcb90cf839'
pnconf.subscribe_key = 'sub-c-7c1de1d9-ea5b-451f-bb88-35ae502a81c4'
pnconf.uuid = 'raspberrypi_device'
pubnub = PubNub(pnconf)
channel = 'chenweisong728'

# GPIO Setup
GPIO.setmode(GPIO.BOARD)
pir = 26                # Motion sensor
temp_sensor = 16        # Temperature sensor (模拟)
led = 18                # LED indicator
fan = 22                # Ventilation fan

GPIO.setup(pir, GPIO.IN)
GPIO.setup(temp_sensor, GPIO.IN)
GPIO.setup(led, GPIO.OUT)
GPIO.setup(fan, GPIO.OUT)

# Initialize outputs
GPIO.output(led, GPIO.LOW)
GPIO.output(fan, GPIO.LOW)

# Global variables
last_motion_time = time.time()
alarm_active = False
heating_active = False
fan_active = False

# Define callback for PubNub messages
class MySubscribeCallback(SubscribeCallback):
    def message(self, pubnub, message):
        global alarm_active, fan_active
        
        # Process messages from the app
        if message.channel == channel:
            data = message.message
            
            # Check if this is a reset alarm message
            if 'reset_alarm' in data and data['reset_alarm'] == True:
                print("Alarm reset received from app")
                alarm_active = False
                GPIO.output(led, GPIO.LOW)
                
                # Send confirmation to app
                pubnub.publish().channel(channel).message({
                    'status': 'alarm_reset',
                    'timestamp': time.time()
                }).sync()
            
            # Check if this is a fan control message
            if 'fan_control' in data:
                if data['fan_control'] == 'on' and not fan_active:
                    GPIO.output(fan, GPIO.HIGH)
                    fan_active = True
                    print("Fan turned ON")
                elif data['fan_control'] == 'off' and fan_active:
                    GPIO.output(fan, GPIO.LOW)
                    fan_active = False
                    print("Fan turned OFF")
                
                # Send confirmation to app
                pubnub.publish().channel(channel).message({
                    'status': 'fan_status',
                    'fan_active': fan_active,
                    'timestamp': time.time()
                }).sync()

# Initialize PubNub callback
pubnub.add_listener(MySubscribeCallback())
pubnub.subscribe().channels(channel).execute()

def send_no_motion_message():
    # Sends a message to PubNub if no motion is detected for 10 seconds.
    global last_motion_time, alarm_active, heating_active
    
    while True:
        time.sleep(1)
        
        # Check if heating is active but no motion for 10 seconds
        if heating_active and time.time() - last_motion_time >= 10 and not alarm_active:
            print("ALERT: No motion detected for 10s while heating is active")
            
            # Activate alarm
            alarm_active = True
            GPIO.output(led, GPIO.HIGH)  # Turn on LED alert
            
            # Send alert to app
            pubnub.publish().channel(channel).message({
                'alert': 'fire_hazard',
                'message': 'No motion detected for 10s while cooking',
                'timestamp': time.time()
            }).sync()
            
        # Send periodic status updates
        if time.time() % 5 < 0.1:  # Send status every 5 seconds
            pubnub.publish().channel(channel).message({
                'status': 'device_status',
                'motion_detected': GPIO.input(pir) == GPIO.HIGH,
                'heating_active': heating_active,
                'alarm_active': alarm_active,
                'fan_active': fan_active,
                'last_motion': int(time.time() - last_motion_time),
                'timestamp': time.time()
            }).sync()

def read_temperature():
    # Function to read temperature sensor (simulated)
    global heating_active
    
    while True:
        time.sleep(3)
        
        # Simulate temperature reading (in real application, read from actual sensor)
        # For demo, we'll toggle heating status every 15 seconds
        heating_active = not heating_active
        status = "active" if heating_active else "inactive"
        print(f"Heating status: {status}")
        
        # Send temperature data to app
        pubnub.publish().channel(channel).message({
            'sensor': 'temperature',
            'heating_active': heating_active,
            'timestamp': time.time()
        }).sync()

# Auto-activate fan after 30 seconds of no response to alarm
def auto_safety_measure():
    global alarm_active, fan_active
    alarm_start_time = 0
    
    while True:
        time.sleep(1)
        
        # If alarm just became active, record the time
        if alarm_active and alarm_start_time == 0:
            alarm_start_time = time.time()
        
        # If alarm has been active for 30+ seconds and fan is not active
        if alarm_active and alarm_start_time > 0 and time.time() - alarm_start_time >= 30 and not fan_active:
            print("Auto-activating fan as safety measure")
            GPIO.output(fan, GPIO.HIGH)
            fan_active = True
            
            # Notify app of automatic fan activation
            pubnub.publish().channel(channel).message({
                'status': 'auto_safety',
                'action': 'fan_activated',
                'timestamp': time.time()
            }).sync()
        
        # Reset timer if alarm is no longer active
        if not alarm_active:
            alarm_start_time = 0

# Start background threads
no_motion_thread = threading.Thread(target=send_no_motion_message, daemon=True)
temp_thread = threading.Thread(target=read_temperature, daemon=True)
safety_thread = threading.Thread(target=auto_safety_measure, daemon=True)

no_motion_thread.start()
temp_thread.start()
safety_thread.start()

print("Waiting for sensor to settle")
time.sleep(2)
print("Kitchen monitoring system active")

# Main loop - detect motion
try:
    while True:
        if GPIO.input(pir):  # Motion detected
            print("Motion Detected!")
            last_motion_time = time.time()  # Reset the timer
            
            # If alarm is active and motion is detected, send update but don't reset alarm
            # (Require explicit app acknowledgment to reset alarm)
            if alarm_active:
                pubnub.publish().channel(channel).message({
                    'status': 'motion_detected',
                    'alarm_active': True,
                    'timestamp': time.time()
                }).sync()
                
            time.sleep(2)  # Delay to avoid multiple detections

        time.sleep(0.1)  # Loop delay
except KeyboardInterrupt:
    print("Exiting program")
    GPIO.cleanup()  # Clean up GPIO on exit
