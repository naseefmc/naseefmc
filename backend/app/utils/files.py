from __future__ import annotations

import shutil
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings


def _unique_target(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    return path.with_name(f"{stem}_{uuid4().hex}{suffix}")


def save_upload(upload: UploadFile, destination: Path | None = None) -> Path:
    """Persist an uploaded file to the storage directory with size validation."""

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    destination_dir = destination or settings.upload_dir
    destination_dir.mkdir(parents=True, exist_ok=True)

    filename = Path(upload.filename or "upload.mp4").name
    target = _unique_target(destination_dir / filename)

    total_written = 0
    try:
        upload.file.seek(0)
        with target.open("wb") as buffer:
            while True:
                chunk = upload.file.read(1024 * 1024)
                if not chunk:
                    break
                total_written += len(chunk)
                if total_written > max_bytes:
                    raise ValueError(
                        f"Uploaded file exceeds maximum size of {settings.max_upload_size_mb} MB"
                    )
                buffer.write(chunk)
    except Exception:
        if target.exists():
            target.unlink(missing_ok=True)
        raise
    finally:
        try:
            upload.file.seek(0)
        except Exception:
            pass

    return target


def copy_file(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def write_bytes(stream: BinaryIO, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("wb") as buffer:
        shutil.copyfileobj(stream, buffer)
