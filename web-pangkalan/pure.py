"""Pure functions: no DB, no HTTP, no filesystem side effects."""

from __future__ import annotations

from datetime import datetime
from functools import reduce
from io import BytesIO
from typing import Any

from PIL import Image
from toolz import pipe  # type: ignore[import-untyped]
from werkzeug.utils import secure_filename


ALLOWED_EXTENSIONS: frozenset[str] = frozenset({"png", "jpg", "jpeg", "gif", "webp"})

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_form(data: dict[str, str], required_fields: list[str]) -> tuple[bool, dict[str, str]]:
    """Return (is_valid, cleaned_data). Empty strings are rejected."""
    cleaned: dict[str, str] = {field: data.get(field, "").strip() for field in required_fields}
    is_valid = all(cleaned.values())
    return is_valid, cleaned


def validate_numeric(value: str) -> int:
    """Parse a numeric string or raise ValueError."""
    return int(value.strip())


def allowed_file(filename: str | None) -> bool:
    """Check whether filename has an allowed image extension."""
    if not filename:
        return False
    has_extension = "." in filename
    if not has_extension:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


# ---------------------------------------------------------------------------
# Formatting / utilities
# ---------------------------------------------------------------------------

def format_timestamp(dt: datetime | None = None) -> str:
    """Format a datetime as a compact timestamp string."""
    return (dt or datetime.now()).strftime("%Y%m%d%H%M%S%f")


def format_created_at(dt: datetime | None = None) -> str:
    """Format a datetime for database storage."""
    return (dt or datetime.now()).strftime("%Y-%m-%d %H:%M:%S")


def format_indonesian_date(dt: datetime | None = None) -> str:
    """Format a datetime as a human-readable Indonesian date."""
    return (dt or datetime.now()).strftime("%d %B %Y")


def generate_filename(timestamp: str, filename: str) -> str:
    """Generate a safe, prefixed filename from a timestamp."""
    return f"{timestamp}_{secure_filename(filename)}"


# ---------------------------------------------------------------------------
# Pagination / query helpers
# ---------------------------------------------------------------------------

def paginate(total: int, page: int, per_page: int) -> dict[str, int]:
    """Return normalized pagination metadata."""
    total_pages: int = max((total + per_page - 1) // per_page, 1)
    page = min(max(page, 1), total_pages)
    return {
        "page": page,
        "total_pages": total_pages,
        "offset": (page - 1) * per_page,
        "per_page": per_page,
        "total": total,
    }


def build_search_query(search: str) -> tuple[str, list[str]]:
    """Return (WHERE clause, params) for an optional nama_agen LIKE search."""
    if not search.strip():
        return "", []
    return "WHERE nama_agen LIKE ?", [f"%{search.strip()}%"]


# ---------------------------------------------------------------------------
# Image processing
# ---------------------------------------------------------------------------

def compress_image(file_data, filename: str) -> tuple[BytesIO, str]:
    """
    Compress an image to JPEG quality 85. Returns (stream, filename).
    On failure, returns the original stream untouched.
    Accepts a BytesIO or a werkzeug FileStorage object.
    """

    def _new_filename(original: str) -> str:
        return original.rsplit(".", 1)[0] + ".jpg"

    def _try_compress() -> tuple[BytesIO, str]:
        if hasattr(file_data, "seek"):
            file_data.seek(0)
        stream = file_data.stream if hasattr(file_data, "stream") else file_data
        img = Image.open(stream)
        rgb = img.convert("RGB")
        out = BytesIO()
        rgb.save(out, format="JPEG", quality=85, optimize=True)
        out.seek(0)
        return out, _new_filename(filename)

    try:
        return _try_compress()
    except Exception:
        if hasattr(file_data, "seek"):
            file_data.seek(0)
        return file_data, filename


# ---------------------------------------------------------------------------
# Record builders (pure)
# ---------------------------------------------------------------------------

def build_pengiriman_record(
    data: dict[str, str],
    numeric_values: dict[str, int],
    filename: str,
    created_at: str,
) -> dict[str, Any]:
    """Build a dict ready for DB insertion."""
    return {
        "nama_agen": data["nama_agen"],
        "nama_pangkalan": data["nama_pangkalan"],
        "tanggal_pengiriman_terakhir": data["tanggal_pengiriman_terakhir"],
        "jumlah_tabung_terakhir": numeric_values["jumlah_tabung_terakhir"],
        "stok_saat_ini": numeric_values["stok_saat_ini"],
        "tanggal_pengiriman_selanjutnya": data["tanggal_pengiriman_selanjutnya"],
        "jumlah_tabung_selanjutnya": numeric_values["jumlah_tabung_selanjutnya"],
        "dokumentasi": filename,
        "created_at": created_at,
    }


def parse_numeric_fields(data: dict[str, str], fields: list[str]) -> dict[str, int]:
    """Parse a list of numeric fields, raising ValueError on first failure."""
    return {field: validate_numeric(data[field]) for field in fields}
