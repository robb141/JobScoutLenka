from __future__ import annotations

import logging
import re
import time
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup, Tag

from jobscout.config import AppConfig
from jobscout.language import german_requirement
from jobscout.location import region_match, tidy_location
from jobscout.models import JobPosting
from jobscout.roles import match_role
from jobscout.sources.base import JobSource


logger = logging.getLogger(__name__)


class KarriereAtSource(JobSource):
    """karriere.at - the largest Austrian job board.

    Queried once per (role, location). The location list is broad on purpose
    (Wien plus the two states that border Kittsee); ``region_match`` then
    throws away everything that is not Vienna or a town within commuting
    distance of Kittsee.
    """

    name = "karriere.at"
    base_url = "https://www.karriere.at"
    default_locations = ("Wien", "Niederösterreich", "Burgenland")

    def fetch(self, config: AppConfig) -> list[JobPosting]:
        settings = config.sources.get("karriere_at", {})
        locations = settings.get("locations") or list(self.default_locations)

        jobs: dict[str, JobPosting] = {}
        for role in config.queries_for("karriere_at"):
            for location in locations:
                for page in range(1, config.max_pages_per_query + 1):
                    params = {"keywords": role, "locations": location}
                    if page > 1:
                        params["page"] = str(page)
                    url = f"{self.base_url}/jobs?{urlencode(params)}"
                    try:
                        response = self._get(url, attempts=2)
                    except requests.RequestException as exc:
                        # karriere.at answers a search with no results (404) and
                        # an out-of-range page (500) with an error status. Either
                        # way there is nothing more for this query - move on
                        # instead of sinking the whole source.
                        logger.warning("karriere.at: %r @ %r stopped: %s", role, location, exc)
                        break
                    soup = BeautifulSoup(response.text, "html.parser")
                    items = soup.select("div.m-jobsListItem")
                    if not items:
                        break

                    for item in items:
                        job = self._parse_item(item, role, config)
                        if job:
                            jobs.setdefault(job.stable_id, job)

                    if len(items) < 15:
                        break
                    time.sleep(config.request_delay_seconds)

                time.sleep(config.request_delay_seconds)

        return list(jobs.values())

    def _parse_item(self, item: Tag, role: str, config: AppConfig) -> JobPosting | None:
        link = item.select_one("a.m-jobsListItem__titleLink")
        if not link:
            return None

        title = self._text(link)
        url = self._attr(link, "href").split("?")[0]
        if not title or not url:
            return None

        location_nodes = item.select("a.m-jobsListItem__location")
        location = tidy_location(
            ", ".join(
                dict.fromkeys(
                    self._text(node).rstrip(" ,") for node in location_nodes if self._text(node).rstrip(" ,")
                )
            )
        )
        match = region_match(location, config.include_unspecified)
        if not match:
            return None

        company = self._text(item.select_one(".m-jobsListItem__companyName"))
        posted = self._text(item.select_one(".m-jobsListItem__date"))
        summary = self._text(
            item.select_one(".m-jobListSummary__text--preview")
            or item.select_one(".m-jobListSummary__text")
        )

        # karriere.at keyword search matches on the full job text, which lets
        # in plainly unrelated titles ("Senior Bauleiter" for "Laborant").
        # Keep only items whose title or teaser actually names a role, in any
        # of the configured languages.
        matched_role = match_role(f"{title} {summary}", config.all_keywords)
        if not matched_role:
            return None

        pills = [
            self._text(pill)
            for pill in item.select(".m-jobsListItem__pill")
            if not pill.select_one("a.m-jobsListItem__location")
        ]
        # karriere.at is a German-language board; note the German level if the
        # title or teaser states one.
        german = german_requirement(f"{title} {summary}")
        parts = [p for p in [german, " | ".join(dict.fromkeys(p for p in pills if p)), summary] if p]
        description = " - ".join(parts)[:300]

        return JobPosting(
            source=self.name,
            source_id=self._source_id(url),
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

    def _source_id(self, url: str) -> str:
        found = re.search(r"/jobs/(\d+)\b", url)
        return found.group(1) if found else url
