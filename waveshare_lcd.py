#!/usr/bin/env python3
"""
Driver for Waveshare 2-inch Mini LCD (240x320) with ST7789VW controller
Uses luma.lcd library for SPI communication
"""

from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.lcd.device import st7789
import RPi.GPIO as GPIO

# Global display instance
display = None
backlight_pwm = None
BACKLIGHT_PIN = 18  # GPIO 18 for backlight control (BCM2835 column in wiring table)
CS_PIN = 8  # Default CE0 for SPI

def init():
    """Initialize the ST7789 display via SPI"""
    global display
    
    # Disable GPIO warnings
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    
    # Configure SPI interface
    # For Waveshare 2-inch LCD with ST7789V:
    # Using BCM2835 pin numbering from wiring table:
    # - DC = GPIO 25
    # - RST = GPIO 27
    # - BL = GPIO 18
    serial = spi(
        port=0,
        device=0,
        gpio_DC=25,  # DC pin
        gpio_RST=27,  # RST pin
        bus_speed_hz=40000000,  # 40MHz as in their example
        transfer_size=4096
    )
    
    # Create ST7789 device instance
    # Waveshare 2-inch LCD in landscape mode (320x240)
    display = st7789(
        serial,
        width=320,
        height=240,
        rotate=0,  # 0 degrees for horizontal/landscape orientation
        mode='RGB',
        bgr=True,  # Waveshare uses BGR color order
        h_offset=0,
        v_offset=0
    )
    
    # Turn on backlight using PWM at 100% duty cycle
    global backlight_pwm
    GPIO.setup(BACKLIGHT_PIN, GPIO.OUT)
    backlight_pwm = GPIO.PWM(BACKLIGHT_PIN, 1000)  # 1kHz frequency
    backlight_pwm.start(100)  # 100% duty cycle for full brightness
    
    print(f"Display initialized: {display.width}x{display.height}")
    print(f"Backlight: GPIO {BACKLIGHT_PIN} PWM at 100%")
    print(f"DC: GPIO 25, RST: GPIO 27")
    
    # Clear display
    clear()

def clear(bg_color="#000000"):
    """Clear the display to specified color"""
    global display
    if display:
        with canvas(display) as draw:
            draw.rectangle(display.bounding_box, fill=bg_color)

def backlight_on():
    """Turn on the backlight"""
    if backlight_pwm:
        backlight_pwm.ChangeDutyCycle(100)

def backlight_off():
    """Turn off the backlight"""
    if backlight_pwm:
        backlight_pwm.ChangeDutyCycle(0)

def set_backlight(brightness):
    """Set backlight brightness (0-100)"""
    if backlight_pwm:
        backlight_pwm.ChangeDutyCycle(max(0, min(100, brightness)))


if __name__ == '__main__':
    """Test the display hardware"""
    from PIL import Image, ImageDraw, ImageFont
    
    print("Initializing display...")
    init()
    
    print("Drawing white screen...")
    with canvas(display) as draw:
        draw.rectangle(display.bounding_box, fill="white")
    
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
    
    display.display(test_img)
    time.sleep(3)
    
    print("Clearing display...")
    clear()
    print("Test complete!")
