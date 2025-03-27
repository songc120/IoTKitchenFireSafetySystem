import adafruit_dht
import board
import time
# sudo apt-get update
# sudo apt-get install python3-pip python3-dev libgpiod2
# pip3 install adafruit-blinka
# pip3 install adafruit-circuitpython-dht

# Initialize the DHT11 sensor connected to GPIO pin 4
dht_device = adafruit_dht.DHT11(board.D4)

try:
    start_time = time.time()
    temperature = dht_device.temperature
    humidity = dht_device.humidity
    end_time = time.time()

    if humidity is not None and temperature is not None:
        print(f"Measured Temp={temperature}°C | Hum={humidity}%")
        print(f"Measurement took {end_time - start_time:.2f}s")
    else:
        print("Failed to retrieve data from humidity sensor")
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    dht_device.exit()

