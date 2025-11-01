import LCD1602
import asyncio
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
from fastapi.templating import Jinja2Templates
from fastapi import Request

class DisplayText(BaseModel):
    text: str

# Global variable to control scrolling
current_scroll_task = None

async def scroll_text(text: str):
    """Scroll text vertically like Star Wars credits"""
    try:
        # Split text into lines, honoring existing newlines
        raw_lines = text.split('\n')
        
        # Break each line into 16-char chunks at word boundaries
        display_lines = []
        for raw_line in raw_lines:
            if not raw_line.strip():
                # Preserve empty lines
                display_lines.append("")
                continue
                
            # Break line into words
            words = raw_line.split()
            current_line = ""
            
            for word in words:
                # If adding this word would exceed 16 chars
                if len(current_line) + len(word) + (1 if current_line else 0) > 16:
                    # If word itself is longer than 16, split it
                    if len(word) > 16:
                        # Add current line if it has content
                        if current_line:
                            display_lines.append(current_line)
                            current_line = ""
                        # Split the long word
                        while len(word) > 16:
                            display_lines.append(word[:16])
                            word = word[16:]
                        current_line = word
                    else:
                        # Save current line and start new one
                        if current_line:
                            display_lines.append(current_line)
                        current_line = word
                else:
                    # Add word to current line
                    if current_line:
                        current_line += " " + word
                    else:
                        current_line = word
            
            # Add any remaining text
            if current_line:
                display_lines.append(current_line)
        
        # Scroll through all lines continuously
        LCD1602.clear()
        while True:
            # Start with blank line, then scroll through all the lines
            # This makes text start from bottom line and scroll up
            for i in range(-1, len(display_lines)):
                # Display two lines at a time
                line1 = display_lines[i] if i >= 0 and i < len(display_lines) else ""
                line2 = display_lines[i + 1] if i + 1 >= 0 and i + 1 < len(display_lines) else ""
                
                LCD1602.write(0, 0, line1[:16].ljust(16))
                LCD1602.write(0, 1, line2[:16].ljust(16))
                
                await asyncio.sleep(0.8)  # Pause between scrolls
            
            # Add a blank line separator before repeating
            LCD1602.write(0, 0, "".ljust(16))
            LCD1602.write(0, 1, "".ljust(16))
            await asyncio.sleep(0.8)
        
    except asyncio.CancelledError:
        # Task was cancelled, clean up
        LCD1602.clear()
        raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize LCD
    LCD1602.init(0x27, 1)
    yield
    # Shutdown: Clear LCD
    LCD1602.clear()

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
