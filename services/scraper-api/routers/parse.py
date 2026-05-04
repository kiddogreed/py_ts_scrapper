# services/scraper-api/routers/parse.py
"""
POST /parse — Stateless HTML parsing endpoint.

Accepts raw HTML and a list of extraction rules, returns structured JSON.
Decoupled from scraping so the pipeline can call it independently:
  Polyglot Pipeline: TS navigator → raw HTML → POST /parse → structured data
  n8n workflow: fetch HTML node → HTTP Request to /parse → store node

WHY separate parse endpoint? Separating scraping from parsing means:
  1. You can re-parse old HTML without re-scraping (idempotent).
  2. The parser can be scaled independently from the browser pool.
  3. Multiple extraction strategies can be tested against the same HTML.
"""
import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from parsers.html_parser import HtmlParser

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/parse", tags=["parsing"])


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class ExtractionRule(BaseModel):
    name: str                               # Key name in output dict
    selector: str                           # CSS selector
    attribute: Optional[str] = None        # Extract attr instead of text (e.g. "href", "src")
    multiple: bool = False                 # Return list vs single value
    transform: Optional[str] = None       # "strip" | "lower" | "int" | "float"


class ParseRequest(BaseModel):
    html: str
    source_url: Optional[str] = None
    rules: list[ExtractionRule] = []        # If empty, falls back to generic extraction
    extract_links: bool = False
    extract_meta: bool = True


class ParseResponse(BaseModel):
    source_url: Optional[str]
    data: dict[str, Any]
    links: list[str] = []
    meta: dict[str, str] = {}


# ---------------------------------------------------------------------------
# Route handler
# ---------------------------------------------------------------------------

@router.post("/", response_model=ParseResponse)
async def parse_html(req: ParseRequest) -> ParseResponse:
    try:
        parser = HtmlParser(req.html, source_url=req.source_url)
        data = parser.extract_rules(req.rules) if req.rules else parser.generic_extract()
        links = parser.extract_links() if req.extract_links else []
        meta = parser.extract_meta() if req.extract_meta else {}

        return ParseResponse(
            source_url=req.source_url,
            data=data,
            links=links,
            meta=meta,
        )
    except Exception as exc:
        logger.exception("Parse failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
