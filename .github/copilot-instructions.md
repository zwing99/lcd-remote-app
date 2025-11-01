# LCD Remote App - AI Coding Agent Instructions

## Project Overview
A FastAPI web service that controls a 16x2 I2C LCD display on a Raspberry Pi. Users send text via a web interface, which scrolls vertically "Star Wars credits" style on the physical LCD.

## Architecture

### Core Components
- **`main.py`**: FastAPI application with async scrolling logic
  - Uses global `current_scroll_task` to manage single active scroll task
  - `scroll_text()` breaks text into 16-char lines at word boundaries, scrolls continuously
  - Lifespan events handle LCD initialization/cleanup
- **`LCD1602.py`**: Low-level I2C LCD driver using smbus2
  - Communicates with LCD at address 0x27 via I2C bus 1
  - 4-bit mode protocol (sends commands/data in two 4-bit nibbles)
- **`templates/index.html`**: Single-page web UI with textarea and status feedback

### Data Flow
1. User submits text via HTML form → POST `/display`
2. Cancel any running scroll task, create new task with `asyncio.create_task()`
3. `scroll_text()` loops indefinitely: splits text into 16-char chunks, displays 2 lines at a time, shifts every 0.8s
4. LCD updated via `LCD1602.write(x, y, text)` with coordinates (0-15, 0-1)

## Development Workflow

### Running Locally (Docker)
```bash
docker compose up
```
- Uses `uv` package manager (no need for separate pip/venv)
- Requires `privileged: true` and `/dev/i2c-1` device access for I2C
- Auto-reload enabled via `uvicorn --reload`

### Running Without Docker
```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Testing LCD Hardware
```bash
uv run python LCD1602.py
```
Displays "Hello world!" test message. Useful for debugging I2C connectivity.

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
- LCD is 16 chars wide × 2 lines
- Word wrapping breaks at spaces to avoid mid-word splits
- Long words (>16 chars) split with hard breaks
- Empty lines preserved for paragraph spacing
- Each line padded to 16 chars with `ljust(16)` to clear previous text

### I2C Hardware Constraints
- **Must run on Raspberry Pi** or system with I2C bus
- LCD address: `0x27`, bus: `1`
- Requires root/privileged access for `/dev/i2c-1`
- Commands sent in 4-bit mode with enable pulse timing (2ms delays critical)

## Dependencies & Tools
- **uv**: Zero-config Python package manager (replaces pip/venv)
- **FastAPI**: Web framework with async support
- **smbus2**: Pure Python I2C library (no system dependencies)
- **uvicorn**: ASGI server with hot reload

## Common Tasks

**Add new LCD function**: Extend `LCD1602.py` with new `send_command()` calls (see init() for command examples)

**Change scroll speed**: Modify `await asyncio.sleep(0.8)` in `scroll_text()`

**Add new endpoint**: Follow FastAPI patterns in `main.py` (use async def, Pydantic models)

**Modify UI**: Edit `templates/index.html` (single-file Jinja2 template)

## Gotchas
- Global `BUS` in `LCD1602.py` initialized once per process (not thread-safe)
- Scroll task runs indefinitely until cancelled - never returns normally
- LCD initialization commands (`0x33`, `0x32`, etc.) are timing-sensitive - don't modify delays
- Container needs `init: true` to properly handle signals and zombie processes
