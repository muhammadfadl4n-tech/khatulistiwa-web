"""Side effects for Berita Kalbar.

Contains all I/O operations: file system reads/writes.
"""
import json


SAMPLE_DATA = {
    "berita": [
        {
            "id": 1,
            "judul": "Pemerintah Provinsi Kalbar Perkuat Koordinasi Pengendalian Inflasi",
            "tanggal": "2026-07-13",
            "sumber": "Berita Kalbar",
            "kategori": "Ekonomi",
            "url": "https://example.com/kalbar-inflasi",
            "isi": "Pemerintah Provinsi Kalimantan Barat memperkuat koordinasi dengan pemerintah kabupaten dan kota untuk menjaga harga kebutuhan pokok tetap stabil. Langkah ini dilakukan melalui pemantauan pasokan beras, cabai, telur, dan komoditas pangan lain di pasar utama.",
            "gambar": "",
        },
        {
            "id": 2,
            "judul": "DPRD Kalbar Bahas Prioritas Pembangunan Infrastruktur Daerah",
            "tanggal": "2026-07-12",
            "sumber": "Berita Kalbar",
            "kategori": "Politik",
            "url": "https://example.com/dprd-kalbar-infrastruktur",
            "isi": "DPRD Kalimantan Barat membahas sejumlah agenda prioritas pembangunan, termasuk peningkatan akses jalan penghubung antarkecamatan dan perbaikan fasilitas publik. Pembahasan dilakukan untuk memastikan program daerah menyentuh kebutuhan masyarakat.",
            "gambar": "",
        },
        {
            "id": 3,
            "judul": "Aparat Tingkatkan Pengawasan Distribusi LPG Bersubsidi di Pontianak",
            "tanggal": "2026-07-11",
            "sumber": "Berita Kalbar",
            "kategori": "LPG",
            "url": "https://example.com/lpg-pontianak",
            "isi": "Pengawasan distribusi LPG bersubsidi di Pontianak ditingkatkan untuk mencegah kelangkaan dan penyalahgunaan. Petugas melakukan pengecekan ke pangkalan resmi serta mengimbau warga membeli sesuai ketentuan.",
            "gambar": "",
        },
        {
            "id": 4,
            "judul": "Dinas Kesehatan Kalbar Dorong Layanan Posyandu Lebih Aktif",
            "tanggal": "2026-07-10",
            "sumber": "Berita Kalbar",
            "kategori": "Kesehatan",
            "url": "https://example.com/posyandu-kalbar",
            "isi": "Dinas Kesehatan Kalimantan Barat mendorong posyandu di berbagai wilayah kembali aktif melayani pemeriksaan ibu dan anak. Program ini menekankan pemantauan tumbuh kembang, imunisasi, dan edukasi gizi keluarga.",
            "gambar": "",
        },
        {
            "id": 5,
            "judul": "Sekolah di Sambas Mulai Terapkan Program Literasi Digital",
            "tanggal": "2026-07-09",
            "sumber": "Berita Kalbar",
            "kategori": "Pendidikan",
            "url": "https://example.com/literasi-digital-sambas",
            "isi": "Sejumlah sekolah di Kabupaten Sambas mulai menerapkan program literasi digital untuk meningkatkan kemampuan siswa menggunakan teknologi secara produktif dan aman. Guru mendapat pendampingan dalam menyusun materi pembelajaran berbasis digital.",
            "gambar": "",
        },
    ]
}


def ensure_data_file(data_file):
    """Ensure data directory exists and a sample JSON file is present."""
    data_file.parent.mkdir(parents=True, exist_ok=True)
    if data_file.exists():
        return
    with data_file.open("w", encoding="utf-8") as file:
        json.dump(SAMPLE_DATA, file, ensure_ascii=False, indent=2)
        file.write("\n")


def load_news_data(data_file):
    """Read and normalize news data from disk.

    Returns a dict with key "berita" and optional "error".
    The returned list is already sorted by tanggal desc, then id desc.
    """
    try:
        with data_file.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {"berita": []}
    except json.JSONDecodeError as exc:
        data = {"berita": [], "error": f"JSON tidak valid: {exc}"}

    berita = data.get("berita", [])
    if not isinstance(berita, list):
        berita = []

    from pure import sort_berita

    return {"berita": sort_berita(berita), "error": data.get("error")}
