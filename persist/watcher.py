import time
from pathlib import Path

from core.logger import logger
from core import usb

_last_seen: set[str] = set()


def _key(p: Path) -> str:
    try:
        return f"{p}:{usb.volume_label(p)}"
    except Exception:
        return str(p)


def watch(interval: int = 5) -> None:
    logger.info("usb watcher started")
    while True:
        try:
            drives = usb.list_removable()
            current = {_key(d) for d in drives}
            new = current - _last_seen
            if new:
                logger.info(f"new usb: {new}")
                for d in drives:
                    if _key(d) in new:
                        try:
                            from main import harvest_on_usb
                            harvest_on_usb(d)
                        except Exception as e:
                            logger.error(f"harvest on {d}: {e}")
            _last_seen = current
        except Exception as e:
            logger.error(f"watcher: {e}")
        time.sleep(interval)
