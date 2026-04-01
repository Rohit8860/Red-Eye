"""
IP-based timezone detection for RED-EYE browser.
Multiple API fallbacks — if one fails, next try hota hai.
"""

import urllib.request
import json
from typing import Optional


def get_timezone_for_ip(ip: Optional[str] = None, fallback: Optional[str] = None) -> Optional[str]:
    """
    IP ke liye IANA timezone string return karta hai.

    Args:
        ip:       IP address. None doge toh current public IP use hogi.
        fallback: Agar sab APIs fail ho jaayein toh ye value return hogi.
                  Profile ki default timezone yahan pass karo.

    Returns:
        Timezone string jaise "America/New_York",
        ya fallback agar sab fail ho jaaye.
    """
    _ip = ip or ""

    # --- Fallback 1: ip-api.com ---
    try:
        url = f"http://ip-api.com/json/{_ip}?fields=status,timezone"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        if data.get("status") == "success" and data.get("timezone"):
            return data["timezone"]
    except Exception:
        pass

    # --- Fallback 2: ipinfo.io ---
    try:
        url = f"https://ipinfo.io/{_ip}/json"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        if data.get("timezone"):
            return data["timezone"]
    except Exception:
        pass

    # --- Fallback 3: worldtimeapi.org ---
    try:
        url = f"http://worldtimeapi.org/api/ip/{_ip}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        if data.get("timezone"):
            return data["timezone"]
    except Exception:
        pass

    return fallback
