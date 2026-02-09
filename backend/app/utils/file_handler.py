"""File validation, storage, and deletion utilities."""

import os
from pathlib import Path

from fastapi import HTTPException


def validate_file(filename: str, size_bytes: int, settings) -> str:
    """Validate file type and size. Returns the file extension.

    Raises HTTPException on invalid file type or size.
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    allowed = [t.strip() for t in settings.allowed_file_types.split(",")]

    if ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '.{ext}'. Allowed: {', '.join(allowed)}",
        )

    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if size_bytes > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size_bytes} bytes). Max: {max_bytes} bytes ({settings.max_file_size_mb} MB)",
        )

    return ext


def save_upload(
    tenant_id: str,
    document_id: str,
    filename: str,
    file_data: bytes,
    upload_dir: str,
) -> str:
    """Save uploaded file to tenant-specific directory.

    Returns the saved file path.
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    tenant_dir = Path(upload_dir) / str(tenant_id)
    tenant_dir.mkdir(parents=True, exist_ok=True)

    file_path = tenant_dir / f"{document_id}.{ext}"
    file_path.write_bytes(file_data)
    return str(file_path)


def delete_file(file_path: str) -> None:
    """Delete a file from disk if it exists."""
    try:
        os.remove(file_path)
    except FileNotFoundError:
        pass
