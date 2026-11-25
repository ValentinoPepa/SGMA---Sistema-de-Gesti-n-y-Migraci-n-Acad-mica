# Auditoría cruzada de la migración C3

**Fecha de revisión:** 24 de noviembre de 2026  \
**Fuentes revisadas:** `Actas_Historicas.csv` y hoja `Detalle` de `Clave_Errores_Inyectados.xlsx`  \
**Método:** preparación en modo de solo lectura con el código actual del ETL; no se abrió conexión a la base ni se modificaron archivos o datos.

## Alcance y resultado

El CSV contiene 204 registros de datos (líneas 2 a 205; línea 1 corresponde al encabezado). Al preparar de nuevo las fuentes con el ETL actual, se obtuvieron 189 actas preparadas y 15 rechazos. La comparación de los números de línea con las anomalías bloqueantes de la clave no encontró rechazos faltantes ni adicionales: ambos conjuntos de 15 filas coinciden exactamente.

| Motivo registrado por el ETL | Clave de anomalías | Cantidad | Filas del CSV |
|---|---|---:|---|
| Fecha posterior a hoy, rechazada como `ERR_03_DATE_INVALID` | `FECHA_FUTURA` | 2 | 4, 82 |
| Referencia a materia inexistente, `ERR_02_FK_NOTFOUND` | `ACTA_MATERIA_INEXISTENTE` | 4 | 19, 91, 112, 120 |
| Referencia a alumno inexistente, `ERR_02_FK_NOTFOUND` | `ACTA_DNI_INEXISTENTE` | 4 | 44, 63, 79, 141 |
| Fecha inválida, `ERR_03_DATE_INVALID` | `FECHA_INVALIDA` | 2 | 147, 197 |
| Nota fuera de rango, `ERR_04_NOTA_OUT_RANGE` | `NOTA_FUERA_RANGO` | 3 | 83, 135, 183 |
| **Total** |  | **15** |  |

## Salvedad sobre revisión manual

La clave indica que las dos fechas futuras (líneas 4 y 82) requieren «revisión manual». El ETL actual las rechaza automáticamente con `ERR_03_DATE_INVALID`; no existe en el flujo una cola, marca ni evidencia de revisión humana. Por eso, el conteo y la clasificación coinciden, pero el tratamiento no cumple por completo lo indicado por la clave para esos dos casos. Debe decidirse si corresponde rechazar ambas fechas sin revisión o incorporar/documentar una revisión manual.

## Límite de la verificación

Este cruce verifica las filas que el ETL actual prepara o rechaza frente a la clave de anomalías. No se consultó la base MariaDB ni se compararon uno a uno los valores persistidos de las 189 actas con el CSV. Las capturas de Workbench disponibles confirman conteos y el resumen del lote, pero no contienen un volcado fila a fila. Por tanto, queda pendiente esa comparación integral de datos migrados si C3 exige verificar cada valor almacenado.

No se incluyeron valores de alumno, DNI ni otros datos personales en este registro.
