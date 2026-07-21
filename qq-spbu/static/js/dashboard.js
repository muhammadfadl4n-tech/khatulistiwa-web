/**
 * Dashboard charts & map — Laporan Pembongkaran BBM SPBU
 */

// ============================================================
// CHART DEFAULTS
// ============================================================
Chart.defaults.font.family = "'Inter', system-ui, sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.color = '#6b7280';
Chart.defaults.plugins.legend.display = false;

// ============================================================
// LINE CHART: Tren Laporan
// ============================================================
function initTrenChart() {
    const ctx = document.getElementById('trenChart');
    if (!ctx) return;

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: trenLabels,
            datasets: [{
                label: 'Laporan',
                data: trenData,
                borderColor: '#1E40AF',
                backgroundColor: 'rgba(30, 64, 175, 0.08)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 6,
                pointHoverBackgroundColor: '#1E40AF',
                pointHoverBorderColor: '#fff',
                pointHoverBorderWidth: 2,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index',
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: {
                        maxTicksLimit: 7,
                        font: { size: 11 },
                    },
                },
                y: {
                    beginAtZero: true,
                    grid: { color: '#f3f4f6' },
                    ticks: {
                        stepSize: 1,
                        font: { size: 11 },
                    },
                },
            },
            plugins: {
                tooltip: {
                    backgroundColor: '#1f2937',
                    titleFont: { size: 12, weight: '600' },
                    bodyFont: { size: 11 },
                    padding: 10,
                    cornerRadius: 8,
                    displayColors: false,
                },
            },
        },
    });
}

// ============================================================
// BAR CHART: Per Kabupaten
// ============================================================
function initKabupatenChart() {
    const ctx = document.getElementById('kabupatenChart');
    if (!ctx) return;

    const colors = ['#1E40AF', '#3B82F6', '#60A5FA', '#93C5FD', '#BFDBFE', '#1E3A8A', '#2563EB'];

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: kotaLabels,
            datasets: [{
                label: 'Laporan',
                data: kotaData,
                backgroundColor: kotaData.map((_, i) => colors[i % colors.length]),
                borderRadius: 6,
                borderSkipped: false,
                barThickness: 'flex',
                maxBarThickness: 40,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: kotaLabels.length > 5 ? 'y' : 'x',
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { font: { size: 11 } },
                },
                y: {
                    grid: { color: '#f3f4f6' },
                    ticks: { font: { size: 11 } },
                },
            },
            plugins: {
                tooltip: {
                    backgroundColor: '#1f2937',
                    cornerRadius: 8,
                    padding: 10,
                },
            },
        },
    });
}

// ============================================================
// PIE/DOUGHNUT CHART: Jenis BBM
// ============================================================
function initBbmChart() {
    const ctx = document.getElementById('bbmChart');
    if (!ctx) return;

    const colors = ['#1E40AF', '#DC2626', '#059669', '#D97706', '#7C3AED', '#0891B2'];

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: bbmLabels,
            datasets: [{
                data: bbmData,
                backgroundColor: colors.slice(0, bbmLabels.length),
                borderWidth: 0,
                hoverOffset: 8,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '65%',
            plugins: {
                legend: {
                    display: true,
                    position: 'bottom',
                    labels: {
                        padding: 12,
                        usePointStyle: true,
                        pointStyle: 'circle',
                        font: { size: 11 },
                    },
                },
                tooltip: {
                    backgroundColor: '#1f2937',
                    cornerRadius: 8,
                    padding: 10,
                },
            },
        },
    });
}

// ============================================================
// LEAFLET MAP
// ============================================================
function initMap() {
    const mapEl = document.getElementById('map');
    if (!mapEl) return;

    const map = L.map('map').setView([-0.5, 109.5], 7);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 18,
    }).addTo(map);

    // Add markers
    if (typeof spbuList !== 'undefined') {
        spbuList.forEach(spbu => {
            const color = '#1E40AF';
            const icon = L.divIcon({
                className: 'custom-marker',
                html: `<div style="background:${color};width:24px;height:24px;border-radius:50%;border:3px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.3);"></div>`,
                iconSize: [24, 24],
                iconAnchor: [12, 12],
            });

            L.marker([spbu.lat, spbu.lng], { icon })
                .addTo(map)
                .bindPopup(`
                    <div style="min-width:180px">
                        <p style="font-weight:600;font-size:13px;margin:0 0 4px">${spbu.nama_pt}</p>
                        <p style="font-size:11px;color:#6b7280;margin:0 0 2px">${spbu.nomor_spbu}</p>
                        <p style="font-size:11px;color:#6b7280;margin:0">${spbu.kota}</p>
                    </div>
                `);
        });
    }

    // Fix map rendering in hidden/resize scenarios
    setTimeout(() => map.invalidateSize(), 100);
    window.addEventListener('resize', () => map.invalidateSize());
}
