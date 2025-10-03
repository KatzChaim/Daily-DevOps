# FastAPI app for "Daily DevOps" dashboard (Hebrew UI; English comments).

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urlparse
import json, datetime, os

# Optional web search (DuckDuckGo)
try:
    from duckduckgo_search import DDGS
except Exception:
    DDGS = None  # If not installed, web search is disabled.

# Local curated content (fallback if content.py missing)
try:
    from content import VIDEOS, TOOLS, LEARNING
except Exception:
    VIDEOS = [
        {"title": "Kubernetes in 100 Seconds", "embed": "https://www.youtube.com/embed/PziYflu8cB0"},
        {"title": "What is CI/CD?",              "embed": "https://www.youtube.com/embed/scEDHsr3APg"},
        {"title": "Intro to Terraform",          "embed": "https://www.youtube.com/embed/h970ZBgKINg"},
    ]
    TOOLS = [
        {"name":"kubectl","desc":"Kubernetes CLI","url":"https://kubernetes.io/docs/reference/kubectl/"},
        {"name":"Helm","desc":"Kubernetes Package Manager","url":"https://helm.sh/"},
    ]
    LEARNING = [
        {"title":"Kubernetes Docs","desc":"Official docs","url":"https://kubernetes.io/docs/home/"},
        {"title":"Terraform Docs","desc":"Official docs","url":"https://developer.hashicorp.com/terraform"},
    ]

# Allow-list (fallback if search_config.py missing)
try:
    from search_config import is_allowed, QUERY_SUFFIX  # type: ignore
except Exception:
    _ALLOW = {
        "kubernetes.io","docs.docker.com","docs.github.com","prometheus.io","grafana.com",
        "developer.hashicorp.com","sre.google","itrevolution.com","aws.amazon.com",
        "learn.microsoft.com","cloud.google.com","helm.sh","terraform.io","hashicorp.com",
        "ubuntu.com","debian.org","python.org","fastapi.tiangolo.com","uvicorn.org",
        "youtube.com","www.youtube.com","youtu.be","medium.com","redhat.com",
    }
    def is_allowed(url: str) -> bool:
        try:
            host = urlparse(url).hostname or ""
            return any(host == d or host.endswith("." + d) for d in _ALLOW)
        except Exception:
            return False
    QUERY_SUFFIX = "DevOps best practice tutorial"

# Paths / app
BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)

app = FastAPI(title="Daily DevOps")
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE / "templates"))

# ---------- helpers ----------
def _pick_daily(items: List[dict]) -> dict:
    if not items:
        return {}
    today = int(datetime.date.today().strftime("%Y%m%d"))
    return items[today % len(items)]

def _load_json(path: Path):
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"{path.name} not found")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load {path.name}: {e}")

def _write_json(path: Path, obj) -> None:
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    tmp.replace(path)

# ---------- health ----------
@app.get("/healthz")
def healthz():
    return {"status": "ok"}

# ---------- data APIs ----------
@app.get("/api/quotes")
def api_quotes():
    data = _load_json(DATA / "quotes.json")
    return JSONResponse(content=data, headers={"Cache-Control": "no-store"})

@app.get("/api/tips")
def api_tips():
    data = _load_json(DATA / "tips.json")
    return JSONResponse(content=data, headers={"Cache-Control": "no-store"})

# ---------- ideas (simple JSON persistence) ----------
IDEAS_FILE = DATA / "ideas.json"

class IdeaIn(BaseModel):
    text: str = Field(min_length=1, description="The idea text")
    name: Optional[str] = Field(default=None, description="Optional author")

def _load_ideas() -> list[dict]:
    if not IDEAS_FILE.exists():
        return []
    try:
        with open(IDEAS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def _save_ideas(items: list[dict]) -> None:
    _write_json(IDEAS_FILE, items)

@app.get("/api/ideas")
def get_ideas(limit: int = 50):
    items = list(reversed(_load_ideas()))[: max(1, limit)]
    return {"items": items}

@app.post("/api/ideas")
def add_idea(idea: IdeaIn):
    items = _load_ideas()
    items.append({
        "text": idea.text.strip(),
        "name": (idea.name or "").strip() or None,
        "ts": datetime.datetime.utcnow().isoformat() + "Z",
    })
    _save_ideas(items)
    return {"ok": True}

# ---------- home page ----------
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    quotes = _load_json(DATA / "quotes.json")
    tips   = _load_json(DATA / "tips.json")
    q = _pick_daily(quotes)  # dict: {text, category?, tags?}
    t = _pick_daily(tips)

    repo = os.getenv("GITHUB_REPOSITORY", "KatzChaim/Daily-DevOps")

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

# ---------- local search ----------
DEVSETS: List[Dict] = [
    *[{"type": "video", **v} for v in VIDEOS],
    *[{"type": "tool",  **t} for t in TOOLS],
    *[{"type": "learn", **l} for l in LEARNING],
]

def _search_local(q: str, limit: int = 10) -> List[Dict]:
    q = (q or "").strip().lower()
    if not q:
        return []
    res: List[Dict] = []
    for item in DEVSETS:
        hay = " ".join(str(item.get(k, "")) for k in ("title", "name", "desc", "url", "category", "tags"))
        if q in hay.lower():
            res.append(item)
        if len(res) >= limit:
            break
    return res

# ---------- web search (DuckDuckGo + allow-list) ----------
def _search_web(q: str, limit: int = 5, strict: bool = True) -> List[Dict]:
    if not q or not DDGS:
        return []
    q2 = f"{q} {QUERY_SUFFIX}".strip()
    out: List[Dict] = []
    try:
        with DDGS() as ddgs:
            for item in ddgs.text(q2, max_results=limit * 4, region="wt-wt", safesearch="moderate"):
                url = item.get("href", "")
                if strict and not is_allowed(url):
                    continue
                out.append({
                    "type": "web",
                    "title": item.get("title", "") or url,
                    "url": url,
                    "desc": item.get("body", ""),
                })
                if len(out) >= limit:
                    break
    except Exception as e:
        print("web search error:", e)
    return out

# ---------- unified search API ----------
@app.get("/search")
def search(q: str = "", limit: int = 10, scope: str = "local", strict: bool = True):
    """
    scope: local | web | all
    strict (web): only allow-listed domains (see search_config.py or defaults)
    """
    q = (q or "").strip()
    results: List[Dict] = []
    if scope in ("local", "all"):
        results.extend(_search_local(q, limit))
    if scope in ("web", "all"):
        results.extend(_search_web(q, limit=5, strict=bool(strict)))
    return {"query": q, "results": results}
