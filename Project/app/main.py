# FastAPI app for "Daily DevOps" dashboard
# Hebrew UI is fine; comments in English.

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from typing import List, Dict
import json, datetime

# Optional web search (DuckDuckGo)
try:
    from duckduckgo_search import DDGS
except Exception:
    DDGS = None  # if missing, web search is simply disabled

# Local curated content
from content import VIDEOS, TOOLS, LEARNING

# Search allow-list (no ENV)
from search_config import is_allowed, QUERY_SUFFIX

# Paths
BASE = Path(__file__).resolve().parent
DATA = BASE / "data"

# App
app = FastAPI(title="Daily DevOps")

# Static & templates
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE / "templates"))

# Utils
def _pick_daily(items):
    today = int(datetime.date.today().strftime("%Y%m%d"))
    return items[today % len(items)] if items else None

def _load_json(path: Path):
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"{path.name} not found")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load {path.name}: {e}")

# Health
@app.get("/healthz")
def healthz():
    return {"status": "ok"}

# -------- Data APIs (from app/data/*.json) --------
@app.get("/api/quotes")
def api_quotes():
    data = _load_json(DATA / "quotes.json")
    return JSONResponse(content=data, headers={"Cache-Control": "no-store"})

@app.get("/api/tips")
def api_tips():
    data = _load_json(DATA / "tips.json")
    return JSONResponse(content=data, headers={"Cache-Control": "no-store"})
# --------------------------------------------------

# Home page
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    quotes = _load_json(DATA / "quotes.json")
    tips   = _load_json(DATA / "tips.json")
    q = _pick_daily(quotes)["text"]
    t = _pick_daily(tips)

    repo = "KatzChaim/Daily-DevOps"  # עדכן אם צריך

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

# ---------- DevOps-only local search ----------
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
        hay = " ".join(str(item.get(k, "")) for k in ("title", "name", "desc", "url", "category", "tags"))
        if q in hay.lower():
            res.append(item)
        if len(res) >= limit:
            break
    return res

# ---------- Web search (DuckDuckGo) + allow-list ----------
def _search_web(q: str, limit: int = 5, strict: bool = True):
    """
    strict=True -> return only results whose domain is in allow-list.
    """
    if not q or not DDGS:
        return []
    q2 = f"{q} {QUERY_SUFFIX}".strip()

    results: List[Dict] = []
    try:
        with DDGS() as ddgs:
            # fetch more than needed because we filter
            for item in ddgs.text(q2, max_results=limit * 4, region="wt-wt", safesearch="moderate"):
                url = item.get("href", "")
                if strict and not is_allowed(url):
                    continue
                results.append({
                    "type": "web",
                    "title": item.get("title", ""),
                    "url":   url,
                    "desc":  item.get("body", ""),
                })
                if len(results) >= limit:
                    break
    except Exception as e:
        print("web search error:", e)
    return results

# ---------- Unified search API (FIXED & PARENTHESIS CLOSED) ----------
@app.get("/search")
def search(q: str = "", limit: int = 10, scope: str = "local", strict: bool = True):
    """
    scope: local | web | all
    strict (web): True => only allow-listed domains (search_config.py)
    """
    q = (q or "").strip()
    results: List[Dict] = []

    if scope in ("local", "all"):
        results.extend(_search_devops(q, limit))

    if scope in ("web", "all"):
        results.extend(_search_web(q, limit=5, strict=bool(strict)))

    return {"query": q, "results": results}
