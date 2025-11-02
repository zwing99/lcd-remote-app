import waveshare_lcd
import text_renderer
import asyncio
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from contextlib import asynccontextmanager
from fastapi.templating import Jinja2Templates
from fastapi import Request
import random
from phrases import PHRASES

class DisplayText(BaseModel):
    text: str
    textColor: str = "#ffffff"  # Default white
    backgroundColor: str = "#000000"  # Default black

# Global variable to control scrolling
current_scroll_task = None

async def scroll_text(text: str, text_color: str = "#ffffff", bg_color: str = "#000000"):
    """Scroll text vertically like Star Wars credits on the graphical LCD with pre-rendered image"""
    try:
        # Configuration for the display (already in landscape: 320x240)
        DISPLAY_WIDTH = 320  # pixels (landscape mode)
        DISPLAY_HEIGHT = 240  # pixels (landscape mode)
        FONT_SIZE = 28
        LINE_SPACING = 6
        SCROLL_SPEED = 3
        FRAME_DELAY = 0.01
        # Note: MAX_CHARS_PER_LINE is a reference value. Actual wrapping uses pixel width
        # to properly handle emoji (which take ~3x the width of regular characters).
        # See text_renderer.TEXT_MARGIN_PX constant to adjust margins for emoji.
        MAX_CHARS_PER_LINE = 18
        
        # Add decorative dashes before and after text
        separator_line = "-" * 28
        decorated_text = f"{separator_line}\n{text}\n{separator_line}"
        
        # PRE-RENDER: Create one tall image with all the text using text_renderer module
        full_image = text_renderer.create_scrollable_text_image(
            text=decorated_text,
            display_width=DISPLAY_WIDTH,
            font_size=FONT_SIZE,
            line_spacing=LINE_SPACING,
            text_color=text_color,
            bg_color=bg_color,
            max_chars_per_line=MAX_CHARS_PER_LINE
        )
        
        total_text_height = full_image.height
        
        # SCROLL: Loop through the pre-rendered image
        y_position = -DISPLAY_HEIGHT  # Start with text below screen
        
        while True:
            # Create display frame by cropping the tall image
            frame = text_renderer.create_scroll_frame(
                full_image=full_image,
                y_position=y_position,
                display_width=DISPLAY_WIDTH,
                display_height=DISPLAY_HEIGHT,
                bg_color=bg_color
            )
            
            # Display the frame (no rotation needed - display is already landscape)
            waveshare_lcd.display.display(frame)
            
            # Move position
            y_position += SCROLL_SPEED
            
            # Loop back when text has scrolled off completely
            if y_position >= total_text_height:
                y_position = -DISPLAY_HEIGHT
            
            await asyncio.sleep(FRAME_DELAY)
            
    except asyncio.CancelledError:
        # Task was cancelled, clean up
        waveshare_lcd.clear(bg_color="#000000")
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
app.mount("/static", StaticFiles(directory="static"), name="static")

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
    
    # Always scroll the text (Star Wars style) with custom colors
    current_scroll_task = asyncio.create_task(
        scroll_text(data.text, data.textColor, data.backgroundColor)
    )
    return {"status": "success", "scrolling": True}

@app.get("/random-phrase")
async def get_random_phrase():
    """Get a random phrase with emoji"""
    phrase = random.choice(PHRASES)
    return {"phrase": phrase}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
