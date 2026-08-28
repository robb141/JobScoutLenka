from bs4 import BeautifulSoup

from jobscout.config import AppConfig
from jobscout.sources.company_pages import CompanyPagesSource
from jobscout.sources.karriere_at import KarriereAtSource
from jobscout.sources.linkedin import LinkedInSource
from jobscout.sources.profesia import ProfesiaSource
from jobscout.sources.stepstone import StepStoneAtSource


def make_config(**overrides) -> AppConfig:
    defaults = dict(
        roles=["Laborant", "Labortechniker", "Biochemist", "Analytical chemist", "Qualitätskontrolle"],
        include_unspecified=True,
        max_pages_per_query=1,
        request_delay_seconds=0.0,
        sources={},
    )
    defaults.update(overrides)
    return AppConfig(**defaults)


# --- Profesia.sk -------------------------------------------------------------

PROFESIA_ROW = """
<li class="list-row">
  <a class="offer-company-logo-link" href="/praca/lekarne-dr-max/C27024"><img alt="Logo"></a>
  <h2>
    <a href="/praca/lekarne-dr-max/O4725253?search_id=f80a8c2c" id="offer4725253">
      <span class="title">Farmaceutický/á laborant/ka - Bratislava</span>
    </a>
  </h2>
  <span class="employer">Lekárne Dr.Max</span>
  <span class="job-location" title="Bratislava">Bratislava</span>
  <span class="label-group">
    <a href="#"><span class="label label-bordered green">1 550 - 1 850 EUR/mesiac</span></a>
  </span>
  <div class="list-footer"><div class="row"><div class="list-footer-right">
    <span class="info"><strong>Včera</strong></span>
  </div></div></div>
</li>
"""

PROFESIA_ROW_NITRA = PROFESIA_ROW.replace('title="Bratislava">Bratislava', 'title="Nitra">Nitra')


def parse_profesia(html: str, config: AppConfig):
    row = BeautifulSoup(html, "html.parser").select_one("li.list-row")
    return ProfesiaSource()._parse_row(row, "Laborant", config)


def test_profesia_row_parses():
    job = parse_profesia(PROFESIA_ROW, make_config())
    assert job is not None
    assert job.source_id == "4725253"
    assert job.company == "Lekárne Dr.Max"
    assert job.title == "Farmaceutický/á laborant/ka - Bratislava"
    assert job.region_match == "Bratislava"
    assert job.posted_date == "Včera"
    assert "1 550 - 1 850 EUR/mesiac" in job.summary
    assert job.url == "https://www.profesia.sk/praca/lekarne-dr-max/O4725253"


def test_profesia_drops_rows_outside_target_regions():
    assert parse_profesia(PROFESIA_ROW_NITRA, make_config()) is None


def test_profesia_keeps_unspecified_region_when_flag_on():
    html = PROFESIA_ROW.replace(
        'title="Bratislava">Bratislava', 'title="Bratislavský kraj">Bratislavský kraj'
    )
    assert parse_profesia(html, make_config()).region_match == "Bratislava region"
    assert parse_profesia(html, make_config(include_unspecified=False)) is None


# --- karriere.at -----------------------------------------------------------

KARRIERE_ITEM = """
<div class="m-jobsListItem">
  <h2 class="m-jobsListItem__title">
    <a class="m-jobsListItem__titleLink" href="https://www.karriere.at/jobs/7844942?foo=bar">
      Analytical Chemist (m/w/d)
    </a>
  </h2>
  <div class="m-jobsListItem__company">
    <a class="m-jobsListItem__companyName">VTU Engineering GmbH</a>
  </div>
  <div class="m-jobsListItem__content">
    <span class="m-jobsListItem__date">vor 7 Tagen veröffentlicht</span>
    <div class="m-jobsListItem__pills">
      <span class="m-jobsListItem__locations m-jobsListItem__pill">
        <a class="m-jobsListItem__location" data-location="wien" href="/jobs/wien">Wien<span
          class="m-jobsListItem__location--lastComma">,</span></a>
      </span>
      <span class="m-jobsListItem__pill">Vollzeit</span>
      <span class="m-jobsListItem__pill">Homeoffice</span>
      <span class="m-jobsListItem__pill">ab 3.800 € monatlich</span>
    </div>
    <div class="m-jobListSummary"><div class="m-jobListSummary__body">
      <p class="m-jobListSummary__text--preview m-jobListSummary__text">
        Projektleitung in der biopharmazeutischen Industrie.
      </p>
    </div></div>
  </div>
</div>
"""


def parse_karriere(html: str, config: AppConfig):
    item = BeautifulSoup(html, "html.parser").select_one("div.m-jobsListItem")
    return KarriereAtSource()._parse_item(item, "Analytical chemist", config)


def test_karriere_item_parses():
    job = parse_karriere(KARRIERE_ITEM, make_config())
    assert job is not None
    assert job.source_id == "7844942"
    assert job.company == "VTU Engineering GmbH"
    assert job.title == "Analytical Chemist (m/w/d)"
    assert job.matched_query == "Analytical chemist"
    assert job.region_match == "Vienna"
    assert job.location == "Wien"  # trailing comma span stripped
    assert job.posted_date == "vor 7 Tagen veröffentlicht"
    assert "Vollzeit" in job.summary  # pills kept, location pill skipped
    assert "biopharmazeutischen" in job.summary
    assert "?" not in job.url


def test_karriere_drops_far_austrian_towns():
    html = KARRIERE_ITEM.replace(">Wien<", ">Eisenstadt<").replace('href="/jobs/wien"', 'href="/jobs/eisenstadt"')
    assert parse_karriere(html, make_config()) is None


def test_karriere_keeps_kittsee_border_town():
    html = KARRIERE_ITEM.replace(">Wien<", ">Hainburg an der Donau<")
    assert parse_karriere(html, make_config()).region_match == "Kittsee area"


# --- StepStone.at ----------------------------------------------------------

STEPSTONE_CARD = """
<article data-testid="job-item" id="job-item-991803">
  <div data-testid="job-card-content">
    <a data-at="company-logo" href="/cmp/de/pichem-161668/jobs"></a>
    <h2>
      <a data-testid="job-item-title"
         href="https://www.stepstone.at/stellenangebote--Chemielabortechniker-m-w-d-Wien-piCHEM--991803-inline.html?foo=1">
        <div><div><div>Chemielabortechniker (m/w/d)</div></div></div>
      </a>
    </h2>
    <div data-at="job-item-middle">
      <span data-at="job-item-company-name">piCHEM Forschungs-und Entwicklungs GmbH</span>
      <span data-at="job-item-location">Wien</span>
      <span data-at="job-item-timeago"><time>vor 1 Woche</time></span>
    </div>
    <div>Analytik im GMP-Labor. Gute Deutschkenntnisse und HPLC-Erfahrung erforderlich.</div>
  </div>
</article>
"""


def parse_stepstone(html: str, config: AppConfig):
    card = BeautifulSoup(html, "html.parser").select_one('article[data-testid="job-item"]')
    return StepStoneAtSource()._parse_card(card, config)


def test_stepstone_card_parses():
    job = parse_stepstone(STEPSTONE_CARD, make_config())
    assert job is not None
    assert job.source_id == "991803"
    assert job.title == "Chemielabortechniker (m/w/d)"
    assert job.company == "piCHEM Forschungs-und Entwicklungs GmbH"
    assert job.region_match == "Vienna"
    # "Labortechniker" matched inside the compound "Chemielabortechniker"
    assert job.matched_query == "Labortechniker"
    assert job.posted_date == "vor 1 Woche"
    assert "?" not in job.url
    assert job.summary.startswith("Nemčina: dobrá (B2)")  # "gute Deutschkenntnisse"


def test_stepstone_drops_far_town():
    html = STEPSTONE_CARD.replace(">Wien<", ">Graz<")
    assert parse_stepstone(html, make_config()) is None


def test_stepstone_drops_unrelated_title():
    html = STEPSTONE_CARD.replace("Chemielabortechniker (m/w/d)", "LKW-Fahrer (m/w/d)").replace(
        "Analytik im GMP-Labor. Gute Deutschkenntnisse und HPLC-Erfahrung erforderlich.", "Führerschein C+E."
    )
    assert parse_stepstone(html, make_config()) is None


# --- LinkedIn ------------------------------------------------------------------

LINKEDIN_CARD = """
<div class="base-card" data-entity-urn="urn:li:jobPosting:4123456789">
  <a class="base-card__full-link" href="https://at.linkedin.com/jobs/view/biochemist-at-acme-4123456789?refId=abc">Biochemist</a>
  <div class="base-search-card__info">
    <h3 class="base-search-card__title">Biochemist</h3>
    <h4 class="base-search-card__subtitle">Acme GmbH</h4>
    <span class="job-search-card__location">Vienna, Vienna, Austria</span>
    <time datetime="2026-08-20">1 week ago</time>
  </div>
</div>
"""


def parse_linkedin(html: str, config: AppConfig):
    card = BeautifulSoup(html, "html.parser").select_one(".base-card")
    return LinkedInSource()._parse_card(card, config)


def test_linkedin_card_parses():
    job = parse_linkedin(LINKEDIN_CARD, make_config())
    assert job is not None
    assert job.source_id == "4123456789"
    assert job.company == "Acme GmbH"
    assert job.region_match == "Vienna"
    assert job.location == "Vienna, Austria"  # "Vienna, Vienna, Austria" de-duped
    assert job.posted_date == "2026-08-20"
    assert "?" not in job.url


def test_linkedin_drops_unrelated_titles():
    html = LINKEDIN_CARD.replace(">Biochemist<", ">Accountant<")
    assert parse_linkedin(html, make_config()) is None


def test_linkedin_drops_out_of_scope_locations():
    html = LINKEDIN_CARD.replace("Vienna, Vienna, Austria", "Graz, Styria, Austria")
    assert parse_linkedin(html, make_config()) is None


# --- Company pages -----------------------------------------------------------

def parse_company(html, *, location="", note="", link_pattern=None, single_site=False, cfg=None):
    import re as _re

    link_re = _re.compile(link_pattern, _re.IGNORECASE) if link_pattern else None
    return CompanyPagesSource()._parse_page(
        html, "https://example.com", "Example", location, note, link_re, single_site, cfg or make_config()
    )


def test_company_pages_matches_role_and_region():
    html = """
      <ul>
        <li><a href="/careers/qc-laborant">QC Laborant (m/w/d)</a> – Bratislava, Ružinov</li>
        <li><a href="/careers/driver">LKW Fahrer</a> – Wien</li>
      </ul>
    """
    jobs = parse_company(html)
    assert len(jobs) == 1
    assert jobs[0].region_match == "Bratislava"
    assert jobs[0].matched_query == "Laborant"


def test_company_pages_note_prefixes_description_and_district_refines_vienna():
    html = '<div><a href="/careers/biochemist">Biochemist</a> – Wien, Austria</div>'
    jobs = parse_company(html, location="Vienna 22 (Donaustadt)", note="Nemčina: B2+")
    assert len(jobs) == 1
    # listing says only "Wien"; the configured district sharpens it
    assert jobs[0].region_match == "Vienna 22"
    assert jobs[0].summary.startswith("Nemčina: B2+")


def test_company_pages_ignores_job_links_for_other_countries():
    # A real job link, but the listing places it abroad - the configured
    # location must not pull it into Vienna.
    html = '<li><a href="https://ex.workable.com/jobs/12345">Analytical chemist – Solna, Sweden</a></li>'
    assert parse_company(html, location="Vienna 3 (Landstraße)") == []


def test_company_pages_single_site_admits_placeless_rows():
    html = '<li><a href="/detail?offer_no=42">Laborant vo výskumnom laboratóriu</a></li>'
    # without single_site the row names no region -> dropped
    assert parse_company(html, location="Bratislava", link_pattern="offer_no=") == []
    # with it, the configured location admits the job
    jobs = parse_company(html, location="Bratislava", link_pattern="offer_no=", single_site=True)
    assert len(jobs) == 1 and jobs[0].region_match == "Bratislava"


def test_company_pages_skips_non_job_links():
    html = '<footer><a href="https://glassdoor.com/x">Glassdoor Laboratory reviews</a></footer>'
    assert parse_company(html, location="Wien") == []
