/**
 * Utility functions — Laporan Pembongkaran BBM SPBU
 */

// ============================================================
// SIDEBAR TOGGLE
// ============================================================
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    sidebar.classList.toggle('-translate-x-full');
    overlay.classList.toggle('hidden');
}

// ============================================================
// USER DROPDOWN
// ============================================================
function toggleUserDropdown() {
    const dropdown = document.getElementById('user-dropdown');
    if (dropdown) {
        dropdown.classList.toggle('hidden');
    }
}

// Close dropdown when clicking outside
document.addEventListener('click', (e) => {
    const container = document.getElementById('user-dropdown-container');
    const dropdown = document.getElementById('user-dropdown');
    if (container && dropdown && !container.contains(e.target)) {
        dropdown.classList.add('hidden');
    }
});

// ============================================================
// MODAL HELPERS
// ============================================================
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('open');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('open');
        document.body.style.overflow = '';
    }
}

// Close modal on backdrop click
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-backdrop')) {
        e.target.classList.remove('open');
        document.body.style.overflow = '';
    }
});

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal-backdrop.open').forEach(modal => {
            modal.classList.remove('open');
        });
        document.body.style.overflow = '';
    }
});

// ============================================================
// TOAST NOTIFICATION
// ============================================================
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    const colors = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        info: 'bg-blue-500',
        warning: 'bg-yellow-500',
    };

    toast.className = `fixed top-4 right-4 z-[200] ${colors[type] || colors.info} text-white px-4 py-3 rounded-xl shadow-lg text-sm font-medium transform translate-x-full transition-transform duration-300`;
    toast.textContent = message;
    document.body.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => {
        toast.classList.remove('translate-x-full');
        toast.classList.add('translate-x-0');
    });

    // Auto remove after 3s
    setTimeout(() => {
        toast.classList.remove('translate-x-0');
        toast.classList.add('translate-x-full');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ============================================================
// FORMAT HELPERS
// ============================================================
function formatTanggal(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des'];
    return `${date.getDate()} ${months[date.getMonth()]} ${date.getFullYear()}`;
}

function formatAngka(num) {
    if (num === null || num === undefined) return '0';
    return num.toLocaleString('id-ID');
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

// ============================================================
// FILE UPLOAD PREVIEW
// ============================================================
function setupUploadPreview(inputId, previewContainerId) {
    const input = document.getElementById(inputId);
    const container = document.getElementById(previewContainerId);
    if (!input || !container) return;

    input.addEventListener('change', (e) => {
        container.innerHTML = '';
        const files = Array.from(e.target.files);

        files.forEach((file, index) => {
            if (!file.type.startsWith('image/')) return;

            const reader = new FileReader();
            reader.onload = (ev) => {
                const div = document.createElement('div');
                div.className = 'gallery-item';
                div.innerHTML = `
                    <img src="${ev.target.result}" alt="${file.name}">
                    <div class="absolute inset-0 bg-black/0 hover:bg-black/20 transition flex items-center justify-center opacity-0 hover:opacity-100">
                        <button type="button" onclick="this.closest('.gallery-item').remove()" class="bg-white/90 rounded-full p-1.5 hover:bg-white transition">
                            <svg class="w-4 h-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
                        </button>
                    </div>
                `;
                container.appendChild(div);
            };
            reader.readAsDataURL(file);
        });
    });
}

// ============================================================
// DRAG & DROP
// ============================================================
function setupDragDrop(zoneId, inputId) {
    const zone = document.getElementById(zoneId);
    const input = document.getElementById(inputId);
    if (!zone || !input) return;

    zone.addEventListener('click', () => input.click());

    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        zone.classList.add('dragover');
    });

    zone.addEventListener('dragleave', () => {
        zone.classList.remove('dragover');
    });

    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('dragover');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            // Create a new DataTransfer to set files on input
            const dt = new DataTransfer();
            Array.from(files).forEach(f => dt.items.add(f));
            input.files = dt.files;
            input.dispatchEvent(new Event('change'));
        }
    });
}

// ============================================================
// SEARCH / FILTER (debounce)
// ============================================================
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ============================================================
// CONFIRM DIALOG (Custom)
// ============================================================
function confirmAction(message, onConfirm, options = {}) {
    const title = options.title || 'Konfirmasi';
    const confirmText = options.confirmText || 'Ya, Lanjutkan';
    const cancelText = options.cancelText || 'Batal';
    const type = options.type || 'warning'; // warning, danger, info

    // Create modal if not exists
    let modal = document.getElementById('custom-confirm-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'custom-confirm-modal';
        modal.className = 'modal-backdrop';
        modal.innerHTML = `
            <div class="modal-content max-w-md">
                <div class="p-6">
                    <div class="flex items-center gap-3 mb-4">
                        <div id="confirm-icon" class="w-10 h-10 rounded-full flex items-center justify-center shrink-0"></div>
                        <h3 id="confirm-title" class="text-lg font-semibold text-gray-800"></h3>
                    </div>
                    <p id="confirm-message" class="text-sm text-gray-600 mb-6"></p>
                    <div class="flex gap-3">
                        <button id="confirm-cancel" class="flex-1 py-2.5 border border-gray-300 text-gray-700 font-medium rounded-xl text-sm hover:bg-gray-50 transition"></button>
                        <button id="confirm-ok" class="flex-1 py-2.5 text-white font-semibold rounded-xl text-sm transition"></button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    // Set content
    document.getElementById('confirm-title').textContent = title;
    document.getElementById('confirm-message').textContent = message;
    document.getElementById('confirm-cancel').textContent = cancelText;
    document.getElementById('confirm-ok').textContent = confirmText;

    // Set icon and button color based on type
    const iconEl = document.getElementById('confirm-icon');
    const okBtn = document.getElementById('confirm-ok');

    if (type === 'danger') {
        iconEl.className = 'w-10 h-10 rounded-full bg-red-100 flex items-center justify-center shrink-0';
        iconEl.innerHTML = '<svg class="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>';
        okBtn.className = 'flex-1 py-2.5 bg-red-600 text-white font-semibold rounded-xl text-sm hover:bg-red-700 transition';
    } else if (type === 'info') {
        iconEl.className = 'w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center shrink-0';
        iconEl.innerHTML = '<svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>';
        okBtn.className = 'flex-1 py-2.5 bg-pertamina-blue text-white font-semibold rounded-xl text-sm hover:bg-pertamina-blue-dark transition';
    } else {
        // warning (default)
        iconEl.className = 'w-10 h-10 rounded-full bg-yellow-100 flex items-center justify-center shrink-0';
        iconEl.innerHTML = '<svg class="w-5 h-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>';
        okBtn.className = 'flex-1 py-2.5 bg-pertamina-blue text-white font-semibold rounded-xl text-sm hover:bg-pertamina-blue-dark transition';
    }

    // Show modal
    modal.classList.add('open');
    document.body.style.overflow = 'hidden';

    // Handle buttons
    const cancelBtn = document.getElementById('confirm-cancel');
    const close = () => {
        modal.classList.remove('open');
        document.body.style.overflow = '';
    };

    cancelBtn.onclick = close;
    okBtn.onclick = () => {
        close();
        if (onConfirm) onConfirm();
    };

    // Close on backdrop click
    modal.onclick = (e) => {
        if (e.target === modal) close();
    };
}

// ============================================================
// DARK MODE TOGGLE
// ============================================================
function toggleDarkMode() {
    const html = document.documentElement;
    const isDark = html.classList.toggle('dark');
    
    // Update icons
    const lightIcon = document.getElementById('dark-mode-icon-light');
    const darkIcon = document.getElementById('dark-mode-icon-dark');
    
    if (isDark) {
        lightIcon?.classList.add('hidden');
        darkIcon?.classList.remove('hidden');
    } else {
        lightIcon?.classList.remove('hidden');
        darkIcon?.classList.add('hidden');
    }
    
    // Save preference
    localStorage.setItem('darkMode', isDark ? 'true' : 'false');
    
    // Show toast
    showToast(isDark ? 'Mode gelap diaktifkan' : 'Mode terang diaktifkan', 'info');
}

// Initialize dark mode from localStorage
function initDarkMode() {
    const isDark = localStorage.getItem('darkMode') === 'true';
    const html = document.documentElement;
    const lightIcon = document.getElementById('dark-mode-icon-light');
    const darkIcon = document.getElementById('dark-mode-icon-dark');
    
    if (isDark) {
        html.classList.add('dark');
        lightIcon?.classList.add('hidden');
        darkIcon?.classList.remove('hidden');
    }
}

// ============================================================
// INIT ON LOAD
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
    // Initialize dark mode
    initDarkMode();
    
    // Auto-dismiss flash messages after 5s
    document.querySelectorAll('.flash-msg').forEach(msg => {
        setTimeout(() => {
            msg.style.opacity = '0';
            msg.style.transform = 'translateX(100%)';
            msg.style.transition = 'all 0.3s ease';
            setTimeout(() => msg.remove(), 300);
        }, 5000);
    });
});

// ============================================================
// LOADING STATE HELPERS
// ============================================================
function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (!element) return;

    // Add loading overlay
    let overlay = element.querySelector('.loading-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.className = 'loading-overlay';
        overlay.innerHTML = '<div class="spinner"></div>';
        element.style.position = 'relative';
        element.appendChild(overlay);
    }
    overlay.classList.add('active');
}

function hideLoading(elementId) {
    const element = document.getElementById(elementId);
    if (!element) return;

    const overlay = element.querySelector('.loading-overlay');
    if (overlay) {
        overlay.classList.remove('active');
    }
}

// Show skeleton loading
function showSkeleton(containerId, type = 'card', count = 3) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // Store original content
    if (!container.dataset.originalContent) {
        container.dataset.originalContent = container.innerHTML;
    }

    let skeletonHtml = '';

    if (type === 'card') {
        for (let i = 0; i < count; i++) {
            skeletonHtml += `
                <div class="skeleton skeleton-card"></div>
            `;
        }
    } else if (type === 'table') {
        for (let i = 0; i < count; i++) {
            skeletonHtml += `
                <div class="flex items-center gap-4 p-4 border-b border-gray-100">
                    <div class="skeleton skeleton-avatar"></div>
                    <div class="flex-1">
                        <div class="skeleton skeleton-text" style="width: 60%"></div>
                        <div class="skeleton skeleton-text-sm" style="width: 40%"></div>
                    </div>
                    <div class="skeleton" style="width: 4rem; height: 1.5rem"></div>
                </div>
            `;
        }
    } else if (type === 'chart') {
        skeletonHtml = `<div class="skeleton skeleton-chart"></div>`;
    }

    container.innerHTML = skeletonHtml;
}

// Hide skeleton and restore content
function hideSkeleton(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (container.dataset.originalContent) {
        container.innerHTML = container.dataset.originalContent;
        delete container.dataset.originalContent;
    }
}
