# Plan de respaldo periódico C7

**Base:** `gestion_academica_v2`  
**Motor local:** MariaDB 10.4.32 de XAMPP  
**Fecha de configuración:** 2026-11-24

## Tarea programada

Se creó la tarea de Windows `SGMA_Respaldo_Diario_gestion_academica_v2`, programada diariamente a las 22:00 hora local. Se ejecuta como el usuario actual con privilegios limitados y llama al script guardado en:

`OneDrive\Documentos\SGMA_Resguardos\BD\backup_sgma_diario.ps1`

La tarea tiene activado `StartWhenAvailable` y omite una segunda instancia si la anterior sigue corriendo. Requiere que la sesión del usuario y el servidor MariaDB local estén disponibles. Si no puede conectarse, registra el error en `respaldo_sgma.log`.

El script genera un archivo SQL fechado en `OneDrive\Documentos\SGMA_Resguardos\BD\dump`. Usa `mysqldump` con `--single-transaction`, `--quick`, `--routines`, `--triggers` y `--events`; no incluye contraseñas en la línea de comandos y no borra respaldos anteriores automáticamente.

## Primera ejecución

El script se ejecutó manualmente y también desde la tarea programada. La última ejecución de Task Scheduler terminó con código `0`.

- Respaldo generado: `gestion_academica_v2_20261124_151455.sql`
- Tamaño: 86.064 bytes
- SHA-256: `4F68E1CC241516097F00EA0156D841D68763E6CEF2BFE7351E61659583363716`
- Registro: `respaldo_sgma.log`, con estado `OK`
- Próxima ejecución: diariamente a las 22:00

## Prueba local de restauración

El archivo creado por la tarea programada, `gestion_academica_v2_20261124_151455.sql` (SHA-256 `4F68E1CC241516097F00EA0156D841D68763E6CEF2BFE7351E61659583363716`), se restauró en el esquema temporal `gestion_academica_c7_restore_20261124b`, sin escribir sobre la base de trabajo. El verificador comparó los nombres de las tablas, conteos de filas, triggers, rutinas y eventos entre origen y restauración:

| Control | Origen | Restauración | Resultado |
|---|---:|---:|---|
| Tablas | 19 | 19 | Coinciden |
| Triggers | 14 | 14 | Coinciden |
| Procedimientos y funciones | 3 | 3 | Coinciden |
| Alumnos | 80 | 80 | Coinciden |
| Carreras | 2 | 2 | Coinciden |
| Materias | 24 | 24 | Coinciden |
| Actas | 189 | 189 | Coinciden |
| Auditoría | 190 | 190 | Coinciden |
| Lotes de carga | 1 | 1 | Coinciden |

El esquema temporal se eliminó después de la comparación.

## Excepción aceptada para la restauración en otro equipo

La persona usuaria no cuenta con otra computadora y pidió omitir la prueba en un segundo equipo. Se acepta esa limitación para continuar con el proyecto. La restauración local al esquema aislado pasó y se compararon tablas, rutinas, triggers y conteos; esta prueba no reemplaza literalmente el criterio de la matriz que pide otro equipo.

Si en el futuro hay acceso a otra computadora, se puede agregar esa evidencia. Con MySQL/MariaDB instalado, la restauración se haría desde el símbolo del sistema con:

```powershell
mysql.exe -h 127.0.0.1 -P 3306 -u root -p -e "CREATE DATABASE gestion_academica_c7_restore CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
mysql.exe -h 127.0.0.1 -P 3306 -u root -p --default-character-set=utf8mb4 gestion_academica_c7_restore < "gestion_academica_v2_20261124_151455.sql"
```

Luego comprobar en Workbench que el esquema restaurado tenga 19 tablas, 14 triggers, 3 rutinas y los conteos de la tabla anterior. No importar el dump sobre la base operativa.

## Archivos operativos

- Script de respaldo: `backup_sgma_diario.ps1`
- Verificador de restauración: `restore_verify_sgma.py`
- Log de ejecución: `OneDrive\Documentos\SGMA_Resguardos\BD\respaldo_sgma.log`
- Dumps fechados: `OneDrive\Documentos\SGMA_Resguardos\BD\dump\`

La carpeta de destino está bajo OneDrive, pero el cliente de sincronización no estaba ejecutándose durante la prueba. La tarea crea el respaldo localmente; esta ejecución no confirma que se haya sincronizado a la nube.
