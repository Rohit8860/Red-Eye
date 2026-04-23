# Red-Eye Browser

Anti-fingerprinting browser automation library built on a custom Firefox 140 binary.

## What is Red-Eye?

Red-Eye is a custom Firefox fork that spoofs browser fingerprints based on a JSON profile.
The browser runs on Windows but can impersonate macOS, Linux, or Windows profiles —
showing only the fonts, GPU, timezone, locale, and navigator data defined in the profile.

## Fingerprints Spoofed

| Fingerprint | Details |
|---|---|
| **User-Agent** | Full UA string from profile |
| **Navigator** | `platform`, `hardwareConcurrency`, `deviceMemory`, `maxTouchPoints`, `languages`, `language` |
| **Screen** | `width`, `height`, `availWidth`, `availHeight`, `colorDepth`, `innerWidth`, `innerHeight`, `outerWidth`, `outerHeight` |
| **Fonts** | System fonts isolated — web sees only profile fonts (macOS 17/51, Linux 7-8/51, Windows 7-10/51 in CreepJS) |
| **WebGL** | `vendor`, `renderer`, `version`, `shadingLanguageVersion`, unmasked vendor/renderer, extension list |
| **Canvas** | Text metrics rounded to prevent font fingerprinting |
| **Timezone** | ICU-level override — affects `Intl.DateTimeFormat`, `Date`, all JS time APIs |
| **Locale** | `Accept-Language` header + `navigator.languages` consistent |
| **HTTP Headers** | `User-Agent` header matches `navigator.userAgent` |
| **CSS Media** | `prefers-color-scheme`, `pointer`, `hover` from profile |
| **Math.random** | Seed influenced by profile hash |
| **Worker Navigator** | Same spoofing as main thread |
| **SVG Text** | Metrics rounded (same as Canvas 2D) |

## Installation

```bash
pip install red-eye-browser
redeye install
```

## Usage

### Async

```python
import asyncio
from redeye import AsyncRedEye

async def main():
    async with AsyncRedEye() as browser:
        page = await browser.new_page()
        await page.goto("https://example.com")

asyncio.run(main())
```

### Sync

```python
from redeye import RedEye

with RedEye() as browser:
    page = browser.new_page()
    page.goto("https://example.com")
```

### With Proxy

```python
from redeye import AsyncRedEye

async with AsyncRedEye(proxy={
    "server": "http://host:port",
    "username": "user",
    "password": "pass"
}) as browser:
    page = await browser.new_page()
    await page.goto("https://example.com")
```

### Persistent Context

```python
import tempfile
from redeye import AsyncRedEye

async with AsyncRedEye(
    persistent_context=True,
    user_data_dir=tempfile.mkdtemp(),
    proxy={"server": "http://host:port", "username": "user", "password": "pass"}
) as context:
    page = context.pages[0]
    await page.goto("https://example.com")
```

## CLI Commands

```bash
redeye install              # Latest browser binary download karo
redeye install 1.0.0        # Specific version
redeye status               # Installed version check karo
redeye uninstall            # Browser binary remove karo
```

## Profile System

Each profile is a JSON file containing fingerprint data:
- **Windows profiles** — impersonate Windows machine
- **macOS profiles** — impersonate macOS machine  
- **Linux profiles** — impersonate Linux machine

50+ pre-built profiles included. Custom profiles supported.

## Author

Rohit Prajapati — prajapatirohit8860@gmail.com
