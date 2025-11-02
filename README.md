# LCD Remote App

A FastAPI web service that displays scrolling text on a **Waveshare 2-inch Mini LCD Screen** (240x320 IPS display with ST7789VW controller). Users can submit text via a web interface, which scrolls vertically in "Star Wars credits" style on the physical LCD.

## Hardware Requirements

- Raspberry Pi (tested on Pi 3/4/5)
- **Waveshare 2-inch Mini LCD** (240x320 resolution, ST7789VW driver, SPI interface)
  - Product page: [Waveshare 2inch LCD Module](https://www.waveshare.com/2inch-lcd-module.htm)
  - Features: 240×320 pixels, 262K RGB colors, SPI interface
  
### Wiring (SPI Connection)

Default GPIO pins for Waveshare 2-inch LCD:
- VCC → 3.3V
- GND → GND  
- DIN → GPIO 10 (MOSI)
- CLK → GPIO 11 (SCLK)
- CS → GPIO 8 (CE0)
- DC → GPIO 25
- RST → GPIO 27
- BL → GPIO 24 (backlight, optional)

### Raspberry Pi Setup

Enable SPI interface:
```bash
sudo raspi-config
# Navigate to: Interface Options → SPI → Enable
```

Or enable directly:
```bash
echo "dtparam=spi=on" | sudo tee -a /boot/config.txt
sudo reboot
```

## Running the Application

### With Docker Compose (Recommended)

```bash
docker compose up
```

The service will be available at `http://localhost` (port 80)

### Without Docker

```bash
# Install dependencies
uv sync

# Run the server
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Test LCD Hardware

```bash
uv run python waveshare_lcd.py
```

This will display a test message and scrolling demo.

## Features

- **Web Interface**: Clean, responsive form to submit text for display
- **Star Wars Credits Effect**: Smooth vertical scrolling with pixel-level control
- **Color Customization**: Pick custom text and background colors
- **Emoji Support**: Full emoji support with intelligent rendering
- **Auto Text Wrapping**: Intelligently wraps long lines
- **Continuous Loop**: Text scrolls continuously until new text is submitted
- **Task Cancellation**: Submitting new text immediately replaces current display
- **Static Assets**: Favicon and CSS bundled for complete offline experience

## Architecture

- **`main.py`**: FastAPI application with async scrolling logic
- **`waveshare_lcd.py`**: ST7789 display driver using luma.lcd library
- **`templates/index.html`**: Web UI for text submission

## Configuration

Edit `main.py` to adjust:
- Font size (`FONT_SIZE = 28`)
- Scroll speed (`SCROLL_SPEED = 3` pixels/frame)
- Frame delay (`FRAME_DELAY = 0.01` seconds)
- Characters per line (`MAX_CHARS_PER_LINE = 18`)

Edit `waveshare_lcd.py` to adjust:
- GPIO pins (if using custom wiring)
- Display rotation (`rotate` parameter: 0/1/2/3)
- Color mode and BGR order

## Dependencies

- **luma.lcd**: Device driver library for ST7789 SPI displays
- **Pillow**: Image processing for text rendering
- **FastAPI**: Web framework
- **uvicorn**: ASGI server

## Troubleshooting

**Display not working:**
1. Verify SPI is enabled: `ls /dev/spidev*` should show `/dev/spidev0.0`
2. Check wiring matches GPIO pins in `waveshare_lcd.py`
3. Test with: `uv run python waveshare_lcd.py`

**Permission errors:**
- Run with sudo or add user to `spi` and `gpio` groups:
  ```bash
  sudo usermod -a -G spi,gpio $USER
  ```

**Display upside down:**
- Change `rotate` parameter in `waveshare_lcd.py` init() function (0, 1, 2, or 3)

**Wrong colors:**
- Try toggling `bgr=True/False` in `st7789()` initialization
