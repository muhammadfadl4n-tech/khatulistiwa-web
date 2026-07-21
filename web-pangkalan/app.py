"""Flask composition layer: thin routes wiring pure functions and effects."""

from __future__ import annotations

import os
from datetime import datetime
from functools import wraps

from flask import (
    Flask,
    Response,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from toolz import pipe  # type: ignore[import-untyped]
from werkzeug.exceptions import RequestEntityTooLarge

import effects
import pure


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
app.config["UPLOAD_FOLDER"] = effects.UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

REQUIRED_FIELDS = [
    "nama_agen",
    "nama_pangkalan",
    "tanggal_pengiriman_terakhir",
    "jumlah_tabung_terakhir",
    "stok_saat_ini",
    "tanggal_pengiriman_selanjutnya",
    "jumlah_tabung_selanjutnya",
]
NUMERIC_FIELDS = [
    "jumlah_tabung_terakhir",
    "stok_saat_ini",
    "jumlah_tabung_selanjutnya",
]


# ---------------------------------------------------------------------------
# Decorators / small helpers
# ---------------------------------------------------------------------------

def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("logged_in"):
            flash("Silakan login terlebih dahulu.", "warning")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return wrapped_view


@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(error):
    flash("Ukuran file terlalu besar. Maksimal 5 MB.", "danger")
    return redirect(request.referrer or url_for("form"))


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/form", methods=["GET", "POST"])
def form():
    daftar_agen, daftar_pangkalan = effects.get_daftar_pangkalan()

    if request.method == "GET":
        return render_template(
            "form.html",
            form={},
            daftar_agen=daftar_agen,
            daftar_pangkalan=daftar_pangkalan,
        )

    # POST: pure validation pipeline
    is_valid, data = pure.validate_form(request.form, REQUIRED_FIELDS)
    if not is_valid:
        flash("Semua field wajib diisi.", "danger")
        return render_template(
            "form.html",
            form=data,
            daftar_agen=daftar_agen,
            daftar_pangkalan=daftar_pangkalan,
        )

    file = request.files.get("dokumentasi")
    if not file or not file.filename:
        flash("Foto dokumentasi wajib diunggah.", "danger")
        return render_template(
            "form.html",
            form=data,
            daftar_agen=daftar_agen,
            daftar_pangkalan=daftar_pangkalan,
        )

    if not pure.allowed_file(file.filename):
        flash("Format foto tidak didukung. Gunakan PNG, JPG, JPEG, GIF, atau WEBP.", "danger")
        return render_template(
            "form.html",
            form=data,
            daftar_agen=daftar_agen,
            daftar_pangkalan=daftar_pangkalan,
        )

    try:
        numeric_values = pure.parse_numeric_fields(data, NUMERIC_FIELDS)
    except ValueError:
        flash("Jumlah tabung dan stok harus berupa angka.", "danger")
        return render_template("form.html", form=data)

    # Effectful pipeline: timestamp -> filename -> compress -> save -> db insert
    timestamp = pure.format_timestamp()
    filename = pure.generate_filename(timestamp, file.filename)
    file.seek(0)

    def _persist():
        compressed, final_name = pure.compress_image(file, filename)
        effects.save_upload_file(compressed, final_name)
        created_at = pure.format_created_at()
        record = pure.build_pengiriman_record(data, numeric_values, final_name, created_at)
        effects.save_pengiriman(record)

    pipe(None, lambda _: _persist())
    flash("Data berhasil disimpan!", "success")
    return redirect(url_for("form"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if username == "admin" and password == "lpg5555":
            session["logged_in"] = True
            flash("Login berhasil.", "success")
            return redirect(request.args.get("next") or url_for("dashboard"))

        flash("Username atau password salah.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Anda telah logout.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    search = request.args.get("search", "").strip()
    raw_page = max(request.args.get("page", 1, type=int), 1)
    per_page = 10

    where_clause, params = pure.build_search_query(search)

    total = effects.get_pengiriman_total(where_clause, params)
    pagination = pure.paginate(total, raw_page, per_page)

    rows = effects.get_pengiriman_list(
        where_clause,
        params,
        limit=pagination["per_page"],
        offset=pagination["offset"],
    )

    return render_template(
        "dashboard.html",
        rows=rows,
        search=search,
        page=pagination["page"],
        total=total,
        total_pages=pagination["total_pages"],
    )


@app.route("/export.csv")
@login_required
def export_csv():
    search = request.args.get("search", "").strip()
    where_clause, params = pure.build_search_query(search)

    csv_content = effects.export_csv_data(where_clause, params)
    filename = effects.export_csv_filename()

    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.route("/api/pangkalan/<path:nama_agen>")
def api_pangkalan(nama_agen):
    daftar = effects.get_pangkalan_by_agen(nama_agen)
    return {"daftar_pangkalan": daftar}


@app.route("/uploads/<path:filename>")
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/delete/<int:data_id>", methods=["POST"])
@login_required
def delete_data(data_id):
    record = effects.get_pengiriman_by_id(data_id)
    if not record:
        return {"ok": False, "error": "Data tidak ditemukan"}, 404

    effects.delete_upload_file(record["dokumentasi"])
    effects.delete_pengiriman(data_id)

    return {"ok": True}


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    effects.init_db()
    app.run(host="0.0.0.0", port=5000)
else:
    effects.init_db()
