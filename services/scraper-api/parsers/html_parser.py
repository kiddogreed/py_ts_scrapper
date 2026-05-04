# services/scraper-api/parsers/html_parser.py
"""
HTML parsing utilities backed by BeautifulSoup + lxml.

WHY Python for parsing?
  - lxml is a C-extension wrapping libxml2 — fastest HTML parser available.
  - BeautifulSoup provides a clean, Pythonic API over lxml's tree.
  - CSS selectors via bs4 + XPath via lxml cover every extraction pattern.
  - The Python data ecosystem (json, re, datetime) makes post-processing trivial.
  TypeScript has Cheerio, but it's slower and lacks the Python ecosystem depth.
"""
import json
import re
import logging
from typing import Any, Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)

# Transforms applied to extracted text
_TRANSFORMS = {
    "strip": lambda v: v.strip() if isinstance(v, str) else v,
    "lower": lambda v: v.strip().lower() if isinstance(v, str) else v,
    "int": lambda v: int(re.sub(r"[^\d]", "", v)) if isinstance(v, str) else v,
    "float": lambda v: float(re.sub(r"[^\d.]", "", v)) if isinstance(v, str) else v,
}


class HtmlParser:
    """
    Stateless HTML parser. Instantiate with raw HTML per request.
    """

    def __init__(self, html: str, source_url: Optional[str] = None) -> None:
        self.soup = BeautifulSoup(html, "lxml")
        self.source_url = source_url

    # ------------------------------------------------------------------
    # Rule-based extraction (driven by ParseRequest.rules)
    # ------------------------------------------------------------------

    def extract_rules(self, rules: list) -> dict[str, Any]:
        """
        Apply a list of ExtractionRule objects to the parsed DOM.
        Each rule maps a CSS selector → a key in the output dict.
        """
        result: dict[str, Any] = {}
        for rule in rules:
            try:
                if rule.multiple:
                    elements = self.soup.select(rule.selector)
                    values = [self._get_value(el, rule.attribute) for el in elements]
                    result[rule.name] = [self._apply_transform(v, rule.transform) for v in values]
                else:
                    el = self.soup.select_one(rule.selector)
                    raw = self._get_value(el, rule.attribute) if el else None
                    result[rule.name] = self._apply_transform(raw, rule.transform)
            except Exception as exc:
                logger.warning("Rule '%s' failed: %s", rule.name, exc)
                result[rule.name] = None
        return result

    # ------------------------------------------------------------------
    # Generic extraction — best-effort schema detection
    # ------------------------------------------------------------------

    def generic_extract(self) -> dict[str, Any]:
        """
        Best-effort extraction when no rules are provided.
        Tries: JSON-LD schema.org, Open Graph meta tags, page title, main text.
        """
        data: dict[str, Any] = {}

        # 1. JSON-LD structured data (richest source — e.g. Product, Article)
        json_ld = self._extract_json_ld()
        if json_ld:
            data["json_ld"] = json_ld

        # 2. Open Graph / Twitter card meta
        og = self._extract_open_graph()
        if og:
            data["open_graph"] = og

        # 3. Fallback: page title + first paragraph
        data["title"] = self._text(self.soup.find("title"))
        data["h1"] = self._text(self.soup.find("h1"))

        main_el = (
            self.soup.find("main")
            or self.soup.find("article")
            or self.soup.find("div", {"id": re.compile(r"content|main", re.I)})
        )
        if main_el:
            paragraphs = [self._text(p) for p in main_el.find_all("p", limit=5)]
            data["paragraphs"] = [p for p in paragraphs if p]

        return data

    # ------------------------------------------------------------------
    # Helpers for routing layer
    # ------------------------------------------------------------------

    def extract_links(self) -> list[str]:
        """Return all absolute links on the page."""
        links = []
        base = self.source_url or ""
        for tag in self.soup.find_all("a", href=True):
            href = tag["href"].strip()
            if href.startswith(("http://", "https://")):
                links.append(href)
            elif href.startswith("/") and base:
                links.append(urljoin(base, href))
        return list(dict.fromkeys(links))  # deduplicate, preserve order

    def extract_meta(self) -> dict[str, str]:
        """Return name/content and property/content meta tag pairs."""
        meta: dict[str, str] = {}
        for tag in self.soup.find_all("meta"):
            key = tag.get("name") or tag.get("property")
            value = tag.get("content")
            if key and value:
                meta[key] = value
        return meta

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_value(self, el: Optional[Tag], attribute: Optional[str]) -> Optional[str]:
        if el is None:
            return None
        if attribute:
            return el.get(attribute)
        return el.get_text(separator=" ", strip=True)

    def _apply_transform(self, value: Any, transform: Optional[str]) -> Any:
        if value is None or transform is None:
            return value
        fn = _TRANSFORMS.get(transform)
        if fn is None:
            return value
        try:
            return fn(value)
        except (ValueError, TypeError):
            return value

    def _text(self, el) -> Optional[str]:
        return el.get_text(strip=True) if el else None

    def _extract_json_ld(self) -> Optional[list[dict]]:
        results = []
        for tag in self.soup.find_all("script", {"type": "application/ld+json"}):
            try:
                obj = json.loads(tag.string or "")
                results.append(obj)
            except (json.JSONDecodeError, TypeError):
                pass
        return results or None

    def _extract_open_graph(self) -> dict[str, str]:
        og: dict[str, str] = {}
        for tag in self.soup.find_all("meta"):
            prop = tag.get("property", "")
            if prop.startswith("og:") or prop.startswith("twitter:"):
                content = tag.get("content", "").strip()
                if content:
                    og[prop] = content
        return og
