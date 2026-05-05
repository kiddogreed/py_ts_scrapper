# pipeline/parser/extractors/product.py
import re
import json
from typing import Any
from bs4 import BeautifulSoup
from .base import BaseExtractor


class ProductExtractor(BaseExtractor):
    """
    Extracts product data from e-commerce product pages.

    Extraction strategy (priority order):
    1. Intercepted XHR/API responses — highest fidelity, structured data
    2. JSON-LD structured data (<script type="application/ld+json">)
    3. Open Graph meta tags
    4. CSS selector heuristics for common page patterns
    """

    def _extract(
        self,
        soup: BeautifulSoup,
        source_url: str,
        intercepted: list[dict],
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "extractor": "ProductExtractor",
            "title": None,
            "price": None,
            "currency": None,
            "description": None,
            "images": [],
            "brand": None,
            "sku": None,
            "availability": None,
            "rating": None,
            "review_count": None,
            "raw_intercepted": [],
        }

        # --- Strategy 1: Intercepted XHR data ---
        if intercepted:
            result["raw_intercepted"] = intercepted
            for entry in intercepted:
                body = entry.get("body", {})
                if isinstance(body, dict):
                    self._apply_intercepted(result, body)

        # --- Strategy 2: JSON-LD structured data ---
        for script in soup.find_all("script", {"type": "application/ld+json"}):
            try:
                data = json.loads(script.string or "")
                schemas = data if isinstance(data, list) else [data]
                for schema in schemas:
                    if schema.get("@type") in ("Product", "ItemPage"):
                        self._apply_json_ld(result, schema)
                        break
            except (json.JSONDecodeError, AttributeError):
                continue

        # --- Strategy 3: Open Graph meta tags ---
        self._apply_open_graph(result, soup)

        # --- Strategy 4: CSS heuristic selectors ---
        self._apply_heuristics(result, soup)

        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _apply_intercepted(self, result: dict, body: dict) -> None:
        """Pull fields from a structured API response body."""
        for key in ("title", "name", "product_name", "productName"):
            if body.get(key) and not result["title"]:
                result["title"] = str(body[key])
                break

        for key in ("price", "sale_price", "current_price", "finalPrice"):
            if body.get(key) is not None and result["price"] is None:
                result["price"] = self._parse_price(str(body[key]))
                break

        if body.get("currency") and not result["currency"]:
            result["currency"] = str(body["currency"])

        for key in ("description", "short_description", "shortDescription"):
            if body.get(key) and not result["description"]:
                result["description"] = str(body[key])
                break

        if body.get("brand") and not result["brand"]:
            brand = body["brand"]
            result["brand"] = brand.get("name") if isinstance(brand, dict) else str(brand)

        for key in ("sku", "id", "product_id", "productId"):
            if body.get(key) and not result["sku"]:
                result["sku"] = str(body[key])
                break

    def _apply_json_ld(self, result: dict, schema: dict) -> None:
        """Extract from Product JSON-LD schema."""
        if not result["title"]:
            result["title"] = schema.get("name")

        if not result["description"]:
            result["description"] = schema.get("description")

        if not result["brand"]:
            brand = schema.get("brand", {})
            result["brand"] = brand.get("name") if isinstance(brand, dict) else brand

        if not result["sku"]:
            result["sku"] = schema.get("sku") or schema.get("productID")

        # Offers
        offers = schema.get("offers", {})
        if isinstance(offers, list) and offers:
            offers = offers[0]
        if isinstance(offers, dict):
            if result["price"] is None:
                result["price"] = self._parse_price(str(offers.get("price", "")))
            if not result["currency"]:
                result["currency"] = offers.get("priceCurrency")
            if not result["availability"]:
                avail = offers.get("availability", "")
                result["availability"] = avail.split("/")[-1] if avail else None

        # Aggregate rating
        rating = schema.get("aggregateRating", {})
        if isinstance(rating, dict):
            if result["rating"] is None:
                result["rating"] = rating.get("ratingValue")
            if result["review_count"] is None:
                result["review_count"] = rating.get("reviewCount")

        # Images
        img = schema.get("image")
        if img:
            imgs = img if isinstance(img, list) else [img]
            result["images"] = list(dict.fromkeys(result["images"] + imgs))

    def _apply_open_graph(self, result: dict, soup: BeautifulSoup) -> None:
        """Extract from Open Graph meta tags."""
        og: dict[str, str] = {}
        for tag in soup.find_all("meta", property=re.compile(r"^og:")):
            key = tag.get("property", "").replace("og:", "")
            og[key] = tag.get("content", "")

        if not result["title"] and og.get("title"):
            result["title"] = og["title"]
        if not result["description"] and og.get("description"):
            result["description"] = og["description"]
        if og.get("image") and og["image"] not in result["images"]:
            result["images"].append(og["image"])

    def _apply_heuristics(self, result: dict, soup: BeautifulSoup) -> None:
        """CSS selector heuristics for common e-commerce patterns."""
        # Title
        if not result["title"]:
            for sel in ("[data-testid='product-title']", "h1.product-title", "h1.pdp-title", "h1"):
                el = soup.select_one(sel)
                if el and el.get_text(strip=True):
                    result["title"] = el.get_text(strip=True)
                    break

        # Price
        if result["price"] is None:
            for sel in (
                "[data-testid='price']",
                ".product-price",
                ".pdp-price",
                ".price",
                "[itemprop='price']",
            ):
                el = soup.select_one(sel)
                if el:
                    text = el.get("content") or el.get_text(strip=True)
                    price = self._parse_price(text)
                    if price is not None:
                        result["price"] = price
                        break

        # Description
        if not result["description"]:
            for sel in (".product-description", "#product-description", "[itemprop='description']"):
                el = soup.select_one(sel)
                if el and el.get_text(strip=True):
                    result["description"] = el.get_text(" ", strip=True)[:2000]
                    break

        # Additional images from <img> tags
        if len(result["images"]) < 3:
            for img in soup.find_all("img", src=re.compile(r"\.(jpg|jpeg|png|webp)", re.I)):
                src = img.get("src", "")
                if src and src not in result["images"]:
                    result["images"].append(src)
                if len(result["images"]) >= 10:
                    break

    @staticmethod
    def _parse_price(raw: str) -> float | None:
        """Extract a numeric price from a raw price string."""
        if not raw:
            return None
        match = re.search(r"[\d,]+\.?\d*", raw.replace(",", ""))
        if match:
            try:
                return float(match.group().replace(",", ""))
            except ValueError:
                return None
        return None
