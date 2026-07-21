"""
Side effects for Portal 5555: DB operations and file I/O.
Each function handles its own open/close connections.
"""
import json
import os
import sqlite3
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).parent
LPG_DB = Path(os.environ.get("HOME", "/root")) / ".hermes" / "lpg_realtime.db"
PANGKALAN_DB = Path("/root/second-brain/02 - LPG Work/database/pangkalan.db")
ALOKASI_JSON = BASE_DIR / "data" / "alokasi.json"
AUTH_CONFIG = BASE_DIR / ".portal_auth"


def load_auth_config():
    if AUTH_CONFIG.exists():
        try:
            return json.loads(AUTH_CONFIG.read_text())
        except Exception as e:
            print(f"[auth] Error loading config: {e}")
    return {"username": "admin", "password": "lpg5555"}


def get_lpg_db():
    if not LPG_DB.exists():
        raise FileNotFoundError("Database not found")
    db = sqlite3.connect(str(LPG_DB))
    db.row_factory = sqlite3.Row
    return db


def get_pangkalan_db():
    if not PANGKALAN_DB.exists():
        raise FileNotFoundError("Pangkalan database not found")
    db = sqlite3.connect(str(PANGKALAN_DB))
    db.row_factory = sqlite3.Row
    return db


def fetch_agen(endpoint, qs):
    db = get_lpg_db()
    try:
        if endpoint == "stats":
            row = db.execute("""
                SELECT
                    COUNT(*) AS total,
                    COUNT(DISTINCT wilayah) AS kabupaten_count,
                    SUM(CAST(alokasi AS INTEGER)) AS tw3_count
                FROM agen
            """).fetchone()
            return {
                "total": row["total"] or 0,
                "kabupaten_count": row["kabupaten_count"] or 0,
                "tw3_count": int(row["tw3_count"] or 0),
            }

        if endpoint == "detail":
            from urllib.parse import unquote_plus
            nama = unquote_plus(qs.get("nama", [""])[0]).strip()
            if not nama:
                return {"_error": "Parameter nama wajib diisi", "_status": 400}
            row = db.execute("SELECT * FROM agen WHERE nama_agen = ?", (nama,)).fetchone()
            if row:
                return dict(row)
            return {"_error": "Agen tidak ditemukan", "_status": 404}

        # list
        from pure import build_agen_query
        where, params = build_agen_query(qs)
        rows = db.execute(f"SELECT * FROM agen{where} ORDER BY nama_agen", params).fetchall()
        return [dict(row) for row in rows]
    finally:
        db.close()


def update_agen(body):
    from pure import build_agen_update_sets
    sold_to = str(body.get("sold_to", "")).strip()
    if not sold_to:
        return {"_error": "Parameter sold_to wajib diisi", "_status": 400}
    sets, params = build_agen_update_sets(body)
    if not sets:
        return {"_error": "Tidak ada field yang diupdate", "_status": 400}
    sets.append("updated_at = CURRENT_TIMESTAMP")
    params.append(sold_to)

    db = get_lpg_db()
    try:
        cur = db.execute(
            f"UPDATE agen SET {', '.join(sets)} WHERE sold_to = ?",
            params
        )
        affected = cur.rowcount
        db.commit()
        if affected == 0:
            return {"_error": "Agen tidak ditemukan", "_status": 404}
        return {
            "success": True,
            "message": f"Data agen (sold_to: {sold_to}) berhasil diupdate",
            "affected": affected,
        }
    finally:
        db.close()


def fetch_lpg_data(endpoint, qs, where, params):
    db = get_lpg_db()
    try:
        all_months = [r["cal_year_month"] for r in
            db.execute("SELECT DISTINCT cal_year_month FROM raw_data ORDER BY cal_year_month").fetchall()]
        all_districts = [r["sales_district"] for r in
            db.execute("SELECT DISTINCT sales_district FROM raw_data ORDER BY sales_district").fetchall()]

        if endpoint == "summary":
            row = db.execute(f"SELECT COUNT(*) as cnt, SUM(billing_qty_mt) as mt, SUM(billing_qty_su) as tb FROM raw_data{where}", params).fetchone()
            mat_rows = db.execute(f"SELECT material, SUM(billing_qty_mt) as mt, SUM(billing_qty_su) as tb FROM raw_data{where} GROUP BY material ORDER BY mt DESC", params).fetchall()
            type_rows = db.execute(f"SELECT price_list_type, customer_group, SUM(billing_qty_mt) as mt, SUM(billing_qty_su) as tb FROM raw_data{where} GROUP BY price_list_type, customer_group", params).fetchall()
            seg_rows = db.execute("""
                SELECT
                    CASE
                        WHEN price_list_type = 'PSO' THEN 'PSO'
                        WHEN price_list_type = 'Standard' AND customer_group = 'Dealer LPG' THEN 'NPSO_RT'
                        WHEN price_list_type = 'Standard' AND customer_group != 'Dealer LPG' THEN 'NPSO_NRT'
                        ELSE 'Lainnya'
                    END as segment,
                    SUM(billing_qty_mt) as mt,
                    SUM(billing_qty_su) as tb,
                    COUNT(*) as trans
                FROM raw_data
                GROUP BY segment
                ORDER BY mt DESC
            """).fetchall()
            plant_rows = db.execute(f"SELECT DISTINCT name_plant FROM raw_data{where} ORDER BY name_plant", params).fetchall()
            pso_agents = db.execute("SELECT COUNT(DISTINCT name_sp) FROM raw_data WHERE price_list_type='PSO'").fetchone()[0]
            npso_agents = db.execute("SELECT COUNT(DISTINCT name_sp) FROM raw_data WHERE price_list_type='Standard'").fetchone()[0]
            upd = db.execute("SELECT * FROM update_log ORDER BY id DESC LIMIT 1").fetchone()
            from pure import format_lpg_summary
            return format_lpg_summary(row, all_months, all_districts, plant_rows, mat_rows, type_rows, seg_rows, upd, pso_agents, npso_agents)

        if endpoint == "monthly":
            rows = db.execute(f"SELECT cal_year_month, SUM(billing_qty_mt) as mt, SUM(billing_qty_su) as tb FROM raw_data{where} GROUP BY cal_year_month ORDER BY cal_year_month", params).fetchall()
            return {r["cal_year_month"]: {"mt": round(r["mt"], 2), "tb": int(r["tb"])} for r in rows}

        if endpoint == "districts":
            rows = db.execute(f"SELECT sales_district as name, SUM(billing_qty_mt) as mt, SUM(billing_qty_su) as tb FROM raw_data{where} GROUP BY sales_district ORDER BY mt DESC", params).fetchall()
            return {r["name"]: {"mt": round(r["mt"], 2), "tb": int(r["tb"])} for r in rows}

        if endpoint == "plants":
            rows = db.execute(f"SELECT name_plant as name, SUM(billing_qty_mt) as mt, SUM(billing_qty_su) as tb FROM raw_data{where} GROUP BY name_plant ORDER BY mt DESC", params).fetchall()
            from pure import clean_plant_name
            data = {}
            for r in rows:
                data[clean_plant_name(r["name"])] = {"mt": round(r["mt"], 2), "tb": int(r["tb"])}
            return data

        if endpoint == "materials":
            rows = db.execute(f"SELECT material as name, SUM(billing_qty_mt) as mt, SUM(billing_qty_su) as tb FROM raw_data{where} GROUP BY material ORDER BY mt DESC", params).fetchall()
            return {r["name"]: {"mt": round(r["mt"], 2), "tb": int(r["tb"])} for r in rows}

        if endpoint == "agents":
            ptype = qs.get("type", ["all"])[0]
            if ptype == "Standard":
                rows = db.execute(f"SELECT name_sp as name, sales_district as district, SUM(billing_qty_mt) as mt, SUM(billing_qty_su) as tb FROM raw_data{where} GROUP BY name_sp ORDER BY mt DESC LIMIT 100", params).fetchall()
                data = {}
                for r in rows:
                    data[r["name"]] = {"mt": round(r["mt"], 2), "tb": int(r["tb"]), "district": r["district"]}
                return data
            else:
                query = "SELECT name_sp as name, sales_district as district, SUM(total_mt) as mt, SUM(total_qty) as tb FROM agent_summary"
                q_params = []
                clauses = []
                if ptype == "PSO":
                    clauses.append("price_list_type = 'PSO'")
                month = qs.get("month", [None])[0]
                year = qs.get("year", [None])[0]
                district = qs.get("district", [None])[0]
                if month:
                    if "." in month:
                        clauses.append("cal_year_month = ?")
                        q_params.append(month)
                    else:
                        clauses.append("cal_year_month LIKE ?")
                        q_params.append(f"{month}.%")
                if year:
                    clauses.append("SUBSTR(cal_year_month,4) = ?")
                    q_params.append(year)
                if district:
                    clauses.append("sales_district = ?")
                    q_params.append(district)
                if clauses:
                    query += " WHERE " + " AND ".join(clauses)
                query += " GROUP BY name_sp ORDER BY mt DESC LIMIT 200"
                rows = db.execute(query, q_params).fetchall()
                data = {}
                for r in rows:
                    data[r["name"]] = {"mt": round(r["mt"], 2), "tb": int(r["tb"]), "district": r["district"]}
                return data

        if endpoint == "compare":
            rows = db.execute(f"SELECT cal_year_month, SUM(billing_qty_mt) as mt, SUM(billing_qty_su) as tb FROM raw_data{where} GROUP BY cal_year_month ORDER BY cal_year_month", params).fetchall()
            monthly = {r["cal_year_month"]: {"mt": round(r["mt"], 2), "tb": int(r["tb"])} for r in rows}
            from pure import compare_years
            return compare_years(monthly)

        return {"_error": "Unknown endpoint", "_status": 404}
    finally:
        db.close()


def fetch_lpg_rekap(qs):
    year = qs.get("year", [None])[0]
    district = qs.get("district", [None])[0]
    agen = qs.get("agen", [""])[0].strip()
    rekap_year = (year or "").strip()
    rekap_district = (district or "").strip()
    params = [
        rekap_year, rekap_year,
        rekap_district, rekap_district,
        f"%{agen}%", agen,
    ]
    db = get_lpg_db()
    try:
        rows = db.execute("""
            SELECT
                a.sold_to_party AS sold_to,
                a.name_sp AS nama_agen,
                a.sales_district AS wilayah,
                a.cal_year_month,
                a.total_mt,
                a.total_qty
            FROM agent_summary a
            WHERE a.price_list_type = 'PSO'
              AND (SUBSTR(a.cal_year_month,4) = ? OR ? = '')
              AND (a.sales_district = ? OR ? = '')
              AND (a.name_sp LIKE ? OR ? = '')
            ORDER BY a.name_sp, a.cal_year_month
        """, params).fetchall()
        return rows
    finally:
        db.close()


def fetch_lpg_performa(qs):
    year = qs.get("year", ["2026"])[0]
    month = qs.get("month", [None])[0]
    district = qs.get("district", [None])[0]
    perf_year = year or "2026"

    real_clauses = ["price_list_type = 'PSO'"]
    real_params = []
    real_clauses.append("SUBSTR(cal_year_month,4) = ?")
    real_params.append(perf_year)
    if month:
        if "." in month:
            real_clauses.append("cal_year_month = ?")
            real_params.append(month)
        else:
            real_clauses.append("cal_year_month LIKE ?")
            real_params.append(f"{month}.%")
    if district:
        real_clauses.append("sales_district = ?")
        real_params.append(district)

    real_where = " WHERE " + " AND ".join(real_clauses)
    sql = f"""
        SELECT
            sales_district AS wilayah,
            SUM(total_mt) AS realisasi_mt,
            SUM(total_qty) AS realisasi_tabung,
            COUNT(DISTINCT name_sp) AS agen_count
        FROM agent_summary
        {real_where}
        GROUP BY sales_district
        ORDER BY sales_district
    """
    db = get_lpg_db()
    try:
        rows = db.execute(sql, real_params).fetchall()
        monthly_rows = db.execute("""
            SELECT
                CAST(SUBSTR(cal_year_month, 1, 2) AS INTEGER) AS month_num,
                SUM(total_mt) AS total_mt
            FROM agent_summary
            WHERE price_list_type = 'PSO' AND SUBSTR(cal_year_month, 4) = ?
            GROUP BY month_num
            ORDER BY month_num
        """, (perf_year,)).fetchall()
        return rows, monthly_rows, perf_year
    finally:
        db.close()


def load_alokasi(tahun=None):
    """Load PSO alokasi from JSON. Returns dict per wilayah."""
    try:
        data = json.loads(ALOKASI_JSON.read_text(encoding="utf-8"))
        if tahun and tahun in data.get("tahun", {}):
            return data["tahun"][tahun]
        return data.get("tahun", {})
    except Exception as e:
        print(f"[load_alokasi] Error: {e}")
        return {}

def load_npso_targets():
    """Load NPSO targets from JSON."""
    try:
        data = json.loads(ALOKASI_JSON.read_text(encoding="utf-8"))
        return data.get("npso_targets", {})
    except Exception as e:
        print(f"[load_npso_targets] Error: {e}")
        return {}


def fetch_pangkalan_check(qs):
    from pure import build_pangkalan_query, build_count_query
    clauses, params, issue = build_pangkalan_query(qs)
    where_clause = " WHERE " + " AND ".join(clauses) if clauses else ""
    issue_clause = ""
    if issue:
        issue_clause = f" AND issue = '{issue}'"
    query = build_count_query(where_clause) + issue_clause
    db = get_pangkalan_db()
    try:
        row = db.execute(query, params).fetchone()
        return {"total_issues": row["cnt"]}
    finally:
        db.close()


def fetch_pangkalan_stats():
    from pure import build_count_query
    db = get_pangkalan_db()
    try:
        total = db.execute("SELECT COUNT(*) AS cnt FROM pangkalan").fetchone()["cnt"]
        kota_kosong = db.execute(build_count_query(" WHERE issue = 'kota_kosong'")).fetchone()["cnt"]
        koordinat_kosong = db.execute(build_count_query(" WHERE issue = 'koordinat_kosong'")).fetchone()["cnt"]
        duplikat = db.execute(build_count_query(" WHERE issue = 'duplikat'")).fetchone()["cnt"]
        return {
            "total_pangkalan": total,
            "kota_kosong_count": kota_kosong,
            "koordinat_kosong_count": koordinat_kosong,
            "duplicate_registrasi_count": duplikat,
        }
    finally:
        db.close()


def fetch_pangkalan_list(qs):
    from pure import build_pangkalan_query
    clauses, params, issue = build_pangkalan_query(qs)
    where_clause = " WHERE " + " AND ".join(clauses) if clauses else ""

    join_clause = """
        LEFT JOIN (
            SELECT id_registrasi
            FROM pangkalan
            WHERE id_registrasi IS NOT NULL AND TRIM(id_registrasi) != ''
            GROUP BY id_registrasi
            HAVING COUNT(*) > 1
        ) dup ON dup.id_registrasi = p.id_registrasi
    """

    if issue:
        issue_map = {
            "kota_kosong": "WHERE kota IS NULL OR TRIM(COALESCE(kota,'')) = ''",
            "koordinat_kosong": "WHERE (latitude IS NULL OR CAST(COALESCE(latitude,0) AS REAL) = 0) AND (longitude IS NULL OR CAST(COALESCE(longitude,0) AS REAL) = 0)",
            "duplikat": "WHERE dup.id_registrasi IS NOT NULL",
        }
        issue_sql = issue_map.get(issue, "")
        query = f"""
            SELECT {','.join(f'p.{c}' for c in [
                'id','nama_agen','nama_pangkalan','id_registrasi','kota','kecamatan',
                'latitude','longitude','status','alamat'
            ])}
            FROM pangkalan p
            {join_clause}
            {issue_sql}
            ORDER BY p.id
        """
    else:
        query = f"""
            SELECT {','.join(f'p.{c}' for c in [
                'id','nama_agen','nama_pangkalan','id_registrasi','kota','kecamatan',
                'latitude','longitude','status','alamat'
            ])}
            FROM pangkalan p
            {join_clause}
            {where_clause}
            ORDER BY p.nama_agen, p.nama_pangkalan
        """

    db = get_pangkalan_db()
    try:
        rows = db.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        db.close()


def export_pangkalan_excel(qs):
    from pure import build_pangkalan_query
    clauses, params, issue = build_pangkalan_query(qs)
    where_clause = " WHERE " + " AND ".join(clauses) if clauses else ""
    db = get_pangkalan_db()
    try:
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Pangkalan"

        columns = ["id", "id_registrasi", "nama_pangkalan", "nama_agen", "kota", "kecamatan", "latitude", "longitude", "status", "alamat"]
        headers = ["ID", "ID Registrasi", "Nama Pangkalan", "Nama Agen", "Kota", "Kecamatan", "Latitude", "Longitude", "Status", "Alamat"]
        ws.append(headers)

        rows = db.execute(f"SELECT {','.join(columns)} FROM pangkalan p{where_clause} ORDER BY p.nama_agen, p.nama_pangkalan", params).fetchall()
        for row in rows:
            ws.append([row[c] for c in columns])

        output = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
        wb.save(output.name)
        output.close()
        content = Path(output.name).read_bytes()
        Path(output.name).unlink()
        return content
    finally:
        db.close()


def export_rekap_excel(rows, _alokasi):
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Rekap Agen PSO"
    ws.append(["Sold To", "Nama Agen", "Wilayah", "Bulan", "Total MT", "Total Tabung"])
    for r in rows:
        ws.append([r["sold_to"], r["nama_agen"], r["wilayah"], r["cal_year_month"], r["total_mt"], r["total_qty"]])
    output = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    wb.save(output.name)
    output.close()
    content = Path(output.name).read_bytes()
    Path(output.name).unlink()
    return content
