import sys
import utime
import network
import uasyncio
from modules.log import Log

# server
from phew import logging, server, access_point, dns, connect_to_wifi
from phew.template import render_template
from phew.server import redirect, Response
from machine import Pin
from tmc.TMC2209_uart import TMC_UART

import tmc.TMC2209_reg as reg

# while True:
#     sparkle_dissolve(rpicostand.display.oled, 1000, 50)
#     expanding_polygon(rpicostand.display.oled, center_x=64, center_y=16, duration_ms=500, sides=6, initial_rotation=30)
#     expanding_polygon(rpicostand.display.oled, center_x=64, center_y=16, duration_ms=500, sides=6, initial_rotation=0)
#     expanding_polygon(rpicostand.display.oled, center_x=64, center_y=16, duration_ms=500, sides=4, initial_rotation=0)
#     expanding_polygon(rpicostand.display.oled, center_x=64, center_y=16, duration_ms=500, sides=3, initial_rotation=0)
#     expanding_polygon(rpicostand.display.oled, center_x=64, center_y=16, duration_ms=500, sides=16, initial_rotation=0)
#     random_expanding_polygons(rpicostand.display.oled, duration_ms=100, num=5, state=1)
#     random_expanding_polygons(rpicostand.display.oled, duration_ms=100, num=5, state=0)
#     random_expanding_polygons(rpicostand.display.oled, duration_ms=100, num=5, state=-1)
from modules.displays import OLED_SSD1306


def compute_crc8_atm(datagram, initial_value=0):
    crc = initial_value
    # Iterate bytes in data
    for byte in datagram:
        # Iterate bits in byte
        for _ in range(0, 8):
            if (crc >> 7) ^ (byte & 0x01):
                crc = ((crc << 1) ^ 0x07) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
            # Shift to next bit
            byte = byte >> 1
    return crc

print("Starting up")
led = Pin("LED", Pin.OUT)
led(1)
utime.sleep_ms(3000)
led(0)
print("Starting display")
dis = OLED_SSD1306(enable_pin=20, sda_pin=18, scl_pin=19)
if dis.oled is None:
    dis = OLED_SSD1306(enable_pin=20, sda_pin=18, scl_pin=19)
    #dis = OLED_SSD1306(enable_pin=13, sda_pin=14, scl_pin=15)
dis.fill(0)
dis.display_centered_text("Init X", 16)
utime.sleep_ms(1000)
print("Initing X")
p_pin_step = Pin(4, Pin.OUT)
p_pin_dir = Pin(5, Pin.OUT)
p_pin_en = Pin(2, Pin.OUT)
p_pin_diag = Pin(3, Pin.IN)
p_pin_step(0)
p_pin_dir(0)
p_pin_en(1)
baudrate = 115200
print("Diag X: ", p_pin_diag.value())
driver = TMC_UART(0, 112500, Pin(1, Pin.IN), Pin(0, Pin.OUT), 2)
driver2 = TMC_UART(0, 112500, Pin(1, Pin.IN), Pin(0, Pin.OUT), 0)
gstat = driver.read_int(reg.GSTAT)
if gstat != -1:
    gstat = driver.set_bit(gstat, reg.reset)
    gstat = driver.set_bit(gstat, reg.drv_err)
    driver.write_reg_check(reg.GSTAT, gstat)
    print("Inited X")
    dis.fill(0)
    dis.display_centered_text("Inited X", 16)
    print("Diag X: ", p_pin_diag.value())
    utime.sleep_ms(1000)
else:
    print("Failed to init X")
    dis.fill(0)
    dis.display_centered_text("FAIL X", 16)
    print("Diag X: ", p_pin_diag.value())
    utime.sleep_ms(1000)

gstat = driver2.read_int(reg.GSTAT)
if gstat != -1:
    gstat = driver2.set_bit(gstat, reg.reset)
    gstat = driver2.set_bit(gstat, reg.drv_err)
    driver2.write_reg_check(reg.GSTAT, gstat)
    print("Inited Y")
    dis.fill(0)
    dis.display_centered_text("Inited Y", 16)
    print("Diag Y: ", p_pin_diag.value())
    utime.sleep_ms(1000)
else:
    print("Failed to init Y")
    dis.fill(0)
    dis.display_centered_text("FAIL Y", 16)
    print("Diag Y: ", p_pin_diag.value())
    utime.sleep_ms(1000)

# p_pin_step = Pin(11, Pin.OUT)
# p_pin_dir = Pin(12, Pin.OUT)
# p_pin_en = Pin(10, Pin.OUT)
# p_pin_diag = Pin(7, Pin.IN)
# p_pin_step(0)
# p_pin_dir(0)
# p_pin_en(0)


# print("Initing Y")
# dis.fill(0)
# dis.display_centered_text("Init Y", 16)
# utime.sleep_ms(1000)
# driver1 = TMC_UART(1, 112500, Pin(9, Pin.IN), Pin(8, Pin.OUT), 0)
# gstat = driver1.read_int(reg.GSTAT)
# if gstat != -1:
#     gstat = driver1.set_bit(gstat, reg.reset)
#     gstat = driver1.set_bit(gstat, reg.drv_err)
#     driver1.write_reg_check(reg.GSTAT, gstat)
#     print("Inited Y")
#     dis.fill(0)
#     dis.display_centered_text("Inited Y", 16)
#     utime.sleep_ms(1000)
# else:
#     print("Failed to init Y")
#     dis.fill(0)
#     dis.display_centered_text("FAIL Y", 16)
#     utime.sleep_ms(1000)
#     print("Diag Y: ", p_pin_diag.value())

#
#

# print("Initing Z")
# dis.fill(0)
# dis.display_centered_text("Init Z", 16)
# utime.sleep_ms(1000)
#
# p_pin_step = Pin(20, Pin.OUT)
# p_pin_dir = Pin(21, Pin.OUT)
# p_pin_en = Pin(19, Pin.OUT)
# p_pin_diag = Pin(18, Pin.IN)
# p_pin_step(0)
# p_pin_dir(0)
# p_pin_en(0)
#
# driver = TMC_UART(0, 60000, Pin(17, Pin.IN), Pin(16, Pin.OUT), 3)
# gstat = driver.read_int(reg.GSTAT)
# if gstat != -1:
#     gstat = driver.set_bit(gstat, reg.reset)
#     gstat = driver.set_bit(gstat, reg.drv_err)
#     driver.write_reg_check(reg.GSTAT, gstat)
#     print("Inited Z")
#     dis.fill(0)
#     dis.display_centered_text("Inited Z", 16)
#     utime.sleep_ms(1000)
# else:
#     print("Failed to init Z")
#     dis.fill(0)
#     dis.display_centered_text("FAIL Z", 16)
#     utime.sleep_ms(1000)
#
# # driver1.ser.deinit()
# driver.ser.deinit()

raise SystemExit

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

@server.route("/restart", methods=['POST'])
def restart(request):
    #uasyncio.create_task(restart_after_while())
    rpicostand.display.oled.fill(0)
    rpicostand.display.display_centered_text("Restarting...", 8)
    utime.sleep_ms(500)
    sys.exit()
    return Response("Restarting...", status=200, headers={"Content-Type": "text/html"})

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
            Log.log_data("Saving credentials!")
            rpicostand.save_wifi_credentials(ssid, password)
            reboot_required = True
            config_changed = True

        if new_hostname and new_hostname != network.hostname():
            Log.log_data(f"Changing hostname to {new_hostname}")
            network.hostname(new_hostname)
            reboot_required = True
            config_changed = True

        if new_x_speed:
            # parse to list of ints
            # remove any non-numeric characters except commas
            new_x_speed = ''.join([x for x in new_x_speed if x.isdigit() or x == ','])
            new_x_speed = [int(x) for x in new_x_speed.split(",")]
            if new_x_speed != rpicostand.motors['x'].speeds and len(new_x_speed) == 3:
                Log.log_data(f"Changing x speeds to {new_x_speed}")
                rpicostand.motors['x'].speeds = new_x_speed
                config_changed = True
            else:
                Log.log_data(f"Invalid x speeds: {new_x_speed}")

        if new_y_speed:
            # parse to list of ints
            # remove any non-numeric characters except commas
            new_y_speed = ''.join([x for x in new_y_speed if x.isdigit() or x == ','])
            new_y_speed = [int(x) for x in new_y_speed.split(",")]
            if new_y_speed != rpicostand.motors['y'].speeds and len(new_y_speed) == 3:
                Log.log_data(f"Changing y speeds to {new_y_speed}")
                rpicostand.motors['y'].speeds = new_y_speed
                config_changed = True
            else:
                Log.log_data(f"Invalid y speeds: {new_y_speed}")

        if new_z_speed:
            # parse to list of ints
            # remove any non-numeric characters except commas
            new_z_speed = ''.join([x for x in new_z_speed if x.isdigit() or x == ','])
            new_z_speed = [int(x) for x in new_z_speed.split(",")]
            if new_z_speed != rpicostand.motors['z'].speeds and len(new_z_speed) == 3:
                Log.log_data(f"Changing z speeds to {new_z_speed}")
                rpicostand.motors['z'].speeds = new_z_speed
                config_changed = True
            else:
                Log.log_data(f"Invalid z speeds: {new_z_speed}")

        if config_changed:
            rpicostand.save_configuration()

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
    rpicostand.display.display_centered_text(f"Moving {motor}.", 8)
    rpicostand.display.display_centered_text(f"{direction}, {speed}", 16)

    if rpicostand.motors.get(motor) is None:
        Log.log_data(f"Invalid motor: {motor}")
        return Response("Invalid motor", status=400, headers={"Content-Type": "text/html"})
    if speed <= 0:
        rpicostand.motors[motor].stop()
        return Response(f"Motor {motor} stopped", status=200, headers={"Content-Type": "text/html"})
    if direction not in ['cw', 'ccw']:
        Log.log_data(f"Invalid direction: {direction}")
        return Response("Invalid direction", status=400, headers={"Content-Type": "text/html"})

    rpicostand.motors[motor].set_direction(direction)
    rpicostand.motors[motor].rotate(speed)

    return Response(f"Motor {motor} moved", status=200, headers={"Content-Type": "text/html"})


@server.route("/stop", methods=["POST"])
def stop_moving_motors(request):
    for motor in rpicostand.motors:
        rpicostand.motors[motor].stop()
    rpicostand.display.display_centered_text("Motors stopped.", 8)
    return Response(f"Motors stopped", status=200, headers={"Content-Type": "text/html"})


@server.route("/log", methods=["GET"])
def fetch_log(request):
    # if any motor is running, return a 503
    for motor in rpicostand.motors:
        if rpicostand.motors[motor].moving:
            return Response("Motors are moving", status=503, headers={"Content-Type": "text/html"})
    return Response(Log.read_log(), status=200, headers={"Content-Type": "text/html"})


#@server.catchall()
def catch_all(request):
    """ Catch and redirect requests """
    if request.headers.get("host") != DOMAIN:
        return redirect("http://" + DOMAIN)


async def restart_after_while():
    await uasyncio.sleep_ms(2000)
    del rpicostand
    raise SystemExit

def index_page():
    # turn speeds into comma separated strings
    return render_template("index.html",
                           hostname=network.hostname(),
                           networks_list=rpicostand.networks,
                           device_log=Log.read_log(),
                           current_mode="Work Mode" if rpicostand.wifi['ssid'] and rpicostand.wifi['password'] else "Pairing Mode",
                           x_speed=','.join([str(x) for x in rpicostand.motors['x'].speeds]),
                            y_speed=','.join([str(x) for x in rpicostand.motors['y'].speeds]),
                            z_speed=','.join([str(x) for x in rpicostand.motors['z'].speeds])
                           )


async def start_work_mode():
    Log.log_data("Starting work mode...")
    # should already be connected to wifi, so just start the server
    await rpicostand.initialize()
    server.run(host="0.0.0.0", port=80)  # Run the server
    Log.log_data("Work mode started.")



async def start_pairing_mode():
    Log.log_data("Starting Captive Portal...")
    # Set to Accesspoint mode
    ap = access_point("RPiPicoMicStand", "PicoStand123")  # NAME YOUR SSID
    ip = ap.ifconfig()[0]  # Grab the IP address and store it
    Log.log_data(f"starting DNS server on {ip}")
    dns.run_catchall(ip)  # Catch all requests and reroute them
    rpicostand.blink_led(100, 2000)
    server.run(host="0.0.0.0", port=80)  # Run the server
    # logging.info("Webserver Started")
    Log.log_data("Captive Portal started.")


def scan_networks():
    # Enumerate available networks
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    rpicostand.blink_led(1, 200)
    rpicostand.networks = wlan.scan()
    Log.log_data("Scanning for networks...")
    Log.log_data(rpicostand.networks)
    # join networks object to string
    rpicostand.blink_led(1, 200)
    wlan.active(False)
    return rpicostand.networks


async def try_connect_to_wifi(ssid, password):
    if not ssid or not password:
        Log.log_data("No Wi-Fi credentials found.")
        return False

    rpicostand.blink_led(50, 200)

    ip = connect_to_wifi(ssid, password, 10)
    if ip:
        Log.log_data(f"Connected to Wi-Fi. IP address: {ip}")
        rpicostand.display.fill(0)
        rpicostand.display.display_image('info', 0)
        await uasyncio.sleep_ms(1000)
        rpicostand.display.display_centered_text("connected.", 8)
        rpicostand.display.display_centered_text(f"{ip}", 0)

        # rpicostand.display_rolling_text("connected", .3)
        # rpicostand.display_rolling_text(f"{ip}", .5, 5)
        rpicostand.set_led(True)
        await uasyncio.sleep_ms(1000)
        return True
    else:
        Log.log_data("Failed to connect to Wi-Fi.")
        rpicostand.blink_led(20, 50)
        await  uasyncio.sleep_ms(1000)
        return False

utime.sleep(1)
rpicostand = RPicoStand()

async def main():
    # load configuration from file
    rpicostand.load_from_file("config.json")
    await rpicostand.show_boot_logo()
    # set machine hostname to DOMAIN
    network.hostname(rpicostand.hostname)

    Log.delete_log_on_startup()
    Log.log_data("Starting up...")
    # blinking thread
    rpicostand.blink_led(5, 100)

    scan_networks()

    if rpicostand.wifi['ssid'] and rpicostand.wifi['password']:
        Log.log_data("Wi-Fi credentials found.")
        rpicostand.blink_led(3, 500)
        success = await try_connect_to_wifi(rpicostand.wifi['ssid'], rpicostand.wifi['password'])
        if not success:
            rpicostand.blink_led(20, 50)
            Log.log_data("Failed to connect to Wi-Fi. Starting pairing mode...")
            rpicostand.display.oled.fill(0)
            rpicostand.display.oled.text("Failed to connect to Wi-Fi.", 0, 0, 1)
            rpicostand.display.oled.text("Starting pairing mode...", 0, 16, 1)
            rpicostand.display.oled.show()
            # rpicostand.display_rolling_text("internet error", .3, 1)
            # rpicostand.display_rolling_text("ap start", .3, 2)
            await start_pairing_mode()
        else:
            rpicostand.blink_led(3, 500)
            await start_work_mode()
    else:
        Log.log_data("No Wi-Fi credentials found. Starting pairing mode...")
        rpicostand.display.oled.fill(0)
        rpicostand.display.oled.text("No Wi-Fi credentials found.", 0, 0, 1)
        rpicostand.display.oled.text("AP Start.", 0, 16, 1)
        rpicostand.display.oled.show()
        # rpicostand.display_rolling_text("internet error", .3, 1)
        # rpicostand.display_rolling_text("ap start", .3, 2)
        rpicostand.blink_led(20, 50)
        await start_pairing_mode()

uasyncio.run(main())