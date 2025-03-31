import ujson, uasyncio
from machine import Pin

from modules.displays import OLED_SSD1306
from modules.json import JSON
from tmc.TMC_2209_StepperDriver import *


class Motor:
    def __init__(self, dir_pin, step_pin, enable_pin, diag_pin, tx_pin, rx_pin, mtr_id=0, substeps=4, speeds=None):
        if speeds is None:
            speeds = [2000, 1000, 500]
        self.steps_per_revolution = 200 * substeps
        self.speeds = speeds
        self.moving = False
        self.diag_pin = diag_pin
        self.dir_pin = dir_pin
        self.step_pin = step_pin
        self.enable_pin = enable_pin
        self.tx_pin = tx_pin
        self.rx_pin = rx_pin
        self.mtr_id = mtr_id
        self.uart_id = 0
        # find the UART ID by pins
        if self.tx_pin in [4,8]:
            self.uart_id = 1
        self.tmc = None

    def __del__(self):
        if self.tmc is not None:
            del self.tmc

    def initialize(self):
        Log.log_data(f"Initializing motor {self.mtr_id}, with pins {self.dir_pin}, {self.step_pin}, {self.enable_pin}, {self.diag_pin}, {self.tx_pin}, {self.rx_pin}, on uart {self.uart_id}")
        self.tmc = TMC_2209(pin_step=self.step_pin, pin_dir=self.dir_pin, pin_en=self.enable_pin, tx_pin=Pin(self.tx_pin),
                            rx_pin=Pin(self.rx_pin), mtr_id=self.mtr_id, serialport=self.uart_id)
        self.tmc.setMotorEnabled(False)
        self.tmc.setDirection_reg(False)
        self.tmc.setVSense(True)
        self.tmc.setCurrent(700)
        self.tmc.setIScaleAnalog(False)
        self.tmc.setInterpolation(True)
        self.tmc.setSpreadCycle(False)
        self.tmc.setMicrosteppingResolution(64)
        self.tmc.setInternalRSense(False)

        self.tmc.readIOIN()
        self.tmc.readCHOPCONF()
        self.tmc.readDRVSTATUS()
        self.tmc.readGCONF()
        self.tmc.tmc_uart.flushSerialBuffer()

    def set_direction(self, direction):
        self.dir_pin.value(1 if direction == 'cw' else 0)

    def rotate(self, speed):
        if speed <= 0:
            self.stop()
            return
        # Set up timer for stepping
        step_duration = self.speeds[max(min(speed, len(self.speeds)) - 1, 0)]
        Log.log_data(f"Rotating motor with {step_duration} step duration")
        #self.enable_pin.value(0)
        self.moving = True
        #self.timer.init(freq=1000000 // step_duration, mode=Timer.PERIODIC, callback=self.internal_step)

    def stop(self):
        #self.timer.deinit()
        #self.enable_pin.value(1)
        self.moving = False

    def internal_step(self, t):
        self.step_pin.value(not self.step_pin.value())

    @staticmethod
    def serializable_fields():
        return ['steps_per_revolution', 'speeds']

    # serialize to json
    def to_json(self):
        return ujson.dumps(JSON.serialize(self))

    def from_json(self, json_str):
        data = ujson.loads(json_str)
        JSON.deserialize(self, data)

class RPicoStand:
    def __init__(self):
        self.motors = {
            'x': Motor(dir_pin=5, step_pin=4, enable_pin=2, diag_pin=3, tx_pin=0, rx_pin=1, mtr_id=1),
            #'y': Motor(dir_pin=Pin(6, Pin.OUT), step_pin=Pin(7, Pin.OUT), enable_pin=Pin(8, Pin.OUT, value=1), diag_pin=Pin(4, Pin.IN), tx_pin=Pin(1, Pin.OUT), rx_pin=Pin(2, Pin.IN)),
            'y': Motor(dir_pin=12, step_pin=11, enable_pin=10, diag_pin=7, tx_pin=8, rx_pin=9, mtr_id=0),
            #'z': Motor(dir_pin=Pin(0, Pin.OUT), step_pin=Pin(1, Pin.OUT), enable_pin=Pin(2, Pin.OUT, value=1), diag_pin=Pin(4, Pin.IN), tx_pin=Pin(1, Pin.OUT), rx_pin=Pin(2, Pin.IN))
            'z': Motor(dir_pin=21, step_pin=20, enable_pin=19, diag_pin=18, tx_pin=16, rx_pin=17, mtr_id=3),
        }
        self.hostname = 'rpicostand'
        self.wifi = {
            'ssid': None,
            'password': None
        }
        self.keep_motors_on = False
        self.LED = Pin("LED", Pin.OUT)
        self.set_led(False)
        self.networks = []

        self.display = OLED_SSD1306(enable_pin=13, sda_pin=14, scl_pin=15)
        # self.display = LED_8SEG()

    def __del__(self):
        for key, motor in self.motors.items():
            del self.motors[key]
        del self.display

    @staticmethod
    def serializable_fields():
        return ['motors', 'hostname', 'wifi']

    # serialize to json
    def to_json(self):
        return ujson.dumps(JSON.serialize(self))

    def from_json(self, json_str):
        data = ujson.loads(json_str)
        JSON.deserialize(self, data)

    def load_from_file(self, filename):
        # load configuration from file if the file exists
        try:
            with open(filename, "r") as f:
                data = f.read()
                self.from_json(data)
        except OSError:
            Log.log_data(f"Failed to load configuration from {filename}")

    # set LED pin function
    def set_led_internal(self, state: bool):
        #await uasyncio.sleep_ms(10)
        self.LED(state)

    # set LED pin function
    def set_led(self, state: bool):
        self.set_led_internal(state)

    # function to set the Next Blink
    def blink_led(self, times, interval):
        uasyncio.create_task(self.blink_led_internal(times, interval))

    # function to blink the LED n number of times with m ms delay
    async def blink_led_internal(self, times, interval_ms):
        self.set_led_internal(False)
        for i in range(times):
            self.set_led_internal(True)
            await uasyncio.sleep_ms(interval_ms)
            self.set_led_internal(False)
            await uasyncio.sleep_ms(interval_ms)

    def save_configuration(self):
        with open("config.json", "w") as f:
            js = self.to_json()
            Log.log_data(f"Saving configuration")
            f.write(js)
            f.flush()
            f.close()
            self.display_rolling_text("config saved", .3, 1)

    # Save Wi-Fi credentials to a file
    def save_wifi_credentials(self, ssid, password):
        self.wifi = {"ssid": ssid, "password": password}
        self.save_configuration()

    def save_hostname(self, hostname):
        self.hostname = hostname
        self.save_configuration()

    def display_text(self, text, duration):
        pass
        # uasyncio.create_task(self.display.display_text(text, duration))

    def display_rolling_text(self, text, duration_per_char, repeat=1, padding=True):
        # uasyncio.create_task(self.display.display_rolling_text(text, duration_per_char,repeat, padding))
        pass

    async def show_boot_logo(self):
        self.display.fill(0)
        self.display.display_image("boot", 1)
        #self.display.test_brightness()
        await uasyncio.sleep_ms(2000)

    async def initialize(self):
        # Initialize motors
        for key, motor in self.motors.items():
            if key in ['z']:
                continue
            Log.log_data(f"Initializing motor {key}")
            motor.initialize()
            await uasyncio.sleep_ms(1000)