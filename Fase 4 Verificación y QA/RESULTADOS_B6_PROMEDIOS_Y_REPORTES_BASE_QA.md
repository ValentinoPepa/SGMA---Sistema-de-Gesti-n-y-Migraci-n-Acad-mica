# B6 - Promedios y reportes academicos

**Alcance:** RF-GAC-04 y reportes faltantes: listado de actas y asistencia por materia.

## Promedios

La busqueda de alumnos y los analiticos PDF/Excel muestran el promedio de actas con aplazos y sin aplazos. El promedio con aplazos usa todas las actas activas con nota numerica; el promedio sin aplazos usa solo actas activas con estado `APROBADO`. Las actas `AUSENTE` no tienen nota y no entran en ninguno. Se agrego tambien el valor sin aplazos al reporte general de alumnos. Los promedios de cursada se muestran por separado.

## Reportes

La pagina `/reportes/academicos` permite filtrar por materia y ciclo:

- Listado de actas activas con alumno, carrera, materia, ciclo, fecha, nota, estado y libro/folio; permite exportar el resultado completo a PDF y Excel.
- Resumen de asistencia por materia y ciclo, con alumnos, presentes, ausentes, justificadas y porcentaje agregado. Las justificadas quedan fuera del denominador, conforme a la regla vigente. Permite exportar a PDF y Excel.

El acceso queda limitado a ADMIN, PRECEPTOR y DIRECTIVO.

## Verificacion QA

Ejecutar `python "Fase 4 Verificacion y QA/pruebas/test_b6_promedios_reportes_base_qa.py"`. La prueba usa solo `gestion_academica_a1_qa`, agrega fixtures temporales, valida promedios frente al conjunto base existente, prueba ambos reportes/Excel y confirma que DOCENTE no puede abrir el reporte general. El script elimina sus filas y desactiva usuarios temporales en `finally`.

**Resultado:** CUMPLE en MariaDB 10.4.32 (`gestion_academica_a1_qa`). Con las filas fixture la prueba comprob? los promedios frente a las actas preexistentes; el resumen temporal de asistencia fue 66.7% (2 presentes, 1 ausente; 1 justificada excluida). Los dos reportes se descargaron correctamente en PDF y Excel y el acceso DOCENTE fue rechazado con HTTP 403.
