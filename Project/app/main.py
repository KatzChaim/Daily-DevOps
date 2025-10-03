"""
Daily DevOps – FastAPI
----------------------

קובץ השרת הראשי. מספק:
- דף הבית (Jinja2)
- בדיקות בריאות (/healthz)
- API נתונים סטטיים: /api/quotes, /api/tips
- API לרעיונות:      GET/POST /api/ideas
- מנוע חיפוש:        /search  (לוקאלי + אופציונלי DuckDuckGo)

הקוד כתוב “שקוף” להבנה:
- קבועים מרוכזים למעלה
- פונקציות שירות קטנות וברורות
- טיפוסים ודגמי Pydantic ל־request/response
- הרבה הערות בעברית
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any

import datetime
import json
import time

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

# חיפוש אינטרנט (לא חובה). אם הספרייה לא מותקנת – פשוט לא מחפשים בחוץ.
try:
    from duckduckgo_search import DDGS
except Exception:
    DDGS = None  # web search disabled if missing

# תוכן מקומי (וידאו/כלים/לימוד) – נשמר בנפרד כדי שיהיה ברור ולא “מלכלך” את הקובץ הזה
from content import VIDEOS, TOOLS, LEARNING

# קובץ קונפיג לחיפוש וובי: דומיינים מאושרים + סיומת למחרוזת החיפוש
from search_config import is_allowed, QUERY_SUFFIX


# ──────────────────────────────────────────────────────────────────────────────
# קבועים ונתיבים
# ──────────────────────────────────────────────────────────────────────────────
BASE_DIR: Path = Path(__file__).resolve().parent      # app/
DATA_DIR: Path = BASE_DIR / "data"                    # app/data/
IDEAS_FILE: Path = DATA_DIR / "ideas.json"            # מאגר רעיונות (JSON)
TEMPLATES = Jinja2Templates(directory=str(BASE_DIR / "templates"))

REPO_SLUG = "KatzChaim/Daily-DevOps"                  # ללינק בפוטר


# ──────────────────────────────────────────────────────────────────────────────
# מודלים ל־API (Pydantic)
# ──────────────────────────────────────────────────────────────────────────────
class IdeaIn(BaseModel):
    """בקשת POST ליצירת רעיון חדש."""
    name: str = Field("", max_length=80, description="שם פרטי (אופציונלי)")
    text: str = Field(..., min_length=3, max_length=2000, description="תיאור הרעיון")


class IdeaOut(IdeaIn):
    """ייצוג רעיון שמור (עם מזהה וזמן)."""
    id: str
    ts: float


# ──────────────────────────────────────────────────────────────────────────────
# שירותים/כלי עזר – פונקציות קטנות וברורות
# ──────────────────────────────────────────────────────────────────────────────
def pick_daily(items: List[Any]) -> Any:
    """בחירת פריט 'יומי' לפי תאריך. אם הרשימה ריקה מחזיר None."""
    if not items:
        return None
    today_num = int(datetime.date.today().strftime("%Y%m%d"))
    return items[today_num % len(items)]


def read_json(path: Path) -> Any:
    """טעינת JSON לקובץ נתון, עם הודעת שגיאה ברורה אם חסר/פגום."""
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"{path.name} missing")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"failed to read {path.name}: {e}")


def ensure_ideas_file() -> None:
    """וידוא שקובץ הרעיונות קיים (אם לא – יצירת [] ריק)."""
    IDEAS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not IDEAS_FILE.exists():
        IDEAS_FILE.write_text("[]", encoding="utf-8")


def list_ideas() -> List[Dict[str, Any]]:
    """קריאת כל הרעיונות מקובץ JSON."""
    ensure_ideas_file()
    try:
        items: List[Dict[str, Any]] = json.loads(IDEAS_FILE.read_text(encoding="utf-8"))
    except Exception:
        items = []
    # מיון חדש->ישן להצגה נוחה
    items.sort(key=lambda x: x.get("ts", 0), reverse=True)
    return items


def append_idea(new_item: Dict[str, Any]) -> None:
    """הוספת רעיון חדש לקובץ (כתיבה אטומית)."""
    ensure_ideas_file()
    items = list_ideas()
    items.append(new_item)

    tmp = IDEAS_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(IDEAS_FILE)


def search_local(q: str, limit: int = 10) -> List[Dict[str, Any]]:
    """חיפוש 'לוקאלי' על התוכן הערוך שלנו (וידאו/כלים/לימוד)."""
    q = (q or "").strip().lower()
    if not q:
        return []

    # מאחדים את כל המאגרים לרשימה אחת עם טיפוס ('video'/'tool'/'learn')
    data: List[Dict[str, Any]] = [
        *[{"type": "video", **v} for v in VIDEOS],
        *[{"type": "tool", **t} for t in TOOLS],
        *[{"type": "learn", **l} for l in LEARNING],
    ]

    results: List[Dict[str, Any]] = []
    for item in data:
        hay = " ".join(str(item.get(k, "")) for k in ("title", "name", "desc", "url", "category", "tags"))
        if q in hay.lower():
            results.append(item)
        if len(results) >= limit:
            break
    return results


def search_web(q: str, limit: int = 5, strict: bool = True) -> List[Dict[str, Any]]:
    """חיפוש DuckDuckGo – מחזיר רק דומיינים מאושרים (strict=True)."""
    if not q or not DDGS:
        return []

    q2 = f"{q} {QUERY_SUFFIX}".strip()
    out: List[Dict[str, Any]] = []

    try:
        with DDGS() as ddgs:
            # נבקש יותר תוצאות ממה שנחזיר – כי נסנן
            for item in ddgs.text(q2, max_results=limit * 4, region="wt-wt", safesearch="moderate"):
                url = item.get("href", "")
                if strict and not is_allowed(url):
                    continue
                out.append({
                    "type": "web",
                    "title": item.get("title", ""),
                    "url": url,
                    "desc": item.get("body", ""),
                })
                if len(out) >= limit:
                    break
    except Exception as e:
        # לא מפילים את האפליקציה – רק מדווחים ללוג
        print("web search error:", e)

    return out


# --- הוסף ב-main.py (קרוב לפונקציות העזר) ---
def _normalize_quote(item):
    # תומך גם בפורמט הישן (מחרוזת) וגם בחדש (אובייקט עם category/tags)
    if isinstance(item, str):
        return {"text": item, "category": None, "tags": []}
    if isinstance(item, dict):
        return {
            "text": item.get("text", ""),
            "category": item.get("category"),
            "tags": item.get("tags", []) or []
        }
    return {"text": str(item), "category": None, "tags": []}


# ──────────────────────────────────────────────────────────────────────────────
# FastAPI – הגדרת האפליקציה והנתיבים
# ──────────────────────────────────────────────────────────────────────────────
app = FastAPI(title="Daily DevOps")

# קבצים סטטיים (CSS/JS/אייקונים)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.get("/healthz")
def healthz() -> Dict[str, str]:
    """בדיקת בריאות פשוטה (ל־probe בקוברנטיס/ALB)."""
    return {"status": "ok"}


# ===== נתונים סטטיים (JSON) – quotes/tips =====
@app.get("/api/quotes")
def api_quotes() -> JSONResponse:
    data = read_json(DATA_DIR / "quotes.json")
    return JSONResponse(content=data, headers={"Cache-Control": "no-store"})


@app.get("/api/tips")
def api_tips() -> JSONResponse:
    data = read_json(DATA_DIR / "tips.json")
    return JSONResponse(content=data, headers={"Cache-Control": "no-store"})


# ===== רעיונות (Ideas) =====
@app.get("/api/ideas", response_model=Dict[str, List[IdeaOut]])
def api_list_ideas():
    """מחזיר את כל הרעיונות (חדש קודם)."""
    return {"items": list_ideas()}


@app.post("/api/ideas", response_model=IdeaOut)
def api_create_idea(payload: IdeaIn):
    """יוצר רעיון חדש ושומר לקובץ JSON."""
    new_item: Dict[str, Any] = {
        "id": f"i{int(time.time() * 1000)}",
        "ts": time.time(),
        "name": (payload.name or "").strip(),
        "text": payload.text.strip(),
    }
    append_idea(new_item)
    return new_item  # Pydantic ימיר ל־IdeaOut


# ===== דף הבית (Jinja2) =====
@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    """טוען את דף הבית עם פריט 'יומי' מכל מאגר (ציטוט/טיפ)."""
    quotes = read_json(DATA_DIR / "quotes.json")
    tips = read_json(DATA_DIR / "tips.json")

    quote = pick_daily(quotes)["text"]
    tip = pick_daily(tips)

    return TEMPLATES.TemplateResponse(
        "index.html",
        {
            "request": request,
            "quote": quote,
            "tip": tip,
            "videos": VIDEOS,
            "tools": TOOLS,
            "learning": LEARNING,
            "repo": REPO_SLUG,
        },
    )


# ===== חיפוש מאוחד (לוקאלי + אופציונלי וובי) =====
@app.get("/search")
def search(q: str = "", limit: int = 10, scope: str = "local", strict: bool = True):
    """
    Unified search API:
    - scope=local | web | all
    - strict (web only): True => מסנן לפי דומיינים מאושרים (ראה search_config.py)
    """
    q = (q or "").strip()
    results: List[Dict[str, Any]] = []

    if scope in ("local", "all"):
        results.extend(search_local(q, limit))

    if scope in ("web", "all"):
        results.extend(search_web(q, limit=5, strict=bool(strict)))

    return {"query": q, "results": results}
