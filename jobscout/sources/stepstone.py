from __future__ import annotations

import logging
import re
import time
from urllib.parse import quote_plus, urlencode

import requests
from bs4 import BeautifulSoup, Tag

from jobscout.config import AppConfig
from jobscout.language import german_requirement
from jobscout.location import region_match, tidy_location
from jobscout.models import JobPosting
from jobscout.roles import match_role
from jobscout.sources.base import JobSource


logger = logging.getLogger(__name__)


class StepStoneAtSource(JobSource):
    """StepStone.at - a second large Austrian board.

    Overlaps karriere.at only partly: StepStone carries a lot of staffing
    agency and mid-size R&D listings that karriere.at does not. Searched with
    a wide radius around Vienna and the Kittsee border, then filtered by
    ``region_match``.
    """

    name = "stepstone.at"
    base_url = "https://www.stepstone.at"
    default_locations = ("Wien", "Hainburg an der Donau")
    radius_km = 30
    page_size = 25

    def fetch(self, config: AppConfig) -> list[JobPosting]:
        settings = config.sources.get("stepstone", {})
        locations = settings.get("locations") or list(self.default_locations)

        jobs: dict[str, JobPosting] = {}
        for role in config.queries_for("stepstone"):
            for location in locations:
                for page in range(1, config.max_pages_per_query + 1):
                    params = {"where": location, "radius": self.radius_km}
                    if page > 1:
                        params["page"] = str(page)
                    url = f"{self.base_url}/work/{quote_plus(role)}?{urlencode(params)}"
                    try:
                        response = self._get(url, attempts=2)
                    except requests.RequestException as exc:
                        logger.warning("stepstone.at: %r @ %r stopped: %s", role, location, exc)
                        break

                    cards = BeautifulSoup(response.text, "html.parser").select(
                        'article[data-testid="job-item"]'
                    )
                    if not cards:
                        break

                    for card in cards:
                        job = self._parse_card(card, config)
                        if job:
                            jobs.setdefault(job.stable_id, job)

                    if len(cards) < self.page_size:
                        break
                    time.sleep(config.request_delay_seconds)

                time.sleep(config.request_delay_seconds)

        return list(jobs.values())

    def _parse_card(self, card: Tag, config: AppConfig) -> JobPosting | None:
        link = card.select_one('a[data-testid="job-item-title"]')
        if not link:
            return None

        title = self._text(link)
        url = self._attr(link, "href").split("?")[0]
        if not title or not url:
            return None

        location = tidy_location(self._text(card.select_one('[data-at="job-item-location"]')))
        match = region_match(location, config.include_unspecified)
        if not match:
            return None

        # StepStone's keyword search matches the whole ad, and its teaser text
        # names the industry ("...im GMP-Umfeld..."), which drags in sales and
        # purchasing roles. Match the title only.
        matched_role = match_role(title, config.all_keywords)
        if not matched_role:
            return None

        company = self._text(card.select_one('[data-at="job-item-company-name"]'))
        posted = self._text(card.select_one('[data-at="job-item-timeago"]'))
        snippet = self._snippet(card, title, company, location, posted)

        german = german_requirement(f"{title} {snippet}")
        description = " - ".join(part for part in [german, snippet] if part)[:300]

        return JobPosting(
            source=self.name,
            source_id=self._source_id(card, url),
            title=title,
            company=company,
            url=url,
            location=location,
            region_match=match,
            posted_date=posted,
            company_description=description,
            summary=description,
            matched_query=matched_role,
        )

    def _snippet(self, card: Tag, *known_parts: str) -> str:
        text = card.get_text(" ", strip=True)
        for part in known_parts:
            if part:
                text = text.replace(part, " ", 1)
        return re.sub(r"\s+", " ", text).strip()[:300]

    def _source_id(self, card: Tag, url: str) -> str:
        card_id = str(card.get("id") or "")
        if card_id.startswith("job-item-"):
            return card_id.removeprefix("job-item-")
        found = re.search(r"--(\d+)-inline", url)
        return found.group(1) if found else url
