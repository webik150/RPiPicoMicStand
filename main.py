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
from phew.template import  render_template
from phew.server import redirect, Response

# Function to log data to the file
def log_data(data):
    with open("micstandlog.txt", "a") as file:
        file.write(f"[{utime.time()}] {str(data)}\n")
        print(data)

config = {
    'wifi' :{
        'ssid': None,
        'password': None
    },
    'hostname': 'rpicostand',
    'motors': {
        'x': {
            'steps_per_revolution': 800,
            'step_duration': 1000
        },
        'y': {
            'steps_per_revolution': 800,
            'step_duration': 1000
        },
        'z': {
            'steps_per_revolution': 800,
            'step_duration': 1000
        }
    }
}

utime.sleep(3)

dir_pin = Pin(15, Pin.OUT)
step_pin = Pin(0, Pin.OUT)
steps_per_revolution = 800

# Initialize timer
tim = Timer()


def step(t):
    global step_pin
    step_pin.value(not step_pin.value())


def rotate_motor(delay):
    # Set up timer for stepping
    tim.init(freq=1000000 // delay, mode=Timer.PERIODIC, callback=step)


def loop():
    while True:
        # Set motor direction clockwise
        dir_pin.value(1)

        # Spin motor slowly
        rotate_motor(2000)
        log_data("Rotating motor clockwise")
        utime.sleep_ms(steps_per_revolution)
        tim.deinit()  # stop the timer
        utime.sleep(1)

        # Set motor direction counterclockwise
        dir_pin.value(0)

        # Spin motor quickly
        rotate_motor(1000)
        log_data("Rotating motor counterclockwise")
        utime.sleep_ms(steps_per_revolution)
        tim.deinit()  # stop the timer
        utime.sleep(1)

#loop()

dir_pin_x = Pin(15, Pin.OUT)
step_pin_x = Pin(0, Pin.OUT)
dir_pin_y = Pin(2, Pin.OUT)
step_pin_y = Pin(3, Pin.OUT)
dir_pin_z = Pin(4, Pin.OUT)
step_pin_z = Pin(5, Pin.OUT)

# Initialize timer
motor_timer_x = Timer()
motor_timer_y = Timer()
motor_timer_z = Timer()

def step_x(t):
    global step_pin_x
    step_pin_x.value(not step_pin_x.value())
def step_y(t):
    global step_pin_y
    step_pin_y.value(not step_pin_y.value())
def step_z(t):
    global step_pin_z
    step_pin_z.value(not step_pin_z.value())


def rotate_motor_x():
    global config
    global motor_timer_x
    # Set up timer for stepping
    log_data(f"Rotating motor X with {config['motors']['x']['step_duration']} step duration")
    motor_timer_x.init(freq=1000000 // config['motors']['x']['step_duration'], mode=Timer.PERIODIC, callback=step_x)

def rotate_motor_y():
    global config
    global motor_timer_y
    # Set up timer for stepping
    motor_timer_y.init(freq=1000000 // config['motors']['y']['step_duration'], mode=Timer.PERIODIC, callback=step_y)

def rotate_motor_z():
    global config
    global motor_timer_z
    # Set up timer for stepping
    motor_timer_z.init(freq=1000000 // config['motors']['z']['step_duration'], mode=Timer.PERIODIC, callback=step_z)

# set machine hostname to DOMAIN
network.hostname("rpicostand")
#DOMAIN = f"{network.hostname()}.local" # This is the address that is shown on the Captive Portal

def delete_log_on_startup():
    try:
        os.remove("micstandlog.txt")
        print("Log file deleted.")
    except OSError:
        print("No log file to delete.")


@server.route("/", methods=['GET','POST'])
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
        ssid = request.form.get("ssid", None)
        password = request.form.get("password", None)
        new_hostname = request.form.get("hostname", None)
        if ssid and password:
            log_data("Saving credentials!")
            save_wifi_credentials(ssid, password)
            reboot_required = True


        if new_hostname and new_hostname != network.hostname():
            log_data(f"Changing hostname to {new_hostname}")
            network.hostname(new_hostname)
            reboot_required = True

        if reboot_required:
            uasyncio.create_task(restart_after_while())
            return Response("Credentials saved! The machine will now restart.", status=200, headers={"Content-Type": "text/html"})
        else:
            return Response("Changes saved", status=200, headers={"Content-Type": "text/html"})



@server.route("/wrong-host-redirect", methods=["GET"])
def wrong_host_redirect(request):
  # if the client requested a resource at the wrong host then present
  # a meta redirect so that the captive portal browser can be sent to the correct location
  body = f"<!DOCTYPE html><head><meta http-equiv=\"refresh\" content=\"0;URL=\'http://{DOMAIN}\'/ /></head>"
  logging.debug("body:",body)
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

    if motor == 'x':
        dir_pin = dir_pin_x
        timer = motor_timer_x
    elif motor == 'y':
        dir_pin = dir_pin_y
        timer = motor_timer_y
    elif motor == 'z':
        dir_pin = dir_pin_z
        timer = motor_timer_z
    else:
        log_data(f"Invalid motor: {motor}")
        return Response("Invalid motor", status=400, headers={"Content-Type": "text/html"})

    if speed == 0:
        timer.deinit()
        return Response("Motor stopped", status=200, headers={"Content-Type": "text/html"})

    if direction == 'cw':
        dir_pin.value(1)
    elif direction == 'ccw':
        dir_pin.value(0)
    else:
        log_data(f"Invalid direction: {direction}")
        return Response("Invalid direction", status=400, headers={"Content-Type": "text/html"})


    if speed == 1:
        step_duration = 2000
    elif speed == 2:
        step_duration = 1000
    elif speed == 3:
        step_duration = 500
    else:
        log_data(f"Invalid speed: {speed}")
        return Response("Invalid speed", status=400, headers={"Content-Type": "text/html"})

    set_motor_config(motor, None, step_duration)

    # Set up timer for stepping
    if motor == 'x':
        rotate_motor_x()
    elif motor == 'y':
        rotate_motor_y()
    elif motor == 'z':
        rotate_motor_z()

    return Response(f"Motor {motor} moved", status=200, headers={"Content-Type": "text/html"})

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
    global config
    with open("config.json", "w") as f:
        ujson.dump(config, f)


# Save Wi-Fi credentials to a file
def save_wifi_credentials(ssid, password):
    global config
    config['wifi'] = {"ssid": ssid, "password": password}
    save_configuration()

def save_hostname(hostname):
    global config
    config['hostname'] = hostname
    save_configuration()

def set_motor_config(motor, steps_per_revolution, step_duration):
    global config
    spr = config['motors'][motor]['steps_per_revolution']
    sd = config['motors'][motor]['step_duration']
    config['motors'][motor] = {"steps_per_revolution": steps_per_revolution if not None else spr, "step_duration": step_duration if not None else sd}

# Load Wi-Fi credentials from file
def load_configuration():
    try:
        with open("config.json", "r") as f:
            return ujson.load(f)
    except OSError:
        return None


def index_page():
    global networks
    global wifi_credentials
    return render_template("index.html",
                           hostname=network.hostname(),
                           networks_list=networks,
                           networks=read_log(),
                           current_mode="Work Mode" if wifi_credentials else "Pairing Mode",
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
    blink_led(100,2000)
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

        # loop = uasyncio.get_event_loop()
        # client = Client(ip)
        # responder = Responder(
        #     client,
        #     own_ip=lambda: ip,
        #     host=lambda: "my-awesome-microcontroller-{}".format(responder.generate_random_postfix()),
        # )
        #
        # def announce_service():
        #     responder.advertise("_http", "_tcp", port=80,
        #                         data={"some": "metadata", "for": ["my", "service"]})
        #
        # log_data("Starting mDNS service...")
        # announce_service()
        # loop.run_forever()


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
tmp_config = load_configuration()

if tmp_config:
    config = tmp_config
    log_data("Configuration loaded.")

wifi_credentials = config['wifi']
scan_networks()


# test motors
# rotate_motor_x()
rotate_motor_x()
utime.sleep_ms(1000)
motor_timer_x.deinit()
# rotate_motor_y()
# rotate_motor_z()


if wifi_credentials:
    log_data("Wi-Fi credentials found.")
    blink_led(3, 500)
    success = try_connect_to_wifi(wifi_credentials['ssid'], wifi_credentials['password'])
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
