
import time
import board
from busio import I2C
import adafruit_bme680
import requests
import os
from aiohttp import web
import threading
import subprocess
 
# Create library object using our Bus I2C port
i2c = I2C(board.SCL, board.SDA)
bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c, debug=False)
 
# change this to match the location's pressure (hPa) at sea level
bme680.sea_level_pressure = 1013.25
 
# You will usually have to add an offset to account for the temperature of
# the sensor. This is usually around 5 degrees but varies by use. Use a
# separate temperature sensor to calibrate this one.
temperature_offset = 0

# Get the token from Ubidots website
UBIDOT_TOKEN = os.environ['UBIDOT_TOKEN']
DEVICE_LABEL = 'RPI-BME680'


def post_request(payload):
    # Creates the headers for the HTTP requests
    url = "http://industrial.api.ubidots.com"
    url = "{}/api/v1.6/devices/{}".format(url, DEVICE_LABEL)
    headers = {"X-Auth-Token": UBIDOT_TOKEN, "Content-Type": "application/json"}

    # Makes the HTTP requests
    status = 400
    attempts = 0
    while status >= 400 and attempts <= 5:
        req = requests.post(url=url, headers=headers, json=payload)
        status = req.status_code
        attempts += 1
        time.sleep(1)

    # Processes results
    print(req.status_code, req.json())
    if status >= 400:
        print("[ERROR] Could not send data after 5 attempts, please check \
            your token credentials and internet connection")
        return False

    print("[INFO] request made properly, your device is updated")
    return True

def send_to_ubidots():
    
    temperature = 0
    humidity = 0
    gas = 0
    pressure = 0

    while True:
        temperature = (bme680.temperature + temperature_offset) * 1.8 + 32
        humidity = bme680.relative_humidity
        gas = bme680.gas
        pressure = bme680.pressure
        print("[INFO] Temperature: %0.1f C" % temperature)
        print("[INFO] Gas: %d ohm" % gas)
        print("[INFO] Humidity: %0.1f %%" % humidity)
        print("[INFO] Pressure: %0.3f hPa" % pressure)

        payload = {
            'Temperature': temperature,
            'Humidity': humidity,
            'Gas': gas,
            'Pressure': pressure }

        print("[INFO] Attemping to send data")
        post_request(payload)
        print("[INFO] finished")
        
        cmd = "raspistill -o ./content/image.jpeg"
        subprocess.call(cmd, shell=True)
        time.sleep(300)


if __name__ == '__main__':
    
    threading.Thread(target=send_to_ubidots,daemon=True).start()
    app = web.Application()
    app.add_routes([web.static('/content', './content')])
    web.run_app(app, port=80)