"""
RED-EYE Async Example
Usage: python example_async.py
"""
import asyncio
from redeye import AsyncRedEye


async def main():
    # ── Random profile (auto-picked) ─────────────────────────────────────────
    async with AsyncRedEye() as browser:
        page = await browser.new_page()
        await page.goto("https://abrahamjuliot.github.io/creepjs/")
        await page.wait_for_timeout(5000)
        print("Title:", await page.title())
        await page.wait_for_timeout(30000)  # 30s to observe results


    # ── Specific profile ─────────────────────────────────────────────────────
    # async with AsyncRedEye(profile="path/to/profile.json") as browser:
    #     page = await browser.new_page()
    #     await page.goto("https://example.com")

    # ── With proxy ───────────────────────────────────────────────────────────
    # async with AsyncRedEye(proxy={"server": "http://host:port", "username": "user", "password": "pass"}) as browser:
    #     page = await browser.new_page()
    #     await page.goto("https://example.com")


asyncio.run(main())
