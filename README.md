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

**Notes**
- Rows without a title or URL are skipped.
- A warning is logged if a category yields zero campaigns.
- URL pagination is used when `pagination.type: url_param` and `page=` exists.
