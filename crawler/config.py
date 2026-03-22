import os
import yaml

# Environment
ENV = os.getenv("ENV", "dev")


def _load_env_file() -> None:
    path = os.getenv("ENV_CONFIG_PATH")
    if not path:
        path = os.path.join(os.path.dirname(__file__), "env", f"{ENV}.yaml")
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    for key, value in data.items():
        if value is None:
            continue
        if key not in os.environ:
            os.environ[key] = str(value)


_load_env_file()

# Database
DATABASE_URL = os.getenv("DATABASE_URL")
PGHOST = os.getenv("PGHOST")
PGPORT = int(os.getenv("PGPORT", "5432"))
PGDATABASE = os.getenv("PGDATABASE")
PGUSER = os.getenv("PGUSER")
PGPASSWORD = os.getenv("PGPASSWORD")

# Crawler
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
BROWSER_TIMEOUT_MS = int(os.getenv("BROWSER_TIMEOUT_MS", "30000"))
NAVIGATION_TIMEOUT_MS = int(os.getenv("NAVIGATION_TIMEOUT_MS", "45000"))

# Rate limiting / politeness
DELAY_MIN_SEC = float(os.getenv("DELAY_MIN_SEC", "0.4"))
DELAY_MAX_SEC = float(os.getenv("DELAY_MAX_SEC", "1.2"))

# Retry
CATEGORY_RETRIES = int(os.getenv("CATEGORY_RETRIES", "3"))

# Scrolling / pagination
ENABLE_INFINITE_SCROLL = os.getenv("ENABLE_INFINITE_SCROLL", "true").lower() == "true"
MAX_SCROLLS = int(os.getenv("MAX_SCROLLS", "30"))
SCROLL_PAUSE_MS = int(os.getenv("SCROLL_PAUSE_MS", "800"))
MAX_PAGES = int(os.getenv("MAX_PAGES", "50"))
ENABLE_URL_PAGINATION = os.getenv("ENABLE_URL_PAGINATION", "true").lower() == "true"

# Site configs
SITE_CONFIG_DIR = os.getenv("SITE_CONFIG_DIR", "crawler/site_configs")

# Insertion
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "500"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
