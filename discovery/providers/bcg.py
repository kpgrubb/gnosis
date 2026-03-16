"""BCG Publications scraper.

Targets the BCG publications page. May return 403 due to bot detection —
this is expected and handled gracefully by BaseProvider.
"""

import requests
from bs4 import BeautifulSoup

from .base import BaseProvider, DiscoveredReport, HEADERS, REQUEST_TIMEOUT

LISTING_URL = "https://www.bcg.com/publications"


class BCGProvider(BaseProvider):
    name = "Boston Consulting Group"
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
        seen_urls = set()

        # BCG uses article cards with links to /publications/...
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/publications/" not in href or href == "/publications":
                continue

            title = a.get_text(strip=True)
            if not title or len(title) < 10:
                continue

            if href.startswith("/"):
                url = f"https://www.bcg.com{href}"
            else:
                url = href

            if url in seen_urls:
                continue
            seen_urls.add(url)

            reports.append(DiscoveredReport(
                title=title,
                url=url,
                provider=self.name,
                trust_tier=self.trust_tier,
            ))

            if len(reports) >= max_results:
                break

        return reports
