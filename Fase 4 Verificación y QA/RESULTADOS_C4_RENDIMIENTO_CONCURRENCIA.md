# C4 - Rendimiento y concurrencia

**Fecha:** 2026-11-24  
**Servidor medido:** MariaDB 10.4.32 (XAMPP), Windows 11 Pro  
**Equipo:** AMD Ryzen 3 3250U, 13.9 GB RAM visible  
**Base operativa:** `gestion_academica_v2`

## Decisión

Se recomienda **mantener activos los triggers de auditoría durante la migración**. En la carga real de 189 actas, la mediana del tramo de escritura y `COMMIT` fue 0.208 s con auditoría y 0.162 s sin el trigger de inserción de actas: una diferencia mediana de 0.046 s (29.4%). La prueba de 1.000 actas generadas para el benchmark dio medianas de 0.762 s y 0.560 s, respectivamente. La auditoría dejó un evento por acta.

No se encontró en el SRS disponible un límite numérico de tiempo para aceptar o rechazar estas mediciones. Por eso la decisión es operativa y provisional: el costo absoluto medido es bajo para estos volúmenes y no justifica perder trazabilidad. No se debe presentar como certificación de SLA.

## Método

- Se crearon esquemas de prueba desechables a partir del DDL del proyecto. La base `gestion_academica_v2` y sus registros no se usaron para escribir.
- Se compararon esquemas idénticos. En la variante “sin auditoría” se quitó únicamente `trg_actas_ai`; los otros triggers y restricciones quedaron igual.
- El tramo de ETL cronometrado comienza después de leer y validar las planillas, y termina después del `COMMIT`. Así se mide la escritura en la base sin mezclarla con apertura de archivos o arranque de Python.
- Para la fuente original se hicieron 7 pares de mediciones: 80 alumnos, 2 carreras, 24 materias y 189 actas por carga.
- Para el volumen de referencia se hicieron 5 pares adicionales con 1.000 actas válidas generadas repitiendo datos ya validados y cambiando libro/folio. No se incorporaron a la base operativa.
- La prueba concurrente usó 10 conexiones simultáneas. Cada conexión hizo 100 búsquedas por alumno y 100 inserciones de actas; total: 1.000 lecturas y 1.000 escrituras por repetición. Cada trabajador confirmó su transacción al terminar.
- El programa comprobó los conteos de actas y auditoría y eliminó los esquemas temporales al finalizar.

## Resultados

| Medición | Con trigger | Sin `trg_actas_ai` | Comparación |
|---|---:|---:|---|
| ETL real, 189 actas: mediana escritura + commit (7 pares) | 0.208 s | 0.162 s | +0.046 s; +29.4% mediana pareada |
| ETL de estrés, 1.000 actas: mediana escritura + commit (5 pares) | 0.762 s | 0.560 s | +0.202 s; +36.0% mediana pareada |
| ETL de estrés, rango observado | 0.420–2.609 s | 0.525–0.683 s | Alta variación en el equipo; incluye un outlier con trigger |
| Diferencia pareada por repetición, carga de 1.000 actas | — | — | Rango: −26.2% a +397.5%; el outlier impide interpretar el 36.0% como costo estable |
| Concurrencia tras ETL real de 189 actas: 1.000 escrituras, mediana total | 0.520 s | 0.421 s | +0.100 s con auditoría |
| Concurrencia tras ETL real: throughput mediano | 1.922 filas/s | 2.377 filas/s | Incluye 1.000 lecturas y 1.000 escrituras por repetición |
| Concurrencia tras ETL real: p95 mediano por `INSERT` | 6.49 ms | 5.07 ms | +1.42 ms con auditoría |
| Concurrencia tras ETL real: p95 de búsqueda por alumno | 5.13 ms | 4.79 ms | +0.34 ms con auditoría |
| Concurrencia tras ETL de estrés de 1.000 actas: tiempo total | 0.498 s | 0.395 s | +0.103 s con auditoría |
| Concurrencia tras ETL de estrés: p95 mediano por `INSERT` | 6.37 ms | 4.30 ms | +2.07 ms con auditoría |

El valor de throughput anterior se expresa en filas de escritura por segundo: 1.000 inserciones divididas por el tiempo total de cada ejecución.
`p95` es el percentil 95 de los tiempos observados: 95% de las operaciones fueron iguales o más rápidas que ese valor.

## Integridad y auditoría

- En cada carga base de 189 actas, la variante con trigger produjo exactamente 189 eventos `INSERT` de auditoría; la variante sin trigger produjo 0.
- En la prueba de estrés, al finalizar había 2.000 actas en cada esquema: 1.000 de la carga y 1.000 concurrentes. Con el trigger activo había 2.000 eventos de auditoría de actas; sin él, 0.
- No hubo fallos de transacción ni diferencias en los conteos de filas entre variantes.
- Después de la limpieza, `gestion_academica_v2` conservaba 80 alumnos, 2 carreras, 24 materias, 189 actas, 190 eventos de auditoría y 1 lote. No quedó ningún esquema `sgma_c4_*`.

## Comparación con objetivos y límites

| Requisito / referencia | Evidencia | Estado de evaluación |
|---|---|---|
| RNF-01: búsquedas rápidas | La consulta indexada por alumno tuvo p95 de 5.13 ms bajo 10 conexiones concurrentes con auditoría. | Medido en la base; falta un máximo de latencia aprobado para declarar cumplimiento formal. |
| RNF-02: rendimiento de migración | 189 actas reales: 0.208 s en escritura. El diseño menciona tandas de ejemplo de 1.000 filas; el estrés de 1.000 actas tardó 0.762 s de mediana, con una repetición atípica de 2.609 s. | Medición favorable en mediana; no hay SLA de tiempo. El ETL actual ejecuta un `INSERT` por registro, no una inserción multi-fila en tandas. |
| RNF-10 | La definición y un umbral para RNF-10 no aparecen en los documentos técnicos disponibles en esta carpeta. | No se certifica cumplimiento hasta contrastarlo con el SRS vigente. |
| RNF-11: uso simultáneo sin pérdida de cambios | 10 conexiones escribieron 1.000 actas; los conteos finales y la auditoría coincidieron exactamente. | Comportamiento medido en MariaDB local; repetir en el motor/entorno objetivo antes de despliegue. |

El diseño del ETL recomienda medir la auditoría y agregar una opción para pausarla solo si RNF-02 no se cumple. Con los tiempos observados, la recomendación es dejarla activa. Si el equipo establece un SLA más estricto o migra un volumen mucho mayor, se debe repetir la prueba con ese objetivo y registrar la decisión.

## Alcance y reproducibilidad

Los resultados describen una prueba local en MariaDB 10.4.32, no MySQL 8.4 ni una instalación de producción. La concurrencia cubre conexiones directas a la base y no mide tiempos HTTP ni el comportamiento completo de la interfaz. La máquina mostró variabilidad notable en la prueba sintética de 1.000 actas.

El código reutilizable del ensayo está en `pruebas/benchmark_c4.py`. Al ejecutarlo, requiere `SGMA_DB_HOST`, `SGMA_DB_USER`, opcionalmente `SGMA_DB_PASSWORD`, `SGMA_DB_PORT`, `SGMA_FUENTES_DIR` y `MYSQL_CLI`. `C4_RUNS`, `C4_WORKERS`, `C4_ROWS_PER_WORKER` y `C4_ETL_ACTS` permiten ajustar repeticiones y volumen. El programa usa esquemas `sgma_c4_*` temporales y los borra al completar.

Fuentes consultadas: matriz de tareas C4; arquitectura ETL (secciones de carga en tandas y decisión de auditoría); DDL v1.2; documento de QA existente; entrevista de requisitos (búsquedas rápidas y concurrencia sin pérdida de cambios).
