# FastAPI app for "Daily DevOps" dashboard
# Notes:
# - Hebrew UI text is fine. Only comments are in English.
# - /search endpoint returns DevOps-only results from local content lists.

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from typing import List, Dict
import json, datetime

# Local curated content (videos/tools/learning)
from content import VIDEOS, TOOLS, LEARNING

# Paths
BASE = Path(__file__).resolve().parent
DATA = BASE / "data"

# App
app = FastAPI(title="Daily DevOps")

# Static and templates setup
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE / "templates"))

# Utility: pick daily item by date modulo list length
def _pick_daily(items):
    today = int(datetime.date.today().strftime("%Y%m%d"))
    return items[today % len(items)] if items else None

# Utility: load JSON file
def _load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# Health endpoint (used by probes/LB)
@app.get("/healthz")
def healthz():
    return {"status": "ok"}

# Home page: quote, tip, videos, tools, learning
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    quotes = _load_json(DATA / "quotes.json")
    tips = _load_json(DATA / "tips.json")
    q = _pick_daily(quotes)["text"]
    t = _pick_daily(tips)

    # Adjust to your GitHub repo path
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

# ---------- DevOps-only Search ----------
# Flattens local curated sets and searches by simple substring match.
DEVSETS: List[Dict] = [
    *[{"type": "video", **v} for v in VIDEOS],
    *[{"type": "tool",  **t} for t in TOOLS],
    *[{"type": "learn", **l} for l in LEARNING],
]

def _search_devops(q: str, limit: int = 10):
    q = (q or "").strip().lower()
    if not q:
        return []
    res = []
    for item in DEVSETS:
        # Concatenate common fields to search through
        hay = " ".join(str(item.get(k, "")) for k in ("title", "name", "desc", "url", "category", "tags"))
        if q in hay.lower():
            res.append(item)
        if len(res) >= limit:
            break
    return res

@app.get("/search")
def search(q: str = "", limit: int = 10):
    return {"query": q, "results": _search_devops(q, limit)}
