# C4 - Rendimiento y concurrencia

**Fecha:** 2026-11-24  
**Servidor medido:** MariaDB 10.4.32 (XAMPP), Windows 11 Pro  
**Equipo:** AMD Ryzen 3 3250U, 13.9 GB RAM visible  
**Base operativa:** `gestion_academica_v2`

## Decisión

Se recomienda **mantener activos los triggers de auditoría durante la migración**. En la carga real de 189 actas, la mediana del tramo de escritura y `COMMIT` fue 0.208 s con auditoría y 0.162 s sin el trigger de inserción de actas: una diferencia mediana de 0.046 s (29.4%). La prueba de 1.000 actas generadas para el benchmark dio medianas de 0.762 s y 0.560 s, respectivamente. La auditoría dejó un evento por acta.

El SRS v1.2 adjunto define umbrales: RNF-01 exige menos de 1,5 s en el 95 % de las búsquedas por legajo e historiales; RNF-02 exige procesar 50.000 registros en menos de 10 minutos; RNF-10 propone 5.000 filas de carga masiva en menos de 2 minutos; RNF-11 propone 20 usuarios simultáneos, sin pérdida de datos y con detección de conflictos de edición. Las pruebas de este informe no alcanzan todos esos escenarios, por lo que no se declara cumplimiento formal. La comparación de auditoría sigue siendo útil para la decisión operativa de mantener los triggers.

## Método

- Se crearon esquemas de prueba desechables a partir del DDL del proyecto. La base `gestion_academica_v2` y sus registros no se usaron para escribir.
- Se compararon esquemas idénticos. En la variante “sin auditoría” se quitó únicamente `trg_actas_ai`; los otros triggers y restricciones quedaron igual.
- El tramo de ETL cronometrado comienza después de leer y validar las planillas, y termina después del `COMMIT`. Así se mide la escritura en la base sin mezclarla con apertura de archivos o arranque de Python.
- Para la fuente original se hicieron 7 pares de mediciones: 80 alumnos, 2 carreras, 24 materias y 189 actas por carga.
- Para el volumen de referencia se hicieron 5 pares adicionales con 1.000 actas válidas generadas repitiendo datos ya validados y cambiando libro/folio. No se incorporaron a la base operativa.
- Para RNF-02 se ejecutó el ETL completo de 50.000 actas sintéticas en `gestion_academica_rnf02`, con triggers activos. El conjunto se generó antes del cronómetro a partir de filas válidas y cambiando libro/folio; el tiempo medido incluye preparación ETL, escritura y `COMMIT`.
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

## Medición adicional RNF-01: ruta web local

- Se ejecutaron 30 solicitudes secuenciales `GET /busqueda?q=1001` desde el navegador, con `cache: no-store` y descarga completa de cada respuesta HTML. Resultado: mediana **27 ms**, p95 **38 ms** y máximo **130 ms**.
- Se ejecutaron otras 30 solicitudes iguales para el legajo 1015, que en la base tenía el historial más extenso: **5 registros asociados**. Resultado: mediana **29 ms**, p95 **42 ms** y máximo **44 ms**.
- En ambas muestras los tiempos p95 y máximos estuvieron por debajo del umbral de **1.500 ms**. La ruta Flask busca por DNI/legajo, carga matrículas, notas y actas, calcula promedios y devuelve el HTML.
- Alcance: 60 solicitudes en total, distribuidas en dos grupos de 30, en el servidor local y un solo equipo. Todos los tiempos observados fueron menores a 130 ms, pero no se calculó un p95 combinado. La muestra de historiales sigue siendo pequeña y no representa producción.

## Medición RNF-02: carga de 50.000 registros

La prueba se ejecutó el 25 de noviembre de 2026 en MariaDB 10.4.32, dentro del esquema aislado `gestion_academica_rnf02`. Se prepararon 50.000 actas históricas válidas para la prueba; las filas se basaron en ejemplos normalizados del archivo de origen y se diferenciaron con libro/folio de prueba. La generación de la muestra quedó fuera del cronómetro. Las fuentes auxiliares de alumnos y plan registraron 10 validaciones/anomalías en total; las actas de la muestra tuvieron cero rechazos, como confirma el lote.

| Medición | Resultado |
|---|---:|
| Registros de acta preparados | 50.000 |
| Tiempo de preparación ETL + escritura + `COMMIT` | 43,297 s |
| Rendimiento medido | 1.154,8 registros/s |
| Lote registrado: total / correctas / error | 50.000 / 50.000 / 0 |
| Eventos de auditoría `INSERT` de actas | 50.000 |
| Umbral RNF-02 | Menos de 600 s |
| Resultado de este escenario | **Cumple** |

Una consulta de verificación posterior confirmó 80 alumnos, 2 carreras, 24 materias, 50.000 actas, un lote y 50.000 eventos de auditoría para las actas. La base operativa `gestion_academica_v2` no fue utilizada. El conjunto fue sintético y se repitieron patrones válidos; esta medición demuestra el umbral para una carga de 50.000 actas en este equipo y motor, no para todo tipo de distribución ni para MySQL de producción. Se conservaron los datos en el esquema aislado para inspección.

## Comparación con objetivos y límites

| Requisito / referencia | Evidencia | Estado de evaluación |
|---|---|---|
| RNF-01: búsquedas e historiales | El benchmark DB previo midió p95 de 5,13 ms con 10 conexiones. En navegador: 30 solicitudes para el legajo 1001 (p95 38 ms, máximo 130 ms) y 30 para el legajo con más historial, 1015 (5 registros; p95 42 ms, máximo 44 ms). | Las dos muestras observadas quedan bajo 1,5 s; evidencia local favorable, aún limitada para declarar cumplimiento general. |
| RNF-02: migración inicial | ETL completo de 50.000 actas sintéticas en el esquema aislado: 43,297 s de preparación, escritura y `COMMIT`; 50.000/50.000/0 en lote y 50.000 eventos de auditoría. | Cumple en este escenario local MariaDB 10.4.32. Alcance limitado a actas sintéticas, patrones repetidos y este equipo. |
| RNF-10: carga masiva | La ruta Flask real `/cargas` procesó una plantilla oficial de 5.000 filas en 16,259 s; lote 5.000/5.000/0 y 5.000 eventos de auditoría nuevos. | Cumple en el ensayo local; alcance limitado a datos sintéticos, cliente de pruebas Flask y MariaDB 10.4.32. |
| RNF-11: concurrencia | Con 20 sesiones autenticadas, se guardaron 20 altas sin perder registros y con legajos distintos. En 20 ediciones simultáneas de la misma ficha, 1 se guardó y 19 recibieron HTTP 409; hubo 1 evento de auditoría para el cambio aceptado. | Cumple en los escenarios locales simulados. No se midió el servidor desplegado ni la red real. |

El diseño del ETL recomienda medir la auditoría y agregar una opción para pausarla solo si RNF-02 no se cumple. La prueba local de 50.000 actas cumplió RNF-02 con la auditoría activa; el resultado se limita al motor, equipo y conjunto sintético descritos. Se recomienda mantener los triggers activos y ampliar RNF-01 con más historiales. RNF-11 superó los escenarios locales descritos; si la conformidad requiere validar el servidor desplegado, repetir la prueba de 20 usuarios a través de la red objetivo. Si la conformidad requiere validación en el motor objetivo MySQL, repetir también el benchmark RNF-02 allí.

## Medición RNF-10: carga masiva de 5.000 filas

La prueba se ejecutó el 25 de noviembre de 2026 contra el esquema aislado `gestion_academica_rnf02`, en MariaDB 10.4.32. Se generó en memoria un libro `.xlsx` con la hoja y los encabezados de la plantilla oficial de actas, usando alumnos y materias ya existentes en QA y folios únicos de prueba. El contenido fue sintético; no se usaron ni modificaron planillas originales.

La medición cronometró el POST autenticado a la ruta Flask `/cargas`, desde el procesamiento del archivo hasta la respuesta posterior al `COMMIT`. Incluye lectura y validación del XLSX, validaciones de referencias, inserciones fila por fila, triggers de auditoría y actualización del lote. Se usó el cliente de pruebas integrado de Flask, por lo que no incluye latencia de red ni múltiples usuarios concurrentes.

| Comprobación | Resultado |
|---|---:|
| Filas enviadas | 5.000 |
| Tiempo del POST (validación, escritura y `COMMIT`) | 16,259 s |
| Filas aceptadas / rechazadas | 5.000 / 0 |
| Conteo de actas antes / después | 50.000 / 55.000 |
| Eventos de auditoría acumulados para actas | 55.000 |
| Umbral RNF-10 | Menos de 120 s |
| Resultado del escenario | **Cumple** |

El resultado demuestra el umbral en esta configuración local y con esta distribución de datos. No reemplaza una medición con un XLSX real ni una prueba de concurrencia. La cuenta de prueba no tenía contraseña en la base local; por eso se ajustó la configuración de Flask para aceptar `SGMA_DB_PASSWORD` vacío cuando el servidor está configurado sin contraseña.

## Alcance y reproducibilidad

Los resultados describen una prueba local en MariaDB 10.4.32, no MySQL 8.4 ni una instalación de producción. La concurrencia cubre conexiones directas a la base y no mide tiempos HTTP ni el comportamiento completo de la interfaz. La máquina mostró variabilidad notable en la prueba sintética de 1.000 actas.

El código reutilizable del ensayo está en `pruebas/benchmark_c4.py`. Al ejecutarlo, requiere `SGMA_DB_HOST`, `SGMA_DB_USER`, opcionalmente `SGMA_DB_PASSWORD`, `SGMA_DB_PORT`, `SGMA_FUENTES_DIR` y `MYSQL_CLI`. `C4_RUNS`, `C4_WORKERS`, `C4_ROWS_PER_WORKER` y `C4_ETL_ACTS` permiten ajustar repeticiones y volumen. El programa usa esquemas `sgma_c4_*` temporales y los borra al completar.

Fuentes consultadas: SRS v1.2 adjunto (RNF-01, RNF-02, RNF-10 y RNF-11); matriz de tareas C4; arquitectura ETL; DDL v1.2; entrevista de requisitos.


## Medición RNF-11: 20 usuarios simultáneos

La prueba final se ejecutó el 25 de noviembre de 2026 en `gestion_academica_rnf02`, MariaDB 10.4.32. Se usaron 20 cuentas temporales de PRECEPTOR, cada una iniciando sesión en una sesión Flask independiente. Se ejecutó con Flask test client en el mismo proceso; no midió tráfico de red ni 20 navegadores independientes.

| Escenario | Resultado |
|---|---:|
| Usuarios/sesiones concurrentes | 20 |
| Altas aceptadas / legajos únicos | 20 / 20 |
| Tiempo total de altas (POST y respuesta) | 0,473 s |
| Latencia individual de alta: mediana / máximo | 0,292 s / 0,429 s |
| Ediciones simultáneas de la misma ficha | 20 |
| Guardados aceptados / conflictos HTTP 409 | 1 / 19 |
| Tiempo total de ediciones y respuestas | 0,169 s |
| Versión final / eventos de auditoría del cambio aceptado | 2 / 1 |

Se agregó control optimista de versión a las fichas de alumnos. Cada formulario lleva la versión que leyó; al guardar, la base incrementa la versión solo si sigue siendo la misma. En la prueba, las 20 sesiones leyeron la versión 1 antes de iniciar el envío concurrente. Una edición la actualizó a la versión 2 y las otras 19 recibieron HTTP 409 con aviso de conflicto. El nombre aceptado quedó registrado una sola vez en auditoría; ninguna edición obsoleta lo sobrescribió.

La verificación cubre la edición de alumnos y las altas desde la ruta Flask con sesiones autenticadas; no demuestra rendimiento del servidor WSGI desplegado en una red con 20 equipos. Las cuentas y alumnos de prueba quedaron desactivados en el esquema QA. No se modificó la base operativa.

Para una base existente, ejecutar una sola vez `Fase 2 Diseño y Base de Datos/migracion_rnf11_version_alumno.sql` en Workbench con seleccionada la base correcta. La base aislada QA ya recibió esta migración. El DDL principal incluye la columna `version` para instalaciones nuevas.
