/**
 * CursosDemo — In-Memory API Mock Layer
 * 
 * Provides a localStorage-backed CRUD API that mirrors the Spring Boot REST
 * endpoints. This allows the web app to run 100% on localhost without
 * requiring the Java backend.
 */

'use strict';

const API = (() => {
    const STORAGE_KEY_INSTRUCTORS = 'cursosDemo_instructors';
    const STORAGE_KEY_CURSOS = 'cursosDemo_cursos';
    const STORAGE_KEY_ACTIVITY = 'cursosDemo_activity';

    let _nextInstructorId = 1;
    let _nextCursoId = 1;

    // ─── Helpers ─────────────────────────────────────────────────────

    function _load(key) {
        try {
            const raw = localStorage.getItem(key);
            return raw ? JSON.parse(raw) : [];
        } catch {
            return [];
        }
    }

    function _save(key, data) {
        localStorage.setItem(key, JSON.stringify(data));
    }

    function _initIds() {
        const instructors = _load(STORAGE_KEY_INSTRUCTORS);
        const cursos = _load(STORAGE_KEY_CURSOS);
        _nextInstructorId = instructors.length > 0
            ? Math.max(...instructors.map(i => i.id)) + 1 : 1;
        _nextCursoId = cursos.length > 0
            ? Math.max(...cursos.map(c => c.id)) + 1 : 1;
    }

    // Seed sample data if empty
    function _seedIfEmpty() {
        const instructors = _load(STORAGE_KEY_INSTRUCTORS);
        if (instructors.length === 0) {
            const seedInstructors = [
                { id: 1, nombre: 'Carlos Mendoza' },
                { id: 2, nombre: 'Ana García' },
                { id: 3, nombre: 'Luis Fernández' },
            ];
            const seedCursos = [
                { id: 1, titulo: 'Programación Java Avanzada', fechaInicio: '2026-10-01', activo: true, instructorId: 1 },
                { id: 2, titulo: 'Desarrollo Web con Spring Boot', fechaInicio: '2026-10-15', activo: true, instructorId: 1 },
                { id: 3, titulo: 'Flutter & Dart Mobile', fechaInicio: '2026-11-01', activo: true, instructorId: 2 },
                { id: 4, titulo: 'Bases de Datos PostgreSQL', fechaInicio: '2026-09-15', activo: false, instructorId: 3 },
                { id: 5, titulo: 'Arquitectura de Software', fechaInicio: '2026-12-01', activo: true, instructorId: 2 },
            ];
            _save(STORAGE_KEY_INSTRUCTORS, seedInstructors);
            _save(STORAGE_KEY_CURSOS, seedCursos);
            _nextInstructorId = 4;
            _nextCursoId = 6;
        }
    }

    // ─── Activity Log ────────────────────────────────────────────────

    function _logActivity(icon, message) {
        const activities = _load(STORAGE_KEY_ACTIVITY);
        activities.unshift({
            icon,
            message,
            time: new Date().toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit' }),
        });
        // Keep only last 20
        if (activities.length > 20) activities.length = 20;
        _save(STORAGE_KEY_ACTIVITY, activities);
    }

    function getActivities() {
        return _load(STORAGE_KEY_ACTIVITY);
    }

    // ─── Instructor CRUD ─────────────────────────────────────────────

    function getInstructors() {
        return _load(STORAGE_KEY_INSTRUCTORS);
    }

    function getInstructor(id) {
        return getInstructors().find(i => i.id === Number(id)) || null;
    }

    function createInstructor(data) {
        const instructors = getInstructors();
        if (!data.nombre || !data.nombre.trim()) {
            throw new Error('El nombre es requerido');
        }
        const instructor = {
            id: _nextInstructorId++,
            nombre: data.nombre.trim(),
        };
        instructors.push(instructor);
        _save(STORAGE_KEY_INSTRUCTORS, instructors);
        _logActivity('person_add', `Instructor "${instructor.nombre}" creado`);
        return instructor;
    }

    function updateInstructor(id, data) {
        const instructors = getInstructors();
        const idx = instructors.findIndex(i => i.id === Number(id));
        if (idx === -1) throw new Error('Instructor no encontrado');
        if (!data.nombre || !data.nombre.trim()) {
            throw new Error('El nombre es requerido');
        }
        instructors[idx] = { ...instructors[idx], nombre: data.nombre.trim() };
        _save(STORAGE_KEY_INSTRUCTORS, instructors);
        _logActivity('edit', `Instructor "${instructors[idx].nombre}" actualizado`);
        return instructors[idx];
    }

    function deleteInstructor(id) {
        const instructors = getInstructors();
        const instructor = instructors.find(i => i.id === Number(id));
        if (!instructor) throw new Error('Instructor no encontrado');
        
        // Check if instructor has courses
        const cursos = getCursos().filter(c => c.instructorId === Number(id));
        if (cursos.length > 0) {
            throw new Error(`No se puede eliminar: tiene ${cursos.length} curso(s) asignado(s)`);
        }
        
        const filtered = instructors.filter(i => i.id !== Number(id));
        _save(STORAGE_KEY_INSTRUCTORS, filtered);
        _logActivity('person_remove', `Instructor "${instructor.nombre}" eliminado`);
        return true;
    }

    // ─── CursoProgramado CRUD ────────────────────────────────────────

    function getCursos() {
        return _load(STORAGE_KEY_CURSOS);
    }

    function getCurso(id) {
        return getCursos().find(c => c.id === Number(id)) || null;
    }

    function createCurso(data) {
        const cursos = getCursos();
        if (!data.titulo || !data.titulo.trim()) {
            throw new Error('El título es requerido');
        }
        const curso = {
            id: _nextCursoId++,
            titulo: data.titulo.trim(),
            fechaInicio: data.fechaInicio || null,
            activo: data.activo !== undefined ? Boolean(data.activo) : true,
            instructorId: data.instructorId ? Number(data.instructorId) : null,
        };
        cursos.push(curso);
        _save(STORAGE_KEY_CURSOS, cursos);
        _logActivity('add_circle', `Curso "${curso.titulo}" creado`);
        return curso;
    }

    function updateCurso(id, data) {
        const cursos = getCursos();
        const idx = cursos.findIndex(c => c.id === Number(id));
        if (idx === -1) throw new Error('Curso no encontrado');
        if (!data.titulo || !data.titulo.trim()) {
            throw new Error('El título es requerido');
        }
        cursos[idx] = {
            ...cursos[idx],
            titulo: data.titulo.trim(),
            fechaInicio: data.fechaInicio || cursos[idx].fechaInicio,
            activo: data.activo !== undefined ? Boolean(data.activo) : cursos[idx].activo,
            instructorId: data.instructorId ? Number(data.instructorId) : cursos[idx].instructorId,
        };
        _save(STORAGE_KEY_CURSOS, cursos);
        _logActivity('edit', `Curso "${cursos[idx].titulo}" actualizado`);
        return cursos[idx];
    }

    function deleteCurso(id) {
        const cursos = getCursos();
        const curso = cursos.find(c => c.id === Number(id));
        if (!curso) throw new Error('Curso no encontrado');
        const filtered = cursos.filter(c => c.id !== Number(id));
        _save(STORAGE_KEY_CURSOS, filtered);
        _logActivity('delete', `Curso "${curso.titulo}" eliminado`);
        return true;
    }

    // ─── Stats ───────────────────────────────────────────────────────

    function getStats() {
        const instructors = getInstructors();
        const cursos = getCursos();
        return {
            instructors: instructors.length,
            courses: cursos.length,
            activeCourses: cursos.filter(c => c.activo).length,
        };
    }

    // ─── Export ──────────────────────────────────────────────────────

    function exportData() {
        return JSON.stringify({
            instructors: getInstructors(),
            cursos: getCursos(),
            exportedAt: new Date().toISOString(),
        }, null, 2);
    }

    // ─── Init ────────────────────────────────────────────────────────

    _seedIfEmpty();
    _initIds();

    return {
        getInstructors,
        getInstructor,
        createInstructor,
        updateInstructor,
        deleteInstructor,
        getCursos,
        getCurso,
        createCurso,
        updateCurso,
        deleteCurso,
        getStats,
        getActivities,
        exportData,
    };
})();
