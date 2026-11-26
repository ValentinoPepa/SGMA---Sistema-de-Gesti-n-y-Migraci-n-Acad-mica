# A9 — Respaldo y estado de la migración definitiva

**Fecha:** 26/11/2026  
**Conexión/base indicada:** `gestion_academica_v2`  
**Motor confirmado:** MariaDB 10.4.32, puerto 3306

## Estado encontrado

La base ya contiene una migración ETL registrada: 80 alumnos, 2 carreras, 24 materias, 189 actas y un lote `MIGRACION` para `Actas_Historicas.csv` (204 filas de origen, 189 aceptadas y 15 rechazadas). Por eso no se volvió a ejecutar `python -m sgma.etl --apply`: el ETL advierte que no debe repetirse sobre una base con lotes de migración existentes y se podrían duplicar o alterar registros.

La carpeta de fuentes indicada (`Fase 2 Diseño y Base de Datos`) contiene el esquema y las plantillas, pero no las planillas/archivos de datos originales `Alumnos_2026_Final.xlsx` ni `Actas_Historicas.csv`. El estado de la base confirma que ya hubo una carga previa, pero no permite repetir una nueva importación desde las fuentes originales.

## Respaldo previo generado y restaurado

- Archivo: `gestion_academica_v2_20261126_152215.sql` (resguardado localmente fuera del repositorio; no versionar el dump)
- Tamaño: 86.684 bytes
- SHA-256: `0F89135457FD6CFFE3F0E4428635C27FF36D2C75CC7F19BD8C8D4F06007205CE`
- Restauración aislada: correcta en `gestion_academica_a9_restore_20261126`; el esquema temporal se eliminó después de la comparación.

| Control | Origen/restauración |
|---|---:|
| Tablas | 19 / 19 |
| Triggers | 14 / 14 |
| Rutinas | 3 / 3 |
| Eventos | 0 / 0 |
| Alumnos | 80 / 80 |
| Carreras | 2 / 2 |
| Materias | 24 / 24 |
| Actas | 189 / 189 |
| Auditoría | 190 / 190 |
| Lotes de carga | 1 / 1 |

## Conclusión

El respaldo actual de `gestion_academica_v2` está generado y su restauración fue verificada. La migración de datos ya está aplicada en esa base, así que A9 no se repitió. La persona usuaria confirmó que no requiere importar datos nuevos; con ello, A9 queda cerrado sobre el estado migrado existente y el respaldo comprobado.
