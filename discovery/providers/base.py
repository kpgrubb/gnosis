"""Base class and data model for provider scrapers."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "GNOSIS-Research-Bot/1.0",
    "Accept": "text/html,application/xhtml+xml",
}

REQUEST_TIMEOUT = 10


@dataclass
class DiscoveredReport:
    """A report discovered on a provider's public listing page."""

    title: str
    url: str
    provider: str
    trust_tier: int
    published: str = "Unknown"
    topic_tags: list[str] = field(default_factory=list)
    abstract: str = ""
    discovered_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class BaseProvider(ABC):
    """Abstract base for provider scrapers.

    Subclasses implement _fetch_listings(). The public scrape() method
    wraps it in error handling so one broken provider never crashes the run.
    """

    name: str = "Unknown"
    trust_tier: int = 3

    def scrape(self, max_results: int = 30) -> list[DiscoveredReport]:
        """Scrape listing page. Returns [] on any failure."""
        try:
            results = self._fetch_listings(max_results)
            if not results:
                logger.warning("[%s] Page loaded but no reports parsed — HTML structure may have changed", self.name)
            else:
                logger.info("[%s] Found %d reports", self.name, len(results))
            return results
        except Exception as e:
            logger.warning("[%s] Scrape failed: %s", self.name, e)
            return []

    @abstractmethod
    def _fetch_listings(self, max_results: int) -> list[DiscoveredReport]:
        """Fetch and parse report listings. May raise on failure."""
        ...


def month_to_quarter(month_str: str, year_str: str) -> str:
    """Convert 'March', '2026' to '2026-Q1'."""
    month_map = {
        "january": 1, "february": 1, "march": 1,
        "april": 2, "may": 2, "june": 2,
        "july": 3, "august": 3, "september": 3,
        "october": 4, "november": 4, "december": 4,
    }
    q = month_map.get(month_str.strip().lower(), 1)
    return f"{year_str.strip()}-Q{q}"
