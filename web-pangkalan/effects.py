"""Side-effecting functions: DB and filesystem operations."""

from __future__ import annotations

import csv
import os
import sqlite3
from datetime import datetime
from io import StringIO
from typing import Any

from toolz import pipe  # type: ignore[import-untyped]


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, "stok_pangkalan.db")
PANGKALAN_DB = os.path.expanduser("~/second-brain/02 - LPG Work/database/pangkalan.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

# ---------------------------------------------------------------------------
# Database connection / schema
# ---------------------------------------------------------------------------

def get_db_connection() -> sqlite3.Connection:
    """Create a SQLite connection with row factory enabled."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Ensure upload folder and pengiriman table exist."""
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pengiriman (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nama_agen TEXT NOT NULL,
                nama_pangkalan TEXT NOT NULL,
                tanggal_pengiriman_terakhir TEXT NOT NULL,
                jumlah_tabung_terakhir INTEGER NOT NULL,
                stok_saat_ini INTEGER NOT NULL,
                tanggal_pengiriman_selanjutnya TEXT NOT NULL,
                jumlah_tabung_selanjutnya INTEGER NOT NULL,
                dokumentasi TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

def get_daftar_pangkalan() -> tuple[list[str], list[str]]:
    """Fetch distinct agen and pangkalan names from the reference DB."""

    def _fetch() -> tuple[list[str], list[str]]:
        if not os.path.exists(PANGKALAN_DB):
            return [], []
        conn = sqlite3.connect(PANGKALAN_DB)
        try:
            agen_rows = conn.execute(
                "SELECT DISTINCT nama_agen FROM pangkalan WHERE kecamatan = 'SUNGAI KAKAP' ORDER BY nama_agen"
            )
            agen = [row[0] for row in agen_rows]
            pangkalan_rows = conn.execute(
                "SELECT DISTINCT nama_pangkalan FROM pangkalan WHERE kecamatan = 'SUNGAI KAKAP' ORDER BY nama_pangkalan"
            )
            pangkalan = [row[0] for row in pangkalan_rows]
            return agen, pangkalan
        finally:
            conn.close()

    try:
        return _fetch()
    except Exception:
        return [], []


def get_pangkalan_by_agen(nama_agen: str) -> list[str]:
    """Fetch pangkalan list for a specific agen from the reference DB."""

    def _fetch() -> list[str]:
        if not os.path.exists(PANGKALAN_DB):
            return []
        conn = sqlite3.connect(PANGKALAN_DB)
        try:
            rows = conn.execute(
                "SELECT DISTINCT nama_pangkalan FROM pangkalan WHERE kecamatan = 'SUNGAI KAKAP' AND nama_agen = ? ORDER BY nama_pangkalan",
                (nama_agen,),
            )
            return [row[0] for row in rows]
        finally:
            conn.close()

    try:
        return _fetch()
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Pengiriman CRUD
# ---------------------------------------------------------------------------

def save_pengiriman(record: dict[str, Any]) -> int:
    """Insert a pengiriman record and return the new row id."""
    with get_db_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO pengiriman (
                nama_agen,
                nama_pangkalan,
                tanggal_pengiriman_terakhir,
                jumlah_tabung_terakhir,
                stok_saat_ini,
                tanggal_pengiriman_selanjutnya,
                jumlah_tabung_selanjutnya,
                dokumentasi,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["nama_agen"],
                record["nama_pangkalan"],
                record["tanggal_pengiriman_terakhir"],
                record["jumlah_tabung_terakhir"],
                record["stok_saat_ini"],
                record["tanggal_pengiriman_selanjutnya"],
                record["jumlah_tabung_selanjutnya"],
                record["dokumentasi"],
                record["created_at"],
            ),
        )
        conn.commit()
        return cur.lastrowid or 0


def get_pengiriman_total(where_clause: str = "", params: list[Any] | None = None) -> int:
    """Return total count of pengiriman rows matching an optional WHERE clause."""
    params = params or []
    with get_db_connection() as conn:
        row = conn.execute(
            f"SELECT COUNT(*) FROM pengiriman {where_clause}", params
        ).fetchone()
        return row[0] if row else 0


def get_pengiriman_list(
    where_clause: str = "",
    params: list[Any] | None = None,
    limit: int = 10,
    offset: int = 0,
) -> list[sqlite3.Row]:
    """Return a page of pengiriman rows."""
    params = params or []
    with get_db_connection() as conn:
        return conn.execute(
            f"""
            SELECT * FROM pengiriman
            {where_clause}
            ORDER BY created_at DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset],
        ).fetchall()


def get_pengiriman_by_id(data_id: int) -> dict[str, Any] | None:
    """Fetch a single pengiriman record by id."""
    with get_db_connection() as conn:
        row = conn.execute("SELECT * FROM pengiriman WHERE id = ?", (data_id,)).fetchone()
        return dict(row) if row else None


def get_pengiriman_dokumentasi(data_id: int) -> str | None:
    """Fetch only the dokumentasi filename for a pengiriman record."""
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT dokumentasi FROM pengiriman WHERE id = ?", (data_id,)
        ).fetchone()
        return row["dokumentasi"] if row else None


def delete_pengiriman(data_id: int) -> bool:
    """Delete a pengiriman record by id."""
    with get_db_connection() as conn:
        cur = conn.execute("DELETE FROM pengiriman WHERE id = ?", (data_id,))
        conn.commit()
        return cur.rowcount > 0


# ---------------------------------------------------------------------------
# File operations
# ---------------------------------------------------------------------------

def save_upload_file(file_data, filename: str) -> str:
    """Write file_data to the upload folder and return the final path."""
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    with open(filepath, "wb") as f:
        f.write(file_data.read())
    return filepath


def delete_upload_file(filename: str) -> bool:
    """Remove an uploaded file if it exists."""
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return True
    return False


def delete_upload_file_by_id(data_id: int) -> bool:
    """Remove the dokumentasi file for a pengiriman record."""
    filename = get_pengiriman_dokumentasi(data_id)
    if not filename:
        return False
    return delete_upload_file(filename)


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def export_csv_data(where_clause: str = "", params: list[Any] | None = None) -> str:
    """Generate CSV content for pengiriman rows."""
    params = params or []
    header = [
        "Nama Agen",
        "Nama Pangkalan",
        "Tgl Kirim Terakhir",
        "Jml Tabung Terakhir",
        "Stok Saat Ini",
        "Tgl Kirim Selanjutnya",
        "Jml Tabung Selanjutnya",
        "Dokumentasi",
        "Tanggal Input",
    ]

    with get_db_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT
                nama_agen,
                nama_pangkalan,
                tanggal_pengiriman_terakhir,
                jumlah_tabung_terakhir,
                stok_saat_ini,
                tanggal_pengiriman_selanjutnya,
                jumlah_tabung_selanjutnya,
                dokumentasi,
                created_at
            FROM pengiriman
            {where_clause}
            ORDER BY created_at DESC, id DESC
            """,
            params,
        ).fetchall()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(header)
    for row in rows:
        writer.writerow(list(row))
    return output.getvalue()


def export_csv_filename(dt: datetime | None = None) -> str:
    """Generate a filename for the CSV export."""
    return (dt or datetime.now()).strftime("pengiriman_lpg_%Y%m%d_%H%M%S.csv")
