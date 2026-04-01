import asyncio
from functools import partial
from typing import Any, Dict, Optional, Union, overload

from playwright.async_api import (
    Browser,
    BrowserContext,
    Playwright,
    PlaywrightContextManager,
)
from typing_extensions import Literal

from .utils import launch_options as _launch_options


class AsyncRedEye(PlaywrightContextManager):
    """
    Async context manager — launches RED-EYE and returns a Playwright Browser.

    Usage::

        async with AsyncRedEye(profile="path/to/profile.json") as browser:
            page = await browser.new_page()
            await page.goto("https://example.com")

        # Random profile:
        async with AsyncRedEye() as browser:
            ...
    """

    def __init__(self, **kwargs: Any):
        super().__init__()
        self._kwargs = kwargs
        self.browser: Optional[Union[Browser, BrowserContext]] = None

    async def __aenter__(self) -> Union[Browser, BrowserContext]:
        _playwright = await super().__aenter__()
        self.browser = await AsyncNewBrowser(_playwright, **self._kwargs)
        return self.browser

    async def __aexit__(self, *args: Any) -> None:
        if self.browser:
            await self.browser.close()
        await super().__aexit__(*args)


@overload
async def AsyncNewBrowser(
    playwright: Playwright,
    *,
    from_options: Optional[Dict[str, Any]] = None,
    persistent_context: Literal[False] = False,
    **kwargs: Any,
) -> Browser: ...


@overload
async def AsyncNewBrowser(
    playwright: Playwright,
    *,
    from_options: Optional[Dict[str, Any]] = None,
    persistent_context: Literal[True],
    **kwargs: Any,
) -> BrowserContext: ...


async def AsyncNewBrowser(
    playwright: Playwright,
    *,
    from_options: Optional[Dict[str, Any]] = None,
    persistent_context: bool = False,
    **kwargs: Any,
) -> Union[Browser, BrowserContext]:
    """
    Async version — launches a RED-EYE browser.

    Parameters:
        playwright:         Playwright instance from async_playwright().
        from_options:       Pre-built dict from launch_options(). All other
                            kwargs ignored when this is provided.
        persistent_context: Return a BrowserContext instead of Browser.
        profile:            Path/dict for a RED-EYE profile JSON.
                            Omit to auto-pick a random profile.
        headless:           Run headless (default False).
        proxy:              Playwright proxy dict.
        **kwargs:           Any other Playwright launch options.
    """
    if not from_options:
        from_options = await asyncio.get_event_loop().run_in_executor(
            None, partial(_launch_options, **kwargs)
        )

    if persistent_context:
        return await playwright.firefox.launch_persistent_context(**from_options)
    return await playwright.firefox.launch(**from_options)
