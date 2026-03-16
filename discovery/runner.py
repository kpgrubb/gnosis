"""Discovery pipeline orchestrator for GNOSIS.

Runs all provider scrapers, deduplicates against seen.json,
tags new reports via GPT-4o-mini, and persists results.
"""

import json
import logging
import time
from dataclasses import asdict
from datetime import datetime

from openai import OpenAI

import config
from discovery.providers import ALL_PROVIDERS

logger = logging.getLogger(__name__)


def load_seen() -> dict:
    """Load seen.json or return default structure."""
    try:
        if config.SEEN_PATH.exists():
            with open(config.SEEN_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Ensure expected keys exist
            data.setdefault("seen_urls", [])
            data.setdefault("pending", [])
            data.setdefault("last_run", None)
            return data
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("seen.json corrupted or unreadable, resetting: %s", e)
    return {"seen_urls": [], "pending": [], "last_run": None}


def save_seen(data: dict) -> None:
    """Write seen.json to disk."""
    config.SEEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(config.SEEN_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def is_stale() -> bool:
    """True if discovery hasn't run in DISCOVERY_STALE_DAYS or has never run."""
    seen = load_seen()
    if seen["last_run"] is None:
        return True
    try:
        last = datetime.fromisoformat(seen["last_run"])
        return (datetime.now() - last).days >= config.DISCOVERY_STALE_DAYS
    except (ValueError, TypeError):
        return True


def dismiss_report(url: str) -> None:
    """Remove a report from the pending list (user dismissed it)."""
    seen = load_seen()
    seen["pending"] = [r for r in seen["pending"] if r.get("url") != url]
    save_seen(seen)


def _tag_reports(reports: list) -> list:
    """Use GPT-4o-mini to generate topic_tags and abstract for each report."""
    client = OpenAI(api_key=config.OPENAI_API_KEY)

    for report in reports:
        try:
            resp = client.chat.completions.create(
                model=config.LLM_MODEL_MINI,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a research librarian. Given a report title and publisher, "
                            "generate topic tags and a brief abstract. Return JSON with exactly "
                            "two keys: \"topic_tags\" (list of 3-5 short strings) and "
                            "\"abstract\" (one paragraph, 2-3 sentences)."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Title: \"{report.title}\" | Publisher: \"{report.provider}\"",
                    },
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=200,
            )
            result = json.loads(resp.choices[0].message.content)
            report.topic_tags = result.get("topic_tags", [])
            report.abstract = result.get("abstract", "")
        except Exception as e:
            logger.warning("Tagging failed for '%s': %s", report.title, e)
            report.topic_tags = []
            report.abstract = ""

    return reports


def run_discovery() -> list[dict]:
    """Run full discovery pipeline. Returns list of pending report dicts."""
    seen = load_seen()
    seen_set = set(seen["seen_urls"])

    new_reports = []

    for provider in ALL_PROVIDERS:
        reports = provider.scrape()
        for report in reports:
            if report.url not in seen_set:
                new_reports.append(report)
                seen_set.add(report.url)

        # Rate-limit between providers
        if len(ALL_PROVIDERS) > 1:
            time.sleep(1)

    # Cap new reports
    new_reports = new_reports[:config.DISCOVERY_MAX_NEW]

    # Tag via GPT-4o-mini
    if new_reports:
        logger.info("Tagging %d new reports via GPT-4o-mini", len(new_reports))
        new_reports = _tag_reports(new_reports)

        # Add to pending and seen_urls
        for report in new_reports:
            seen["pending"].append(asdict(report))
        seen["seen_urls"] = list(seen_set)

    seen["last_run"] = datetime.now().isoformat()
    save_seen(seen)

    provider_count = len(ALL_PROVIDERS)
    logger.info(
        "Discovery complete: %d providers checked, %d new reports found, %d total pending",
        provider_count, len(new_reports), len(seen["pending"]),
    )

    return seen["pending"]
