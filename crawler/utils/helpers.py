import hashlib
import random
import time
from datetime import datetime, timezone
from uuid import uuid4


def generate_crawl_id() -> str:
    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y%m%d_%H%M%S")
    suffix = uuid4().hex[:8]
    return f"run_{ts}_{suffix}"


def hash_campaign_uid(title: str, url: str) -> str:
    data = (title or "") + "|" + (url or "")
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def iso_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def random_delay(min_sec: float, max_sec: float) -> None:
    if max_sec <= 0:
        return
    time.sleep(random.uniform(min_sec, max_sec))
