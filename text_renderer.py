"""
Text rendering module for creating scrollable text images with emoji support.
Handles pre-rendering of text into tall images for efficient scrolling.
"""

from PIL import Image, ImageDraw, ImageFont
import textwrap

# Configuration constants
# When text contains emoji, they take ~3x the width of regular characters
# Adjust margin to leave space on edges for better centering with emoji
TEXT_MARGIN_PX = 10  # Pixels of margin on each side of display
EMOJI_WIDTH_MULTIPLIER = 3  # Approximate: emoji ≈ 3 regular chars in width


def get_font(size=16):
    """Get a font for rendering text."""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansMono-Regular.ttf",
    ]
    
    for font_path in font_paths:
        try:
            return ImageFont.truetype(font_path, size)
        except (FileNotFoundError, OSError):
            continue
    
    return ImageFont.load_default()


def get_emoji_font(size=109):
    """
    Get Noto Color Emoji font for emoji rendering.
    Returns None if font is not available.
    """
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", size)
    except (FileNotFoundError, OSError):
        return None


def is_emoji_char(char):
    """
    Check if a character is an emoji using Unicode ranges.
    More reliable than emoji.is_emoji() for single characters.
    """
    if not char:
        return False
    
    code = ord(char)
    
    # Common emoji Unicode ranges
    emoji_ranges = [
        (0x1F600, 0x1F64F),  # Emoticons
        (0x1F300, 0x1F5FF),  # Misc Symbols and Pictographs
        (0x1F680, 0x1F6FF),  # Transport and Map
        (0x1F1E0, 0x1F1FF),  # Regional indicators (flags)
        (0x2600, 0x26FF),    # Misc symbols
        (0x2700, 0x27BF),    # Dingbats
        (0xFE00, 0xFE0F),    # Variation selectors
        (0x1F900, 0x1F9FF),  # Supplemental Symbols and Pictographs
        (0x1FA00, 0x1FA6F),  # Chess Symbols
        (0x1FA70, 0x1FAFF),  # Symbols and Pictographs Extended-A
        (0x2300, 0x23FF),    # Misc Technical
        (0x203C, 0x3299),    # Various symbols
    ]
    
    for start, end in emoji_ranges:
        if start <= code <= end:
            return True
    
    return False


def calculate_text_width(text, font, emoji_font_size=28):
    """
    Calculate the actual rendered width of text including emoji.
    
    Args:
        text: Text string possibly containing emoji
        font: Regular font for text
        emoji_font_size: Target size for emoji rendering
    
    Returns:
        Total width in pixels
    """
    # Create a temporary draw object to measure text
    temp_img = Image.new('RGB', (1, 1))
    draw = ImageDraw.Draw(temp_img)
    
    emoji_font = get_emoji_font(size=109)
    emoji_scale = emoji_font_size / 109.0
    scaled_emoji_size = int((109 + 40) * emoji_scale)  # Include padding
    
    total_width = 0
    i = 0
    while i < len(text):
        char = text[i]
        
        # Skip variation selectors and zero-width joiners
        if ord(char) in range(0xFE00, 0xFE10) or char == '\u200D':
            i += 1
            continue
        
        # Check if character is an emoji
        if emoji_font and is_emoji_char(char):
            # Emoji takes up scaled size
            total_width += scaled_emoji_size
        else:
            # Regular character
            char_bbox = draw.textbbox((0, 0), char, font=font)
            char_width = char_bbox[2] - char_bbox[0]
            total_width += char_width
        
        i += 1
    
    return total_width


def render_text_with_emoji(draw, position, text, font, text_color, emoji_font_size=28):
    """
    Render text with emoji support by compositing emoji glyphs from Noto Color Emoji.
    
    Args:
        draw: PIL ImageDraw object
        position: (x, y) tuple for text position
        text: Text string possibly containing emoji
        font: Regular font for text
        text_color: Color for regular text (hex string or RGB tuple)
        emoji_font_size: Target size for emoji rendering
    """
    x, y = position
    
    # Try to load emoji font
    emoji_font = get_emoji_font(size=109)  # Native size for NotoColorEmoji
    
    if emoji_font is None:
        # Fallback: use regular text rendering without emoji
        draw.text(position, text, fill=text_color, font=font)
        return
    
    # Get text height for scaling emoji
    bbox = draw.textbbox((0, 0), "Ay", font=font)
    text_height = bbox[3] - bbox[1]
    
    # Scale factor to match emoji to text height
    emoji_scale = emoji_font_size / 109.0
    scaled_emoji_size = int(109 * emoji_scale)
    
    # Process text character by character
    i = 0
    while i < len(text):
        char = text[i]
        
        # Skip variation selectors and zero-width joiners
        if ord(char) in range(0xFE00, 0xFE10) or char == '\u200D':
            i += 1
            continue
        
        # Check if character is an emoji using Unicode ranges
        if is_emoji_char(char):
            # Create temporary image for emoji with padding
            padding = 20
            temp_size = 109 + padding * 2
            emoji_img = Image.new('RGBA', (temp_size, temp_size), (0, 0, 0, 0))
            emoji_draw = ImageDraw.Draw(emoji_img)
            
            # Draw emoji at native size
            emoji_draw.text((padding, padding), char, font=emoji_font, embedded_color=True)
            
            # Scale emoji to match text
            scaled_size = int(temp_size * emoji_scale)
            emoji_img = emoji_img.resize((scaled_size, scaled_size), Image.Resampling.LANCZOS)
            
            # Paste emoji onto main image
            base_img = draw._image
            paste_y = int(y - padding * emoji_scale)  # Adjust for padding
            base_img.paste(emoji_img, (int(x), paste_y), emoji_img)
            
            # Advance x position
            x += scaled_size
        else:
            # Regular character
            draw.text((x, y), char, fill=text_color, font=font)
            char_bbox = draw.textbbox((0, 0), char, font=font)
            char_width = char_bbox[2] - char_bbox[0]
            x += char_width
        
        i += 1


def wrap_text_with_emoji(text, font, max_width_px, emoji_font_size=28):
    """
    Wrap text accounting for emoji width, breaking at max pixel width instead of character count.
    
    Args:
        text: Text to wrap (may contain emoji)
        font: Regular font for text
        max_width_px: Maximum width in pixels before wrapping
        emoji_font_size: Target size for emoji rendering
    
    Returns:
        List of text lines that fit within max_width_px
    """
    if not text.strip():
        return [""]
    
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        # Try adding the word to current line
        test_line = current_line + (" " if current_line else "") + word
        test_width = calculate_text_width(test_line, font, emoji_font_size)
        
        if test_width <= max_width_px:
            # Word fits, add it
            current_line = test_line
        else:
            # Word doesn't fit
            if current_line:
                # Save current line and start new one
                lines.append(current_line)
                current_line = word
                
                # Check if single word is too long
                if calculate_text_width(word, font, emoji_font_size) > max_width_px:
                    # Break long word character by character
                    current_line = ""
                    char_line = ""
                    for char in word:
                        test_char_line = char_line + char
                        if calculate_text_width(test_char_line, font, emoji_font_size) <= max_width_px:
                            char_line = test_char_line
                        else:
                            if char_line:
                                lines.append(char_line)
                            char_line = char
                    current_line = char_line
            else:
                # Current line is empty, word is too long, break it
                char_line = ""
                for char in word:
                    test_char_line = char_line + char
                    if calculate_text_width(test_char_line, font, emoji_font_size) <= max_width_px:
                        char_line = test_char_line
                    else:
                        if char_line:
                            lines.append(char_line)
                        char_line = char
                current_line = char_line
    
    # Add remaining text
    if current_line:
        lines.append(current_line)
    
    return lines if lines else [""]


def create_scrollable_text_image(text, display_width=320, font_size=28, line_spacing=6,
                                  text_color="#ffffff", bg_color="#000000", max_chars_per_line=18):
    """
    Pre-render text into a tall image for scrolling.
    
    Args:
        text: Text to render (can contain newlines and emoji)
        display_width: Width of the display in pixels
        font_size: Font size for text
        line_spacing: Additional spacing between lines
        text_color: Color for text (hex string)
        bg_color: Background color (hex string)
        max_chars_per_line: Maximum characters per line (used as fallback/reference only)
                           Actual wrapping is done by pixel width to account for emoji
    
    Returns:
        PIL Image object containing the rendered text
    """
    font = get_font(font_size)
    
    # Calculate max width in pixels (leave margin on edges)
    # Use module constant for consistent margin across emoji and text
    max_width_px = display_width - (2 * TEXT_MARGIN_PX)
    
    # Split text into lines, honoring existing newlines
    raw_lines = text.split('\n')
    
    # Wrap long lines to fit display width using pixel-based wrapping
    display_lines = []
    for raw_line in raw_lines:
        if not raw_line.strip():
            display_lines.append("")
        else:
            # Use smart wrapping that accounts for emoji width
            wrapped = wrap_text_with_emoji(raw_line, font, max_width_px, emoji_font_size=font_size)
            display_lines.extend(wrapped)
    
    # Calculate total image height
    line_height = font_size + line_spacing
    total_height = len(display_lines) * line_height
    
    # Create tall image for all text
    full_image = Image.new('RGB', (display_width, total_height), color=bg_color)
    draw = ImageDraw.Draw(full_image)
    
    # Render each line with emoji support
    y_offset = 0
    for line in display_lines:
        if line.strip():
            # Calculate actual width including emoji for proper centering
            text_width = calculate_text_width(line, font, emoji_font_size=font_size)
            x = (display_width - text_width) // 2
            
            # Render text with emoji support
            render_text_with_emoji(draw, (x, y_offset), line, font, text_color, emoji_font_size=font_size)
        
        y_offset += line_height
    
    return full_image


def create_scroll_frame(full_image, y_position, display_width=320, display_height=240, bg_color="#000000"):
    """
    Create a single frame by cropping the pre-rendered tall image.
    
    Args:
        full_image: Pre-rendered tall image
        y_position: Current scroll position (0 = top of full_image)
        display_width: Display width in pixels
        display_height: Display height in pixels
        bg_color: Background color for empty areas
    
    Returns:
        PIL Image object for the current frame
    """
    total_text_height = full_image.height
    frame = Image.new('RGB', (display_width, display_height), color=bg_color)
    
    # Calculate which part of the full_image to show
    if y_position < 0:
        # Text hasn't fully entered yet - show bottom portion
        src_y = 0
        src_height = min(total_text_height, display_height + y_position)
        dest_y = -y_position
        if src_height > 0:
            crop = full_image.crop((0, src_y, display_width, src_y + src_height))
            frame.paste(crop, (0, dest_y))
    elif y_position + display_height <= total_text_height:
        # Text is fully visible - crop from full_image
        crop = full_image.crop((0, y_position, display_width, y_position + display_height))
        frame.paste(crop, (0, 0))
    else:
        # Text is scrolling off the top
        src_height = total_text_height - y_position
        if src_height > 0:
            crop = full_image.crop((0, y_position, display_width, total_text_height))
            frame.paste(crop, (0, 0))
    
    return frame
