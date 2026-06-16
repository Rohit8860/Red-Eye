"""
iframe-aware click for RED-EYE.

Playwright's `frame_locator(...).locator(...).click()` times out in RED-EYE
for cross-origin (OOPIF) iframes (hCaptcha, reCAPTCHA, embedded payment).
See `feedback_iframe_oopif_limitation` memory note.

This helper clicks the iframe AREA on the parent page using
`page.mouse.click()`. The browser's hit-testing routes the synthetic
mouse event into the iframe content naturally — same path a real user
takes. No contentDocument access required (which fails for cross-origin),
no Playwright frame_locator needed.

Anti-bot view:
  - humanize Bezier mousemove to the target (visible curve, page-side
    mousemove events on parent page leading up to the click)
  - real mousedown + mouseup dispatched at the target viewport coords
  - iframe receives the click via browser hit-testing — same as a human

Usage::

    from redeye.iframe_click import iframe_click

    # Click center of an hCaptcha checkbox iframe
    await iframe_click(page, 'iframe[src*="hcaptcha"]')

    # Click an offset inside the iframe (anchored top-left of iframe rect)
    await iframe_click(
        page,
        'iframe[src*="hcaptcha"]',
        offset_x=30,    # 30 px from iframe left (where the checkbox sits)
        offset_y=None,  # vertical center
    )
"""
import asyncio
from typing import Optional


async def iframe_click(
    page,
    iframe_selector: str,
    *,
    iframe_index: int = 0,
    offset_x: Optional[float] = None,
    offset_y: Optional[float] = None,
    pre_click_delay_ms: int = 600,
) -> None:
    """
    Humanely move + click inside an iframe area on the parent page.

    The click point defaults to the iframe's center. Pass offset_x / offset_y
    in pixels relative to the iframe's top-left corner to target a specific
    location inside the iframe (e.g. the hCaptcha checkbox is ~30px from the
    iframe's left edge, vertically centered).

    Args:
        page:               Playwright Page.
        iframe_selector:    CSS selector for the iframe on the parent page.
        iframe_index:       If multiple iframes match, which one (default 0).
        offset_x:           X offset inside iframe (None = center).
        offset_y:           Y offset inside iframe (None = center).
        pre_click_delay_ms: Pause between humanize move and click (default 600).
    """
    rect = await page.evaluate(
        """([sel, idx]) => {
            const list = document.querySelectorAll(sel);
            if (!list || list.length <= idx) return null;
            const ifr = list[idx];
            const r = ifr.getBoundingClientRect();
            return { x: r.left, y: r.top, w: r.width, h: r.height };
        }""",
        [iframe_selector, iframe_index],
    )
    if not rect or rect["w"] == 0 or rect["h"] == 0:
        raise RuntimeError(f"iframe_click: iframe not found / zero-sized "
                           f"for selector {iframe_selector!r}")

    target_x = rect["x"] + (offset_x if offset_x is not None else rect["w"] / 2)
    target_y = rect["y"] + (offset_y if offset_y is not None else rect["h"] / 2)

    # Humanize mousemove to target — fires Bezier trajectory.
    await page.mouse.move(target_x, target_y)

    if pre_click_delay_ms > 0:
        await asyncio.sleep(pre_click_delay_ms / 1000.0)

    # Synthetic click at viewport coords — browser routes to iframe content
    # via hit-testing, same as a real user click.
    await page.mouse.click(target_x, target_y)
