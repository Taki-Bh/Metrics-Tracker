#!/usr/bin/env python3
"""
fetch_metrics.py

Pulls a snapshot of your public GitHub stats and appends it as a new row
to data/metrics.csv. Designed to be run once a day (see the included
GitHub Action), so the repo accumulates a real, growing time series of
your own dev activity instead of noise.

Usage:
    GITHUB_USERNAME=yourname GITHUB_TOKEN=ghp_xxx python scripts/fetch_metrics.py

GITHUB_TOKEN is optional locally (raises your rate limit from 60/hr to
5000/hr) but required in the Action, where it's supplied automatically
as secrets.GITHUB_TOKEN.
"""

import csv
import os
import sys
import datetime
import urllib.request
import json

API_BASE = "https://api.github.com"
DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "metrics.csv")

FIELDS = [
    "date",
    "public_repos",
    "followers",
    "following",
    "total_stars",
    "total_forks",
    "public_gists",
    "account_age_days",
]


def gh_request(path, token=None):
    req = urllib.request.Request(f"{API_BASE}{path}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "dev-metrics-tracker")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def gh_paginated(path, token=None, max_pages=10):
    """Yield items across paginated GitHub endpoints."""
    page = 1
    while page <= max_pages:
        sep = "&" if "?" in path else "?"
        items = gh_request(f"{path}{sep}per_page=100&page={page}", token)
        if not items:
            break
        yield from items
        if len(items) < 100:
            break
        page += 1


def collect_metrics(username, token=None):
    user = gh_request(f"/users/{username}", token)

    total_stars = 0
    total_forks = 0
    for repo in gh_paginated(f"/users/{username}/repos", token):
        total_stars += repo.get("stargazers_count", 0)
        total_forks += repo.get("forks_count", 0)

    created_at = datetime.datetime.strptime(
        user["created_at"], "%Y-%m-%dT%H:%M:%SZ"
    )
    account_age_days = (datetime.datetime.utcnow() - created_at).days

    return {
        "date": datetime.date.today().isoformat(),
        "public_repos": user.get("public_repos", 0),
        "followers": user.get("followers", 0),
        "following": user.get("following", 0),
        "total_stars": total_stars,
        "total_forks": total_forks,
        "public_gists": user.get("public_gists", 0),
        "account_age_days": account_age_days,
    }


def append_row(row):
    file_exists = os.path.isfile(DATA_FILE)
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

    # If today's date is already the last row, overwrite it instead of
    # duplicating (handy for re-running the Action or testing locally).
    rows = []
    if file_exists:
        with open(DATA_FILE, newline="") as f:
            rows = list(csv.DictReader(f))

    if rows and rows[-1]["date"] == row["date"]:
        rows[-1] = row
    else:
        rows.append(row)

    with open(DATA_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main():
    username = os.environ.get("GITHUB_USERNAME")
    token = os.environ.get("GITHUB_TOKEN")

    if not username:
        print("ERROR: set GITHUB_USERNAME env var", file=sys.stderr)
        sys.exit(1)

    try:
        row = collect_metrics(username, token)
    except Exception as e:
        print(f"ERROR fetching metrics: {e}", file=sys.stderr)
        sys.exit(1)

    append_row(row)
    print(f"Recorded snapshot for {username} on {row['date']}: {row}")


if __name__ == "__main__":
    main()
