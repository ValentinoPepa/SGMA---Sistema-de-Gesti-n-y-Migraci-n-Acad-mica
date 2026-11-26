# Resultados A8 — Carga masiva y permisos con base real

**Fecha:** 26/11/2026  
**Base verificada:** `gestion_academica_rnf02`  
**Motor:** MariaDB 10.4.32, puerto 3306

## Resultado

Se ejecutó `pruebas/test_a8_integracion_base_real.py`. La aplicación Flask usó `mysql.connector` conectado al esquema QA real; no se reemplazaron conexiones ni cursores por simulaciones. La carga se envió por la ruta `/cargas` con un `test_client` de Flask, por lo que esta medición cubre el procesamiento de la aplicación y la base local, pero no incluye tráfico de red externa ni el servidor HTTP de despliegue.

| Comprobación | Resultado |
|---|---:|
| Acceso a `/cargas` como ADMIN | HTTP 200 |
| Acceso a `/cargas` como PRECEPTOR | HTTP 200 |
| Acceso a `/cargas` como DIRECTIVO | HTTP 403 |
| Filas enviadas y confirmadas | 5.000 / 5.000 |
| Filas rechazadas en lote | 0 |
| Actas en base antes/después | 55.000 / 60.000 |
| Tiempo del POST de 5.000 filas | 26,934 s |
| Umbral RNF-10 (<120 s) | CUMPLE |

Lote registrado: `A8_4BFF9C0AF5_5000.xlsx`, con total/aceptadas/rechazadas `5000/5000/0`. Las tres cuentas temporales de prueba se desactivaron al finalizar. La verificación posterior encontró cero cuentas A8 activas.

## Alcance

La prueba comprobó el acceso de lectura a la pantalla de carga por rol y realizó una carga completa de actas con folios únicos. El DIRECTIVO quedó denegado por la protección del servidor. La medición usó la base de QA aislada y no tocó `gestion_academica_v2`.

## Repetición

Desde la carpeta raíz del proyecto, ejecutar:

```powershell
python "Fase 4 Verificación y QA/pruebas/test_a8_integracion_base_real.py"
```

El script rechaza cualquier esquema distinto de `gestion_academica_rnf02`, crea usuarios con nombres únicos, genera folios únicos y desactiva las cuentas temporales al terminar.
