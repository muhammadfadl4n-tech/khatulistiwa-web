"""Pure functions for Berita Kalbar.

No side effects: no file I/O, no network, no global mutable state.
"""


MIME_TYPES = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "svg": "image/svg+xml",
    "webp": "image/webp",
    "css": "text/css",
    "js": "application/javascript",
    "json": "application/json",
}


def guess_mime(ext, default="application/octet-stream"):
    """Return MIME type for a file extension (without dot) or default."""
    normalized = ext.lower().lstrip(".") if ext else ""
    return MIME_TYPES.get(normalized, default)


def guess_mime_from_bytes(data, ext_fallback=""):
    """Detect MIME type from content magic bytes, fallback to extension."""
    # Check magic bytes
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if data[:2] == b"\xff\xd8":
        return "image/jpeg"
    if data[:4] == b"\x89PNG":
        return "image/png"
    if data[:4] == b"GIF8":
        return "image/gif"
    if data[:4] == b"<svg" or data[:5] == b"<?xml":
        return "image/svg+xml"
    # Fallback to extension-based guess
    return guess_mime(ext_fallback)


def sort_berita(berita):
    """Return a new list of news items sorted by tanggal desc, then id desc."""
    return sorted(
        berita,
        key=lambda item: (str(item.get("tanggal", "")), int(item.get("id", 0) or 0)),
        reverse=True,
    )


def filter_berita(berita, date_from=None, date_to=None, kategori=None):
    """Filter news list by date range and/or category.

    Dates are compared as strings in ISO format (YYYY-MM-DD).
    Empty/None filters are ignored. Category match is case-sensitive exact.
    """
    result = berita
    if date_from:
        result = [item for item in result if str(item.get("tanggal", "")) >= date_from]
    if date_to:
        result = [item for item in result if str(item.get("tanggal", "")) <= date_to]
    if kategori:
        result = [item for item in result if item.get("kategori") == kategori]
    return result
