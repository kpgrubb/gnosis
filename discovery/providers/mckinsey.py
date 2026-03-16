"""McKinsey Financial Services Insights scraper.

Targets the public insights listing page. May return 403 due to bot
detection — this is expected and handled gracefully by BaseProvider.
"""

import re

import requests
from bs4 import BeautifulSoup

from .base import BaseProvider, DiscoveredReport, HEADERS, REQUEST_TIMEOUT

LISTING_URL = "https://www.mckinsey.com/industries/financial-services/our-insights"


class McKinseyProvider(BaseProvider):
    name = "McKinsey & Company"
    trust_tier = 2

    def _fetch_listings(self, max_results: int) -> list[DiscoveredReport]:
        resp = requests.get(LISTING_URL, headers={
            **HEADERS,
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        }, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        reports: list[DiscoveredReport] = []

        # McKinsey uses article cards with links to /industries/financial-services/our-insights/...
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/our-insights/" not in href or href == LISTING_URL:
                continue

            title = a.get_text(strip=True)
            if not title or len(title) < 10:
                continue

            # Build absolute URL
            if href.startswith("/"):
                url = f"https://www.mckinsey.com{href}"
            else:
                url = href

            # Avoid duplicates within this scrape
            if any(r.url == url for r in reports):
                continue

            reports.append(DiscoveredReport(
                title=title,
                url=url,
                provider=self.name,
                trust_tier=self.trust_tier,
            ))

            if len(reports) >= max_results:
                break

        return reports
