#https://www.electronicshub.org/raspberry-pi-dht11-humidity-temperature-sensor-interface/
import sys
import Adafruit_DHT
import time
# sudo apt-get update
# sudo apt-get install python3-pip python3-dev libgpiod2
# pip3 install adafruit-blinka
# pip3 install adafruit-circuitpython-dht
while True:

    humidity, temperature = Adafruit_DHT.read_retry(11, 4)

    print('Temp: {0:0.1f} C  Humidity: {1:0.1f} %'.format(temperature, humidity))
    time.sleep(1)