# B3 ? Asignaci?n de docentes por materia y ciclo

**Requisito:** RF-GAC-07. Un docente asignado puede cargar notas de su materia y ciclo, sin acceso a otras cursadas.

## Implementaci?n

- Pantalla `/asignaciones-docentes`, disponible para ADMIN, PRECEPTOR y DIRECTIVO.
- PRECEPTOR puede crear una asignaci?n eligiendo un docente activo, una materia activa y un ciclo lectivo.
- ADMIN y DIRECTIVO consultan la tabla; los intentos de modificaci?n se rechazan con HTTP 403.
- El m?dulo de cursadas limita el listado de docentes y valida en servidor cada nota usando la asignaci?n docente-materia-ciclo.

## Verificaci?n

Ejecutar `python "Fase 4 Verificaci?n y QA/pruebas/test_b3_asignaciones_base_qa.py"` con MariaDB local disponible. El script se restringe expl?citamente a `gestion_academica_a1_qa`; crea datos de prueba temporales y los elimina en `finally`.

**Resultado:** CUMPLE en MariaDB 10.4.32 (`gestion_academica_a1_qa`). PRECEPTOR abri? la pantalla y guard? la asignaci?n (HTTP 200); DOCENTE vio solo la materia asignada, registr? all? una nota y el intento en otra materia fue rechazado con HTTP 403. El script confirm? una ?nica nota temporal y limpi? los registros de prueba.
