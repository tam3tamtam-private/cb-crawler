# cb-crawler

Crawl cashback campaign data and store raw snapshots into PostgreSQL (Supabase).

**Overview**
- Python 3 + Playwright (sync) crawler
- Category list loaded from `cb_m_category`
- Inserts into `cb_fr_campaigns`
- Per-site selectors via YAML

**Setup**
1. Create a virtual environment with `uv`.
```bash
uv venv
uv sync
```

2. Install Playwright browsers.
```bash
uv run playwright install
```

**Site Configs (Required)**
A site config YAML is required for each `webpage_id`.

Path pattern:
- `crawler/site_configs/<webpage_id>.yaml`

Example:
```yaml
campaign_card: "a[href*='detail.php'], a[href*='ad/detail.php']"
title: "h3"
reward: "em"
link:
  selector: "a"
  attribute: "href"
pagination:
  type: "url_param"   # or next_button
  selector: ""        # required if next_button
scroll: false
```

**Environment Settings**
Environment configs live in:
- `crawler/env/dev.yaml`
- `crawler/env/stg.yaml`
- `crawler/env/prod.yaml`

Select environment by setting `ENV`.

**Run (DEV)**
```bash
ENV=dev uv run python -m crawler.main
```

**Run One Website**
Pass `--webpage-id` to filter the crawl by `webpage_id`.
```bash
ENV=dev uv run python -m crawler.main --webpage-id 2
```

Multiple IDs are supported (comma-separated):
```bash
ENV=dev uv run python -m crawler.main --webpage-id 2,80
```

**Run From Python**
```python
from crawler import crawl

# Single website
crawl(webpage_id="2")

# Multiple websites
crawl(webpage_id="2,80")
```

**Run (STG / PROD)**
For remote Supabase, keep password out of YAML and export it.
```bash
export PGPASSWORD="your_secret"
ENV=stg uv run python -m crawler.main
```

**Headed Mode (UI visible)**
```bash
ENV=stg HEADLESS=false uv run python -m crawler.main
```

**Docker**
This repo includes a Docker image based on Playwright's Python image (`mcr.microsoft.com/playwright/python:v1.43.0-jammy`).

Build the image locally:
```bash
docker build -t cb-crawler .
```

Published image tag:
```bash
ghcr.io/tam3tamtam-private/cb-crawler:latest
```

Run it by passing the same environment variables the app already expects:
```bash
docker run --rm \
  -e ENV=stg \
  -e DATABASE_URL="your_database_url" \
  -e PGPASSWORD="your_secret" \
  ghcr.io/tam3tamtam-private/cb-crawler:latest
```

You can also override the command to target one or more websites:
```bash
docker run --rm \
  -e ENV=dev \
  ghcr.io/tam3tamtam-private/cb-crawler:latest \
  python -m crawler.main --webpage-id 2,80
```

Run in headed mode inside the container:
```bash
docker run --rm \
  -e ENV=dev \
  -e DATABASE_URL="your_database_url" \
  -e HEADLESS=false \
  ghcr.io/tam3tamtam-private/cb-crawler:latest
```

Note: `HEADLESS=false` inside Docker does not automatically display a browser window on your host machine. It only runs the browser in headed mode inside the container.

**GitHub Actions Docker Publish**
This repo includes `.github/workflows/docker-publish.yml` to build and publish an image to GitHub Container Registry:
- Registry: `ghcr.io/tam3tamtam-private/cb-crawler`
- Triggers: pushes to `main`, tags matching `v*`, and manual runs from the Actions tab
- Tags: branch name, git tag, commit SHA, and `latest` on the default branch
- On pushes to `main`, the workflow also SSHes into the Oracle Cloud VM, pulls `:latest`, and restarts the `cb-crawler` container

Before the first publish, make sure:
1. GitHub Actions is enabled for the repository.
2. In `Settings -> Actions -> General -> Workflow permissions`, `Read and write permissions` is enabled so `GITHUB_TOKEN` can publish the package.
3. If your default branch is not `main`, update the workflow trigger.
4. If this is the first GHCR publish for the repo, confirm the package is visible to the repository and inherits repository permissions.
5. Add these GitHub Actions variables: `ORACLE_VM_HOST`, `ORACLE_VM_USER`, `ORACLE_VM_PORT` (optional), and `GHCR_USERNAME`.
6. Add these GitHub Actions secrets: `ORACLE_VM_SSH_KEY` and `GHCR_TOKEN`.
7. On the Oracle VM, create `/opt/cb-crawler/cb-crawler.env` with the runtime environment variables the container needs, for example `ENV=prod`, database settings, and `PGPASSWORD`.

After the workflow runs, pull the image with:
```bash
docker pull ghcr.io/tam3tamtam-private/cb-crawler:latest
```

**Notes**
- Rows without a title or URL are skipped.
- A warning is logged if a category yields zero campaigns.
- URL pagination is used when `pagination.type: url_param` and `page=` exists.
