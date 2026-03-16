"""PwC Financial Services scraper.

Targets PwC's financial services insights page.
May be JS-rendered — handled gracefully by BaseProvider.
"""

import re

import requests
from bs4 import BeautifulSoup

from .base import BaseProvider, DiscoveredReport, HEADERS, REQUEST_TIMEOUT

LISTING_URL = "https://www.pwc.com/us/en/industries/financial-services.html"


class PwCProvider(BaseProvider):
    name = "PwC"
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

        # Look for article/insight links under /us/en/industries/financial-services/
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/financial-services/" not in href:
                continue
            # Skip nav links, the current page, and anchors
            if href == LISTING_URL or href.endswith("financial-services.html"):
                continue

            title = a.get_text(strip=True)
            if not title or len(title) < 10:
                continue

            if href.startswith("/"):
                url = f"https://www.pwc.com{href}"
            else:
                url = href

            url_clean = url.split("?")[0]
            if url_clean in seen_urls:
                continue
            seen_urls.add(url_clean)

            year_match = re.search(r"(20\d{2})", title)
            published = f"{year_match.group(1)}" if year_match else "Unknown"

            reports.append(DiscoveredReport(
                title=title,
                url=url_clean,
                provider=self.name,
                trust_tier=self.trust_tier,
                published=published,
            ))

            if len(reports) >= max_results:
                break

        return reports
