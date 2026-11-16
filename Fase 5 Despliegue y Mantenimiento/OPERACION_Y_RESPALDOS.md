# Operación, despliegue y respaldos

## Puesta en marcha

1. Usar MySQL 8.0.16 o superior y ejecutar `Fase 2 Diseño y Base de Datos/gestion_academica.sql` sobre la base `gestion_academica`.
2. Crear un usuario de base de datos de aplicación con los permisos mínimos requeridos por el DDL y el panel.
3. Instalar las dependencias de `requirements.txt` en un entorno virtual.
4. Configurar `SGMA_DB_HOST`, `SGMA_DB_PORT`, `SGMA_DB_USER`, `SGMA_DB_PASSWORD`, `SGMA_DB_NAME` y una clave aleatoria en `SGMA_SECRET_KEY` mediante el gestor de secretos del servidor.
5. En producción, configurar `SGMA_COOKIE_SECURE=true`, HTTPS y un servidor WSGI de producción. No usar el servidor de desarrollo de Flask expuesto a Internet.
6. Crear la cuenta inicial en `/setup`, comprobar los roles y luego operar con cuentas individuales.
7. Ejecutar primero `python -m sgma.etl` para revisar el ensayo; solo después de aprobar conteos y errores, programar una ventana y ejecutar `python -m sgma.etl --apply` con acceso autorizado a la base.

## Respaldo de las fuentes legadas

Conservar sin modificaciones los archivos originales `Alumnos_2026_Final.xlsx`, `Plan_Estudios.xlsx`, `Actas_Historicas.csv` y `Clave_Errores_Inyectados.xlsx` en un repositorio de respaldo con acceso restringido. Mantener una copia separada del equipo que ejecuta el panel y verificar periódicamente que los archivos puedan abrirse. No guardar contraseñas ni datos personales en logs públicos.

## Respaldo periódico de MySQL

Configurar el respaldo en el servidor con una cuenta de solo lectura para dumps, guardando las credenciales fuera del script (por ejemplo, en un archivo de opciones MySQL protegido por permisos del sistema). Ejemplo para Linux, adaptando base, ruta y retención:

```sh
#!/bin/sh
set -eu
umask 077
DB_NAME="${SGMA_DB_NAME:-gestion_academica}"
BACKUP_DIR="/var/backups/sgma"
mkdir -p "$BACKUP_DIR"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
mysqldump --defaults-extra-file=/etc/sgma/backup.cnf --single-transaction --routines --triggers "$DB_NAME" \
  | gzip > "$BACKUP_DIR/${DB_NAME}_${STAMP}.sql.gz"
find "$BACKUP_DIR" -type f -name 'gestion_academica_*.sql.gz' -mtime +30 -delete
```

Programar el script con `cron` o el planificador de la infraestructura, con salida y errores enviados al monitoreo del servidor. El ejemplo retiene 30 días; ajustar esa política con el responsable del sistema. La configuración real, el destino externo y la política de retención dependen del servidor y no se aplican desde este repositorio.

### Windows: fuentes legadas y respaldos de MySQL

Los archivos fuente contienen datos personales. El respaldo debe guardarse en un destino separado de la carpeta del proyecto, con acceso restringido y, preferentemente, en un disco cifrado que no sea el mismo disco del servidor. No agregar respaldos ni archivos de credenciales a Git.

Para hacer una copia verificada de las planillas originales, abrir PowerShell y ejecutar el script con las rutas reales:

```powershell
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File "<repo>\Fase 5 Despliegue y Mantenimiento\scripts\backup_legacy_sources_windows.ps1" -SourceDirectory "<carpeta v1.1 con las fuentes>" -BackupDirectory "<destino separado>"
```

El script copia las cuatro fuentes esperadas, compara sus hashes SHA-256 y crea un manifiesto. No transforma ni borra las fuentes.

Para respaldar MySQL, crear fuera del repositorio un archivo de opciones, por ejemplo `C:\ProgramData\SGMA\backup.cnf`, con formato MySQL:

```ini
[client]
host=127.0.0.1
port=3306
user=sgma_backup
password=CAMBIAR_POR_UN_SECRETO_LOCAL
```

Reemplazar el ejemplo por un usuario dedicado con los permisos mínimos que requiera la versión de MySQL. Restringir mediante ACL de Windows quién puede leer ese archivo; no guardar la contraseña en el comando, en el repositorio ni en Trello.

Ejecución manual de ejemplo (ajustar todas las rutas):

```powershell
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File "<repo>\Fase 5 Despliegue y Mantenimiento\scripts\backup_mysql_windows.ps1" -BackupDirectory "<destino separado>\mysql" -DefaultsFile "C:\ProgramData\SGMA\backup.cnf" -MySqlDumpPath "<ruta MySQL>\bin\mysqldump.exe" -DatabaseName "gestion_academica" -RetentionDays 30
```

El script genera un dump con rutinas y triggers, lo comprime, verifica que se pueda leer como SQL y aplica la retención indicada. Para programarlo, crear una tarea en el Programador de tareas de Windows que ejecute el mismo comando una vez al día, con una cuenta que tenga acceso al archivo de opciones, al ejecutable de MySQL y al destino. Configurar el historial de la tarea y revisar su resultado después de cada ejecución.

La verificación de compresión no demuestra que el dump restaure correctamente. Antes de cerrar la tarea de backup, restaurar una copia reciente en una base aislada, comprobar tablas y conteos y registrar fecha, responsable y resultado. Mientras el único destino sea la misma PC, la copia no protege contra la pérdida de ese equipo.

## Restauración y verificación

Probar la restauración en un entorno aislado antes de depender del respaldo. Para un dump comprimido:

```sh
gzip -dc /var/backups/sgma/gestion_academica_FECHA.sql.gz | mysql --defaults-extra-file=/etc/sgma/backup.cnf gestion_academica_restauracion
```

Validar que las tablas y relaciones estén presentes, revisar conteos representativos y probar el acceso al panel. Registrar fecha, responsable y resultado de cada ensayo. No restaurar sobre producción sin una ventana autorizada y un respaldo previo.

## Límites del paquete actual

La migración definitiva, la prueba real de claves foráneas, rendimiento y concurrencia, y la programación efectiva de respaldos requieren un servidor MySQL, credenciales y una política operativa del entorno de despliegue.
