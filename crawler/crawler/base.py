from pathlib import Path
from playwright.sync_api import Browser, Page
from crawler import config


class BaseCrawler:
    def __init__(self, browser: Browser):
        self.browser = browser
        self.context = self.browser.new_context()
        self.page: Page = self.context.new_page()
        self.page.set_default_timeout(config.BROWSER_TIMEOUT_MS)

    def close(self) -> None:
        try:
            self.page.close()
        finally:
            self.context.close()

    def capture_failure_screenshot(self, category_id: str, attempt: int) -> str | None:
        output_dir = Path(config.FAILURE_SCREENSHOT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        safe_category_id = str(category_id).replace("/", "_")
        path = output_dir / f"{safe_category_id}_attempt_{attempt}.png"
        self.page.screenshot(path=str(path), full_page=True)
        return str(path)
