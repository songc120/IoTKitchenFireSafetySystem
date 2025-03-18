# Importing required libraries
from pubnub.pubnub import PubNub, SubscribeListener, SubscribeCallback, PNStatusCategory
from pubnub.pnconfiguration import PNConfiguration
from pubnub.exceptions import PubNubException
import RPi.GPIO as GPIO
import time
import threading

# PubNub Configuration
pnconf = PNConfiguration()
pnconf.publish_key = 'pub-c-85ba3694-4855-4861-a14b-fdfcb90cf839'
pnconf.subscribe_key = 'sub-c-7c1de1d9-ea5b-451f-bb88-35ae502a81c4'
pnconf.uuid = 'userId'
pubnub = PubNub(pnconf)
channel = 'chenweisong728'

# GPIO Setup
GPIO.setmode(GPIO.BOARD)
pir = 26
GPIO.setup(pir, GPIO.IN)

# Last motion detection time
last_motion_time = time.time()

def send_no_motion_message():
    # Sends a message to PubNub if no motion is detected for 10 seconds.
    global last_motion_time
    while True:
        time.sleep(1)
        if time.time() - last_motion_time >= 10:
            pubnub.publish().channel(channel).message({'alert': 'No motion detected for 10s'}).sync()
            last_motion_time = time.time()  # Reset timer to avoid duplicate messages

# Start no-motion detection thread
no_motion_thread = threading.Thread(target=send_no_motion_message, daemon=True)
no_motion_thread.start()

print("Waiting for sensor to settle")
time.sleep(2)
print("Detecting motion")

while True:
    if GPIO.input(pir):  # Motion detected
        print("Motion Detected!")
        last_motion_time = time.time()  # Reset the timer
        time.sleep(2)  # Delay to avoid multiple detections

    time.sleep(0.1)  # Loop delay should be less than detection delay
