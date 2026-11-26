# A2 - Trazabilidad y rollback de la migracion ETL

**Estado: completada**  
**Fecha de verificacion:** 26 de noviembre de 2026  
**Base QA:** `gestion_academica_a2_qa`  
**Servidor:** MariaDB 10.4.32

## Alcance y resultado

La migracion ETL registra un lote por archivo fuente en `lotes_carga`. Los tres lotes quedan asociados al usuario ADMIN `id_usuario = 1`. En la conexion, el ETL establece `@app_user_id = 1`; los triggers registraron los 189 INSERT de actas con esa identidad.

Los archivos y sus datos se cargan dentro de una sola transaccion. El ensayo de rollback introdujo un fallo controlado despues de dos INSERT de acta. El programa informo `ROLLBACK_OK` y verifico que los conteos de carreras, materias, alumnos, lotes, actas y auditoria no cambiaran.

## Conteos verificados

| Archivo | Entidad | Usuario | Filas fuente | Filas aceptadas | Filas rechazadas |
| --- | --- | ---: | ---: | ---: | ---: |
| `Alumnos_2026_Final.xlsx` | alumnos | 1 | 83 | 80 | 3 |
| `Plan_Estudios.xlsx` | plan_estudios | 1 | 25 | 24 | 1 |
| `Actas_Historicas.csv` | actas_examen | 1 | 204 | 189 | 15 |

La ejecucion del ETL informo 25 entradas de validacion en el log. Esa cifra incluye advertencias de campos opcionales que no impidieron cargar la fila; `filas_error` en cada lote cuenta filas rechazadas.

## Evidencias

- [Ensayo de rollback](evidencias/A2/A2_rollback_ok.png)
- [Salida de la carga ETL](evidencias/A2/A2_carga_etl_powershell.png)
- [Lotes por archivo en Workbench](evidencias/A2/A2_lotes_workbench.png)
- [Eventos de auditoria en Workbench](evidencias/A2/A2_auditoria_workbench.png)

## Consultas de verificacion

```sql
SELECT archivo, entidad, id_usuario, filas_total, filas_ok, filas_error
FROM lotes_carga
WHERE tipo = 'MIGRACION'
ORDER BY id_lote;

SELECT id_usuario, tabla, operacion, COUNT(*) AS eventos
FROM auditoria
WHERE tabla = 'actas_examen' AND operacion = 'INSERT'
GROUP BY id_usuario, tabla, operacion;

SELECT VERSION() AS servidor, DATABASE() AS base_actual;
```