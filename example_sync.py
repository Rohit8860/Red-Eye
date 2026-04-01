"""
RED-EYE Sync Example
Usage: python example_sync.py
"""
from redeye import RedEye


# ── Random profile (auto-picked) ─────────────────────────────────────────────
with RedEye() as browser:
    page = browser.new_page()
    page.goto("https://abrahamjuliot.github.io/creepjs/")
    page.wait_for_timeout(5000)
    print("Title:", page.title())
    page.wait_for_timeout(30000)  # 30s to observe results

# ── Specific profile ──────────────────────────────────────────────────────────
# with RedEye(profile="path/to/profile.json") as browser:
#     page = browser.new_page()
#     page.goto("https://example.com")

# ── With proxy ────────────────────────────────────────────────────────────────
# with RedEye(proxy={"server": "http://host:port", "username": "user", "password": "pass"}) as browser:
#     page = browser.new_page()
#     page.goto("https://example.com")
