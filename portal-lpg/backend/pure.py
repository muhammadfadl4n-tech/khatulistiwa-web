"""
Pure functions for Portal 5555.
No DB calls, HTTP, file I/O, or side effects.
"""
from datetime import datetime, timedelta
from urllib.parse import parse_qs, unquote_plus, urlparse
from toolz import pipe, curry

MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css",
    ".js": "application/javascript",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
    ".json": "application/json",
    ".txt": "text/plain; charset=utf-8",
}

SESSION_DURATION_SECONDS = 43200  # 12 hours


def _get_query_int(path, name, required=True):
    qs = parse_qs(urlparse(path).query)
    value = qs.get(name, [""])[0]
    if not value:
        if required:
            raise ValueError(f"Parameter {name} wajib diisi")
        return None
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"Parameter {name} harus berupa angka")


def row_dict(row):
    return dict(row) if row else None


def is_public_path(path):
    return path in ("/login", "/api/health", "/api/auth/check", "/favicon.svg", "/icons.svg") or path.startswith("/static/") or path.startswith("/assets/")


def validate_issue_type(issue, valid_set):
    return issue in valid_set


def pso_status(pct):
    if pct >= 100:
        return "berlebih"
    elif pct >= 85:
        return "tepat"
    elif pct >= 50:
        return "kurang"
    else:
        return "kritis"


def raw_where(ptype, month, year, district):
    clauses = []
    params = []
    if ptype == "PSO":
        clauses.append("kategori = 'PSO'")
    elif ptype == "NPSO_RT":
        clauses.append("kategori = 'NPSO RT'")
    elif ptype == "NPSO_NRT":
        clauses.append("kategori = 'NPSO NRT'")
    if month:
        if "." in month:
            clauses.append("cal_year_month = ?")
            params.append(month)
        else:
            clauses.append("cal_year_month LIKE ?")
            params.append(f"{month}.%")
    if year:
        clauses.append("cal_year_month LIKE ?")
        params.append(f"%.{year}")
    if district:
        clauses.append("sales_district = ?")
        params.append(district)
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    return where, params


def build_agen_query(qs):
    q = qs.get("q", [""])[0].strip()
    wilayah = qs.get("wilayah", [""])[0].strip()
    rayon = qs.get("rayon", [""])[0].strip()
    afiliasi = qs.get("afiliasi", [""])[0].strip()
    pengusaha = qs.get("pengusaha", [""])[0].strip()

    clauses = []
    params = []
    if wilayah:
        clauses.append("wilayah = ?")
        params.append(wilayah)
    if rayon:
        clauses.append("rayon_sbm = ?")
        params.append(rayon)
    if afiliasi:
        clauses.append("afiliasi LIKE ?")
        params.append(f"%{afiliasi}%")
    if pengusaha:
        clauses.append("pengusaha LIKE ?")
        params.append(f"%{pengusaha}%")
    if q:
        clauses.append("(nama_agen LIKE ? OR sold_to LIKE ? OR afiliasi LIKE ? OR pengusaha LIKE ?)")
        like = f"%{q}%"
        params.extend([like, like, like, like])
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    return where, params


def build_pangkalan_query(qs):
    agen = qs.get("agen", [""])[0].strip()
    kota = qs.get("kota", [""])[0].strip()
    kecamatan = qs.get("kecamatan", [""])[0].strip()
    status = qs.get("status", [""])[0].strip()
    search = qs.get("search", [""])[0].strip()
    issue = qs.get("issue", [""])[0].strip()

    clauses = []
    params = []
    if agen:
        clauses.append("nama_agen = ?")
        params.append(agen)
    if kota:
        clauses.append("kota = ?")
        params.append(kota)
    if kecamatan:
        clauses.append("kecamatan = ?")
        params.append(kecamatan)
    if status:
        clauses.append("status = ?")
        params.append(status)
    if search:
        clauses.append("(nama_pangkalan LIKE ? OR id_registrasi LIKE ?)")
        like = f"%{search}%"
        params.extend([like, like])
    return clauses, params, issue


def build_count_query(where_clause):
    return f"""
        WITH dup AS (
            SELECT id_registrasi
            FROM pangkalan
            WHERE id_registrasi IS NOT NULL AND TRIM(id_registrasi) != ''
            GROUP BY id_registrasi
            HAVING COUNT(*) > 1
        ),
        base AS (
            SELECT
                id,
                status,
                CASE
                    WHEN kota IS NULL OR TRIM(kota) = '' THEN 'kota_kosong'
                    WHEN latitude IS NULL OR CAST(latitude AS REAL) = 0
                      OR longitude IS NULL OR CAST(longitude AS REAL) = 0 THEN 'koordinat_kosong'
                    WHEN d.id_registrasi IS NOT NULL THEN 'duplikat'
                    ELSE NULL
                END AS issue
            FROM pangkalan p
            LEFT JOIN dup d ON d.id_registrasi = p.id_registrasi
        )
        SELECT COUNT(*) AS cnt FROM base{where_clause}
    """


def format_rekap_data(rows):
    months_set = set()
    agents = {}
    total_mt = 0.0
    total_tb = 0
    for r in rows:
        key = r["sold_to"]
        if key not in agents:
            agents[key] = {
                "nama_agen": r["nama_agen"],
                "sold_to": r["sold_to"],
                "wilayah": r["wilayah"],
                "monthly": {},
                "total_mt": 0.0,
                "total_tabung": 0,
            }
        agents[key]["monthly"][r["cal_year_month"]] = {
            "mt": round(float(r["total_mt"] or 0), 2),
            "tb": int(r["total_qty"] or 0),
        }
        agents[key]["total_mt"] += float(r["total_mt"] or 0)
        agents[key]["total_tabung"] += int(r["total_qty"] or 0)
        total_mt += float(r["total_mt"] or 0)
        total_tb += int(r["total_qty"] or 0)
        months_set.add(r["cal_year_month"])

    months = sorted(months_set, key=lambda m: (m.split(".")[1], m.split("."))[0])
    data_rows = sorted(
        [{
            "nama_agen": a["nama_agen"],
            "sold_to": a["sold_to"],
            "wilayah": a["wilayah"],
            "monthly": a["monthly"],
            "total_mt": round(a["total_mt"], 2),
            "total_tabung": a["total_tabung"],
        } for a in agents.values()],
        key=lambda x: (-x["total_mt"], x["nama_agen"])
    )
    return {
        "summary": {
            "total_agen": len(data_rows),
            "total_mt": round(total_mt, 2),
            "total_tabung": total_tb,
            "months": months,
        },
        "data": data_rows,
    }


def format_performa_data(rows, alokasi_data, sort_by):
    data_rows = []
    for row in rows:
        wilayah = row["wilayah"] or "-"
        realisasi_mt = float(row["realisasi_mt"] or 0)
        realisasi_tabung = int(row["realisasi_tabung"] or 0)
        agen_count = int(row["agen_count"] or 0)
        alokasi = float(alokasi_data.get(wilayah, 0))
        pct_realisasi = (realisasi_mt / alokasi * 100) if alokasi else 0
        selisih = round(alokasi - realisasi_mt, 2)
        data_rows.append({
            "wilayah": wilayah,
            "alokasi": round(alokasi, 2),
            "realisasi_mt": round(realisasi_mt, 2),
            "realisasi_tabung": realisasi_tabung,
            "agen_count": agen_count,
            "pct_realisasi": round(pct_realisasi, 2),
            "selisih_mt": selisih if selisih >= 0 else 0,
            "status": pso_status(pct_realisasi),
        })

    for wil, alok in alokasi_data.items():
        if alok > 0 and not any(r["wilayah"] == wil for r in data_rows):
            data_rows.append({
                "wilayah": wil,
                "alokasi": round(float(alok), 2),
                "realisasi_mt": 0,
                "realisasi_tabung": 0,
                "agen_count": 0,
                "pct_realisasi": 0,
                "selisih_mt": round(float(alok), 2),
                "status": "kritis",
            })

    if sort_by == "pct_desc":
        data_rows.sort(key=lambda x: (-x["pct_realisasi"], x["wilayah"]))
    elif sort_by == "wilayah":
        data_rows.sort(key=lambda x: x["wilayah"])
    elif sort_by == "alokasi_desc":
        data_rows.sort(key=lambda x: (-x["alokasi"], x["wilayah"]))
    else:
        data_rows.sort(key=lambda x: (x["pct_realisasi"], x["wilayah"]))
    return data_rows


def calculate_prognosis(monthly_rows, perf_year, total_alokasi):
    if not monthly_rows:
        return {}
    months_data = {}
    for mr in monthly_rows:
        months_data[int(mr["month_num"])] = float(mr["total_mt"] or 0)
    latest_month = max(months_data.keys()) if months_data else 0
    total_so_far = sum(months_data.values())
    months_elapsed = len(months_data)
    if months_elapsed <= 0:
        return {}
    avg_mt_per_month = total_so_far / months_elapsed
    remaining_months = 12 - latest_month
    prognosa = total_so_far + (avg_mt_per_month * remaining_months)
    return {
        "tahun": perf_year,
        "total_realisasi_ytd": round(total_so_far, 2),
        "bulan_terakhir": latest_month,
        "bulan_berjalan": months_elapsed,
        "rata_rata_per_bulan": round(avg_mt_per_month, 2),
        "sisa_bulan": remaining_months,
        "prognosa_akhir_tahun": round(prognosa, 2),
        "total_alokasi_tahunan": round(total_alokasi, 2),
        "prognosa_vs_alokasi_pct": round(prognosa / total_alokasi * 100, 2) if total_alokasi else 0,
        "selisih_prognosa": round(prognosa - total_alokasi, 2),
    }


def compare_years(monthly):
    years = {}
    for ym, d in monthly.items():
        yr = ym.split(".")[1]
        if yr not in years:
            years[yr] = {"mt": 0, "tb": 0, "months": {}}
        years[yr]["mt"] += d["mt"]
        years[yr]["tb"] += d["tb"]
        years[yr]["months"][ym] = d

    all_years = sorted(years.keys())
    ytd = {}
    if len(all_years) >= 2:
        y1, y2 = all_years[-2], all_years[-1]
        m1 = {k.split(".")[0]: v for k, v in years[y1]["months"].items()}
        m2 = {k.split(".")[0]: v for k, v in years[y2]["months"].items()}
        common_months = sorted(set(m1.keys()) & set(m2.keys()))
        ytd = {
            "years": [y1, y2],
            "months": common_months,
            "data": {y1: [m1[m] for m in common_months], y2: [m2[m] for m in common_months]},
            "totals": {y1: sum(m1[m]["mt"] for m in common_months), y2: sum(m2[m]["mt"] for m in common_months)}
        }

    sorted_yms = sorted(monthly.keys())
    mtm = {}
    for i, ym in enumerate(sorted_yms[1:], 1):
        prev = sorted_yms[i - 1]
        cur = monthly[ym]
        prv = monthly[prev]
        change = cur["mt"] - prv["mt"]
        pct = (change / prv["mt"] * 100) if prv["mt"] else 0
        mtm[ym] = {"current": cur, "previous": prv, "change": round(change, 2), "change_pct": round(pct, 2)}

    return {"monthly": monthly, "years": years, "ytd": ytd, "mtm": mtm}


def clean_plant_name(name):
    return name.replace("SPBE-", "").replace("Depot mini LPG ", "Depot ")


def parse_date_range(upd):
    if not upd or not upd["date_range_end"]:
        return None
    parts = upd["date_range_end"].split("-")
    if len(parts) != 3:
        return upd["date_range_end"]
    bln = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
    try:
        return f"{int(parts[2])} {bln[int(parts[1]) - 1]} {parts[0]}"
    except Exception:
        return upd["date_range_end"]


def new_session_token():
    # Kept pure; caller stores it in SESSIONS
    import secrets
    return secrets.token_hex(32)


def format_pangkalan_check_summary(total_row, kota_row, koordinat_row, dup_row):
    return {
        "total_pangkalan": total_row["cnt"] or 0,
        "kota_kosong_count": kota_row["cnt"] or 0,
        "koordinat_kosong_count": koordinat_row["cnt"] or 0,
        "duplicate_registrasi_count": dup_row["cnt"] or 0,
    }


def format_pangkalan_check_detail(detail_rows):
    per_agen = {}
    for row in detail_rows:
        name = row["nama_agen"] or "-"
        if name not in per_agen:
            per_agen[name] = {
                "nama_agen": name,
                "total": 0,
                "kota_kosong": 0,
                "koordinat_kosong": 0,
                "duplikat": 0,
            }
        per_agen[name]["total"] += 1
        per_agen[name][row["issue_type"]] += 1
    return sorted(per_agen.values(), key=lambda x: (-x["total"], x["nama_agen"]))


def format_lpg_summary(row, all_months, all_districts, plant_rows, mat_rows, type_rows, seg_rows, upd, pso_agents, npso_agents):
    last_data_date = parse_date_range(upd)
    return {
        "total_mt": round(row["mt"] or 0, 2),
        "total_tabung": int(row["tb"] or 0),
        "total_rows": row["cnt"],
        "total_months": len(all_months),
        "total_districts": len(all_districts),
        "total_plants": len(plant_rows),
        "months": all_months,
        "districts": all_districts,
        "materials": [{"name": r["material"], "mt": round(r["mt"], 2), "tb": int(r["tb"])} for r in mat_rows],
        "types": [{"name": r["price_list_type"], "mt": round(r["mt"], 2), "tb": int(r["tb"])} for r in type_rows],
        "segments": [{"name": r["segment"], "mt": round(r["mt"], 2), "tb": int(r["tb"]), "trans": r["trans"]} for r in seg_rows],
        "date_from": all_months[0] if all_months else None,
        "date_to": all_months[-1] if all_months else None,
        "last_data_date": last_data_date,
        "last_update": upd["created_at"] if upd else None,
        "pso_agents": pso_agents or 0,
        "npso_agents": npso_agents or 0,
    }


def build_agen_update_sets(body):
    allowed = {
        "nama_agen", "alamat_kantor", "alamat_gudang", "desa_kel", "kecamatan",
        "latitude", "longitude", "pengusaha", "no_pengusaha", "pic", "no_pic",
        "kepemilikan_armada_truk", "kepemilikan_armada_pick_up",
        "support_pertamina", "background", "afiliasi", "alokasi", "lo_harian",
    }
    sets = []
    params = []
    for key, val in body.items():
        if key in allowed and val is not None:
            sets.append(f"{key} = ?")
            params.append(str(val))
    return sets, params
