# B4 ? Matr?culas por carrera

**Requisito:** RF-GAC-11. Registrar y consultar la carrera asociada a cada alumno.

## Implementaci?n

- Pantalla `/matriculas` disponible para ADMIN, PRECEPTOR y DIRECTIVO.
- PRECEPTOR puede matricular un alumno activo en una carrera activa e indicar el a?o de ingreso.
- La pantalla lista alumno, legajo, carrera, a?o y estado de cada matr?cula.
- ADMIN y DIRECTIVO consultan; las altas de otros roles se rechazan en el servidor.
- Se valida rango de a?o y se previene duplicar el v?nculo alumno-carrera, de acuerdo con la restricci?n ?nica de la base.

## Verificaci?n

Prueba reproducible: `python "Fase 4 Verificaci?n y QA/pruebas/test_b4_matriculas_base_qa.py"`. Se limita a `gestion_academica_a1_qa`, usa un alumno/carrera existente sin v?nculo previo y elimina la matr?cula temporal al finalizar.

**Resultado:** CUMPLE en MariaDB 10.4.32 (`gestion_academica_a1_qa`). PRECEPTOR registr? y consult? la matr?cula (HTTP 200); se rechaz? el v?nculo duplicado. ADMIN pudo consultar y su alta fue denegada con HTTP 403. El v?nculo temporal se elimin? al finalizar.
