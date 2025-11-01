import waveshare_lcd
import asyncio
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
from fastapi.templating import Jinja2Templates
from fastapi import Request
import textwrap

class DisplayText(BaseModel):
    text: str

# Global variable to control scrolling
current_scroll_task = None

async def scroll_text(text: str):
    """Scroll text vertically like Star Wars credits on the graphical LCD"""
    try:
        # Configuration for the display
        DISPLAY_WIDTH = 320  # pixels (landscape mode)
        FONT_SIZE = 28  # Increased from 14 for better visibility
        LINE_SPACING = 6
        SCROLL_SPEED = 4  # Reduced to 75% of previous (5 * 0.75 = 3.75 ≈ 4)
        FRAME_DELAY = 0.025  # Adjusted for smoother scrolling
        
        # Calculate max chars per line based on font size
        # With 28pt font, approximately 12-15 characters fit per line
        MAX_CHARS_PER_LINE = 18
        
        # Split text into lines, honoring existing newlines
        raw_lines = text.split('\n')
        
        # Wrap long lines to fit display width
        display_lines = []
        for raw_line in raw_lines:
            if not raw_line.strip():
                # Preserve empty lines
                display_lines.append("")
            else:
                # Wrap line to fit within display width
                wrapped = textwrap.wrap(raw_line, width=MAX_CHARS_PER_LINE, break_long_words=True)
                display_lines.extend(wrapped if wrapped else [""])
        
        # Calculate total scroll distance
        # Start with all text below screen, end with all text above screen
        line_height = FONT_SIZE + LINE_SPACING
        total_height = len(display_lines) * line_height
        start_offset = 240  # Start below screen (display height in landscape)
        end_offset = -total_height - 50  # End above screen (less padding)
        
        # Scroll continuously
        while True:
            # Scroll from bottom to top
            for y_offset in range(start_offset, end_offset, -SCROLL_SPEED):
                waveshare_lcd.draw_text_screen(
                    display_lines,
                    y_offset=y_offset,
                    font_size=FONT_SIZE,
                    line_spacing=LINE_SPACING
                )
                await asyncio.sleep(FRAME_DELAY)
            
            # Brief pause before repeating
            await asyncio.sleep(0.5)
        
    except asyncio.CancelledError:
        # Task was cancelled, clean up
        waveshare_lcd.clear()
        raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize LCD
    waveshare_lcd.init()
    yield
    # Shutdown: Clear LCD
    waveshare_lcd.clear()

app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/display")
async def display_text(data: DisplayText, background_tasks: BackgroundTasks):
    global current_scroll_task
    
    # Cancel any existing scroll task
    if current_scroll_task is not None and not current_scroll_task.done():
        current_scroll_task.cancel()
        try:
            await current_scroll_task
        except asyncio.CancelledError:
            pass
    
    # Always scroll the text (Star Wars style)
    current_scroll_task = asyncio.create_task(scroll_text(data.text))
    return {"status": "success", "scrolling": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
