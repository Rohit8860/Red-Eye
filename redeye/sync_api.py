from typing import Any, Dict, Optional, Union, overload

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Playwright,
    PlaywrightContextManager,
)
from typing_extensions import Literal

from .utils import launch_options as _launch_options


class RedEye(PlaywrightContextManager):
    """
    Sync context manager — launches RED-EYE and returns a Playwright Browser.

    Usage::

        with RedEye(profile="path/to/profile.json") as browser:
            page = browser.new_page()
            page.goto("https://example.com")

        # Random profile:
        with RedEye() as browser:
            ...
    """

    def __init__(self, **kwargs: Any):
        super().__init__()
        self._kwargs = kwargs
        self.browser: Optional[Union[Browser, BrowserContext]] = None

    def __enter__(self) -> Union[Browser, BrowserContext]:
        super().__enter__()
        self.browser = NewBrowser(self._playwright, **self._kwargs)
        return self.browser

    def __exit__(self, *args: Any) -> None:
        if self.browser:
            self.browser.close()
        super().__exit__(*args)


@overload
def NewBrowser(
    playwright: Playwright,
    *,
    from_options: Optional[Dict[str, Any]] = None,
    persistent_context: Literal[False] = False,
    **kwargs: Any,
) -> Browser: ...


@overload
def NewBrowser(
    playwright: Playwright,
    *,
    from_options: Optional[Dict[str, Any]] = None,
    persistent_context: Literal[True],
    **kwargs: Any,
) -> BrowserContext: ...


def NewBrowser(
    playwright: Playwright,
    *,
    from_options: Optional[Dict[str, Any]] = None,
    persistent_context: bool = False,
    **kwargs: Any,
) -> Union[Browser, BrowserContext]:
    """
    Launches a RED-EYE browser.

    Parameters:
        playwright:         Playwright instance from sync_playwright().
        from_options:       Pre-built dict from launch_options(). All other
                            kwargs ignored when this is provided.
        persistent_context: Return a BrowserContext instead of Browser.
        profile:            Path/dict for a RED-EYE profile JSON.
                            Omit to auto-pick a random profile.
        headless:           Run headless (default False).
        proxy:              Playwright proxy dict.
        **kwargs:           Any other Playwright launch options.
    """
    options = from_options or _launch_options(**kwargs)

    if persistent_context:
        return playwright.firefox.launch_persistent_context(**options)
    return playwright.firefox.launch(**options)
