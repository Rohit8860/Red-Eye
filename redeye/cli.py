"""
redeye CLI — browser binary install/manage karna

Usage:
    redeye install          # latest release download karo
    redeye install 1.2.0    # specific version
    redeye status           # installed version check karo
    redeye uninstall        # browser binary remove karo
"""

import argparse
import hashlib
import json
import os
import platform
import shutil
import sys
import tempfile
import urllib.request
import zipfile
import tarfile
from pathlib import Path

GITHUB_REPO   = "Rohit8860/Red-Eye"
REDEYE_HOME   = Path.home() / ".redeye"

# --- Install access gate -------------------------------------------------
# Binary install ke liye ek code chahiye: `redeye install <code>`.
# Plaintext code yahan KABHI store nahi hota — sirf salted SHA-256 digest.
_INSTALL_CODE_SALT = "red-eye-install::"
_INSTALL_CODE_HASH = "e44d618048aaf0e43dbe53a50ab86677e3900376aae5ed2408cc7724867a90dc"
_INSTALL_CODE_MSG  = (
    "An installation code is required to install the Red-Eye binary.\n"
    "Please contact Rohit Prajapati - he will provide a code for binary installation.\n"
    "\n"
    "    Usage: redeye install <code>"
)


def _check_install_code(code) -> None:
    """Code valid hai ya nahi verify karo; warna message dikhakar exit."""
    if not code or hashlib.sha256(
        (_INSTALL_CODE_SALT + str(code)).encode("utf-8")
    ).hexdigest() != _INSTALL_CODE_HASH:
        print(_INSTALL_CODE_MSG)
        sys.exit(1)
BROWSER_DIR   = REDEYE_HOME / "browser"
VERSION_FILE  = REDEYE_HOME / "version.json"


def _get_platform_asset() -> str:
    """OS ke hisaab se GitHub Release asset name return karo."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "windows":
        return "red-eye-windows.zip"
    elif system == "darwin":
        if "arm" in machine or "aarch64" in machine:
            return "red-eye-macos-arm64.tar.gz"
        return "red-eye-macos-x64.tar.gz"
    elif system == "linux":
        if "arm" in machine or "aarch64" in machine:
            return "red-eye-linux-arm64.tar.gz"
        return "red-eye-linux-x64.tar.gz"
    else:
        print(f"Unsupported platform: {system}")
        sys.exit(1)


def _get_latest_version() -> str:
    """GitHub API se latest release version fetch karo."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    req = urllib.request.Request(url, headers={"User-Agent": "redeye-cli"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
            return data["tag_name"]
    except Exception as e:
        print(f"Could not fetch latest version: {e}")
        sys.exit(1)


def _get_installed_version() -> str | None:
    """Installed version return karo, None agar installed nahi hai."""
    if VERSION_FILE.exists():
        try:
            return json.loads(VERSION_FILE.read_text()).get("version")
        except Exception:
            pass
    return None


def _download_with_progress(url: str, dest: Path) -> None:
    """File download karo progress bar ke saath."""
    req = urllib.request.Request(url, headers={"User-Agent": "redeye-cli"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            total = int(r.headers.get("Content-Length", 0))
            downloaded = 0
            chunk_size = 1024 * 512  # 512KB chunks

            with open(dest, "wb") as f:
                while True:
                    chunk = r.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = downloaded / total * 100
                        mb = downloaded / 1024 / 1024
                        total_mb = total / 1024 / 1024
                        print(f"\r  Downloading... {mb:.1f}/{total_mb:.1f} MB ({pct:.0f}%)", end="", flush=True)
            print()
    except Exception as e:
        print(f"\nDownload failed: {e}")
        sys.exit(1)


def cmd_install(code: str | None = None, version: str | None = None) -> None:
    """Browser binary install karo (access code required)."""
    _check_install_code(code)

    if version is None:
        print("Fetching latest version...")
        version = _get_latest_version()

    installed = _get_installed_version()
    if installed == version:
        print(f"Red-Eye {version} already installed.")
        return

    asset    = _get_platform_asset()
    url      = f"https://github.com/{GITHUB_REPO}/releases/download/{version}/{asset}"

    print(f"Installing Red-Eye {version} ({platform.system()})...")
    print(f"Downloading: {asset}")

    # Temp dir mein download karo
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp) / asset
        _download_with_progress(url, tmp_path)

        # Purani binary remove karo
        if BROWSER_DIR.exists():
            shutil.rmtree(BROWSER_DIR)
        BROWSER_DIR.mkdir(parents=True, exist_ok=True)

        # Extract karo
        print("  Extracting...")
        if asset.endswith(".zip"):
            with zipfile.ZipFile(tmp_path) as zf:
                zf.extractall(BROWSER_DIR)
        else:
            with tarfile.open(tmp_path) as tf:
                tf.extractall(BROWSER_DIR)

        # Linux/macOS pe executable permission do
        if platform.system() != "Windows":
            binary = BROWSER_DIR / "red-eye"
            if binary.exists():
                binary.chmod(0o755)

    # Version file save karo
    REDEYE_HOME.mkdir(parents=True, exist_ok=True)
    VERSION_FILE.write_text(json.dumps({"version": version}))

    print(f"Red-Eye {version} installed successfully!")
    print(f"Location: {BROWSER_DIR}")


def cmd_status() -> None:
    """Installed version aur path dikhao."""
    version = _get_installed_version()
    if version:
        binary = BROWSER_DIR / "bin" / ("red-eye.exe" if os.name == "nt" else "red-eye")
        exists = binary.exists()
        print(f"Red-Eye version : {version}")
        print(f"Location        : {BROWSER_DIR}")
        print(f"Binary found    : {'Yes' if exists else 'No (reinstall karo)'}")
    else:
        print("Red-Eye is not installed. Run: redeye install")


def cmd_uninstall() -> None:
    """Browser binary remove karo."""
    if BROWSER_DIR.exists():
        shutil.rmtree(BROWSER_DIR)
        print(f"Removed: {BROWSER_DIR}")
    if VERSION_FILE.exists():
        VERSION_FILE.unlink()
    print("Red-Eye uninstalled.")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="redeye",
        description="Red-Eye browser manager",
    )
    sub = parser.add_subparsers(dest="command")

    # install
    p_install = sub.add_parser("install", help="Browser binary install karo (code required)")
    p_install.add_argument("code", nargs="?", default=None,
                           help="Installation code (contact Rohit Prajapati)")
    p_install.add_argument("version", nargs="?", default=None,
                           help="Version to install (default: latest)")

    # status
    sub.add_parser("status", help="Installed version check karo")

    # uninstall
    sub.add_parser("uninstall", help="Browser binary remove karo")

    args = parser.parse_args()

    if args.command == "install":
        cmd_install(args.code, args.version)
    elif args.command == "status":
        cmd_status()
    elif args.command == "uninstall":
        cmd_uninstall()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
