import sys
import ujson
import utime
import network
import time
from machine import Pin, Timer
import os
import uasyncio

# server
from phew import logging, template, server, access_point, dns, connect_to_wifi
from phew.template import render_template
from phew.server import redirect, Response


class JSON:


    @staticmethod
    def deserialize(obj, data):
        if not isinstance(data, dict):
            raise TypeError(f"Expected data to be a dictionary, got {type(data)}")

        for key, value in data.items():
            if hasattr(obj, 'serializable_fields') and key not in obj.serializable_fields():
                raise AttributeError(f"{obj} has no attribute {key}")
            else:
                # if obj is dict, deserialize the value and set it
                if isinstance(obj, dict):
                    # if value is of basic type, set it
                    if isinstance(obj[key], (int, float, str, bool, type(None))):
                        obj[key] = value
                    elif isinstance(obj[key], list) and isinstance(value, list):
                        obj[key].clear()
                        obj[key].extend(value)
                    elif isinstance(obj[key], dict) and isinstance(value, dict):
                        JSON.deserialize(obj[key], value)
                    elif hasattr(obj[key], 'from_json'):
                        obj[key].from_json(ujson.dumps(value))

                    continue

                attr = getattr(obj, key)
                if isinstance(attr, (int, float, str, bool, type(None))):
                    setattr(obj, key, value)
                elif isinstance(attr, list) and isinstance(value, list):
                    attr.clear()
                    attr.extend(value)
                elif isinstance(attr, dict) and isinstance(value, dict):
                    JSON.deserialize(attr, value)
                elif hasattr(attr, 'from_json'):
                    attr.from_json(ujson.dumps(value))
                # elif isinstance(attr, dict):
                #     print(f"Deserializing dict {key}: {value}")
                #     setattr(obj, key, value)

    @staticmethod
    def serialize(obj):
        if isinstance(obj, (int, float, str, bool, type(None))):
            return obj
        elif isinstance(obj, dict):
            return {key: JSON.serialize(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [JSON.serialize(item) for item in obj]
        elif hasattr(obj, 'serializable_fields'):
            return {field: JSON.serialize(getattr(obj, field)) for field in obj.serializable_fields()}
        else:
            raise TypeError(f"Type {type(obj)} not serializable")


# Function to log data to the file
def log_data(data):
    with open("micstandlog.txt", "a") as file:
        file.write(f"[{utime.time()}] {str(data)}\n")
        print(data)


class Motor:
    def __init__(self, dir_pin, step_pin, enable_pin, substeps=4, speeds=None):
        if speeds is None:
            speeds = [2000, 1000, 500]
        self.dir_pin = dir_pin
        self.step_pin = step_pin
        self.enable_pin = enable_pin
        self.steps_per_revolution = 200 * substeps
        self.speeds = speeds
        self.timer = Timer()
        self.moving = False

    def set_direction(self, direction):
        self.dir_pin.value(1 if direction == 'cw' else 0)

    def rotate(self, speed):
        if speed <= 0:
            self.stop()
            return
        # Set up timer for stepping
        step_duration = self.speeds[max(min(speed, len(self.speeds)) - 1, 0)]
        log_data(f"Rotating motor with {step_duration} step duration")
        self.enable_pin.value(0)
        self.moving = True
        self.timer.init(freq=1000000 // step_duration, mode=Timer.PERIODIC, callback=self.internal_step)

    def stop(self):
        self.timer.deinit()
        self.enable_pin.value(1)
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
            'x': Motor(dir_pin=Pin(15, Pin.OUT), step_pin=Pin(0, Pin.OUT), enable_pin=Pin(16, Pin.OUT, value=1)),
            'y': Motor(Pin(2, Pin.OUT), Pin(3, Pin.OUT), Pin(4, Pin.OUT, value=1)),
            'z': Motor(Pin(5, Pin.OUT), Pin(6, Pin.OUT), Pin(7, Pin.OUT, value=1))
        }
        self.hostname = 'rpicostand'
        self.wifi = {
            'ssid': None,
            'password': None
        }

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
            log_data(f"Failed to load configuration from {filename}")


utime.sleep(3)
rpicostand = RPicoStand()
log_data(rpicostand.to_json())
log_data(rpicostand.motors['x'])
# load configuration from file
rpicostand.load_from_file("config.json")

log_data(rpicostand.to_json())
log_data(rpicostand.motors['x'])

# set machine hostname to DOMAIN
network.hostname(rpicostand.hostname)


#DOMAIN = f"{network.hostname()}.local" # This is the address that is shown on the Captive Portal

def delete_log_on_startup():
    try:
        os.remove("micstandlog.txt")
        print("Log file deleted.")
    except OSError:
        print("No log file to delete.")


@server.route("/", methods=['GET', 'POST'])
def index(request):
    """ Render the Index page and respond to form requests """
    if request.method == 'GET':
        # logging.debug("Get request")
        # give the webpage access to python variables
        return index_page()
    if request.method == 'POST':
        text = request.form.get("text", None)
        #logging.debug(f'posted message: {text}')
        return index_page()


@server.route("/configure", methods=['POST'])
def configure(request):
    """ Render the Index page and respond to form requests """
    if request.method == 'POST':
        reboot_required = False
        config_changed = False
        ssid = request.form.get("ssid", None)
        password = request.form.get("password", None)
        new_hostname = request.form.get("hostname", None)
        new_x_speed = request.form.get("x_speed", None)
        new_y_speed = request.form.get("y_speed", None)
        new_z_speed = request.form.get("z_speed", None)

        if ssid and password:
            log_data("Saving credentials!")
            save_wifi_credentials(ssid, password)
            reboot_required = True
            config_changed = True

        if new_hostname and new_hostname != network.hostname():
            log_data(f"Changing hostname to {new_hostname}")
            network.hostname(new_hostname)
            reboot_required = True
            config_changed = True

        if new_x_speed:
            # parse to list of ints
            # remove any non-numeric characters except commas
            new_x_speed = ''.join([x for x in new_x_speed if x.isdigit() or x == ','])
            new_x_speed = [int(x) for x in new_x_speed.split(",")]
            if new_x_speed != rpicostand.motors['x'].speeds and len(new_x_speed) == 3:
                log_data(f"Changing x speeds to {new_x_speed}")
                rpicostand.motors['x'].speeds = new_x_speed
                config_changed = True
            else:
                log_data(f"Invalid x speeds: {new_x_speed}")

        if new_y_speed:
            # parse to list of ints
            # remove any non-numeric characters except commas
            new_y_speed = ''.join([x for x in new_y_speed if x.isdigit() or x == ','])
            new_y_speed = [int(x) for x in new_y_speed.split(",")]
            if new_y_speed != rpicostand.motors['y'].speeds and len(new_y_speed) == 3:
                log_data(f"Changing y speeds to {new_y_speed}")
                rpicostand.motors['y'].speeds = new_y_speed
                config_changed = True
            else:
                log_data(f"Invalid y speeds: {new_y_speed}")

        if new_z_speed:
            # parse to list of ints
            # remove any non-numeric characters except commas
            new_z_speed = ''.join([x for x in new_z_speed if x.isdigit() or x == ','])
            new_z_speed = [int(x) for x in new_z_speed.split(",")]
            if new_z_speed != rpicostand.motors['z'].speeds and len(new_z_speed) == 3:
                log_data(f"Changing z speeds to {new_z_speed}")
                rpicostand.motors['z'].speeds = new_z_speed
                config_changed = True
            else:
                log_data(f"Invalid z speeds: {new_z_speed}")

        if config_changed:
            save_configuration()

        if reboot_required:
            uasyncio.create_task(restart_after_while())
            return Response("Credentials saved! The machine will now restart.", status=200,
                            headers={"Content-Type": "text/html"})
        else:
            return Response("Changes saved", status=200, headers={"Content-Type": "text/html"})


@server.route("/wrong-host-redirect", methods=["GET"])
def wrong_host_redirect(request):
    # if the client requested a resource at the wrong host then present
    # a meta redirect so that the captive portal browser can be sent to the correct location
    body = f"<!DOCTYPE html><head><meta http-equiv=\"refresh\" content=\"0;URL=\'http://{DOMAIN}\'/ /></head>"
    logging.debug("body:", body)
    return body


@server.route("/hotspot-detect.html", methods=["GET"])
def hotspot(request):
    """ Redirect to the Index Page """
    #return render_template("index.html", disco = str(disco))
    return index_page()


@server.route("/move", methods=["POST"])
def move_motor(request):
    motor = request.data.get("axis", None)
    direction = request.data.get("direction", None)
    speed = request.data.get("speed", None)

    if rpicostand.motors.get(motor) is None:
        log_data(f"Invalid motor: {motor}")
        return Response("Invalid motor", status=400, headers={"Content-Type": "text/html"})
    if speed <= 0:
        rpicostand.motors[motor].stop()
        return Response(f"Motor {motor} stopped", status=200, headers={"Content-Type": "text/html"})
    if direction not in ['cw', 'ccw']:
        log_data(f"Invalid direction: {direction}")
        return Response("Invalid direction", status=400, headers={"Content-Type": "text/html"})

    rpicostand.motors[motor].set_direction(direction)
    rpicostand.motors[motor].rotate(speed)

    return Response(f"Motor {motor} moved", status=200, headers={"Content-Type": "text/html"})


@server.route("/stop", methods=["POST"])
def stop_moving_motors(request):
    for motor in rpicostand.motors:
        rpicostand.motors[motor].stop()

    return Response(f"Motors stopped", status=200, headers={"Content-Type": "text/html"})


@server.route("/log", methods=["GET"])
def fetch_log(request):
    # if any motor is running, return a 503
    for motor in rpicostand.motors:
        if rpicostand.motors[motor].moving:
            return Response("Motors are moving", status=503, headers={"Content-Type": "text/html"})
    return Response(read_log(), status=200, headers={"Content-Type": "text/html"})


#@server.catchall()
def catch_all(request):
    """ Catch and redirect requests """
    if request.headers.get("host") != DOMAIN:
        return redirect("http://" + DOMAIN)


# set LED pin function
async def set_led_internal(state: bool):
    await uasyncio.sleep_ms(10)
    Pin("LED", Pin.OUT)(state)


# set LED pin function
def set_led(state: bool):
    uasyncio.create_task(set_led_internal(state))


async def restart_after_while():
    await uasyncio.sleep_ms(5000)
    sys.exit()


set_led(False)
nextBlink = None
networks = []


# function to set the Next Blink
def blink_led(times, interval):
    uasyncio.create_task(blink_led_internal(times, interval))
    global nextBlink
    nextBlink = {"times": times, "interval": interval}


# function to set the Next Blink
def keep_blinking(times, interval, pause_interval):
    global nextBlink
    nextBlink = {"times": times, "interval": interval, "pause_interval": pause_interval}


# function to blink the LED n number of times with m ms delay
async def blink_led_internal(times, interval_ms):
    await set_led_internal(False)
    for i in range(times):
        await set_led_internal(True)
        await uasyncio.sleep_ms(interval_ms)
        await set_led_internal(False)
        await uasyncio.sleep_ms(interval_ms)


def save_configuration():
    global rpicostand
    with open("config.json", "w") as f:
        js = rpicostand.to_json()
        log_data(f"Saving configuration: {js}")
        f.write(js)
        f.flush()
        f.close()


# Save Wi-Fi credentials to a file
def save_wifi_credentials(ssid, password):
    global rpicostand
    rpicostand.wifi = {"ssid": ssid, "password": password}
    save_configuration()


def save_hostname(hostname):
    global rpicostand
    rpicostand.hostname = hostname
    save_configuration()


def index_page():
    global networks
    global rpicostand
    # turn speeds into comma separated strings
    return render_template("index.html",
                           hostname=network.hostname(),
                           networks_list=networks,
                           device_log=read_log(),
                           current_mode="Work Mode" if rpicostand.wifi['ssid'] and rpicostand.wifi['password'] else "Pairing Mode",
                           x_speed=','.join([str(x) for x in rpicostand.motors['x'].speeds]),
                            y_speed=','.join([str(x) for x in rpicostand.motors['y'].speeds]),
                            z_speed=','.join([str(x) for x in rpicostand.motors['z'].speeds])
                           )


def start_work_mode():
    log_data("Starting work mode...")
    # should already be connected to wifi, so just start the server
    server.run(host="0.0.0.0", port=80)  # Run the server
    log_data("Work mode started.")


def start_pairing_mode():
    log_data("Starting Captive Portal...")
    # Set to Accesspoint mode
    ap = access_point("RPiPicoMicStand", "PicoStand123")  # NAME YOUR SSID
    ip = ap.ifconfig()[0]  # Grab the IP address and store it
    log_data(f"starting DNS server on {ip}")
    dns.run_catchall(ip)  # Catch all requests and reroute them
    global DOMAIN
    #DOMAIN = ip
    blink_led(100, 2000)
    server.run(host="0.0.0.0", port=80)  # Run the server
    # logging.info("Webserver Started")
    log_data("Captive Portal started.")


def scan_networks():
    # Enumerate available networks
    global networks
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    blink_led(1, 200)
    networks = wlan.scan()
    log_data("Scanning for networks...")
    log_data(networks)
    # join networks object to string
    blink_led(1, 200)
    wlan.active(False)
    return networks


def try_connect_to_wifi(ssid, password):
    if not ssid or not password:
        log_data("No Wi-Fi credentials found.")
        return False

    blink_led(50, 200)

    ip = connect_to_wifi(ssid, password, 10)
    if ip:
        log_data(f"Connected to Wi-Fi. IP address: {ip}")
        set_led(True)
        utime.sleep_ms(1000)
        return True
    else:
        log_data("Failed to connect to Wi-Fi.")
        blink_led(20, 50)
        utime.sleep_ms(1000)
        return False


# Function to read the log file
def read_log():
    try:
        with open("micstandlog.txt", "r") as file:
            data = file.read()
        return data
    except OSError:
        return "Log file not found."


delete_log_on_startup()
log_data("Starting up...")
#blinking thread
blink_led(5, 100)

scan_networks()

if rpicostand.wifi['ssid'] and rpicostand.wifi['password']:
    log_data("Wi-Fi credentials found.")
    blink_led(3, 500)
    success = try_connect_to_wifi(rpicostand.wifi['ssid'], rpicostand.wifi['password'])
    if not success:
        blink_led(20, 50)
        log_data("Failed to connect to Wi-Fi. Starting pairing mode...")
        start_pairing_mode()
    else:
        blink_led(3, 500)
        start_work_mode()
else:
    log_data("No Wi-Fi credentials found. Starting pairing mode...")
    blink_led(20, 50)
    start_pairing_mode()
