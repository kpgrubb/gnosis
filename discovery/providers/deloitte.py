"""Deloitte Financial Services Insights scraper.

Targets the banking/FS outlook page which has structured article links.
"""

import re

import requests
from bs4 import BeautifulSoup

from .base import BaseProvider, DiscoveredReport, HEADERS, REQUEST_TIMEOUT

LISTING_URL = "https://www2.deloitte.com/us/en/pages/financial-services/articles/banking-industry-outlook.html"


class DeloitteProvider(BaseProvider):
    name = "Deloitte Insights"
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

        # Skip generic nav/section labels
        skip_titles = {"financial services", "about", "contact", "subscribe"}

        # Look for article links under /insights/industry/financial-services/
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/insights/industry/financial-services/" not in href and "/Industries/financial-services/" not in href:
                continue

            title = a.get_text(strip=True)
            if not title or len(title) < 15:
                continue
            if title.lower().rstrip(".") in skip_titles:
                continue

            # Build absolute URL
            if href.startswith("/"):
                url = f"https://www2.deloitte.com{href}"
            else:
                url = href

            # Strip query params for dedup
            url_clean = url.split("?")[0]
            if url_clean in seen_urls:
                continue
            seen_urls.add(url_clean)

            # Try to extract year from title (e.g. "2026 banking outlook")
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
