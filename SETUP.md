# Setup

1. Create a new GitHub repo and push this project to it.
2. That's it for basic use — `GITHUB_TOKEN` is provided automatically
   inside GitHub Actions, and `github.repository_owner` is used as the
   tracked username, so the workflow in
   `.github/workflows/daily.yml` works with no configuration as long
   as this repo lives under your own account.
3. The workflow runs daily at 06:00 UTC. To trigger it immediately
   (don't wait for tomorrow): go to the repo's **Actions** tab →
   **Daily metrics update** → **Run workflow**.
4. After the first run, check that `data/metrics.csv`,
   `assets/chart.png`, and `README.md` were updated and committed by
   the `github-actions[bot]` user.

## Tracking a different username

If you want to track a username other than the repo owner (e.g. this
repo lives in an org but should track your personal profile), edit
the `GITHUB_USERNAME` line in `.github/workflows/daily.yml` to a fixed
value instead of `${{ github.repository_owner }}`.

## Adding more metrics

`scripts/fetch_metrics.py` currently pulls repos, followers,
following, stars, forks, gists, and account age from the GitHub REST
API. To track something else (LeetCode solved count, a personal site's
uptime, etc.), add a field to `FIELDS`, fetch it in
`collect_metrics()`, and add it to `PLOTTED_METRICS` in
`scripts/generate_readme.py` if you want it charted.
