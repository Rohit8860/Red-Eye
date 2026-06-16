import asyncio
from functools import partial
from typing import Any, Dict, Optional, Union, overload

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    PlaywrightContextManager,
)
from typing_extensions import Literal

from .utils import launch_options as _launch_options
from .cursor_overlay import _build_script


class AsyncRedEye(PlaywrightContextManager):
    """
    Async context manager — launches RED-EYE and returns a Playwright Browser.

    Usage::

        async with AsyncRedEye(profile="path/to/profile.json") as browser:
            page = await browser.new_page()
            await page.goto("https://example.com")

        # Random profile + humanize cursor (cursor overlay auto-attached red):
        async with AsyncRedEye(humanize=True) as browser:
            page = await browser.new_page()
            await page.goto("...")    # Red cursor overlay visible — no setup needed
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
        humanize:           True/False/float to enable humanize cursor.
        cursor:             Visible cursor overlay control:
                              None (default) -> auto-on when humanize is on
                              True / preset name ('red','orange',...) / CSS color string -> force on
                              False -> force off
        cursor_size:        Cursor diameter in pixels (default 18).
        **kwargs:           Any other Playwright launch options.
    """
    # Extract RED-EYE-specific cursor settings (not Playwright opts).
    cursor = kwargs.pop("cursor", None)
    cursor_size = kwargs.pop("cursor_size", 18)
    humanize_enabled = bool(kwargs.get("humanize"))

    # When humanize is on, PageHandler.js renders the cursor chrome-side
    # automatically (cross-origin iframe safe — page-level overlays can't
    # track mousemove inside cross-origin iframes due to Same-Origin Policy).
    # cursor=None defaults to off; user can still force a page-level overlay
    # with cursor="red" if they want a second cursor for some reason.
    if cursor is None:
        cursor = False
    elif cursor is True:
        cursor = "red"

    if not from_options:
        from_options = await asyncio.get_event_loop().run_in_executor(
            None, partial(_launch_options, **kwargs)
        )

    if persistent_context:
        result = await playwright.firefox.launch_persistent_context(**from_options)
    else:
        result = await playwright.firefox.launch(**from_options)

    # Always default no_viewport=True on new_page/new_context — prevents the
    # Juggler resize-delta bug that shrunk the browser ~240 px each launch.
    # Fixed earlier in PyPI red-eye-browser 1.0.3, regressed.
    _apply_no_viewport_default(result)

    if cursor:
        _wrap_for_auto_cursor(result, color=str(cursor), size=int(cursor_size))

    return result


def _apply_no_viewport_default(target) -> None:
    """Wrap new_context/new_page to default no_viewport=True when caller
    didn't explicitly pass viewport / no_viewport. Fixes shrinking-window bug."""
    def _ensure_no_viewport(kwargs):
        if "viewport" not in kwargs and "no_viewport" not in kwargs:
            kwargs["no_viewport"] = True
        return kwargs

    if isinstance(target, Browser):
        _orig_new_context = target.new_context
        _orig_new_page = target.new_page

        async def patched_new_context(*args, **kwargs):
            return await _orig_new_context(*args, **_ensure_no_viewport(kwargs))

        async def patched_new_page(*args, **kwargs):
            return await _orig_new_page(*args, **_ensure_no_viewport(kwargs))

        target.new_context = patched_new_context  # type: ignore
        target.new_page = patched_new_page  # type: ignore


def _wrap_for_auto_cursor(target, color: str, size: int) -> None:
    """
    Patch new_page / new_context to auto-inject the cursor overlay.
    no_viewport defaulting is handled separately by _apply_no_viewport_default.
    """
    script = _build_script(color=color, size=size)

    if isinstance(target, Browser):
        _orig_new_context = target.new_context
        _orig_new_page = target.new_page

        async def patched_new_context(*args, **kwargs):
            ctx = await _orig_new_context(*args, **kwargs)
            await ctx.add_init_script(script)
            _patch_context_new_page(ctx, script)
            return ctx

        async def patched_new_page(*args, **kwargs):
            page = await _orig_new_page(*args, **kwargs)
            await page.context.add_init_script(script)
            try:
                await page.evaluate(script)
            except Exception:
                pass
            return page

        target.new_context = patched_new_context  # type: ignore
        target.new_page = patched_new_page  # type: ignore

    elif isinstance(target, BrowserContext):
        _patch_context_new_page(target, script)
        asyncio.create_task(target.add_init_script(script))


def _patch_context_new_page(ctx: BrowserContext, script: str) -> None:
    _orig = ctx.new_page

    async def patched_new_page(*args, **kwargs):
        page = await _orig(*args, **kwargs)
        try:
            await page.evaluate(script)
        except Exception:
            pass
        return page

    ctx.new_page = patched_new_page  # type: ignore
