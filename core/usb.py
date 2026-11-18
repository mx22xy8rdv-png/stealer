import ctypes
import string
from pathlib import Path

DRIVE_REMOVABLE = 2


def list_removable() -> list[Path]:
    drives = []
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    for i, letter in enumerate(string.ascii_uppercase):
        if bitmask & (1 << i):
            root = f"{letter}:\\"
            dtype = ctypes.windll.kernel32.GetDriveTypeW(ctypes.c_wchar_p(root))
            if dtype == DRIVE_REMOVABLE:
                p = Path(root)
                if p.exists():
                    drives.append(p)
    return drives


def volume_label(drive: Path) -> str:
    try:
        buf = ctypes.create_unicode_buffer(261)
        ctypes.windll.kernel32.GetVolumeInformationW(
            str(drive), buf, 261, None, None, None, None, 0
        )
        return buf.value
    except Exception:
        return ""


def free_space(drive: Path) -> int:
    try:
        free = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(
            str(drive), None, None, ctypes.byref(free)
        )
        return free.value
    except Exception:
        return 0
