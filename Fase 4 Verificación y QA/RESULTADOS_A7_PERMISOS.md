# Resultados A7 — Permisos del panel por rol

**Alcance:** permisos del panel web y protección de datos académicos por rol, según la matriz A7.

## Reglas aplicadas

| Rol | Acceso y operaciones |
|---|---|
| ADMIN | Consulta los datos académicos; no crea ni modifica alumnos, estructura, docentes, cursadas o asistencias desde las rutas académicas. Conserva la administración de usuarios y la carga masiva. |
| PRECEPTOR | Gestiona alumnos, carreras, materias, docentes y ciclos; administra cursadas y asistencias. |
| DOCENTE | Consulta únicamente los datos básicos de alumnos vinculados a sus materias asignadas. Registra notas y asistencias dentro de sus asignaciones; no administra estructura, usuarios, cargas masivas ni reportes individuales. |
| DIRECTIVO | Consulta información académica y reportes; no ejecuta operaciones de escritura. |

Los controles se aplican en el servidor, además de ocultar acciones no disponibles en las plantillas. Por ello, enviar un POST directamente a una ruta no habilitada devuelve `403`.

## Ajuste de alcance docente

Al registrar un acta, la ruta `/cursadas` ya comprobaba que el docente tuviera asignada la materia y el ciclo enviados. Se agregó una segunda comprobación para exigir que la mesa elegida esté activa y corresponda a esa misma materia y ciclo. Esto impide asociar el acta a una mesa de otro ciclo aunque comparta materia.

## Cobertura existente

`pruebas/test_web_permisos_y_plantillas.py` incluye comprobaciones de lectura académica del ADMIN, escritura del PRECEPTOR, limitación de datos del DOCENTE en alumnos y búsqueda, y denegación de acceso docente a docentes. Esta actualización no ejecutó la suite.
