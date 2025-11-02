#!/usr/bin/env python3
"""
Driver for Waveshare 2-inch Mini LCD (240x320) with ST7789VW controller
Uses luma.lcd library for SPI communication
"""

from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.lcd.device import st7789
import RPi.GPIO as GPIO

# Default GPIO pins and constants
BACKLIGHT_PIN = 18  # GPIO 18 for backlight control (BCM2835 column in wiring table)
DC_PIN = 25
RST_PIN = 27


class LcdController:
    """Singleton controller for the Waveshare ST7789 display.

    Usage:
      - Use LcdController.get_instance() to get the singleton (will initialize on first call).
      - Call LcdController.clear_instance() from FastAPI lifespan shutdown to dispose resources.

    Public methods mirror the previous module-level API: init(), clear(), backlight_on(), backlight_off(), set_backlight(), dispose().
    """

    _instance = None

    def __init__(self):
        # instance attributes
        self.display = None
        self.backlight_pwm = None

    @classmethod
    def instance(cls):
        """Return the singleton instance, initializing it on first call."""
        if cls._instance is None:
            inst = cls()
            inst.init()
            cls._instance = inst
        return cls._instance

    @classmethod
    def clear_instance(cls):
        """Dispose of the singleton and clear the reference (call from FastAPI shutdown)."""
        if cls._instance is not None:
            try:
                cls._instance.dispose()
            finally:
                cls._instance = None

    def init(self):
        """Initialize the ST7789 display via SPI (idempotent)."""
        if self.display is not None:
            return

        # Disable GPIO warnings and set BCM numbering
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        # Configure SPI interface
        serial = spi(
            port=0,
            device=0,
            gpio_DC=DC_PIN,
            gpio_RST=RST_PIN,
            bus_speed_hz=40000000,
            transfer_size=4096,
        )

        # Create ST7789 device instance (Waveshare 2-inch in landscape)
        self.display = st7789(
            serial,
            width=320,
            height=240,
            rotate=0,
            mode='RGB',
            bgr=True,
            h_offset=0,
            v_offset=0,
        )

        # Start backlight PWM
        GPIO.setup(BACKLIGHT_PIN, GPIO.OUT)
        self.backlight_pwm = GPIO.PWM(BACKLIGHT_PIN, 1000)
        try:
            self.backlight_pwm.start(100)
        except Exception:
            # If PWM start fails, ensure attribute remains consistent
            self.backlight_pwm = None

        print(f"Display initialized: {self.display.width}x{self.display.height}")
        print(f"Backlight: GPIO {BACKLIGHT_PIN} PWM at 100%")
        print(f"DC: GPIO {DC_PIN}, RST: GPIO {RST_PIN}")

        # Clear display on init
        self.clear()

    def clear(self, bg_color="#000000"):
        """Clear the display to specified color."""
        if self.display:
            with canvas(self.display) as draw:
                draw.rectangle(self.display.bounding_box, fill=bg_color)

    def backlight_on(self):
        """Turn on the backlight (100%)."""
        if self.backlight_pwm:
            try:
                self.backlight_pwm.ChangeDutyCycle(100)
            except Exception:
                pass

    def backlight_off(self):
        """Turn off the backlight (0%)."""
        if self.backlight_pwm:
            try:
                self.backlight_pwm.ChangeDutyCycle(0)
            except Exception:
                pass

    def set_backlight(self, brightness):
        """Set backlight brightness (0-100)."""
        if self.backlight_pwm:
            try:
                self.backlight_pwm.ChangeDutyCycle(max(0, min(100, int(brightness))))
            except Exception:
                pass

    def dispose(self):
        """Cleanly stop PWM, clear display, and cleanup GPIO resources."""
        # Try to turn display to black first
        try:
            if self.display:
                with canvas(self.display) as draw:
                    draw.rectangle(self.display.bounding_box, fill="#000000")
        except Exception:
            pass

        # Stop PWM
        try:
            if self.backlight_pwm:
                self.backlight_pwm.stop()
                self.backlight_pwm = None
                self.backlight_off()
        except Exception:
            pass

        # Clear display reference
        self.display = None

        # Attempt to cleanup GPIO (safe to call multiple times)
        try:
            GPIO.cleanup()
        except Exception:
            pass


# Module-level wrappers for backward compatibility
def init():
    """Initialize the global singleton instance (keeps original API)."""
    LcdController.instance()


def clear(bg_color="#000000"):
    LcdController.instance().clear(bg_color)


def backlight_on():
    LcdController.instance().backlight_on()


def backlight_off():
    LcdController.instance().backlight_off()


def set_backlight(brightness):
    LcdController.instance().set_backlight(brightness)


def dispose():
    """Dispose the singleton and free resources."""
    LcdController.clear_instance()


if __name__ == '__main__':
    """Test the display hardware"""
    from PIL import Image, ImageDraw, ImageFont
    
    print("Initializing display...")
    init()

    lcd = LcdController.instance()

    print("Drawing white screen...")
    if lcd.display:
        with canvas(lcd.display) as draw:
            draw.rectangle(lcd.display.bounding_box, fill="white")
    
    import time
    time.sleep(2)
    
    print("Drawing test pattern...")
    # Create a simple test image
    test_img = Image.new('RGB', (320, 240), color='black')
    draw = ImageDraw.Draw(test_img)
    
    # Draw colored rectangles
    draw.rectangle([0, 0, 106, 240], fill='red')
    draw.rectangle([107, 0, 213, 240], fill='green')
    draw.rectangle([214, 0, 320, 240], fill='blue')
    
    # Draw text
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 48)
    except:
        font = ImageFont.load_default()
    
    draw.text((80, 100), "Hello\nWorld!", fill='white', font=font)
    
    if lcd.display:
        lcd.display.display(test_img)
    time.sleep(3)
    
    print("Clearing display...")
    clear()
    print("Test complete!")
