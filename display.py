from machine import Pin, SPI, PWM
import framebuf
import utime
import uasyncio
from ucollections import deque

MOSI = 19
SCK = 18
RCLK = 20
PWR = 21

THOUSANDS   = 0xFE
HUNDREDS  = 0xFD
TENS      = 0xFB
UNITS     = 0xF7
Dot       = 0x80

SEG8Code = [
    0x3F,  # 0
    0x06,  # 1
    0x5B,  # 2
    0x4F,  # 3
    0x66,  # 4
    0x6D,  # 5
    0x7D,  # 6
    0x07,  # 7
    0x7F,  # 8
    0x6F,  # 9
    0x77,  # A
    0x7C,  # b
    0x39,  # C
    0x5E,  # d
    0x79,  # E
    0x71,  # F
    0x3D,  # G
    0x76,  # H
    0x06,  # I
    0x1E,  # J
    0x38,  # L
    0x54,  # n
    0x5C,  # o
    0x73,  # P
    0x50,  # r
    0x78,  # t
    0x3E,  # U
    0x6E,  # Y
    0x00,  # Blank (16)
    0x00  # Decimal Point (17)
    ]

char_to_code = {
            '0': 0x3F, '1': 0x06, '2': 0x5B, '3': 0x4F, '4': 0x66,
            '5': 0x6D, '6': 0x7D, '7': 0x07, '8': 0x7F, '9': 0x6F,
            'A': 0x77, 'B': 0x7C, 'C': 0x39, 'D': 0x5E, 'E': 0x79,
            'F': 0x71, 'G': 0x3D, 'H': 0x76, 'I': 0x06, 'J': 0x1E,
            'L': 0x38, 'N': 0x54, 'O': 0x5C, 'P': 0x73, 'R': 0x50,
            'T': 0x78, 'U': 0x3E, 'Y': 0x6E, ' ': 0x00, '.': 0x80,
            'S': 0x6D
        }


def get_code_from_char(char):
    return char_to_code.get(char.upper(), 0x00)

class LED_8SEG():
    def __init__(self):
        self.displaying = False
        self.rclk = Pin(RCLK, Pin.OUT)
        self.rclk(1)
        self.pwr = Pin(PWR, Pin.OUT)
        self.pwr(1)
        #self.spi = SPI(0)
        #self.spi = SPI(0, 1000_000)
        self.spi = SPI(0, 10000_000, polarity=0, phase=0, sck=Pin(SCK), mosi=Pin(MOSI), miso=None)
        self.SEG8 = SEG8Code
        self.queue = deque((), 10)  # Queue with a maximum size of 10

    '''
    function: Send Command
    parameter: 
        Num: bit select
        Seg：segment select       
    Info:The data transfer
    '''

    def write_cmd(self, Num, Seg):
        self.rclk(1)
        self.spi.write(bytearray([Num]))
        self.spi.write(bytearray([Seg]))
        self.rclk(0)
        utime.sleep(0.001)
        self.rclk(1)

    def debug_infinite_loop(self):
        #while 1:
            #for o in range(99999):
        o = 4231
        utime.sleep(0.005)
        self.write_cmd(UNITS, self.SEG8[o % 10])
        utime.sleep(0.005)
        self.write_cmd(TENS, self.SEG8[(o % 100) // 10])
        utime.sleep(0.005)
        self.write_cmd(HUNDREDS, self.SEG8[(o % 1000) // 100])
        utime.sleep(0.005)
        self.write_cmd(THOUSANDS, self.SEG8[(o % 10000) // 1000])

    async def display_text(self, text, duration):
        self.queue.append((text, duration, False))
        await self._process_queue()

    async def display_rolling_text(self, text, duration_per_char, repeat_times=1, padding=True):
        if padding:
            text = '    ' + text + '    '
        for _ in range(repeat_times):
            self.queue.append((text, duration_per_char, True))
        await self._process_queue()

    async def _process_queue(self):
        if not self.displaying:
            self.displaying = True
            positions = [THOUSANDS, HUNDREDS, TENS, UNITS]
            while self.queue:
                text, duration, rolling = self.queue.popleft()
                if rolling:
                    for start in range(len(text) - 3):
                        end_time = utime.ticks_add(utime.ticks_ms(), int(duration * 1000))
                        while utime.ticks_diff(end_time, utime.ticks_ms()) > 0:
                            for i in range(4):
                                char = text[start + i]
                                code = get_code_from_char(char)
                                if start + i + 1 < len(text) and text[start + i + 1] == '.':
                                    code |= 0x80  # Set the dot segment
                                self.write_cmd(positions[i], code)
                                await uasyncio.sleep(0.005)
                else:
                    end_time = utime.ticks_add(utime.ticks_ms(), int(duration * 1000))
                    while utime.ticks_diff(end_time, utime.ticks_ms()) > 0:
                        for i, char in enumerate(text):
                            if i < 4:
                                code = get_code_from_char(char)
                                if i + 1 < len(text) and text[i + 1] == '.':
                                    code |= 0x80  # Set the dot segment
                                self.write_cmd(positions[i], code)
                                await uasyncio.sleep(0.005)
                    for i in range(4):
                        self.write_cmd(positions[i], get_code_from_char(' '))
            self.displaying = False