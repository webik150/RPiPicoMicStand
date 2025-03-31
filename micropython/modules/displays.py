import urandom
import math
from ssd1306 import SSD1306_I2C
import utime
import uasyncio
from machine import Pin, SPI, I2C
from ucollections import deque
from modules.log import Log

def shuffle_list(lst):
    """
    Shuffle a list in place using urandom.

    Parameters:
        lst: The list to shuffle.
    """
    for i in range(len(lst) - 1, 0, -1):
        # Generate a random index from 0 to i
        j = urandom.getrandbits(16) % (i + 1)
        # Swap elements at indices i and j
        lst[i], lst[j] = lst[j], lst[i]

async def random_expanding_polygons(oled, duration_ms=1000, num=5, state=1):
    """
    Creates an expanding polygon ripple effect.

    Parameters:
        oled: The SSD1306 OLED object.
        center_x: X-coordinate of the polygon's center.
        center_y: Y-coordinate of the polygon's center.
        duration_ms: Total duration of the effect in milliseconds.
        sides: Number of sides of the polygon.
        initial_rotation: Initial rotation angle in degrees.
    """
    width, height = oled.width, oled.height
    max_radius = int(math.sqrt(width ** 2 + height ** 2))  # Maximum ripple distance
    total_frames = max_radius  # One frame per radius step
    frame_delay = duration_ms // total_frames  # Delay per frame in ms
    frames_per_ms = -1
    # if frame delay is less than 1, calculate the number of frames to draw per drawcall to stay within the max duration
    if frame_delay < 1:
        frames_per_ms = math.floor(1 / (duration_ms / total_frames))
        frames_per_ms = 1

    shapes  = []
    for i in range(num):
        initial_rotation = urandom.getrandbits(16) % 360
        sides = urandom.getrandbits(16) % 8 + 3
        initial_position = (urandom.getrandbits(16) % width, urandom.getrandbits(16) % height)
        shapes.append((sides, initial_rotation, initial_position))

    def calculate_polygon_vertices(cx, cy, radius, sides, rotation):
        """Calculate the vertices of a polygon."""
        vertices = []
        angle_step = 360 / sides
        for i in range(sides):
            angle = math.radians(i * angle_step + rotation)  # Convert to radians
            x = int(cx + radius * math.cos(angle))
            y = int(cy + radius * math.sin(angle))
            vertices.append((x, y))
        return vertices

    def draw_polygon(oled, sides, initial_rotation, initial_position, radius, state):
        """Draw a polygon with the given parameters."""
        # Calculate vertices for the current radius
        vertices = calculate_polygon_vertices(initial_position[0], initial_position[1], radius, sides, initial_rotation)
        # Draw the polygon by connecting vertices
        for i in range(len(vertices)):
            x1, y1 = vertices[i]
            x2, y2 = vertices[(i + 1) % len(vertices)]
            if state == -1:
                oled.line(x1, y1, x2, y2, 0 if oled.pixel(x1, y1) else 1)
            else:
                oled.line(x1, y1, x2, y2, state)

    frame_counter = 0
    # Start the ripple effect
    for radius in range(1, max_radius + 1):
        # for each shape
        # oled.fill(0)  # Clear the screen
        for sides, initial_rotation, initial_position in shapes:
            draw_polygon(oled, sides, initial_rotation, initial_position, radius, state)

        oled.show()
        if (frames_per_ms > 1 and frame_counter % frames_per_ms == 0) or frames_per_ms <= 1:
            await uasyncio.sleep_ms(frame_delay)

async def expanding_polygon(oled, center_x, center_y, duration_ms=1000, sides=6, initial_rotation=0):
    """
    Creates an expanding polygon ripple effect.

    Parameters:
        oled: The SSD1306 OLED object.
        center_x: X-coordinate of the polygon's center.
        center_y: Y-coordinate of the polygon's center.
        duration_ms: Total duration of the effect in milliseconds.
        sides: Number of sides of the polygon.
        initial_rotation: Initial rotation angle in degrees.
    """
    width, height = oled.width, oled.height
    max_radius = int(math.sqrt(width ** 2 + height ** 2))  # Maximum ripple distance
    total_frames = max_radius  # One frame per radius step
    frame_delay = duration_ms // total_frames  # Delay per frame in ms

    def calculate_polygon_vertices(cx, cy, radius, sides, rotation):
        """Calculate the vertices of a polygon."""
        vertices = []
        angle_step = 360 / sides
        for i in range(sides):
            angle = math.radians(i * angle_step + rotation)  # Convert to radians
            x = int(cx + radius * math.cos(angle))
            y = int(cy + radius * math.sin(angle))
            vertices.append((x, y))
        return vertices

    # Start the ripple effect
    for radius in range(1, max_radius + 1):
        oled.fill(0)  # Clear the screen

        # Calculate vertices for the current radius
        vertices = calculate_polygon_vertices(center_x, center_y, radius, sides, initial_rotation)

        # Draw the polygon by connecting vertices
        for i in range(len(vertices)):
            x1, y1 = vertices[i]
            x2, y2 = vertices[(i + 1) % len(vertices)]  # Wrap around to the first vertex
            oled.line(x1, y1, x2, y2, 1)

        oled.show()
        await uasyncio.sleep_ms(frame_delay)

    # Clear the screen after the effect
    oled.fill(0)
    oled.show()

async def circular_lines(oled, center_x, center_y, duration_ms=1000):
    """
    Creates a circular ripple effect from a given center position.

    Parameters:
        oled: The SSD1306 OLED object.
        center_x: X-coordinate of the ripple's center.
        center_y: Y-coordinate of the ripple's center.
        duration_ms: Total duration of the effect in milliseconds.
    """
    width, height = oled.width, oled.height
    max_radius = int(math.sqrt(width ** 2 + height ** 2))  # Maximum ripple distance
    total_frames = max_radius  # One frame per radius step
    frame_delay = duration_ms // total_frames  # Delay per frame in ms

    # Start the ripple
    for radius in range(1, max_radius + 1):
        for angle in range(0, 360, 5):  # Steps of 5 degrees for smoother circle
            # Calculate the x, y position on the circle
            rad = math.radians(angle)
            x = int(center_x + radius * math.cos(rad))
            y = int(center_y + radius * math.sin(rad))

            # Draw the pixel if within bounds
            if 0 <= x < width and 0 <= y < height:
                oled.pixel(x, y, 1)

        oled.show()  # Update the display
        await uasyncio.sleep_ms(frame_delay)

    # Clear the screen after the effect
    oled.fill(0)
    oled.show()

async def sparkle_dissolve(oled, duration_ms=1000, sparkle_count=50):
    """
    Creates a sparkle dissolve transition effect.

    Parameters:
        oled: The SSD1306 OLED object.
        duration_ms: Total duration of the effect in milliseconds.
        sparkle_count: Number of sparkles per frame.
    """
    # Get the dimensions of the display
    width = oled.width
    height = oled.height
    total_pixels = width * height
    total_frames = total_pixels // sparkle_count
    # Calculate the total number of frames based on duration
    frame_delay = duration_ms // (total_frames * 2)  # 2 phases: filling and clearing

    # create list of all pixels and shuffle it
    pixels = [(x, y) for x in range(width) for y in range(height)]
    shuffle_list(pixels)

    async def apply_sparkles(state):
        """Applies sparkle effect with the given state (1=on, 0=off)."""
        counter = 0
        while pixels:
            x, y = pixels.pop()
            oled.pixel(x, y, state)
            counter += 1
            if counter >= sparkle_count:
                oled.show()
                await uasyncio.sleep_ms(frame_delay)
                counter = 0
        oled.show()

    await apply_sparkles(1)
    # clear the display
    pixels = [(x, y) for x in range(width) for y in range(height)]
    shuffle_list(pixels)
    await apply_sparkles(0)


class LED_8SEG:
    def __init__(self):
        self.displaying = False
        self.rclk = Pin(20, Pin.OUT)
        self.rclk(1)
        self.pwr = Pin(21, Pin.OUT)
        self.pwr(1)
        #self.spi = SPI(0)
        #self.spi = SPI(0, 1000_000)
        self.spi = SPI(0, 10000_000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(19), miso=None)
        self.queue = deque((), 10)  # Queue with a maximum size of 10
        self.THOUSANDS = 0xFE
        self.HUNDREDS = 0xFD
        self.TENS = 0xFB
        self.UNITS = 0xF7
        self.Dot = 0x80
        self.positions = [self.THOUSANDS, self.HUNDREDS, self.TENS, self.UNITS]
        self.char_to_code = {
            '0': 0x3F, '1': 0x06, '2': 0x5B, '3': 0x4F, '4': 0x66,
            '5': 0x6D, '6': 0x7D, '7': 0x07, '8': 0x7F, '9': 0x6F,
            'A': 0x77, 'B': 0x7C, 'C': 0x39, 'D': 0x5E, 'E': 0x79,
            'F': 0x71, 'G': 0x3D, 'H': 0x76, 'I': 0x06, 'J': 0x1E,
            'L': 0x38, 'N': 0x54, 'O': 0x5C, 'P': 0x73, 'R': 0x50,
            'T': 0x78, 'U': 0x3E, 'Y': 0x6E, ' ': 0x00, '.': 0x80,
            'S': 0x6D
        }

    def get_code_from_char(self, char):
        return self.char_to_code.get(char.upper(), 0x00)

    '''
    function: Send Command
    parameter: 
        Num: bit select
        Seg：segment select       
    Info:The data transfer
    '''

    async def write_cmd(self, Num, Seg):
        self.rclk(1)
        self.spi.write(bytearray([Num]))
        self.spi.write(bytearray([Seg]))
        self.rclk(0)
        await uasyncio.sleep_ms(1)
        self.rclk(1)

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
            while self.queue:
                text, duration, rolling = self.queue.popleft()
                if rolling:
                    for start in range(len(text) - 3):
                        end_time = utime.ticks_add(utime.ticks_ms(), int(duration * 1000))
                        while utime.ticks_diff(end_time, utime.ticks_ms()) > 0:
                            for i in range(4):
                                char = text[start + i]
                                code = self.get_code_from_char(char)
                                if start + i + 1 < len(text) and text[start + i + 1] == '.':
                                    code |= 0x80  # Set the dot segment
                                await self.write_cmd(self.positions[i], code)
                                await uasyncio.sleep(0.005)
                else:
                    end_time = utime.ticks_add(utime.ticks_ms(), int(duration * 1000))
                    while utime.ticks_diff(end_time, utime.ticks_ms()) > 0:
                        for i, char in enumerate(text):
                            if i < 4:
                                code = self.get_code_from_char(char)
                                if i + 1 < len(text) and text[i + 1] == '.':
                                    code |= 0x80  # Set the dot segment
                                await self.write_cmd(self.positions[i], code)
                                await uasyncio.sleep(0.005)
                    for i in range(4):
                        self.write_cmd(self.positions[i], self.get_code_from_char(' '))
            self.displaying = False

class Icon:
    def __init__(self, data):
        self.data = data


class OLED_SSD1306:
    def __init__(self, enable_pin, sda_pin, scl_pin):
        self.displaying = False
        self.queue = deque((), 10)  # Queue with a maximum size of 10
        self.display_pwr = Pin(enable_pin, Pin.OUT)
        self.display_pwr(1)
        uasyncio.sleep_ms(100)
        try:
            self.i2c = I2C(1, sda=Pin(sda_pin), scl=Pin(scl_pin), freq=400000)
            self.oled = SSD1306_I2C(128, 64, self.i2c)
            self.oled.poweron()  # power on the display, pixels redrawn
            self.oled.contrast(10)
            Log.log_data("OLED detected")
        except OSError:
            Log.log_data("OLED not detected")
            self.i2c = None
            self.oled = None
        self.icons = {}

    async def test_brightness(self):
        for i in range(256):
            self.oled.contrast(i)
            self.display_centered_text(f"{i}", 32)
            await uasyncio.sleep_ms(10)
            self.oled.show()

    def get_image_data(self, key):
        """
        Get image data from a 1-bit BMP image.

        Parameters:
            key: valid keys are [boot, info, error].

        Returns:
            A bytearray containing the image data loaded from a bmp file with filename key_width_height.bmp.
        """
        width = self.oled.width
        height = self.oled.height
        Log.log_data(f"Loading image {key}_{width}_{height}.bmp")
        with open(f"/img/{key}_{width}_{height}.bmp", "rb") as f:
            # Parse BMP header
            f.seek(10)
            offset = int.from_bytes(f.read(4), 'little')  # Start of pixel array
            f.seek(18)
            width = int.from_bytes(f.read(4), 'little')
            height = int.from_bytes(f.read(4), 'little')
            print(f"Width: {width}, Height: {height}, Offset: {offset}")
            # Ensure the width is a multiple of 8
            if width % 8 != 0:
                raise ValueError("Width must be a multiple of 8 for monochrome BMP")
            row_size = ((width + 31) // 32) * 4  # Each row is padded to the nearest 4 bytes
            # Read raw pixel data
            f.seek(offset)
            raw_data = f.read(row_size * abs(height))  # Read the raw bitmap data
            # convert to bytearray
            # raw_data = bytearray(raw_data)
            # Log.log_data(raw_data)
            return raw_data

    def load_icons(self, keys):
        """
        Get icon data from a 1-bit BMP image.

        Parameters:
            key: valid keys are [wifi, hotspot, info, error].

        Returns:
            A bytearray containing the image data loaded from a bmp file with filename key_16_16.bmp.
        """

        icon_width = 8
        icon_height = 8
        spritesheet_width = 64
        spritesheet_height = 64

        with open(f"../img/icons.bmp", "rb") as f:
            f.seek(10)
            offset = int.from_bytes(f.read(4), 'little')
            f.seek(18)
            width = int.from_bytes(f.read(4), 'little')
            height = int.from_bytes(f.read(4), 'little')

            f.seek(offset)
            data = bytearray(f.read(width * height // 8))

            # split byte array into 8x8 icons
            for i in range(0, len(data), icon_width):
                if i > len(keys):
                    break
                icon_data = data[i:i + icon_height]
                self.icons[keys[i]] = Icon(icon_data)

    def blit_bitmap(self, data, width, height, x, y, color=1):
        """
        Blit a 1-bit BMP image to the display.

        Parameters:
            data: A bytearray containing the image data.
            width: The width of the image.
            height: The height of the image.
            x: The X-coordinate where the image should be positioned.
            y: The Y-coordinate where the image should be positioned.
            color: The color to use for the image (default is 1).
        """
        if self.oled is None:
            return

        # Create a frame buffer from the image data
        # convert image data into MONO_VLSB

        #fbuf = framebuf.FrameBuffer(bytearray(width * height), width, height, framebuf.MONO_VLSB)
        row_size = ((width + 31) // 32) * 4
        for row in range(height):
            row_index = height - row - 1  # BMP stores rows bottom-to-top
            row_start = row_index * row_size
            for col in range(width):
                byte_index = row_start + (col // 8)
                bit_index = 7 - (col % 8)
                if color==1:
                    if data[byte_index] & (1 << bit_index):
                        self.oled.pixel(col, row, 1)
                else:
                    if data[byte_index] & (1 << bit_index):
                        pass
                    else:
                        self.oled.pixel(col, row, 1)

    def fill(self, color):
        if self.oled is None:
            return
        self.oled.fill(color)

    def display_image(self, key, color=1):
        """
        Display an image on the OLED.

        Parameters:
            key: valid keys are [boot, info, error].
        """
        if self.oled is None:
            return
        data = self.get_image_data(key)
        self.blit_bitmap(data, self.oled.width, self.oled.height, 0, 0, color)
        self.oled.show()

    def display_centered_text(self, text, y_level):
        """
        Displays text centered horizontally and at a variable Y-level.

        Parameters:
            oled: The SSD1306 OLED object.
            text: The text string to display.
            y_level: The Y-coordinate where the text should be positioned.
            font: The font to be used for rendering the text (should be a tuple containing character bitmaps).
            max_width: The maximum width of the display (default is 128 for 128x64 displays).
        """

        if self.oled is None:
            return
        # Calculate total width of the text
        text_width = len(text) * 8  # Each character is 8 pixels wide

        # Calculate starting X position to center the text
        x_level = (self.oled.width - text_width) // 2

        # Fill the text rect with 0
        self.oled.fill_rect(x_level, y_level, self.oled.width, 8, 0)


        self.oled.text(text, x_level, y_level, 1)

        # Show the text on the OLED
        self.oled.show()


def bmp_to_ascii(file_path):
    """
    Converts a monochrome BMP file into a 2D list of dots and spaces for debugging.

    Parameters:
        file_path: Path to the BMP file.

    Returns:
        A list of strings, where each string represents a row of the image.
        "." for on pixels, " " for off pixels.
    """
    with open(file_path, "rb") as f:
        # Parse BMP header
        f.seek(10)
        offset = int.from_bytes(f.read(4), 'little')  # Start of pixel array
        f.seek(18)
        width = int.from_bytes(f.read(4), 'little')
        height = int.from_bytes(f.read(4), 'little')
        print(f"Width: {width}, Height: {height}, Offset: {offset}")
        # Ensure the width is a multiple of 8
        if width % 8 != 0:
            raise ValueError("Width must be a multiple of 8 for monochrome BMP")
        row_size = ((width + 31) // 32) * 4  # Each row is padded to the nearest 4 bytes
        # Read raw pixel data
        f.seek(offset)
        raw_data  = f.read(row_size * abs(height))  # Read the raw bitmap data

        # Convert raw pixel data into a 2D list of dots and spaces
        rows = []
        for row in range(height):
            row_index = height - row - 1  # BMP stores rows bottom-to-top
            row_start = row_index * row_size
            row_pixels = []
            for col in range(width):
                byte_index = row_start + (col // 8)
                bit_index = 7 - (col % 8)
                if raw_data[byte_index] & (1 << bit_index):
                    row_pixels.append(".")
                else:
                    row_pixels.append(" ")
            rows.append("".join(row_pixels))

        return rows