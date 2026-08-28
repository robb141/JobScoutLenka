# Lenka's Biochem Job Scout

Collects open biochemistry / lab / pharma positions that Lenka (based in
Kittsee) could realistically take, and writes:

- `output/index.html` with new jobs highlighted

Every posting is sorted into one of these regions, and anything that lands
outside them is dropped:

- **Bratislava** – the city and its boroughs
- **Vienna** – shown as `Wien 3`, `Wien 22`, … when the district can be read
  from a postal code or district name, otherwise just `Vienna`
- **Kittsee area** – Austrian border towns within roughly 25 km of Kittsee
  (Hainburg, Bruck an der Leitha, Parndorf, Neusiedl am See, …)

The report columns:

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
- `sources.profesia.region` – Slovak region slug pinned in the URL
- `sources.karriere_at.locations` / `sources.linkedin.locations` – Austrian
  states / LinkedIn geos to search before region filtering
- `sources.company_pages.pages` – direct career pages of biotech/pharma
  employers to scan; each entry takes `location` (Vienna district if known)
  and `note` (e.g. the German level the employer expects), both surfaced in
  the report

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
- **LinkedIn** – public guest search; rate-limited, so some queries may be
  skipped on busy runs
- **Company pages** – direct career pages listed in `config.yml`

Not wired up yet, but sensible next additions: AMS *alle jobs* (jobs.ams.at)
and Indeed (`at.indeed.com`, `sk.indeed.com`).
