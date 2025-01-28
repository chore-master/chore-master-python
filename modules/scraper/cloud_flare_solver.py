# https://github.com/Xewdy444/CF-Clearance-Scraper/tree/playwright

from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from typing import Any, Iterable, Optional

from patchright.async_api import Cookie, Frame, async_playwright

from modules.utils.file_system_utils import FileSystemUtils

browser_args = [
    "--window-size=1300,570",
    "--window-position=000,000",
    "--disable-dev-shm-usage",
    "--no-sandbox",
    "--disable-web-security",
    "--disable-features=site-per-process",
    "--disable-setuid-sandbox",
    "--disable-accelerated-2d-canvas",
    "--no-first-run",
    "--no-zygote",
    "--use-gl=egl",
    "--disable-blink-features=AutomationControlled",
    "--disable-background-networking",
    "--enable-features=NetworkService,NetworkServiceInProcess",
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "--disable-breakpad",
    "--disable-client-side-phishing-detection",
    "--disable-component-extensions-with-background-pages",
    "--disable-default-apps",
    "--disable-extensions",
    "--disable-features=Translate",
    "--disable-hang-monitor",
    "--disable-ipc-flooding-protection",
    "--disable-popup-blocking",
    "--disable-prompt-on-repost",
    "--disable-renderer-backgrounding",
    "--disable-sync",
    "--force-color-profile=srgb",
    "--metrics-recording-only",
    "--enable-automation",
    "--password-store=basic",
    "--use-mock-keychain",
    "--hide-scrollbars",
    "--mute-audio",
]


class ChallengePlatform(Enum):
    """Cloudflare challenge platform types."""

    JAVASCRIPT = "non-interactive"
    MANAGED = "managed"
    INTERACTIVE = "interactive"


challenge_messages = {
    ChallengePlatform.JAVASCRIPT: "Solving Cloudflare challenge [JavaScript]...",
    ChallengePlatform.MANAGED: "Solving Cloudflare challenge [Managed]...",
    ChallengePlatform.INTERACTIVE: "Solving Cloudflare challenge [Interactive]...",
}


class CloudflareSolver:
    @staticmethod
    def extract_clearance_cookie(cookies: Iterable[Cookie]) -> Optional[Cookie]:
        """
        Extract the Cloudflare clearance cookie from a list of cookies.

        Parameters
        ----------
        cookies : Iterable[Cookie]
            List of cookies.

        Returns
        -------
        Optional[Cookie]
            The Cloudflare clearance cookie. Returns None if the cookie is not found.
        """
        for cookie in cookies:
            if cookie["name"] == "cf_clearance":
                return cookie

        return None

    def __init__(self, timeout: int = 300, is_debugging: bool = False):
        self._timeout = timeout
        self._is_debugging = is_debugging

    async def __aenter__(self) -> CloudflareSolver:
        self._playwright = await async_playwright().start()
        browser = await self._playwright.chromium.launch(
            headless=False, args=browser_args
        )
        context = await browser.new_context(user_agent=self.user_agent)
        context.set_default_timeout(self._timeout * 1000)
        self.page = await context.new_page()
        self._screenshot_count = 0
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self._playwright.stop()

    @property
    def user_agent(self) -> str:
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"

    async def _screenshot(self) -> str:
        if not self._is_debugging:
            return
        FileSystemUtils.ensure_directory("./screenshots")
        screenshot_path = f"./screenshots/screenshot_{self._screenshot_count}.png"
        self._log("screenshot_path", screenshot_path)
        await self.page.screenshot(path=screenshot_path)
        self._screenshot_count += 1
        return screenshot_path

    async def get_cookies(self) -> list[Cookie]:
        """The cookies from the current page."""
        return await self.page.context.cookies()

    async def detect_challenge(self) -> Optional[ChallengePlatform]:
        """
        Detect the Cloudflare challenge platform on the current page.

        Returns
        -------
        Optional[ChallengePlatform]
            The Cloudflare challenge platform.
        """
        html = await self.page.content()

        for platform in ChallengePlatform:
            if f"cType: '{platform.value}'" in html:
                return platform

        return None

    async def solve_challenge(self) -> None:
        """Solve the Cloudflare challenge on the current page."""
        verify_button_pattern = re.compile(
            "Verify (I am|you are) (not a bot|(a )?human)"
        )

        verify_button = self.page.get_by_role("button", name=verify_button_pattern)
        self._log("verify_button", verify_button)
        challenge_spinner = self.page.locator("#challenge-spinner")
        self._log("challenge_spinner", challenge_spinner)
        challenge_stage = self.page.locator("#challenge-stage")
        self._log("challenge_stage", challenge_stage)
        start_timestamp = datetime.now()

        while (
            self.extract_clearance_cookie(await self.get_cookies()) is None
            and await self.detect_challenge() is not None
            and (datetime.now() - start_timestamp).seconds < self._timeout
        ):
            self._log("@seconds", (datetime.now() - start_timestamp).seconds)
            if await challenge_spinner.is_visible():
                self._log("challenge_spinner", challenge_spinner)
                await self._screenshot()
                await challenge_spinner.wait_for(state="hidden")
                await self._screenshot()

            turnstile_frame = self._get_turnstile_frame()

            if await verify_button.is_visible():
                self._log("verify_button", verify_button)
                await self._screenshot()
                await verify_button.click()
                await self._screenshot()
                await challenge_stage.wait_for(state="hidden")
            elif turnstile_frame is not None:
                self._log("turnstile_frame", turnstile_frame)
                await self._screenshot()
                await self.page.mouse.click(210, 290)
                await self._screenshot()
                await challenge_stage.wait_for(state="hidden")

            await self.page.wait_for_timeout(5000)

    async def get_clearance_token(self, url: str) -> str:
        await self.page.goto(url)
        cookies = await self.get_cookies()
        self._log("cookies")
        self._log(cookies)
        clearance_cookie = self.extract_clearance_cookie(cookies)
        if clearance_cookie is None:
            challenge_platform = await self.detect_challenge()
            if challenge_platform is None:
                raise ValueError("No Cloudflare challenge detected.")
            self._log(challenge_messages[challenge_platform])
            await self.solve_challenge()
            cookies = await self.get_cookies()
            self._log("cookies")
            self._log(cookies)
            clearance_cookie = self.extract_clearance_cookie(cookies)
            if clearance_cookie is None:
                raise ValueError("Failed to retrieve a Cloudflare clearance cookie.")
        return clearance_cookie["value"]

    def _get_turnstile_frame(self) -> Optional[Frame]:
        """
        Get the Cloudflare turnstile frame.

        Returns
        -------
        Optional[Frame]
            The Cloudflare turnstile frame.
        """
        return self.page.frame(
            url=re.compile(
                "https://challenges.cloudflare.com/cdn-cgi/challenge-platform/h/[bg]/turnstile"
            ),
        )

    def _log(self, *args: Any):
        if not self._is_debugging:
            return
        print(*args)
