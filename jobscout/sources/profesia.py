from __future__ import annotations

import logging
import re
import time
from urllib.parse import urlencode, urljoin

import requests
from bs4 import BeautifulSoup, Tag

from jobscout.config import AppConfig
from jobscout.location import region_match
from jobscout.models import JobPosting
from jobscout.roles import match_role
from jobscout.sources.base import JobSource


logger = logging.getLogger(__name__)


class ProfesiaSource(JobSource):
    """Profesia.sk - by far the largest Slovak job board.

    Free-text search lives in the ``search_anywhere`` query parameter; a
    region can be pinned by putting its slug in the path. The default region
    ``bratislavsky-kraj`` covers Bratislava and its commuter belt, which is
    the Slovak side of what Lenka can reach from Kittsee.
    """

    name = "profesia.sk"
    base_url = "https://www.profesia.sk"

    def fetch(self, config: AppConfig) -> list[JobPosting]:
        settings = config.sources.get("profesia", {})
        region = str(settings.get("region", "bratislavsky-kraj")).strip("/")
        path = f"/praca/{region}/" if region else "/praca/"

        jobs: dict[str, JobPosting] = {}
        for role in config.queries_for("profesia"):
            for page in range(1, config.max_pages_per_query + 1):
                params = {"search_anywhere": role}
                if page > 1:
                    params["page_num"] = str(page)
                url = f"{self.base_url}{path}?{urlencode(params)}"
                try:
                    response = self._get(url)
                except requests.RequestException as exc:
                    logger.warning("profesia: %r p%d stopped: %s", role, page, exc)
                    break
                soup = BeautifulSoup(response.text, "html.parser")
                rows = [
                    row
                    for row in soup.select("li.list-row")
                    if "promo-tile-list-row" not in (row.get("class") or [])
                ]
                if not rows:
                    break

                for row in rows:
                    job = self._parse_row(row, role, config)
                    if job:
                        jobs.setdefault(job.stable_id, job)

                time.sleep(config.request_delay_seconds)

        return list(jobs.values())

    def _parse_row(self, row: Tag, role: str, config: AppConfig) -> JobPosting | None:
        link = row.select_one("h2 a")
        if not link:
            return None

        title = self._text(row.select_one("h2 a span.title")) or self._text(link)
        href = self._attr(link, "href")
        if not title or not href:
            return None

        location_node = row.select_one(".job-location")
        location = self._text(location_node)
        location_hint = f"{location} {self._attr(location_node, 'title')}"
        match = region_match(location_hint, config.include_unspecified)
        if not match:
            return None

        company = self._text(row.select_one(".employer"))

        # Profesia's free-text search is broad - a query for "Chemik" also
        # returns cooks and car electricians whose ad text mentions a keyword
        # somewhere. Keep only rows whose title actually names a role.
        matched_role = match_role(f"{title} {company}", config.all_keywords)
        if not matched_role:
            return None

        posted = self._text(row.select_one(".list-footer .info strong"))
        labels = [self._text(label) for label in row.select(".label-group .label")]
        summary = " | ".join(dict.fromkeys(label for label in labels if label))[:300]

        return JobPosting(
            source=self.name,
            source_id=self._source_id(link, href),
            title=title,
            company=company,
            url=urljoin(self.base_url, href).split("?")[0],
            location=location,
            region_match=match,
            posted_date=posted,
            company_description=summary,
            summary=summary,
            matched_query=matched_role,
        )

    def _source_id(self, link: Tag, href: str) -> str:
        link_id = self._attr(link, "id")
        if link_id.startswith("offer"):
            return link_id.removeprefix("offer")
        found = re.search(r"/O(\d+)\b", href)
        return found.group(1) if found else href
