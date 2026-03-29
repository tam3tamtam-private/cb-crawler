from typing import Dict, List
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from crawler.crawler.base import BaseCrawler
from crawler.utils import helpers
from crawler.utils.site_config import SiteConfig
from crawler import config


class CashbackCrawler(BaseCrawler):
    def _wait_for_items(self, site: SiteConfig) -> None:
        for sel in [site.campaign_card]:
            try:
                self.page.wait_for_selector(
                    sel, timeout=config.BROWSER_TIMEOUT_MS, state="attached"
                )
                return
            except PlaywrightTimeoutError:
                continue
        raise PlaywrightTimeoutError(
            f"Campaign items not found (selector={site.campaign_card})"
        )

    def _find_campaign_items(self, site: SiteConfig):
        for sel in [site.campaign_card]:
            loc = self.page.locator(sel)
            if loc.count() > 0:
                return loc
        return self.page.locator(site.campaign_card)

    def _first_text(self, root, selectors: List[str]) -> str:
        for sel in selectors:
            loc = root.locator(sel).first
            if loc.count() == 0:
                continue
            text = loc.text_content()
            if text:
                return text.strip()
        return ""

    def _first_attr(self, root, selector: str, attribute: str) -> str:
        loc = root.locator(selector).first
        if loc.count() == 0:
            return ""
        value = loc.get_attribute(attribute)
        return value.strip() if value else ""

    def _first_url(self, root, site: SiteConfig) -> str:
        href = root.get_attribute(site.link_attribute)
        if href:
            return href.strip()

        value = self._first_attr(root, site.link_selector, site.link_attribute)
        if value:
            return value
        return ""

    def _is_disabled(self, loc) -> bool:
        aria = loc.get_attribute("aria-disabled")
        if aria and aria.lower() == "true":
            return True
        if loc.get_attribute("disabled") is not None:
            return True
        cls = (loc.get_attribute("class") or "").lower()
        return "disabled" in cls

    def _find_next_button(self, site: SiteConfig):
        selectors = [site.pagination_selector] if site.pagination_selector else []
        for sel in selectors:
            loc = self.page.locator(sel).first
            if loc.count() == 0:
                continue
            if loc.is_visible() and not self._is_disabled(loc):
                return loc
        return None

    def _scroll_to_load_all(self) -> None:
        prev_height = 0
        stable_rounds = 0
        for _ in range(config.MAX_SCROLLS):
            self.page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
            self.page.wait_for_timeout(config.SCROLL_PAUSE_MS)
            height = self.page.evaluate("() => document.body.scrollHeight")
            if height == prev_height:
                stable_rounds += 1
                if stable_rounds >= 2:
                    break
            else:
                stable_rounds = 0
            prev_height = height

    def _next_page_url(self, current_url: str, page_num: int) -> str:
        parsed = urlparse(current_url)
        qs = parse_qs(parsed.query)
        if "page" not in qs:
            return ""
        qs["page"] = [str(page_num)]
        new_query = urlencode(qs, doseq=True)
        return urlunparse(
            (parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment)
        )

    def _has_page_param(self, current_url: str) -> bool:
        parsed = urlparse(current_url)
        qs = parse_qs(parsed.query)
        return "page" in qs

    def _extract_campaigns(
        self, category: Dict[str, str], seen: set, site: SiteConfig
    ) -> List[Dict[str, object]]:
        items = self._find_campaign_items(site)
        count = items.count()
        results: List[Dict[str, object]] = []

        for i in range(count):
            el = items.nth(i)
            title = self._first_text(el, [site.title])
            reward = self._first_text(el, [site.reward])
            url = self._first_url(el, site)
            if url:
                url = urljoin(self.page.url, url)

            campaign_uid = helpers.hash_campaign_uid(title, url)
            if campaign_uid in seen:
                continue
            seen.add(campaign_uid)

            if not title:
                continue
            if not url:
                continue

            raw = {
                "webpage_id": category["webpage_id"],
                "category_id": category["category_id"],
                "title": title,
                "reward": reward,
                "url": url,
                "scraped_at": helpers.iso_timestamp(),
            }
            results.append(
                {
                    "raw_campaign_url": url,
                    "webpage_id": category["webpage_id"],
                    "category_id": category["category_id"],
                    "raw_campaign_name": title,
                    "raw_cb_value": reward,
                    "raw_json": raw,
                }
            )
        return results

    def crawl_category(
        self, category: Dict[str, str], site: SiteConfig
    ) -> List[Dict[str, object]]:
        self.page.goto(
            category["category_url"],
            timeout=config.NAVIGATION_TIMEOUT_MS,
            wait_until="domcontentloaded",
        )
        self._wait_for_items(site)

        results: List[Dict[str, object]] = []
        seen = set()

        next_button = self._find_next_button(site) if site.pagination_type == "next_button" else None
        if next_button is not None:
            pages = 0
            while True:
                page_rows = self._extract_campaigns(category, seen, site)
                if not page_rows:
                    break
                results.extend(page_rows)
                pages += 1
                if pages >= config.MAX_PAGES:
                    break

                next_button = self._find_next_button(site)
                if next_button is None:
                    break
                next_button.click()
                self.page.wait_for_load_state("networkidle", timeout=config.NAVIGATION_TIMEOUT_MS)
                helpers.random_delay(config.DELAY_MIN_SEC, config.DELAY_MAX_SEC)
        else:
            current_url = self.page.url
            if (
                site.pagination_type == "url_param"
                and config.ENABLE_URL_PAGINATION
                and self._has_page_param(current_url)
            ):
                pages = 1
                while True:
                    page_rows = self._extract_campaigns(category, seen, site)
                    if not page_rows:
                        break
                    results.extend(page_rows)
                    pages += 1
                    if pages > config.MAX_PAGES:
                        break
                    next_url = self._next_page_url(current_url, pages)
                    if not next_url:
                        break
                    try:
                        self.page.goto(
                            next_url,
                            timeout=config.NAVIGATION_TIMEOUT_MS,
                            wait_until="domcontentloaded",
                        )
                        self._wait_for_items(site)
                        helpers.random_delay(config.DELAY_MIN_SEC, config.DELAY_MAX_SEC)
                    except PlaywrightTimeoutError:
                        break
            else:
                if site.scroll and config.ENABLE_INFINITE_SCROLL:
                    self._scroll_to_load_all()
                results = self._extract_campaigns(category, seen, site)

        return results
