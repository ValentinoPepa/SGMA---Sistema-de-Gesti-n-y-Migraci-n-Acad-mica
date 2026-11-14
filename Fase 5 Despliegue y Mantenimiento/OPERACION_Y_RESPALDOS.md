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

## Restauración y verificación

Probar la restauración en un entorno aislado antes de depender del respaldo. Para un dump comprimido:

```sh
gzip -dc /var/backups/sgma/gestion_academica_FECHA.sql.gz | mysql --defaults-extra-file=/etc/sgma/backup.cnf gestion_academica_restauracion
```

Validar que las tablas y relaciones estén presentes, revisar conteos representativos y probar el acceso al panel. Registrar fecha, responsable y resultado de cada ensayo. No restaurar sobre producción sin una ventana autorizada y un respaldo previo.

## Límites del paquete actual

La migración definitiva, la prueba real de claves foráneas, rendimiento y concurrencia, y la programación efectiva de respaldos requieren un servidor MySQL, credenciales y una política operativa del entorno de despliegue.
