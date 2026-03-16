"""BIS (Bank for International Settlements) provider scraper.

Scrapes the IFC publications page which has a clean table structure:
  td[0] = "Month Year"  (e.g. "February 2026")
  td[1] = description with <a href="/ifc/publ/...">Title</a>

BIS is fully open — no auth required — making it the best provider for testing.
"""

import re

import requests
from bs4 import BeautifulSoup

from .base import BaseProvider, DiscoveredReport, HEADERS, REQUEST_TIMEOUT, month_to_quarter

IFC_URL = "https://www.bis.org/ifc/"


class BISProvider(BaseProvider):
    name = "Bank for International Settlements"
    trust_tier = 1

    def _fetch_listings(self, max_results: int) -> list[DiscoveredReport]:
        resp = requests.get(IFC_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        reports: list[DiscoveredReport] = []

        for tr in soup.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) < 2:
                continue

            # td[0] has the date, td[1] has the description + link
            date_text = tds[0].get_text(strip=True)
            link = tds[1].find("a", href=True)
            if not link:
                continue

            href = link["href"]
            # Only keep publication links (bulletins, reports, PDFs)
            if "/ifc/publ/" not in href:
                continue

            title = link.get_text(strip=True)
            if not title:
                continue

            # Build absolute URL
            if href.startswith("/"):
                url = f"https://www.bis.org{href}"
            else:
                url = href

            # Parse date: "February 2026" -> "2026-Q1"
            published = self._parse_date(date_text)

            reports.append(DiscoveredReport(
                title=title,
                url=url,
                provider=self.name,
                trust_tier=self.trust_tier,
                published=published,
            ))

            if len(reports) >= max_results:
                break

        return reports

    @staticmethod
    def _parse_date(date_text: str) -> str:
        """Parse 'Month Year' into 'YYYY-QN' format."""
        match = re.match(r"([A-Za-z]+)\s+(\d{4})", date_text.strip())
        if match:
            return month_to_quarter(match.group(1), match.group(2))
        # Try just a year
        year_match = re.match(r"(\d{4})", date_text.strip())
        if year_match:
            return year_match.group(1)
        return "Unknown"
