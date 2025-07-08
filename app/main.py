# app/main.py

from dotenv import load_dotenv
load_dotenv()

import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Get the parent directory (ai-coffee root)
BASE_DIR = Path(__file__).parent.parent

app = FastAPI()

# 2) Serve static assets from ./static
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# 3) Tell FastAPI where to find templates
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# 4) Root route → landing page
@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Start/onboarding route
@app.get("/start", response_class=HTMLResponse)
async def start(request: Request):
    return templates.TemplateResponse("start.html", {"request": request})

# Legal page route
@app.get("/legal", response_class=HTMLResponse)
async def legal(request: Request):
    return templates.TemplateResponse("legal.html", {"request": request})

# 5) CORS (allow your front-end fetch)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # in prod, lock this to your domain
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


