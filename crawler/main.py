from typing import Dict, List
from playwright.sync_api import sync_playwright
from crawler import config
from crawler.crawler.cashback import CashbackCrawler
from crawler.db import fetch_categories, get_connection, bulk_insert_campaigns
from crawler.utils.helpers import generate_crawl_id, hash_campaign_uid, random_delay
from crawler.utils.logger import setup_logger
from crawler.utils.site_config import load_site_config


def _dedupe_run(rows: List[Dict[str, object]], seen: set) -> List[Dict[str, object]]:
    unique = []
    for r in rows:
        raw = r.get("raw_json") or {}
        title = raw.get("title") or r.get("raw_campaign_name") or ""
        url = raw.get("url") or ""
        uid = hash_campaign_uid(title, url)
        if uid in seen:
            continue
        seen.add(uid)
        unique.append(r)
    return unique


def main() -> None:
    logger = setup_logger()
    crawl_id = generate_crawl_id()
    logger.info("Starting crawl: %s", crawl_id)

    conn = get_connection()
    categories = fetch_categories(conn)
    logger.info("Loaded %d categories", len(categories))

    seen = set()
    all_rows: List[Dict[str, object]] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config.HEADLESS)
        crawler = CashbackCrawler(browser)

        try:
            site_cache = {}
            for idx, category in enumerate(categories, 1):
                webpage_id = category["webpage_id"]
                if webpage_id not in site_cache:
                    site_cache[webpage_id] = load_site_config(webpage_id)
                site = site_cache[webpage_id]

                logger.info(
                    "[%d/%d] Crawling category %s (webpage_id=%s, site_config=%s)",
                    idx,
                    len(categories),
                    category["category_id"],
                    webpage_id,
                    site.source_path,
                )

                success = False
                for attempt in range(1, config.CATEGORY_RETRIES + 1):
                    try:
                        rows = crawler.crawl_category(category, site)
                        for r in rows:
                            r["crawl_id"] = crawl_id
                        rows = _dedupe_run(rows, seen)
                        all_rows.extend(rows)
                        if len(rows) == 0:
                            logger.warning(
                                "Category %s: no campaigns found",
                                category["category_id"],
                            )
                        else:
                            logger.info(
                                "Category %s: %d campaigns",
                                category["category_id"],
                                len(rows),
                            )
                        success = True
                        break
                    except Exception as exc:
                        logger.exception(
                            "Category %s failed (attempt %d/%d): %s",
                            category["category_id"],
                            attempt,
                            config.CATEGORY_RETRIES,
                            exc,
                        )
                        random_delay(config.DELAY_MIN_SEC, config.DELAY_MAX_SEC)

                if not success:
                    logger.error("Category %s skipped after retries", category["category_id"])

                random_delay(config.DELAY_MIN_SEC, config.DELAY_MAX_SEC)
        finally:
            crawler.close()
            browser.close()

    inserted = bulk_insert_campaigns(conn, all_rows, config.BATCH_SIZE)
    logger.info("Inserted %d rows", inserted)
    conn.close()


if __name__ == "__main__":
    main()
