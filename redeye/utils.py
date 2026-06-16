import json
import os
import random
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Browser binary: ~/.redeye/browser/  (redeye install se aata hai)
# Profiles: package ke saath bundle hain (redeye/profiles/)
_REDEYE_HOME = Path.home() / ".redeye"
_BIN_DIR     = _REDEYE_HOME / "browser"

if os.name == "nt":  # Windows
    DEFAULT_EXECUTABLE = _BIN_DIR / "bin" / "red-eye.exe"
else:                # Linux / macOS
    DEFAULT_EXECUTABLE = _BIN_DIR / "bin" / "red-eye"

DEFAULT_PROFILES_DIR = Path(__file__).resolve().parent / "profiles"


def _load_profile(profile: Union[str, Path, Dict[str, Any]]) -> Dict[str, Any]:
    if isinstance(profile, dict):
        return profile
    with open(profile, "r", encoding="utf-8") as f:
        return json.load(f)


def get_random_profile(profiles_dir: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """Returns a randomly chosen profile from the profiles directory."""
    dir_path = Path(profiles_dir) if profiles_dir else DEFAULT_PROFILES_DIR
    profile_files = list(dir_path.glob("*.json"))
    if not profile_files:
        raise FileNotFoundError(f"No profile JSON files found in: {dir_path}")
    return _load_profile(random.choice(profile_files))


def launch_options(
    *,
    profile: Optional[Union[str, Path, Dict[str, Any]]] = None,
    profiles_dir: Optional[Union[str, Path]] = None,
    executable_path: Optional[Union[str, Path]] = None,
    headless: Optional[bool] = None,
    firefox_user_prefs: Optional[Dict[str, Any]] = None,
    args: Optional[List[str]] = None,
    env: Optional[Dict[str, Union[str, float, bool]]] = None,
    proxy: Optional[Dict[str, str]] = None,
    humanize: Union[bool, float, None] = None,
    humanize_min_time: Optional[float] = None,
    humanize_max_time: Optional[float] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Builds Playwright Firefox launch options for RED-EYE.

    Parameters:
        profile:          Profile JSON path, Path, or dict.
                          If None, a random profile is picked from profiles_dir.
        profiles_dir:     Where to pick random profiles from.
                          Defaults to <bin>/profiles/browserforge_auto/
        executable_path:  Path to red-eye.exe.
                          Defaults to <bin>/red-eye.exe (auto-resolved).
        headless:         Run headless. Defaults to False.
        firefox_user_prefs: Extra Firefox prefs.
        args:             Extra browser args.
        env:              Extra environment variables.
        proxy:            Playwright proxy dict (server, username, password).
        humanize:         Enable human-like Bezier cursor trajectory for
                          Page.dispatchMouseEvent mousemove. Pass True/False
                          to toggle, or a float to enable and set the max
                          movement duration in seconds (e.g. humanize=1.5).
        humanize_min_time: Min cursor movement duration in seconds (default 0).
        humanize_max_time: Max cursor movement duration in seconds (default 1.5).
        **kwargs:         Any additional Playwright launch options.
    """
    profile_data = _load_profile(profile) if profile is not None else get_random_profile(profiles_dir)

    # RED-EYE humanize cursor — inject into profile JSON so the C++ side
    # (RedEyeConfig::Init + ChromeUtils.redEyeGetBool) picks it up.
    if humanize is not None:
        if isinstance(humanize, bool):
            profile_data["humanize"] = humanize
        else:
            profile_data["humanize"] = True
            profile_data["humanize:maxTime"] = float(humanize)
    if humanize_min_time is not None:
        profile_data["humanize:minTime"] = float(humanize_min_time)
    if humanize_max_time is not None:
        profile_data["humanize:maxTime"] = float(humanize_max_time)

    if headless is None:
        headless = False
    if firefox_user_prefs is None:
        firefox_user_prefs = {}
    if args is None:
        args = []

    # Serialize profile JSON
    profile_json = json.dumps(profile_data, ensure_ascii=False)

    # Build env: start from current process env, then overlay RED_EYE vars
    env_vars: Dict[str, str] = dict(os.environ)

    # Windows Playwright pipe limit: ~2047 chars per env var value.
    # Split large JSON into chunks: RED_EYE_CONFIG_JSON_1, _2, _3, ...
    # C++ code reassembles them in order. For small profiles pass as single var.
    _CHUNK = 2047
    chunks = [profile_json[i:i+_CHUNK] for i in range(0, len(profile_json), _CHUNK)]
    if len(chunks) == 1:
        env_vars["RED_EYE_CONFIG_JSON"] = chunks[0]
    else:
        for idx, chunk in enumerate(chunks, start=1):
            env_vars[f"RED_EYE_CONFIG_JSON_{idx}"] = chunk

    # User-supplied env overrides
    if env:
        env_vars.update({str(k): str(v) for k, v in env.items()})

    exe = str(executable_path or DEFAULT_EXECUTABLE)

    result: Dict[str, Any] = {
        "executable_path": exe,
        "headless": headless,
        "args": args,
        "env": env_vars,
        "firefox_user_prefs": firefox_user_prefs,
        **kwargs,
    }

    if proxy is not None:
        result["proxy"] = proxy

    return result
