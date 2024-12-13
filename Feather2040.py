import busio
from microcontroller import pin
from digitalio import DigitalInOut, Direction
from vl53l5cx.cp import VL53L5CXCP
from vl53l5cx import DATA_TARGET_STATUS, DATA_DISTANCE_MM
from vl53l5cx import STATUS_VALID, RESOLUTION_8X8, RANGING_MODE_CONTINUOUS
import json

# Setup pins
scl_pin, sda_pin, lpn_pin, _ = (pin.GPIO3, pin.GPIO2, pin.GPIO28, pin.GPIO5)
i2c = busio.I2C(scl_pin, sda_pin, frequency=1_000_000)
lpn = DigitalInOut(lpn_pin)
lpn.direction = Direction.OUTPUT
lpn.value = True

# Initialize sensor
tof = VL53L5CXCP(i2c, lpn=lpn)
if not tof.is_alive():
    raise ValueError("VL53L5CX not detected")

tof.init()
tof.ranging_mode = RANGING_MODE_CONTINUOUS
tof.resolution = RESOLUTION_8X8
tof.ranging_freq = 15
tof.start_ranging({DATA_DISTANCE_MM, DATA_TARGET_STATUS})

while True:
    if tof.check_data_ready():
        results = tof.get_ranging_data()
        distance = results.distance_mm
        status = results.target_status

        # Create array of valid distances, use None for invalid readings
        data = [d if s == STATUS_VALID else None for d, s in zip(distance, status)]

        # Send JSON-formatted data
        print(json.dumps({"data": data}))
