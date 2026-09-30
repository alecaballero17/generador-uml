/**
 * CursosDemo — Main Application Controller
 * 
 * Handles routing, UI interactions, CRUD operations via the API layer,
 * and all user-facing features (modals, toasts, search, theme).
 */

'use strict';

document.addEventListener('DOMContentLoaded', () => {
    // ─── DOM References ──────────────────────────────────────────────

    const splash = document.getElementById('splash');
    const app = document.getElementById('app');
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
    const pageTitle = document.getElementById('page-title');
    const themeToggle = document.getElementById('theme-toggle');
    const navItems = document.querySelectorAll('.nav-item');

    // Dashboard
    const countInstructors = document.getElementById('count-instructors');
    const countCourses = document.getElementById('count-courses');
    const countActive = document.getElementById('count-active');
    const activityList = document.getElementById('activity-list');

    // Modal
    const modalOverlay = document.getElementById('modal-overlay');
    const modal = document.getElementById('modal');
    const modalTitle = document.getElementById('modal-title');
    const modalBody = document.getElementById('modal-body');
    const modalClose = document.getElementById('modal-close');
    const modalCancel = document.getElementById('modal-cancel');
    const modalSave = document.getElementById('modal-save');

    // Confirm
    const confirmOverlay = document.getElementById('confirm-overlay');
    const confirmTitle = document.getElementById('confirm-title');
    const confirmMessage = document.getElementById('confirm-message');
    const confirmCancel = document.getElementById('confirm-cancel');
    const confirmOk = document.getElementById('confirm-ok');

    // Toast
    const toastContainer = document.getElementById('toast-container');

    // API Response panel
    const apiResponsePanel = document.getElementById('api-response-panel');
    const apiResponseBody = document.getElementById('api-response-body');
    const apiResponseClose = document.getElementById('api-response-close');

    // Notification badge
    const notifBadge = document.getElementById('notif-badge');

    // State
    let currentPage = 'dashboard';
    let currentModal = null; // { type: 'instructor'|'curso', mode: 'create'|'edit', id?: number }
    let confirmCallback = null;
    let notifCount = 0;

    // ─── Theme ───────────────────────────────────────────────────────

    function initTheme() {
        const saved = localStorage.getItem('cursosDemo_theme');
        if (saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
            document.documentElement.setAttribute('data-theme', 'dark');
            themeToggle.querySelector('.material-icons-round').textContent = 'light_mode';
        }
    }

    themeToggle.addEventListener('click', () => {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        document.documentElement.setAttribute('data-theme', isDark ? 'light' : 'dark');
        localStorage.setItem('cursosDemo_theme', isDark ? 'light' : 'dark');
        themeToggle.querySelector('.material-icons-round').textContent = isDark ? 'dark_mode' : 'light_mode';
    });

    // ─── Splash ──────────────────────────────────────────────────────

    function hideSplash() {
        setTimeout(() => {
            splash.classList.add('fade-out');
            app.classList.remove('hidden');
            setTimeout(() => splash.remove(), 600);
        }, 2000);
    }

    // ─── Sidebar ─────────────────────────────────────────────────────

    sidebarToggle.addEventListener('click', () => {
        sidebar.classList.toggle('collapsed');
    });

    mobileMenuToggle.addEventListener('click', () => {
        sidebar.classList.toggle('mobile-open');
    });

    // Close mobile sidebar on nav click
    function closeMobileSidebar() {
        sidebar.classList.remove('mobile-open');
    }

    // ─── Navigation ──────────────────────────────────────────────────

    const pageTitles = {
        dashboard: 'Dashboard',
        instructores: 'Instructores',
        cursos: 'Cursos Programados',
        api: 'API Explorer',
        about: 'Acerca de',
    };

    function navigateTo(page) {
        if (page === currentPage) return;
        currentPage = page;

        // Update nav
        navItems.forEach(item => {
            item.classList.toggle('active', item.dataset.page === page);
        });

        // Update page
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        const target = document.getElementById(`page-${page}`);
        if (target) target.classList.add('active');

        // Update title
        pageTitle.textContent = pageTitles[page] || page;

        // Refresh data
        if (page === 'dashboard') refreshDashboard();
        if (page === 'instructores') refreshInstructors();
        if (page === 'cursos') refreshCursos();

        closeMobileSidebar();
    }

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            navigateTo(item.dataset.page);
        });
    });

    // ─── Dashboard ───────────────────────────────────────────────────

    function refreshDashboard() {
        const stats = API.getStats();
        animateNumber(countInstructors, stats.instructors);
        animateNumber(countCourses, stats.courses);
        animateNumber(countActive, stats.activeCourses);
        refreshActivityList();
    }

    function animateNumber(el, target) {
        const start = parseInt(el.textContent) || 0;
        if (start === target) return;
        const duration = 600;
        const startTime = performance.now();
        
        function step(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            el.textContent = Math.round(start + (target - start) * eased);
            if (progress < 1) requestAnimationFrame(step);
        }
        requestAnimationFrame(step);
    }

    function refreshActivityList() {
        const activities = API.getActivities();
        if (activities.length === 0) {
            activityList.innerHTML = `
                <div class="activity-empty">
                    <span class="material-icons-round">history</span>
                    <p>Sin actividad reciente</p>
                </div>`;
            return;
        }
        activityList.innerHTML = activities.slice(0, 8).map(a => `
            <div class="activity-item">
                <span class="material-icons-round">${a.icon}</span>
                <span>${a.message}</span>
                <span class="activity-time">${a.time}</span>
            </div>
        `).join('');
    }

    // Quick Actions
    document.getElementById('qa-add-instructor').addEventListener('click', () => {
        navigateTo('instructores');
        setTimeout(() => openInstructorModal('create'), 300);
    });

    document.getElementById('qa-add-curso').addEventListener('click', () => {
        navigateTo('cursos');
        setTimeout(() => openCursoModal('create'), 300);
    });

    document.getElementById('qa-export').addEventListener('click', () => {
        const data = API.exportData();
        const blob = new Blob([data], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'cursos_demo_export.json';
        a.click();
        URL.revokeObjectURL(url);
        showToast('success', 'Datos exportados correctamente');
    });

    // Stat card clicks
    document.getElementById('stat-instructors').addEventListener('click', () => navigateTo('instructores'));
    document.getElementById('stat-courses').addEventListener('click', () => navigateTo('cursos'));
    document.getElementById('stat-active').addEventListener('click', () => navigateTo('cursos'));

    // ─── Instructors ─────────────────────────────────────────────────

    const instructorsTbody = document.getElementById('instructors-tbody');
    const instructorsEmpty = document.getElementById('instructors-empty');
    const instructorSearch = document.getElementById('instructor-search');

    function refreshInstructors(filter = '') {
        let instructors = API.getInstructors();
        const cursos = API.getCursos();
        
        if (filter) {
            const f = filter.toLowerCase();
            instructors = instructors.filter(i => i.nombre.toLowerCase().includes(f));
        }

        if (instructors.length === 0) {
            instructorsTbody.innerHTML = '';
            instructorsEmpty.classList.remove('hidden');
            return;
        }

        instructorsEmpty.classList.add('hidden');
        instructorsTbody.innerHTML = instructors.map(inst => {
            const courseCount = cursos.filter(c => c.instructorId === inst.id).length;
            return `
                <tr>
                    <td><code>#${inst.id}</code></td>
                    <td><strong>${escapeHtml(inst.nombre)}</strong></td>
                    <td>
                        <span class="status-badge ${courseCount > 0 ? 'active' : 'inactive'}">
                            ${courseCount} curso${courseCount !== 1 ? 's' : ''}
                        </span>
                    </td>
                    <td>
                        <div class="table-actions">
                            <button class="table-action-btn edit" data-id="${inst.id}" title="Editar" aria-label="Editar instructor">
                                <span class="material-icons-round">edit</span>
                            </button>
                            <button class="table-action-btn delete" data-id="${inst.id}" title="Eliminar" aria-label="Eliminar instructor">
                                <span class="material-icons-round">delete_outline</span>
                            </button>
                        </div>
                    </td>
                </tr>`;
        }).join('');

        // Bind actions
        instructorsTbody.querySelectorAll('.edit').forEach(btn => {
            btn.addEventListener('click', () => openInstructorModal('edit', Number(btn.dataset.id)));
        });
        instructorsTbody.querySelectorAll('.delete').forEach(btn => {
            btn.addEventListener('click', () => confirmDeleteInstructor(Number(btn.dataset.id)));
        });
    }

    instructorSearch.addEventListener('input', (e) => {
        refreshInstructors(e.target.value);
    });

    document.getElementById('btn-add-instructor').addEventListener('click', () => openInstructorModal('create'));
    document.getElementById('btn-add-instructor-empty').addEventListener('click', () => openInstructorModal('create'));

    function openInstructorModal(mode, id = null) {
        currentModal = { type: 'instructor', mode, id };
        modalTitle.textContent = mode === 'create' ? 'Nuevo Instructor' : 'Editar Instructor';
        
        const existing = id ? API.getInstructor(id) : null;
        modalBody.innerHTML = `
            <div class="form-group">
                <label class="form-label">Nombre <span class="required">*</span></label>
                <input type="text" class="form-input" id="form-nombre" placeholder="Nombre del instructor"
                       value="${existing ? escapeHtml(existing.nombre) : ''}" autofocus>
                <div class="form-error hidden" id="form-nombre-error"></div>
            </div>`;
        
        showModal();
        setTimeout(() => document.getElementById('form-nombre').focus(), 100);
    }

    function confirmDeleteInstructor(id) {
        const inst = API.getInstructor(id);
        if (!inst) return;
        showConfirm(
            'Eliminar Instructor',
            `¿Está seguro que desea eliminar al instructor "${inst.nombre}"?`,
            () => {
                try {
                    API.deleteInstructor(id);
                    refreshInstructors(instructorSearch.value);
                    refreshDashboard();
                    showToast('success', `Instructor "${inst.nombre}" eliminado`);
                    incrementNotif();
                } catch (e) {
                    showToast('error', e.message);
                }
            }
        );
    }

    // ─── Cursos ──────────────────────────────────────────────────────

    const cursosTbody = document.getElementById('cursos-tbody');
    const cursosEmpty = document.getElementById('cursos-empty');
    const cursosSearch = document.getElementById('cursos-search');

    function refreshCursos(filter = '') {
        let cursos = API.getCursos();
        const instructors = API.getInstructors();
        
        if (filter) {
            const f = filter.toLowerCase();
            cursos = cursos.filter(c => c.titulo.toLowerCase().includes(f));
        }

        if (cursos.length === 0) {
            cursosTbody.innerHTML = '';
            cursosEmpty.classList.remove('hidden');
            return;
        }

        cursosEmpty.classList.add('hidden');
        cursosTbody.innerHTML = cursos.map(curso => {
            const instructor = instructors.find(i => i.id === curso.instructorId);
            const fecha = curso.fechaInicio ? formatDate(curso.fechaInicio) : '—';
            return `
                <tr>
                    <td><code>#${curso.id}</code></td>
                    <td><strong>${escapeHtml(curso.titulo)}</strong></td>
                    <td>${fecha}</td>
                    <td>
                        <span class="status-badge ${curso.activo ? 'active' : 'inactive'}">
                            ${curso.activo ? 'Activo' : 'Inactivo'}
                        </span>
                    </td>
                    <td>${instructor ? escapeHtml(instructor.nombre) : '<em style="color:var(--text-3)">Sin asignar</em>'}</td>
                    <td>
                        <div class="table-actions">
                            <button class="table-action-btn edit" data-id="${curso.id}" title="Editar" aria-label="Editar curso">
                                <span class="material-icons-round">edit</span>
                            </button>
                            <button class="table-action-btn delete" data-id="${curso.id}" title="Eliminar" aria-label="Eliminar curso">
                                <span class="material-icons-round">delete_outline</span>
                            </button>
                        </div>
                    </td>
                </tr>`;
        }).join('');

        // Bind actions
        cursosTbody.querySelectorAll('.edit').forEach(btn => {
            btn.addEventListener('click', () => openCursoModal('edit', Number(btn.dataset.id)));
        });
        cursosTbody.querySelectorAll('.delete').forEach(btn => {
            btn.addEventListener('click', () => confirmDeleteCurso(Number(btn.dataset.id)));
        });
    }

    cursosSearch.addEventListener('input', (e) => {
        refreshCursos(e.target.value);
    });

    document.getElementById('btn-add-curso').addEventListener('click', () => openCursoModal('create'));
    document.getElementById('btn-add-curso-empty').addEventListener('click', () => openCursoModal('create'));

    function openCursoModal(mode, id = null) {
        currentModal = { type: 'curso', mode, id };
        modalTitle.textContent = mode === 'create' ? 'Nuevo Curso' : 'Editar Curso';
        
        const existing = id ? API.getCurso(id) : null;
        const instructors = API.getInstructors();
        const instructorOptions = instructors.map(i => 
            `<option value="${i.id}" ${existing && existing.instructorId === i.id ? 'selected' : ''}>${escapeHtml(i.nombre)}</option>`
        ).join('');

        modalBody.innerHTML = `
            <div class="form-group">
                <label class="form-label">Título <span class="required">*</span></label>
                <input type="text" class="form-input" id="form-titulo" placeholder="Título del curso"
                       value="${existing ? escapeHtml(existing.titulo) : ''}">
                <div class="form-error hidden" id="form-titulo-error"></div>
            </div>
            <div class="form-group">
                <label class="form-label">Fecha de Inicio</label>
                <input type="date" class="form-input" id="form-fecha"
                       value="${existing && existing.fechaInicio ? existing.fechaInicio : ''}">
            </div>
            <div class="form-group">
                <label class="form-label">Instructor</label>
                <select class="form-select" id="form-instructor">
                    <option value="">— Sin asignar —</option>
                    ${instructorOptions}
                </select>
            </div>
            <div class="form-group">
                <label class="form-label">Estado</label>
                <div class="toggle-wrapper">
                    <label class="toggle">
                        <input type="checkbox" id="form-activo" ${!existing || existing.activo ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                    <span class="toggle-label" id="toggle-label-activo">${!existing || existing.activo ? 'Activo' : 'Inactivo'}</span>
                </div>
            </div>`;

        // Toggle label update
        const activoCheckbox = document.getElementById('form-activo');
        const toggleLabel = document.getElementById('toggle-label-activo');
        activoCheckbox.addEventListener('change', () => {
            toggleLabel.textContent = activoCheckbox.checked ? 'Activo' : 'Inactivo';
        });

        showModal();
        setTimeout(() => document.getElementById('form-titulo').focus(), 100);
    }

    function confirmDeleteCurso(id) {
        const curso = API.getCurso(id);
        if (!curso) return;
        showConfirm(
            'Eliminar Curso',
            `¿Está seguro que desea eliminar el curso "${curso.titulo}"?`,
            () => {
                try {
                    API.deleteCurso(id);
                    refreshCursos(cursosSearch.value);
                    refreshDashboard();
                    showToast('success', `Curso "${curso.titulo}" eliminado`);
                    incrementNotif();
                } catch (e) {
                    showToast('error', e.message);
                }
            }
        );
    }

    // ─── Modal Logic ─────────────────────────────────────────────────

    function showModal() {
        modalOverlay.classList.remove('hidden');
    }

    function hideModal() {
        modalOverlay.classList.add('hidden');
        currentModal = null;
    }

    modalClose.addEventListener('click', hideModal);
    modalCancel.addEventListener('click', hideModal);
    modalOverlay.addEventListener('click', (e) => {
        if (e.target === modalOverlay) hideModal();
    });

    modalSave.addEventListener('click', () => {
        if (!currentModal) return;

        if (currentModal.type === 'instructor') {
            const nombre = document.getElementById('form-nombre').value;
            const errorEl = document.getElementById('form-nombre-error');
            
            if (!nombre.trim()) {
                errorEl.textContent = 'El nombre es requerido';
                errorEl.classList.remove('hidden');
                document.getElementById('form-nombre').classList.add('error');
                return;
            }

            try {
                if (currentModal.mode === 'create') {
                    API.createInstructor({ nombre });
                    showToast('success', `Instructor "${nombre}" creado exitosamente`);
                } else {
                    API.updateInstructor(currentModal.id, { nombre });
                    showToast('success', `Instructor actualizado`);
                }
                refreshInstructors(instructorSearch.value);
                refreshDashboard();
                incrementNotif();
                hideModal();
            } catch (e) {
                showToast('error', e.message);
            }
        }

        if (currentModal.type === 'curso') {
            const titulo = document.getElementById('form-titulo').value;
            const errorEl = document.getElementById('form-titulo-error');
            
            if (!titulo.trim()) {
                errorEl.textContent = 'El título es requerido';
                errorEl.classList.remove('hidden');
                document.getElementById('form-titulo').classList.add('error');
                return;
            }

            const data = {
                titulo,
                fechaInicio: document.getElementById('form-fecha').value || null,
                instructorId: document.getElementById('form-instructor').value || null,
                activo: document.getElementById('form-activo').checked,
            };

            try {
                if (currentModal.mode === 'create') {
                    API.createCurso(data);
                    showToast('success', `Curso "${titulo}" creado exitosamente`);
                } else {
                    API.updateCurso(currentModal.id, data);
                    showToast('success', `Curso actualizado`);
                }
                refreshCursos(cursosSearch.value);
                refreshDashboard();
                incrementNotif();
                hideModal();
            } catch (e) {
                showToast('error', e.message);
            }
        }
    });

    // ─── Confirm Dialog ──────────────────────────────────────────────

    function showConfirm(title, message, callback) {
        confirmTitle.textContent = title;
        confirmMessage.textContent = message;
        confirmCallback = callback;
        confirmOverlay.classList.remove('hidden');
    }

    function hideConfirm() {
        confirmOverlay.classList.add('hidden');
        confirmCallback = null;
    }

    confirmCancel.addEventListener('click', hideConfirm);
    confirmOverlay.addEventListener('click', (e) => {
        if (e.target === confirmOverlay) hideConfirm();
    });

    confirmOk.addEventListener('click', () => {
        if (confirmCallback) confirmCallback();
        hideConfirm();
    });

    // ─── Toast ───────────────────────────────────────────────────────

    function showToast(type, message, duration = 4000) {
        const icons = {
            success: 'check_circle',
            error: 'error',
            info: 'info',
            warning: 'warning',
        };

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <span class="material-icons-round">${icons[type] || 'info'}</span>
            <span class="toast-text">${escapeHtml(message)}</span>
            <button class="toast-close" aria-label="Close">
                <span class="material-icons-round">close</span>
            </button>`;
        
        toastContainer.appendChild(toast);

        toast.querySelector('.toast-close').addEventListener('click', () => removeToast(toast));

        setTimeout(() => removeToast(toast), duration);
    }

    function removeToast(toast) {
        if (!toast.parentNode) return;
        toast.classList.add('removing');
        setTimeout(() => toast.remove(), 300);
    }

    // ─── Notifications ───────────────────────────────────────────────

    function incrementNotif() {
        notifCount++;
        notifBadge.textContent = notifCount;
        notifBadge.setAttribute('data-count', notifCount);
    }

    document.getElementById('notif-btn').addEventListener('click', () => {
        notifCount = 0;
        notifBadge.textContent = '0';
        notifBadge.setAttribute('data-count', '0');
        showToast('info', 'Notificaciones limpiadas');
    });

    // ─── API Explorer ────────────────────────────────────────────────

    document.querySelectorAll('.btn-try').forEach(btn => {
        btn.addEventListener('click', () => {
            const endpoint = btn.dataset.endpoint;
            let data;
            if (endpoint === 'GET /api/instructors') {
                data = API.getInstructors();
            } else if (endpoint === 'GET /api/curso-programados') {
                data = API.getCursos();
            }
            apiResponseBody.textContent = JSON.stringify(data, null, 2);
            apiResponsePanel.classList.add('visible');
        });
    });

    apiResponseClose.addEventListener('click', () => {
        apiResponsePanel.classList.remove('visible');
    });

    // ─── Keyboard Shortcuts ──────────────────────────────────────────

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            if (!modalOverlay.classList.contains('hidden')) hideModal();
            if (!confirmOverlay.classList.contains('hidden')) hideConfirm();
        }
        // Enter to save in modals
        if (e.key === 'Enter' && !modalOverlay.classList.contains('hidden')) {
            e.preventDefault();
            modalSave.click();
        }
    });

    // ─── Utilities ───────────────────────────────────────────────────

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function formatDate(dateStr) {
        if (!dateStr) return '—';
        try {
            const d = new Date(dateStr + 'T00:00:00');
            return d.toLocaleDateString('es', { day: '2-digit', month: 'short', year: 'numeric' });
        } catch {
            return dateStr;
        }
    }

    // ─── Init ────────────────────────────────────────────────────────

    initTheme();
    hideSplash();
    refreshDashboard();
});
