import sys
import ujson
import utime
import network
import time
from machine import Pin
import os
import asyncio

# server
from phew import logging, template, server, access_point, dns, connect_to_wifi
from phew.template import  render_template
from phew.server import redirect, Response

utime.sleep(3)

# set machine hostname to DOMAIN
network.hostname("rpistand")
DOMAIN = f"{network.hostname()}.local" # This is the address that is shown on the Captive Portal

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
            asyncio.create_task(restart_after_while())
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

#@server.catchall()
def catch_all(request):
    """ Catch and redirect requests """
    if request.headers.get("host") != DOMAIN:
        return redirect("http://" + DOMAIN)

# set LED pin function
async def set_led_internal(state: bool):
    await asyncio.sleep_ms(10)
    Pin("LED", Pin.OUT)(state)

# set LED pin function
def set_led(state: bool):
    asyncio.create_task(set_led_internal(state))

async def restart_after_while():
    await asyncio.sleep_ms(5000)
    sys.exit()

set_led(False)
nextBlink = None
networks = []

# function to set the Next Blink
def blink_led(times, interval):
    asyncio.create_task(blink_led_internal(times, interval))
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
        await asyncio.sleep_ms(interval_ms)
        await set_led_internal(False)
        await asyncio.sleep_ms(interval_ms)


def check_if_should_blink():
    global nextBlink
    if nextBlink is not None:
        times = nextBlink['times']
        interval = nextBlink['interval']
        if 'pause_interval' in nextBlink:
            pause_interval = nextBlink['pause_interval']
            blink_led_internal(times, interval)
            utime.sleep_ms(pause_interval)
        else:
            nextBlink = None
            blink_led_internal(times, interval)


# thread function that will check if the LED should blink
def check_if_should_blink_thread():
    while True:
        check_if_should_blink()
        utime.sleep_ms(50)


# Save Wi-Fi credentials to a file
def save_wifi_credentials(ssid, password):
    data = {"ssid": ssid, "password": password}
    with open("wifi_config.json", "w") as f:
        ujson.dump(data, f)


# Load Wi-Fi credentials from file
def load_wifi_credentials():
    try:
        with open("wifi_config.json", "r") as f:
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

# Function to log data to the file
def log_data(data):
    with open("micstandlog.txt", "a") as file:
        file.write(f"[{utime.time()}] {str(data)}\n")
        print(data)

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
wifi_credentials = load_wifi_credentials()
scan_networks()


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
