from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import json, datetime

from content import VIDEOS, TOOLS, LEARNING

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"

app = FastAPI(title="Daily DevOps")

# static & templates
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE / "templates"))

def _pick_daily(items):
    today = int(datetime.date.today().strftime("%Y%m%d"))
    return items[today % len(items)] if items else None

def _load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    quotes = _load_json(DATA / "quotes.json")
    tips = _load_json(DATA / "tips.json")
    q = _pick_daily(quotes)["text"]
    t = _pick_daily(tips)
    repo = "katzchaim/financial-management"
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "quote": q,
            "tip": t,
            "videos": VIDEOS,
            "tools": TOOLS,
            "learning": LEARNING,
            "repo": repo,
        },
    )

@app.get("/quote")
def quote():
    quotes = _load_json(DATA / "quotes.json")
    q = _pick_daily(quotes)
    return JSONResponse(q)

@app.get("/tips")
def tips():
    tips = _load_json(DATA / "tips.json")
    t = _pick_daily(tips)
    return JSONResponse(t)
