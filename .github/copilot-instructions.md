# LCD Remote App - AI Coding Agent Instructions

## Project Overview
A FastAPI web service that controls a **Waveshare 2-inch Mini LCD display** (240x320 pixels, ST7789VW controller) on a Raspberry Pi. Users send text via a web interface, which scrolls vertically "Star Wars credits" style on the physical LCD.

## Architecture

### Core Components
- **`main.py`**: FastAPI application with async scrolling logic
  - Uses global `current_scroll_task` to manage single active scroll task
  - `scroll_text()` wraps text to ~35 chars/line, scrolls pixel-by-pixel continuously
  - Lifespan events handle LCD initialization/cleanup
- **`waveshare_lcd.py`**: ST7789 display driver using luma.lcd library
  - Communicates via SPI (port 0, device 0)
  - Uses GPIO 25 (DC), GPIO 27 (RST) for control signals
  - Renders text graphically using PIL/Pillow with TrueType fonts
- **`templates/index.html`**: Single-page web UI with textarea and status feedback

### Data Flow
1. User submits text via HTML form → POST `/display`
2. Cancel any running scroll task, create new task with `asyncio.create_task()`
3. `scroll_text()` loops indefinitely: wraps text to display width, scrolls from bottom to top pixel-by-pixel
4. LCD updated via `waveshare_lcd.draw_text_screen()` which renders text using PIL ImageDraw

## Development Workflow

### Running Locally (Docker)
```bash
docker compose up
```
- Uses `uv` package manager (no need for separate pip/venv)
- Requires `privileged: true` and `/dev/spidev0.0`, `/dev/gpiomem` device access for SPI
- Auto-reload enabled via `uvicorn --reload`

### Running Without Docker
```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Testing LCD Hardware
```bash
uv run python waveshare_lcd.py
```
Displays centered "Hello World!" test message and scrolling demo. Useful for debugging SPI connectivity.

## Critical Patterns

### Async Task Management
- **Always cancel previous task before starting new one** (prevents multiple simultaneous scrolls)
- Pattern in `main.py` `/display` endpoint:
  ```python
  if current_scroll_task is not None and not current_scroll_task.done():
      current_scroll_task.cancel()
      try:
          await current_scroll_task
      except asyncio.CancelledError:
          pass
  ```

### Text Processing
- LCD is 240px wide × 320px tall (graphical display, not character-based)
- Text wrapped using `textwrap.wrap()` to ~35 chars/line (font-dependent)
- Font size: 14pt by default (configurable)
- Scrolling: pixel-by-pixel from bottom (y=320) to top (y=-total_height)
- Frame delay: 0.03s between updates (smooth 33fps scrolling)

### SPI Hardware Constraints
- **Must run on Raspberry Pi** or system with SPI bus
- SPI device: `/dev/spidev0.0` (port 0, device 0)
- GPIO pins: DC=25, RST=27, (optional BL=24 for backlight)
- Requires SPI enabled in `/boot/config.txt`: `dtparam=spi=on`
- Needs root/privileged access or user in `spi`/`gpio` groups
- Display uses BGR color order (set in st7789 device init)

## Dependencies & Tools
- **uv**: Zero-config Python package manager (replaces pip/venv)
- **FastAPI**: Web framework with async support
- **luma.lcd**: Device driver library for ST7789 SPI displays
- **Pillow (PIL)**: Image processing and text rendering
- **uvicorn**: ASGI server with hot reload

## Common Tasks

**Add new LCD function**: Extend `waveshare_lcd.py` with new canvas drawing operations using PIL ImageDraw

**Change scroll speed**: Modify `SCROLL_SPEED` (pixels/frame) or `FRAME_DELAY` (seconds) in `scroll_text()`

**Change font**: Edit `get_font()` in `waveshare_lcd.py` to use different TrueType font paths

**Adjust display orientation**: Change `rotate` parameter (0/1/2/3) in `st7789()` device initialization

**Add new endpoint**: Follow FastAPI patterns in `main.py` (use async def, Pydantic models)

**Modify UI**: Edit `templates/index.html` (single-file Jinja2 template)

## Gotchas
- Display initialized once during lifespan startup - not thread-safe
- Scroll task runs indefinitely until cancelled - never returns normally
- Font rendering requires TrueType fonts or falls back to bitmap default
- SPI bus speed (40MHz) and transfer size (4096 bytes) tuned for performance - adjust if display glitches
- Container needs `init: true` to properly handle signals and zombie processes
- BGR color order specific to Waveshare hardware - other ST7789 displays may need `bgr=False`
