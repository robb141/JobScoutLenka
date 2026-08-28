from __future__ import annotations

import re
import time
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from jobscout.config import AppConfig
from jobscout.location import VIENNA, region_match
from jobscout.models import JobPosting
from jobscout.roles import match_role
from jobscout.sources.base import JobSource


# A link only counts as a job posting if its href looks like a job-detail URL.
# Without this, marketing/nav links ("Glassdoor", "Life at Takeda", category
# filters) on modern career portals sail through the keyword match.
_JOB_HREF_RE = re.compile(
    r"(?:^|[/.])(?:jobs?|stelle|stellen|position|vacanc\w+|angebot|opening|career|careers|karriere)(?:[/_-]|$)"
    r"|/job/[^/]+/\d"
    r"|/\d{5,}(?:/|$|[?#])"
    r"|workable\.com/|personio\.|myworkdayjobs|successfactors|smartrecruiters|greenhouse\.io",
    re.IGNORECASE,
)


class CompanyPagesSource(JobSource):
    """Direct career pages of biotech / pharma employers around the region.

    Configure entries under ``sources.company_pages.pages``; the collector
    scans every link on the page for the role keywords and keeps the ones
    that also resolve to one of Lenka's target regions. A ``location`` given
    per page is used as the fallback when the link itself names no place.
    """

    name = "company_pages"

    def fetch(self, config: AppConfig) -> list[JobPosting]:
        pages = config.sources.get("company_pages", {}).get("pages") or []
        jobs: dict[str, JobPosting] = {}

        for page in pages:
            company = str(page.get("company", "")).strip()
            url = str(page.get("url", "")).strip()
            default_location = str(page.get("location", "")).strip()
            note = str(page.get("note", "")).strip()
            if not company or not url:
                continue

            try:
                response = self._get(url)
            except Exception:  # noqa: BLE001 - one broken page must not sink the rest
                continue

            for job in self._parse_page(response.text, url, company, default_location, note, config):
                jobs.setdefault(job.stable_id, job)

            time.sleep(config.request_delay_seconds)

        return list(jobs.values())

    def _parse_page(
        self,
        html: str,
        page_url: str,
        company: str,
        default_location: str,
        note: str,
        config: AppConfig,
    ) -> list[JobPosting]:
        soup = BeautifulSoup(html, "html.parser")
        jobs = []

        for link in soup.select("a[href]"):
            text = self._text(link)
            href = str(link.get("href") or "")
            if len(text) < 6 or not _JOB_HREF_RE.search(href):
                continue

            nearby = self._nearby_text(link)
            matched_role = match_role(f"{text} {href} {nearby}", config.all_keywords)
            if not matched_role:
                continue

            # The listing itself must place the job in a target region - a
            # global career site lists jobs for every country, and the
            # configured `location` is not license to claim all of them.
            match = region_match(f"{text} {href}", config.include_unspecified) or region_match(
                nearby, config.include_unspecified
            )
            if not match:
                continue

            # Use the employer's known district to sharpen a bare "Vienna".
            if match == VIENNA and default_location:
                refined = region_match(default_location, config.include_unspecified)
                if refined and refined.startswith("Wien "):
                    match = refined

            description = " - ".join(part for part in [note, self._shorten(nearby)] if part)[:300]
            jobs.append(
                JobPosting(
                    source=self.name,
                    source_id=urljoin(page_url, href),
                    title=text or matched_role,
                    company=company,
                    url=urljoin(page_url, href),
                    location=default_location or match,
                    region_match=match,
                    posted_date="",
                    company_description=description,
                    summary=description,
                    matched_query=matched_role,
                )
            )

        return jobs

    def _nearby_text(self, link: Tag) -> str:
        # Climb toward the job-listing container, but stop before the
        # container text balloons into whole-page noise.
        node = link
        text = self._text(link)
        for _ in range(4):
            parent = node.parent
            if parent is None or parent.name in {"body", "html", "[document]"}:
                break
            # Stop before a container that holds another listing (a second
            # job-detail link), or whose text balloons into whole-page noise.
            # "Apply" / "save" links in the same card are fine - they are not
            # job-detail URLs.
            job_links = [a for a in parent.find_all("a", href=True) if _JOB_HREF_RE.search(str(a.get("href") or ""))]
            if len(job_links) > 1:
                break
            parent_text = self._text(parent)
            if len(parent_text) > 400:
                break
            node = parent
            text = parent_text
        return text

    def _shorten(self, text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()[:300]
