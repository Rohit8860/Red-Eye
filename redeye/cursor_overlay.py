"""
Visible cursor overlay for RED-EYE pages.

`page.mouse.move()` aur Playwright clicks ke time pe humanize jo Bezier
trajectory waypoints fire karta hai — unhe ek orange circle ke roop mein
page pe dikhao. Camoufox style.

Usage:
    from redeye.cursor_overlay import attach_cursor

    async with AsyncRedEye(humanize=True) as browser:
        page = await browser.new_page()
        await attach_cursor(page)            # ek page pe
        # ya saare future pages pe:
        await attach_cursor(browser.contexts[0], persistent=True)
"""
from typing import Union

# Cursor overlay template. {fill}, {ring}, {glow}, {size} are formatted in.
# z-index max + pointer-events:none so it never interferes with the page.
_CURSOR_TEMPLATE = r"""
(() => {
  if (window.__redEyeCursor) {
    // already attached — just update style and exit
    const old = window.__redEyeCursor;
    old.style.width  = '{size}px';
    old.style.height = '{size}px';
    old.style.background = '{fill}';
    old.style.border = '2px solid {ring}';
    old.style.boxShadow = '0 0 8px {glow}';
    return;
  }
  const c = document.createElement('div');
  c.id = '__red_eye_cursor';
  c.style.cssText = [
    'position:fixed',
    'left:-100px', 'top:-100px',
    'width:{size}px', 'height:{size}px',
    'border-radius:50%',
    'background:{fill}',
    'border:2px solid {ring}',
    'box-shadow:0 0 8px {glow}',
    'pointer-events:none',
    'z-index:2147483647',
    'transform:translate(-50%,-50%)',
    'transition:none',
  ].join(';');
  const attach = () => {
    if (document.documentElement && !c.isConnected)
      document.documentElement.appendChild(c);
  };
  attach();
  new MutationObserver(attach).observe(document, {childList:true, subtree:true});
  document.addEventListener('mousemove', (e) => {
    c.style.left = e.clientX + 'px';
    c.style.top  = e.clientY + 'px';
  }, true);
  window.__redEyeCursor = c;
})();
"""

# Named presets — sirf yahan se add karo, attach_cursor(color="red") chalega
_PRESETS = {
    "orange": ("rgba(255,140,0,0.55)", "rgba(255,90,0,0.95)",  "rgba(255,140,0,0.6)"),
    "red":    ("rgba(255,60,60,0.55)", "rgba(220,20,20,0.95)", "rgba(255,60,60,0.6)"),
    "green":  ("rgba(60,220,90,0.55)", "rgba(20,170,40,0.95)", "rgba(60,220,90,0.6)"),
    "blue":   ("rgba(60,140,255,0.55)", "rgba(20,90,220,0.95)", "rgba(60,140,255,0.6)"),
    "yellow": ("rgba(255,220,30,0.6)",  "rgba(220,180,0,0.95)", "rgba(255,220,30,0.7)"),
    "purple": ("rgba(180,80,255,0.55)", "rgba(140,40,220,0.95)","rgba(180,80,255,0.6)"),
    "pink":   ("rgba(255,90,180,0.55)", "rgba(220,40,140,0.95)","rgba(255,90,180,0.6)"),
    "white":  ("rgba(255,255,255,0.7)", "rgba(60,60,60,0.95)",  "rgba(255,255,255,0.6)"),
    "black":  ("rgba(20,20,20,0.7)",   "rgba(0,0,0,0.95)",     "rgba(80,80,80,0.6)"),
}


def _build_script(color: str = "orange", size: int = 18) -> str:
    if color in _PRESETS:
        fill, ring, glow = _PRESETS[color]
    else:
        # Treat as a single CSS color literal — use it for all three.
        fill = ring = glow = color
    # .replace() not .format() — JS template has {...} blocks that .format()
    # would try to parse as placeholders and crash.
    return (_CURSOR_TEMPLATE
            .replace("{fill}", fill)
            .replace("{ring}", ring)
            .replace("{glow}", glow)
            .replace("{size}", str(int(size))))


async def attach_cursor(target, persistent: bool = False,
                        color: str = "orange", size: int = 18) -> None:
    """
    Attach a visible cursor overlay that follows mousemove events.

    Args:
        target:     A Playwright `Page` or `BrowserContext`.
        persistent: If True (only valid for BrowserContext), inject via
                    add_init_script so every future page gets the overlay
                    on navigation. If False, run once on the current page.
        color:      Preset name ('orange','red','green','blue','yellow',
                    'purple','pink','white','black') or any CSS color
                    string ('#ff00ff', 'rgba(...)', 'cyan', etc).
        size:       Diameter in pixels (default 18).
    """
    script = _build_script(color=color, size=size)
    if persistent:
        await target.add_init_script(script)
        return
    await target.evaluate(script)
