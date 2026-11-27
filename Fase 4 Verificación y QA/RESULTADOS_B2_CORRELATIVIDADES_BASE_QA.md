# B2 — Pantalla de correlatividades

**Fecha:** 26/11/2026  
**Esquema de prueba:** `gestion_academica_a1_qa`  
**Motor:** MariaDB 10.4.32

## Implementación

Se agregó `/correlatividades` y su enlace de navegación para ADMIN, PRECEPTOR y DIRECTIVO. PRECEPTOR puede definir reglas; ADMIN y DIRECTIVO solo consultan. El formulario usa materias activas, rechaza una materia correlativa de sí misma y evita ciclos entre reglas. La lista muestra la materia que requiere aprobación previa y su correlativa.

Al intentar una inscripción a cursada, el panel comprueba que el alumno tenga un acta activa `APROBADO` de cada materia requerida. Si falta una, muestra el código `ERR_06_CORRELATIVA` y no inserta la inscripción.

## Verificación

Se ejecutó `pruebas/test_b2_correlatividades_base_qa.py` contra MariaDB real en el esquema aislado de QA, con acceso SQL directo de la aplicación y sin cursores simulados.

| Caso | Resultado |
|---|---|
| PRECEPTOR define una correlativa y la ve en la lista | OK |
| ADMIN ve la pantalla en modo consulta | OK |
| ADMIN intenta modificar la regla | HTTP 403 |
| Se intenta crear una relación circular | Rechazada |
| Alumno sin acta aprobada intenta inscribirse en la materia objetivo | Bloqueado con `ERR_06_CORRELATIVA` |
| Inscripción creada por el intento bloqueado | 0 filas |

El esquema QA quedó sin correlatividades, ciclos ni inscripciones de prueba. Los conteos académicos se mantuvieron en 80 alumnos y 189 actas. Las cuatro cuentas sintéticas creadas en las dos ejecuciones están inactivas; no se modificó `gestion_academica_v2`.
