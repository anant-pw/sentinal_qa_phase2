from playwright.sync_api import Page, expect
from loguru import logger

LOAD_TIMEOUT = 30000  # 30s — safe for public demo environments

class ActionRegistry:
    @staticmethod
    def navigate(page: Page, data: str):
        logger.info(f"Navigating to: {data}")
        page.goto(data)
        # Wait for network to settle before any further actions.
        # Prevents race conditions on SPA navigation (e.g. OrangeHRM React shell).
        page.wait_for_load_state("networkidle", timeout=LOAD_TIMEOUT)
        logger.info("Page stable (networkidle)")

    @staticmethod
    def type(page: Page, selector: str, data: str):
        logger.info(f"Typing '{data}' into {selector}")
        # Ensure element is in DOM and visible before filling
        page.wait_for_selector(selector, state="visible", timeout=LOAD_TIMEOUT)
        page.locator(selector).fill(str(data))

    @staticmethod
    def click(page: Page, selector: str, data: str = None):
        logger.info(f"Clicking on: {selector}")
        # Ensure element is clickable before interacting
        page.wait_for_selector(selector, state="visible", timeout=LOAD_TIMEOUT)
        page.locator(selector).click()

    @staticmethod
    def verify_text(page: Page, selector: str, data: str):
        logger.info(f"Verifying text '{data}' in {selector}")
        # Wait for element to appear — critical after post-login SPA redirect
        page.wait_for_selector(selector, state="visible", timeout=LOAD_TIMEOUT)
        expect(page.locator(selector)).to_contain_text(data)