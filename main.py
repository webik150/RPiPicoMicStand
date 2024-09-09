from machine import Pin
import time

led = Pin("LED", Pin.OUT)

led.value(1)

# flash the led quickly 10 times
for i in range(10):
    led.value(not led.value())
    time.sleep(0.3)