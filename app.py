import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import openai
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def ask_menu_bot(question: str) -> str:
    resp = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role":"system","content":"You are AI Coffee, a friendly chatbot for coffee menus."},
            {"role":"user","content":question}
        ],
        temperature=0.7,
    )
    return resp.choices[0].message.content.strip()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "answer": None})

@app.post("/ask", response_class=HTMLResponse)
async def ask(request: Request, question: str = Form(...)):
    answer = ask_menu_bot(question)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "answer": answer, "question": question}
    )
