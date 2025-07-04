# app/main.py

from dotenv import load_dotenv
load_dotenv()

import os
from pathlib import Path
import openai
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# 1) Configure OpenAI from .env
openai.api_key = os.getenv("OPENAI_API_KEY")

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

# 5) CORS (allow your front-end fetch)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # in prod, lock this to your domain
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# 6) Schemas
class ChatRequest(BaseModel):
    user_id: str
    message: str

class ChatResponse(BaseModel):
    reply: str

# 7) Chat endpoint → calls OpenAI
@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    try:
        completion = await openai.ChatCompletion.acreate(
            model="gpt-4o-mini",
            messages=[
                {"role": "system",
                 "content": (
                     "You are AIChatFlows—a friendly, expert virtual assistant for businesses. "
                     "You answer questions about the AIChatFlows service: AI chatbot setups, pricing tiers, "
                     "social media automation, customer service integrations, and feature details. "
                     "Be helpful, concise, and professional."
                 )},
                {"role": "user", "content": req.message},
            ],
            temperature=0.7,
        )
        reply = completion.choices[0].message.content.strip()
        return ChatResponse(reply=reply)

    except Exception as e:
        raise HTTPException(502, detail=f"OpenAI error: {e}")

@app.post("/api/demo-chat", response_model=ChatResponse)
async def demo_chat(req: ChatRequest):
    # Enhanced demo responses based on common questions
    message_lower = req.message.lower()
    
    if any(word in message_lower for word in ['price', 'cost', 'pricing', 'how much']):
        demo_reply = "Great question! AIChatFlows offers three tiers: Basic ($99/mo), Pro ($149/mo), and Enterprise ($249/mo). Each includes setup fees and different feature sets. Would you like details on a specific plan?"
    elif any(word in message_lower for word in ['feature', 'what', 'how', 'does']):
        demo_reply = "AIChatFlows provides 24/7 AI chatbots, social media automation, and customer service integration. Our bots work across Instagram, Facebook, SMS, and more. What specific feature interests you most?"
    elif any(word in message_lower for word in ['demo', 'test', 'try']):
        demo_reply = "You're already using our demo! This showcases how our AI responds to questions. In the full version, you'd get customized responses, integrations, and detailed analytics. Impressed so far?"
    elif any(word in message_lower for word in ['hello', 'hi', 'hey']):
        demo_reply = "Hello! I'm the AIChatFlows demo assistant. I can answer questions about our AI chatbot services, pricing, and features. What would you like to know?"
    else:
        demo_reply = f"Thanks for your message! This is a demo showcasing AIChatFlows' AI capabilities. Your question '{req.message}' would be answered by our full AI system with detailed, contextual responses. Want to learn more about our services?"
    
    return ChatResponse(reply=demo_reply)
