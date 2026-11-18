import ctypes
import os
import platform
import socket
import uuid
from pathlib import Path

import winreg


def hostname() -> str:
    return socket.gethostname()


def _machine_guid() -> str:
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Cryptography",
            0,
            winreg.KEY_READ | winreg.KEY_WOW64_64KEY,
        )
        val, _ = winreg.QueryValueEx(key, "MachineGuid")
        winreg.CloseKey(key)
        return val
    except Exception:
        return "unknown"


def _volume_serial() -> str:
    try:
        serial = ctypes.c_ulong(0)
        ctypes.windll.kernel32.GetVolumeInformationW(
            "C:\\", None, 0, ctypes.byref(serial), None, None, None, 0
        )
        return f"{serial.value:08X}"
    except Exception:
        return "unknown"


def _local_ip() -> str:
    try:
        return socket.gethostbyname(socket.gethostname())
    except Exception:
        return "unknown"


def _av_list() -> str:
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows Defender\Exclusions\Paths",
            0,
            winreg.KEY_READ,
        )
        winreg.CloseKey(key)
        return "defender reachable"
    except Exception:
        return "unknown"


def collect() -> dict:
    return {
        "hostname": hostname(),
        "username": os.getenv("USERNAME", "unknown"),
        "userprofile": os.getenv("USERPROFILE", "unknown"),
        "os": platform.platform(),
        "os_version": platform.version(),
        "machine_arch": platform.machine(),
        "processor": platform.processor(),
        "machine_guid": _machine_guid(),
        "volume_serial": _volume_serial(),
        "local_ip": _local_ip(),
        "python": platform.python_version(),
        "uuid": str(uuid.uuid4()),
        "av": _av_list(),
    }


def write_report(path: Path, data: dict) -> None:
    lines = [f"{k}: {v}" for k, v in data.items()]
    path.write_text("\n".join(lines), encoding="utf-8")
