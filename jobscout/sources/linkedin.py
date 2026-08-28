from __future__ import annotations

import logging
import re
import time
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup, Tag

from jobscout.config import AppConfig
from jobscout.location import region_match, tidy_location
from jobscout.models import JobPosting
from jobscout.roles import match_role, role_terms
from jobscout.sources.base import JobSource


logger = logging.getLogger(__name__)


class LinkedInSource(JobSource):
    """Public guest job search - no login, but strict rate limits.

    A failed query (usually HTTP 429) is logged and skipped so one angry
    response does not throw away the queries that already succeeded. Each of
    Lenka's target areas is searched separately because LinkedIn's geo
    filter is per-request.
    """

    name = "linkedin"
    search_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    default_locations = ("Bratislava, Slovakia", "Vienna, Austria", "Kittsee, Austria")
    page_size = 25
    # When the IP is being throttled every query 429s. Give up on the whole
    # source after this many failures in a row instead of grinding through
    # dozens of slow retry/back-off cycles.
    max_consecutive_failures = 4

    def fetch(self, config: AppConfig) -> list[JobPosting]:
        settings = config.sources.get("linkedin", {})
        locations = settings.get("locations") or list(self.default_locations)

        jobs: dict[str, JobPosting] = {}
        failures = 0
        # Query distinctive terms instead of raw roles so near-duplicate
        # roles ("Biochemist", "Biochemik") cost one request, not two.
        for term, _role in role_terms(config.queries_for("linkedin")):
            if failures >= self.max_consecutive_failures:
                logger.warning("linkedin: too many rate-limited queries, skipping the rest")
                break
            for location in locations:
                if failures >= self.max_consecutive_failures:
                    break
                start = 0
                for _ in range(config.max_pages_per_query):
                    params = {"keywords": term, "location": location, "start": str(start)}
                    url = f"{self.search_url}?{urlencode(params)}"
                    try:
                        response = self._get(url, attempts=2)
                    except requests.RequestException as exc:
                        logger.warning("linkedin: query %r @ %r failed, skipping: %s", term, location, exc)
                        failures += 1
                        break

                    failures = 0
                    cards = BeautifulSoup(response.text, "html.parser").select(
                        ".base-card, .job-search-card"
                    )
                    if not cards:
                        break

                    for card in cards:
                        job = self._parse_card(card, config)
                        if job:
                            jobs.setdefault(job.stable_id, job)

                    if len(cards) < self.page_size:
                        break
                    start += self.page_size
                    time.sleep(config.request_delay_seconds)

                time.sleep(config.request_delay_seconds)

        return list(jobs.values())

    def _parse_card(self, card: Tag, config: AppConfig) -> JobPosting | None:
        link = card.select_one("a.base-card__full-link, a[href*='/jobs/view/']")
        title = self._text(card.select_one(".base-search-card__title"))
        company = self._text(card.select_one(".base-search-card__subtitle"))
        location = tidy_location(self._text(card.select_one(".job-search-card__location")))
        if not link or not title:
            return None

        # Keyword search is fuzzy; keep only titles matching a configured role.
        matched_role = match_role(title, config.all_keywords)
        if not matched_role:
            return None

        match = region_match(location, config.include_unspecified)
        if not match:
            return None

        url = self._attr(link, "href").split("?")[0]
        source_id = self._source_id(card, url)
        posted = self._attr(card.select_one("time[datetime]"), "datetime")
        summary = self._text(card.select_one(".job-search-card__salary-info"))

        return JobPosting(
            source=self.name,
            source_id=source_id,
            title=title,
            company=company,
            url=url,
            location=location,
            region_match=match,
            posted_date=posted,
            company_description=summary,
            summary=summary,
            matched_query=matched_role,
        )

    def _source_id(self, card: Tag, url: str) -> str:
        urn = self._attr(card, "data-entity-urn")
        found = re.search(r"jobPosting:(\d+)", urn) or re.search(r"-(\d+)/?$", url)
        return found.group(1) if found else url
