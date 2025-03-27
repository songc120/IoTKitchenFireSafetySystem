# Importing required libraries
from pubnub.pubnub import PubNub, SubscribeListener, SubscribeCallback, PNStatusCategory
from pubnub.pnconfiguration import PNConfiguration
from pubnub.exceptions import PubNubException
import RPi.GPIO as GPIO
import time
import threading
import json
import adafruit_dht
import board

# PubNub Configuration
pnconf = PNConfiguration()
pnconf.publish_key = 'pub-c-85ba3694-4855-4861-a14b-fdfcb90cf839'
pnconf.subscribe_key = 'sub-c-7c1de1d9-ea5b-451f-bb88-35ae502a81c4'
pnconf.uuid = 'userId'
pubnub = PubNub(pnconf)
channel = 'chenweisong728'

# GPIO Setup - 保留必要的传感器设置
GPIO.setmode(GPIO.BCM)
pir = 26  # Motion sensor
# 设置PIR传感器为输入
GPIO.setup(pir, GPIO.IN)

# 设置fan传感器
#GPIO.setmode(GPIO.BCM)  # Use BCM numbering scheme
GPIO.setwarnings(False)  # Disable GPIO warnings
fan_pin = 17
# Set GPIO pin 17 as output (you can change this to your desired pin)
GPIO.setup(fan_pin, GPIO.OUT)
GPIO.output(fan_pin, GPIO.LOW)

# 温度传感器
# Initialize the DHT11 sensor connected to GPIO pin 4
dht_device = adafruit_dht.DHT11(board.D4)

# 全局变量
last_motion_time = time.time()
last_report_time = time.time()
alarm_active = False
heating_active = False
fan_active = False
TEMP_THRESHOLD = 27.0
detect_frequency = 5 # motion and temp sensor detect each 5s
no_motion_time = 10
alert_duraction = 5
report_duraction = 2

# Define callback for PubNub messages
class MySubscribeCallback(SubscribeCallback):
    def message(self, pubnub, message):
        global alarm_active

        # Process messages from the app
        if message.channel == channel:
            data = message.message

            # Check if this is a reset alarm message
            if 'reset_alarm' in data and data['reset_alarm'] == "True":
                print("Alarm reset received from app")
                alarm_active = False

                # Send confirmation to app
                pubnub.publish().channel(channel).message({
                    'status': 'alarm_reset',
                    'timestamp': time.time()
                }).sync()

                # Send confirmation to app
                pubnub.publish().channel(channel).message({
                    'status': 'fan_status',
                    'alarm_active': alarm_active,
                    'timestamp': time.time()
                }).sync()

# Initialize PubNub callback
pubnub.add_listener(MySubscribeCallback())
pubnub.subscribe().channels(channel).execute()

# Auto-activate fan and LED when alert active
def auto_alert_action():
    global alarm_active, fan_active
    while True:
        time.sleep(1)
        if alarm_active and not fan_active:
            fan_active = True
            GPIO.output(fan_pin, GPIO.HIGH)
            print("GPIO pin set to HIGH")
        elif not alarm_active:
            fan_active = False
            GPIO.output(fan_pin, GPIO.LOW)
            print("GPIO pin set to LOW")


def send_alert_message():
    # Sends a message to PubNub if no motion is detected for 10 seconds.
    global last_motion_time, alarm_active, heating_active,last_report_time

    while True:
        time.sleep(1)
        #print(last_motion_time, alarm_active,heating_active,fan_active)
        #print(time.time() - last_motion_time)
        # Check if heating is active but no motion for 10 seconds
        if heating_active and time.time() - last_motion_time >= no_motion_time and not alarm_active:
            print("ALERT: No motion detected for 10s while heating is active")

            # Activate alarm
            alarm_active = True

          

        # Send periodic status updates
        if time.time() - last_report_time >= report_duraction:
            pubnub.publish().channel(channel).message({
                'status': 'device_status',
                'motion_detected': GPIO.input(pir) == GPIO.HIGH,
                'heating_active': heating_active,
                'alarm_active': alarm_active,
                'last_motion_time': last_motion_time,
                'no_motion_time': no_motion_time
            }).sync()
            last_report_time = time.time()

def read_temperature():
    # Function to read temperature sensor (completely simulated)
    global heating_active

    while True:
        try:
            temperature = dht_device.temperature
            if temperature is not None:
                print(f"current temperature: {temperature}°C")
                if temperature > TEMP_THRESHOLD:
                    heating_active = True

                    print("Warning! Temp or humidity exceed threshold!！")
            else:
                print("无法从传感器获取数据")
        except Exception as e:
            print(f"Error reading data from the temp/humidity sensor: {e}")
        time.sleep(detect_frequency )  # 每detect_frequency秒读取一次数据

# Start background threads
send_alert_thread = threading.Thread(target=send_alert_message, daemon=True)
temp_thread = threading.Thread(target=read_temperature, daemon=True)
alert_action_thread = threading.Thread(target=auto_alert_action, daemon=True)

send_alert_thread.start()
temp_thread.start()
alert_action_thread.start()

print("Waiting for sensor to settle")
time.sleep(2)
print("Kitchen monitoring system active")

# Main loop - detect motion
try:
    while True:
        if GPIO.input(pir):  # Motion detected - 保留PIR传感器的实际检测
            print("Motion Detected!")
            last_motion_time = time.time()  # Reset the timer
            time.sleep(detect_frequency)  # Delay to avoid multiple detections

        time.sleep(0.1)  # Loop delay
except KeyboardInterrupt:
    print("Exiting program")
    GPIO.output(fan_pin, GPIO.LOW)
    GPIO.cleanup()  # Clean up GPIO on exit
