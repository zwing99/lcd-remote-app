#!/usr/bin/env python3
"""
Driver for Waveshare 2-inch Mini LCD (240x320) with ST7789VW controller
Uses luma.lcd library for SPI communication
"""

from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.lcd.device import st7789
from PIL import ImageFont, ImageDraw
import RPi.GPIO as GPIO
import os

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

def clear():
    """Clear the display to black"""
    global display
    if display:
        with canvas(display) as draw:
            draw.rectangle(display.bounding_box, fill="black")

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

def get_font(size=16):
    """Get a font for rendering text. Falls back to default if custom font not found."""
    try:
        # Try to use DejaVu Sans Mono (common on Linux)
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", size)
    except:
        try:
            # Fallback to another common font
            return ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf", size)
        except:
            # Use default bitmap font as last resort
            return ImageFont.load_default()

def draw_text_screen(lines, y_offset=0, font_size=16, line_spacing=4):
    """
    Draw multiple lines of text on the screen
    
    Args:
        lines: List of text lines to display
        y_offset: Vertical offset in pixels (for scrolling)
        font_size: Size of the font
        line_spacing: Additional spacing between lines in pixels
    """
    global display
    if not display:
        return
    
    font = get_font(font_size)
    
    with canvas(display) as draw:
        # Fill background
        draw.rectangle(display.bounding_box, fill="black")
        
        # Calculate line height
        # Use a sample character to get consistent height
        bbox = draw.textbbox((0, 0), "Ay", font=font)
        line_height = bbox[3] - bbox[1] + line_spacing
        
        # Draw each line
        y = y_offset
        for line in lines:
            if y > -line_height and y < display.height:  # Only draw visible lines
                draw.text((5, y), line, fill="white", font=font)
            y += line_height

def write_centered_text(text, font_size=24):
    """Display centered text (useful for status messages)"""
    global display
    if not display:
        return
    
    font = get_font(font_size)
    
    with canvas(display) as draw:
        draw.rectangle(display.bounding_box, fill="black")
        
        # Get text bounding box for centering
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (display.width - text_width) // 2
        y = (display.height - text_height) // 2
        
        draw.text((x, y), text, fill="white", font=font)

if __name__ == '__main__':
    # Test the display
    print("Initializing display...")
    init()
    
    print("Drawing white screen...")
    # Draw a completely white screen to test
    with canvas(display) as draw:
        draw.rectangle(display.bounding_box, fill="white")
    
    import time
    time.sleep(2)
    
    print("Drawing centered text...")
    write_centered_text("Hello\nWorld!", 48)  # Increased from 24 to 48
    
    time.sleep(3)
    
    print("Testing scrolling text...")
    # Test scrolling text
    lines = ["Line " + str(i) for i in range(20)]
    for offset in range(0, -400, -2):
        draw_text_screen(lines, offset, font_size=24)  # Increased from 14 to 24
        time.sleep(0.01)
    
    print("Clearing display...")
    clear()
    print("Test complete!")
