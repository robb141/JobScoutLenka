# Lenka's Biochem Job Scout

Collects open biochemistry / lab / pharma positions that Lenka (based in
Kittsee) could realistically take, and writes:

- `output/index.html` with new jobs highlighted

Every posting is sorted into one of these regions, and anything that lands
outside them is dropped:

- **Bratislava** – the city and its boroughs
- **Vienna** – shown as `Vienna 3`, `Vienna 22`, … when the district can be
  read from a postal code or district name, otherwise just `Vienna`
- **Kittsee area** – Austrian border towns within roughly 25 km of Kittsee
  (Hainburg, Bruck an der Leitha, Parndorf, Neusiedl am See, …)

The report columns:

- **Region** – always English (`Bratislava`, `Vienna`, `Vienna 22`,
  `Kittsee area`). The **Location** column keeps whatever the board printed,
  so it may read `Wien` (karriere.at) or `Vienna, Austria` (LinkedIn).
- **Zverejnené** – when it was posted, normalised to Slovak (`Dnes`, `Včera`,
  `pred 3 dňami`, `pred 2 týždňami`, or a `d. m. yyyy` date)
- **Description** – for karriere.at rows, prefixed with the German level the
  ad asks for (`Nemčina B2`, `Nemčina: plynulá (C1+)`, …) when it states one

The app remembers previously seen job IDs in `data/state.json`, so the next
run can mark fresh postings as `NEW`.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Configure

Edit `config.yml`:

- `roles` – global keyword list, in **English**. LinkedIn searches these
  directly.
- `sources.profesia.keywords` – **Slovak** search terms for Profesia
- `sources.karriere_at.keywords` – **German** search terms for karriere.at
  (shared with StepStone via the `&de_keywords` YAML anchor)
- `sources.profesia.region` – Slovak region slug pinned in the URL
- `sources.karriere_at.locations` / `sources.linkedin.locations` – Austrian
  states / LinkedIn geos to search before region filtering
- `sources.company_pages.pages` – direct career / listing pages to scan.
  Per entry: `location` (Vienna district if known), `note` (e.g. the German
  level expected) – both shown in the report – plus optional `link_pattern`
  (regex an href must match, for quirky URL schemes) and `single_site: true`
  (let `location` admit rows that name no place – only for one-location
  employers). Currently: Slovak Academy of Sciences, Lexogen, University of
  Vienna, Takeda, Boehringer Ingelheim, Valneva.

Each board is searched in its own language, but a scraped posting is kept
only if its **title** matches one of the keywords in *any* language (with a
little slack for Slovak/German word endings, so "laborantka" matches
"Laborant"). If the report is too noisy, tighten the keyword lists (e.g.
drop broad terms like "Kontrola kvality" that also catch production-line QC);
if it misses jobs, add title variants.

## Run

```bash
.venv/bin/python -m jobscout collect
```

Open the generated web report:

```bash
.venv/bin/python -m jobscout serve
```

Then visit http://127.0.0.1:8000.

## Test

```bash
.venv/bin/pip install pytest
.venv/bin/python -m pytest
```

## Sources

- **Profesia.sk** – the largest Slovak board (Bratislava side)
- **karriere.at** – the largest Austrian board (Vienna + border towns)
- **StepStone.at** – a second Austrian board; searched with a 30 km radius
  around Vienna and Hainburg, different employer base (staffing agencies,
  mid-size pharma/R&D)
- **LinkedIn** – public guest search; rate-limited, so some queries may be
  skipped on busy runs
- **Company pages** – direct career / listing pages listed in `config.yml`
  (Slovak Academy of Sciences job board, Lexogen, University of Vienna,
  Takeda, Boehringer Ingelheim, Valneva)

Indeed (`at.indeed.com` / `sk.indeed.com`) blocks non-browser requests, so
it is not viable. AMS *alle jobs* (jobs.ams.at) is a JavaScript app. Most
employer career sites are JavaScript apps this scraper cannot read.
