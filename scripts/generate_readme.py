#!/usr/bin/env python3
"""
generate_readme.py

Reads data/metrics.csv and regenerates:
  - assets/chart.png   (trend lines for the tracked metrics)
  - README.md          (summary table + embedded chart)

Run after fetch_metrics.py. Safe to run with as little as one data row
(chart will just show a single point until more days accumulate).
"""

import csv
import os
import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

ROOT = os.path.join(os.path.dirname(__file__), "..")
DATA_FILE = os.path.join(ROOT, "data", "metrics.csv")
CHART_FILE = os.path.join(ROOT, "assets", "chart.png")
README_FILE = os.path.join(ROOT, "README.md")

PLOTTED_METRICS = ["followers", "total_stars", "public_repos", "total_forks"]


def load_rows():
    with open(DATA_FILE, newline="") as f:
        return list(csv.DictReader(f))


def make_chart(rows):
    dates = [datetime.date.fromisoformat(r["date"]) for r in rows]

    fig, ax = plt.subplots(figsize=(9, 4.5))
    for metric in PLOTTED_METRICS:
        values = [int(r[metric]) for r in rows]
        ax.plot(dates, values, marker="o", markersize=3, linewidth=1.6, label=metric.replace("_", " "))

    ax.set_title("Dev metrics over time")
    ax.legend(loc="upper left", fontsize=8, frameon=False)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    fig.autofmt_xdate()
    ax.grid(alpha=0.25)
    fig.tight_layout()

    os.makedirs(os.path.dirname(CHART_FILE), exist_ok=True)
    fig.savefig(CHART_FILE, dpi=150)
    plt.close(fig)


def delta(rows, field, days_back):
    if len(rows) <= days_back:
        return None
    return int(rows[-1][field]) - int(rows[-1 - days_back][field])


def fmt_delta(d):
    if d is None:
        return "n/a"
    return f"+{d}" if d >= 0 else str(d)


def build_readme(rows):
    latest = rows[-1]
    first_date = rows[0]["date"]
    days_tracked = len(rows)

    d7 = {m: delta(rows, m, 7) for m in PLOTTED_METRICS}
    d30 = {m: delta(rows, m, 30) for m in PLOTTED_METRICS}

    table_rows = "\n".join(
        f"| {m.replace('_', ' ').title()} | {latest[m]} | {fmt_delta(d7[m])} | {fmt_delta(d30[m])} |"
        for m in PLOTTED_METRICS
    )

    content = f"""# Dev Metrics Tracker

A daily snapshot of my own public GitHub activity — repos, followers,
stars, forks — tracked over time as an actual dataset instead of a
one-off stat.

Every day a [GitHub Action](.github/workflows/daily.yml) pulls fresh
numbers from the GitHub API, appends a row to
[`data/metrics.csv`](data/metrics.csv), and regenerates this README
and the chart below.

**Tracking since:** {first_date} &nbsp;·&nbsp; **Days recorded:** {days_tracked} &nbsp;·&nbsp; **Last updated:** {latest['date']}

## Current snapshot

| Metric | Current | 7-day change | 30-day change |
|---|---|---|---|
{table_rows}

## Trend

![Metrics chart](assets/chart.png)

## How it works

1. `scripts/fetch_metrics.py` — hits the GitHub REST API for the
   configured user, aggregates stats across all public repos, and
   appends/updates today's row in `data/metrics.csv`.
2. `scripts/generate_readme.py` — reads the full CSV history, renders
   `assets/chart.png` with matplotlib, and rewrites this README.
3. `.github/workflows/daily.yml` — runs both scripts once a day on a
   cron schedule and commits the result.

## Running it yourself

```bash
export GITHUB_USERNAME=your-username
export GITHUB_TOKEN=your-token   # optional locally, raises rate limit
python scripts/fetch_metrics.py
python scripts/generate_readme.py
```

## Why

Wanted a lightweight way to actually see my own GitHub activity trend
over time instead of just eyeballing the profile page — and a reason
for this repo to update daily that isn't just noise.
"""

    with open(README_FILE, "w") as f:
        f.write(content)


def main():
    if not os.path.isfile(DATA_FILE):
        print("No data/metrics.csv yet — run fetch_metrics.py first.")
        return

    rows = load_rows()
    if not rows:
        print("data/metrics.csv is empty — run fetch_metrics.py first.")
        return

    make_chart(rows)
    build_readme(rows)
    print(f"Regenerated README.md and assets/chart.png from {len(rows)} row(s).")


if __name__ == "__main__":
    main()
