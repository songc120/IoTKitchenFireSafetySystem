#https://www.electronicshub.org/raspberry-pi-dht11-humidity-temperature-sensor-interface/
import sys
import Adafruit_DHT
import time

while True:

    humidity, temperature = Adafruit_DHT.read_retry(11, 4)

    print('Temp: {0:0.1f} C  Humidity: {1:0.1f} %'.format(temperature, humidity))
    time.sleep(1)