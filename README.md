# linkedin-connections-toolkit

A small, dependency-free Python toolkit for parsing and analyzing your own
LinkedIn `Connections.csv` export. Stdlib only, runs offline, on data you
already own.

LinkedIn's export is slightly awkward to parse (a "Notes:" preamble before the
real header, a BOM, a date column in a human format). This toolkit handles that
once and gives you clean records plus a few plain, useful views of your network.

## What it does

- **Parses** `Connections.csv` into normalized `Connection` records (skips the
  preamble, strips the BOM, parses `Connected On` into a real date).
- **Analyzes**, with four independent views:
  - `years` - how many connections you added each year (recency shape)
  - `companies` - where your network concentrates
  - `seniority` - a transparent title-keyword breakdown
  - `staleness` - how much of your network is dormant (old and untouched)

It is deliberately un-opinionated: no scoring, no ranking, no model. Just clean
ETL and four counts you can build on.

## Get your data

LinkedIn -> **Settings & Privacy -> Data Privacy -> Get a copy of your data ->
Connections**. Unzip the download to get `Connections.csv`.

## Install

```bash
pip install git+https://github.com/flashesofbrilliance/linkedin-connections-toolkit.git
```

Or clone and run without installing (it is stdlib-only):

```bash
git clone https://github.com/flashesofbrilliance/linkedin-connections-toolkit.git
cd linkedin-connections-toolkit
python3 -m linkedin_connections summary sample_connections.csv
```

## Use it (CLI)

```bash
# Everything at once
linkedin-connections summary Connections.csv

# Individual views
linkedin-connections years Connections.csv
linkedin-connections companies Connections.csv --limit 30
linkedin-connections seniority Connections.csv

# Machine-readable output (works on any subcommand)
linkedin-connections summary Connections.csv --json > report.json
```

If you did not install the console script, replace `linkedin-connections` with
`python3 -m linkedin_connections`.

### Options

- `--json` - emit JSON instead of the text report (any subcommand).
- `--limit N` - how many top companies to show (`summary`, `companies`).
- `--stale-after-years N` - age past which a connection counts as stale
  (`summary`, default 4).
- `--as-of-year YYYY` - reference year for staleness (`summary`, default: the
  latest year present in your data).

## Use it (library)

```python
from linkedin_connections import load_connections, summary, top_companies

connections = load_connections("Connections.csv")

print(len(connections), "connections")
for company, count in top_companies(connections, limit=10):
    print(count, company)

report = summary(connections)          # a plain dict, ready to serialize
print(report["staleness"])             # {'active': ..., 'stale': ..., 'undated': ...}
```

Each `Connection` exposes `first_name`, `last_name`, `name`, `company`,
`position`, `url`, `email`, `connected_on` (a `datetime.date` or `None`), and
`connected_year`.

## Seniority is a heuristic

`seniority` classifies each job title with a simple, ordered keyword match
(executive -> vp -> director -> manager -> senior -> individual -> unknown). It
is a rough estimate, not a judgement, and it is easy to tune: edit
`SENIORITY_KEYWORDS` in `linkedin_connections/analyze.py`.

## Privacy

Your `Connections.csv` is personal data about other people. This toolkit runs
entirely offline and never uploads anything. The included `.gitignore` excludes
`Connections.csv` and the raw export folder so you do not commit it by accident.
The repo ships only a small synthetic `sample_connections.csv` for trying the
tool.

## License

MIT. See [LICENSE](./LICENSE).
---

## Part of the ARCS family

An open, MIT-licensed tool in the [flashesofbrilliance](https://github.com/flashesofbrilliance) / ARCS family — small, composable, provenance-carrying. The tools are open; the ARCS intelligence that orchestrates them is private.
