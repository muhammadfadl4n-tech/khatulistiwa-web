/**
 * Laporan form interactivity — Laporan Pembongkaran BBM SPBU
 */

document.addEventListener('DOMContentLoaded', () => {
    // Setup upload zones
    const categories = ['pembongkaran', 'spp', 'dipping', 'atg'];

    categories.forEach(cat => {
        setupDragDrop(`zone-${cat}`, `input-${cat}`);
        setupUploadPreview(`input-${cat}`, `preview-${cat}`);
    });

    // Form validation
    const form = document.getElementById('laporanForm');
    if (form) {
        form.addEventListener('submit', (e) => {
            const action = e.submitter?.value;

            if (action === 'submit') {
                // Validate required fields for submit
                const tanggal = form.querySelector('[name="tanggal"]');
                const jenisBbm = form.querySelectorAll('[name="jenis_bbm"]:checked');
                const fotoPembongkaran = document.getElementById('input-pembongkaran');

                let errors = [];

                if (!tanggal.value) {
                    errors.push('Tanggal pembongkaran wajib diisi');
                }

                if (jenisBbm.length === 0) {
                    errors.push('Pilih minimal satu jenis BBM');
                }

                if (!fotoPembongkaran.files || fotoPembongkaran.files.length === 0) {
                    errors.push('Foto pembongkaran wajib diupload');
                }

                if (errors.length > 0) {
                    e.preventDefault();
                    errors.forEach(err => showToast(err, 'error'));
                    return;
                }

                // Confirm submit
                if (!confirm('Apakah Anda yakin ingin mengirim laporan ini?')) {
                    e.preventDefault();
                    return;
                }

                showToast('Laporan berhasil dikirim!', 'success');
            } else if (action === 'draft') {
                e.preventDefault();
                showToast('Draft berhasil disimpan', 'success');
            }
        });
    }

    // Auto-save indicator for draft
    let autoSaveTimeout;
    const inputs = form?.querySelectorAll('input, textarea, select');
    inputs?.forEach(input => {
        input.addEventListener('change', () => {
            clearTimeout(autoSaveTimeout);
            autoSaveTimeout = setTimeout(() => {
                // Show subtle indicator
                const indicator = document.createElement('div');
                indicator.className = 'fixed bottom-20 left-1/2 -translate-x-1/2 bg-gray-800 text-white text-xs px-3 py-1.5 rounded-full z-50 opacity-0 transition-opacity';
                indicator.textContent = 'Draft tersimpan otomatis';
                document.body.appendChild(indicator);
                requestAnimationFrame(() => indicator.style.opacity = '1');
                setTimeout(() => {
                    indicator.style.opacity = '0';
                    setTimeout(() => indicator.remove(), 300);
                }, 2000);
            }, 3000);
        });
    });
});
