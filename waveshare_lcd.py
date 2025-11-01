#!/usr/bin/env python3
"""
Driver for Waveshare 2-inch Mini LCD (240x320) with ST7789VW controller
Uses luma.lcd library for SPI communication
"""

from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.lcd.device import st7789
from PIL import ImageFont, ImageDraw, Image
import RPi.GPIO as GPIO
import emoji
import re
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

def get_font(size=16):
    """Get a font for rendering text with emoji support."""
    font_paths = [
        # Primary: DejaVu Sans (best for regular text)
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        # Secondary: Liberation Sans
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        # Fallback: DejaVu Sans Mono
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        # Last resort: Noto Sans Mono
        "/usr/share/fonts/truetype/noto/NotoSansMono-Regular.ttf",
    ]
    
    for font_path in font_paths:
        try:
            return ImageFont.truetype(font_path, size)
        except (FileNotFoundError, OSError):
            continue
    
    # Use default bitmap font as last resort
    return ImageFont.load_default()

def get_emoji_font(size=109):
    """
    Get Noto Color Emoji font for emoji rendering.
    Note: This is a bitmap font with fixed sizes (only works at 109px)
    """
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", size)
    except:
        # Fallback to regular font
        return get_font(size)

def draw_text_with_emoji(draw_obj, position, text, font, text_color, emoji_font_size=109):
    """
    Draw text with proper emoji rendering.
    Detects emoji in text and renders them using Noto Color Emoji font.
    
    Args:
        draw_obj: PIL ImageDraw object
        position: (x, y) tuple for text position
        text: Text string possibly containing emoji
        font: Regular font for text
        text_color: Color for regular text
        emoji_font_size: Size for emoji font (109 is native size for Noto Color Emoji)
    """
    x, y = position
    
    # Try to load emoji font at native size
    try:
        emoji_font = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", emoji_font_size)
    except:
        # If emoji font fails, just use regular rendering
        draw_obj.text(position, text, fill=text_color, font=font)
        return
    
    # Get font size to scale emoji proportionally
    bbox = draw_obj.textbbox((0, 0), "A", font=font)
    text_height = bbox[3] - bbox[1]
    
    # Scale emoji to match text height (emoji font is 109px native)
    emoji_scale = text_height / emoji_font_size
    
    # Process text character by character, skipping variation selectors
    i = 0
    while i < len(text):
        char = text[i]
        
        # Skip variation selectors (U+FE00 to U+FE0F) and zero-width joiners
        if ord(char) in range(0xFE00, 0xFE10) or char == '\u200D':
            i += 1
            continue
        
        # Check if character is an emoji
        if emoji.is_emoji(char):
            # Render emoji at full size on temporary image with extra padding
            # Add padding to prevent cutoff
            padded_size = emoji_font_size + 20
            emoji_img = Image.new('RGBA', (padded_size, padded_size), (0, 0, 0, 0))
            emoji_draw = ImageDraw.Draw(emoji_img)
            emoji_draw.text((10, 10), char, font=emoji_font, embedded_color=True)
            
            # Scale emoji to match text height
            scaled_size = int(emoji_font_size * emoji_scale)
            scaled_padded = int(padded_size * emoji_scale)
            emoji_img = emoji_img.resize((scaled_padded, scaled_padded), Image.Resampling.LANCZOS)
            
            # Paste emoji onto main image
            # Get the image from the draw object
            base_img = draw_obj._image
            base_img.paste(emoji_img, (int(x), int(y)), emoji_img)
            
            # Advance x position - use the full padded width plus extra spacing
            x += scaled_padded + 3
        else:
            # Regular character - draw normally
            draw_obj.text((x, y), char, fill=text_color, font=font)
            # Get actual width of this character
            char_bbox = draw_obj.textbbox((x, y), char, font=font)
            char_width = char_bbox[2] - char_bbox[0]
            x += char_width
        
        i += 1

def draw_text_screen(lines, y_offset=0, font_size=16, line_spacing=4, text_color="#ffffff", bg_color="#000000"):
    """
    Draw multiple lines of text on the screen with real emoji support.
    
    Args:
        lines: List of text lines to display
        y_offset: Vertical offset in pixels (for scrolling)
        font_size: Size of the font
        line_spacing: Additional spacing between lines in pixels
        text_color: Color of the text (hex format, e.g., "#ffffff")
        bg_color: Background color (hex format, e.g., "#000000")
    """
    global display
    if not display:
        return
    
    font = get_font(font_size)
    
    # Create a temporary image to render text
    temp_img = Image.new('RGB', (display.width, display.height), color=bg_color)
    draw = ImageDraw.Draw(temp_img)
    
    # Calculate line height
    bbox = draw.textbbox((0, 0), "Ay", font=font)
    line_height = bbox[3] - bbox[1] + line_spacing
    
    # Draw each line with emoji support
    y = y_offset
    for line in lines:
        if y > -line_height and y < display.height:  # Only draw visible lines
            try:
                # Draw text with real emoji rendering
                draw_text_with_emoji(draw, (5, y), line, font, text_color)
            except Exception as e:
                # Fallback: simple text rendering
                try:
                    draw.text((5, y), line, fill=text_color, font=font)
                except:
                    pass
        y += line_height
    
    # Display the rendered image directly using display.display()
    display.display(temp_img)

def write_centered_text(text, font_size=24):
    """Display centered text with emoji support (useful for status messages)"""
    global display
    if not display:
        return
    
    font = get_font(font_size)
    
    # Create temporary image for rendering
    temp_img = Image.new('RGB', (display.width, display.height), color='black')
    draw = ImageDraw.Draw(temp_img)
    
    # Get text bounding box for centering
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
    except:
        # Fallback for emoji or special characters
        bbox = draw.textbbox((0, 0), "A", font=font)
    
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (display.width - text_width) // 2
    y = (display.height - text_height) // 2
    
    try:
        draw.text((x, y), text, fill="white", font=font)
    except:
        pass
    
    # Display the rendered image directly
    display.display(temp_img)

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
