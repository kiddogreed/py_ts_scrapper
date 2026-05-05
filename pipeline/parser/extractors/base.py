# pipeline/parser/extractors/base.py
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from typing import Any


class BaseExtractor(ABC):
    """Abstract base for all page-specific extractors."""

    def extract(
        self,
        html: str,
        source_url: str,
        intercepted: list[dict],
    ) -> dict[str, Any]:
        """Parse HTML and intercepted XHR data into a structured dict."""
        soup = BeautifulSoup(html, "lxml")
        result = self._extract(soup, source_url, intercepted)
        result["source_url"] = source_url
        return result

    @abstractmethod
    def _extract(
        self,
        soup: BeautifulSoup,
        source_url: str,
        intercepted: list[dict],
    ) -> dict[str, Any]:
        """Implement extraction logic per page type."""
        ...
