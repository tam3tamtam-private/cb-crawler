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
