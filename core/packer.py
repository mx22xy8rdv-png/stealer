import os
import shutil
import zipfile
from pathlib import Path

import zstandard as zstd
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes


def _zip_dir(src: Path, dst: Path) -> None:
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(src):
            for f in files:
                full = Path(root) / f
                rel = full.relative_to(src)
                zf.write(full, rel)


def _derive(password: str, salt: bytes) -> tuple[bytes, bytes]:
    key = PBKDF2(password, salt, dkLen=32, count=200_000)
    return key, salt


def _encrypt(in_path: Path, out_path: Path, password: str) -> None:
    salt = get_random_bytes(16)
    key, salt = _derive(password, salt)
    nonce = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)

    with open(in_path, "rb") as fin, open(out_path, "wb") as fout:
        fout.write(b"USEC" + salt + nonce)
        while True:
            chunk = fin.read(64 * 1024)
            if not chunk:
                break
            fout.write(cipher.encrypt(chunk))
        fout.write(cipher.digest())


def pack(src_dir: Path, password: str) -> Path:
    tmp_zip = src_dir.with_suffix(".zip")
    _zip_dir(src_dir, tmp_zip)
    if not tmp_zip.exists() or tmp_zip.stat().st_size == 0:
        raise RuntimeError("zip creation failed")

    cctx = zstd.ZstdCompressor(level=19)
    tmp_zst = src_dir.with_suffix(".zst")
    with open(tmp_zip, "rb") as fin, open(tmp_zst, "wb") as fout:
        cctx.copy_stream(fin, fout)

    tmp_zip.unlink(missing_ok=True)

    out = src_dir.with_suffix(".usec")
    _encrypt(tmp_zst, out, password)
    tmp_zst.unlink(missing_ok=True)

    if out.stat().st_size == 0:
        raise RuntimeError("encryption failed")

    pwd_file = out.with_suffix(".key.txt")
    pwd_file.write_text(password, encoding="utf-8")

    shutil.rmtree(src_dir, ignore_errors=True)
    return out
