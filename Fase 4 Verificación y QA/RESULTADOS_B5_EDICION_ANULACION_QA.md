# B5 ? Edici?n y anulaci?n de registros acad?micos

**Requisito:** permitir corregir y anular registros; la correcci?n de actas queda exclusivamente a cargo del PRECEPTOR (D2). Toda anulaci?n deja `activo = FALSE` y debe quedar auditada.

## Implementaci?n

- PRECEPTOR puede corregir notas de cursada y los campos de actas (fecha, libro, folio, nota y estado).
- PRECEPTOR puede anular inscripciones a cursada, notas y actas mediante baja l?gica. No se eliminan f?sicamente desde el panel.
- Las actas y notas usan sus triggers de auditor?a; la anulaci?n de inscripciones agrega el evento al procedimiento `sp_auditar`.
- DOCENTE conserva la carga de actas, pero cualquier intento de corregir o anular un registro recibe HTTP 403.
- Las notas de cursadas anuladas quedan excluidas de los listados activos.

## Verificaci?n

Ejecutar `python "Fase 4 Verificaci?n y QA/pruebas/test_b5_edicion_anulacion_base_qa.py"`. El script se limita a `gestion_academica_a1_qa`, crea datos temporales, comprueba permisos, los valores `activo=0` y los eventos de auditor?a asociados al usuario PRECEPTOR; despu?s elimina las filas temporales y desactiva las cuentas de prueba.

**Resultado:** CUMPLE en MariaDB 10.4.32 (`gestion_academica_a1_qa`). PRECEPTOR corrigi? un acta; la anulaci?n de otra acta, una nota y una inscripci?n dej? `activo=0`. Los tres tipos de anulaci?n y la correcci?n del acta quedaron auditados con el usuario PRECEPTOR. El intento de DOCENTE de corregir el acta fue rechazado con HTTP 403 y los registros temporales se limpiaron.
