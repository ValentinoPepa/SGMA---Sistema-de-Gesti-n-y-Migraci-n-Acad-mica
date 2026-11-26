# Código SGMA

## Stack tecnológico

- **Base de datos objetivo:** MySQL 8.0.16 o superior, motor InnoDB (DDL y restricciones `CHECK`).
- **Aplicación web:** Python con Flask 3.x; acceso a la base mediante `mysql-connector-python`.
- **Entorno de verificación:** algunas pruebas de integración y rendimiento se ejecutaron localmente en MariaDB 10.4.32; esos resultados se identifican como MariaDB y no como MySQL.

Implementación Python del proyecto, alineada con los artefactos vigentes de Fase 2 v1.2.

Consultar el [manual de usuario](../../Fase%205%20Despliegue%20y%20Mantenimiento/MANUAL_DE_USUARIO.md)
y la [guía de operación y respaldos](../../Fase%205%20Despliegue%20y%20Mantenimiento/OPERACION_Y_RESPALDOS.md).

## Preparar el entorno

Desde esta carpeta, instalar dependencias. Para ejecutar las pruebas de QA
desde el mismo directorio, usar también el segundo comando:

```powershell
python -m pip install -r requirements.txt
python -m unittest discover -s "../../Fase 4 Verificación y QA/pruebas" -v
```

## Vista previa ETL

El comando predeterminado solo lee `Alumnos_2026_Final.xlsx`, `Plan_Estudios.xlsx`
y `Actas_Historicas.csv` desde la carpeta indicada por `SGMA_FUENTES_DIR` (por
defecto, la raíz del proyecto); valida los registros y genera `errores_migracion.log`.
Los archivos personales se mantienen fuera de Git. Copiarlos desde el resguardo
autorizado a una carpeta local y establecer `SGMA_FUENTES_DIR` con esa ruta.
No se conecta a MySQL ni escribe en la base.

```powershell
python -m sgma.etl
```

## Aplicar la migracion

Ejecutar primero el DDL vigente en un esquema vacio. Configurar `SGMA_DB_HOST`, `SGMA_DB_USER` y `SGMA_DB_NAME` con la conexion y la base elegidas. `SGMA_DB_PASSWORD` es opcional: si el usuario de MySQL no tiene contrasena, dejarla sin definir.

Antes de aplicar, crear una cuenta ADMIN activa en esa base mediante `/setup` y consultar su `id_usuario` en Workbench. Definir `SGMA_MIGRACION_USER_ID` con ese ID. El ETL valida que corresponda a un usuario ADMIN activo.

```powershell
$env:SGMA_MIGRACION_USER_ID = "<id del ADMIN activo>"
python -m sgma.etl --apply
```

La migracion crea un registro de `lotes_carga` por cada archivo fuente (alumnos, plan de estudios y actas), asigna el usuario ADMIN responsable y establece `@app_user_id` en la conexion para los triggers de auditoria. Los tres lotes y los datos se aplican en una unica transaccion: ante un error, el ETL revierte todo. No volver a ejecutar sobre una base que ya tenga un lote de migracion para cualquiera de esos archivos.

El log registra archivo, fila, campo, codigo y mensaje; omite valores personales de las planillas. `filas_error` cuenta filas rechazadas; las advertencias de campos opcionales que no impiden cargar una fila permanecen en el log.
## Panel web

Ejecutar primero el DDL en MySQL y configurar las variables de conexión. Antes
de iniciar, generar una clave aleatoria para `SGMA_SECRET_KEY`. Para desarrollo
local:

```powershell
$env:SGMA_SECRET_KEY = python -c "import secrets; print(secrets.token_hex(32))"
python -m flask --app sgma.web:app run
```

Abrir `http://127.0.0.1:5000/setup` para crear la primera cuenta ADMIN; la ruta
se bloquea automáticamente después de crear el primer usuario. En producción,
configurar además `SGMA_COOKIE_SECURE=true` y servir el panel detrás de HTTPS.

Para una base existente que ya tiene el DDL anterior, antes de usar la edición de
alumnos ejecutar una sola vez `../../Fase 2 Diseño y Base de Datos/migracion_rnf11_version_alumno.sql`
en Workbench con la base SGMA correcta seleccionada. Las instalaciones nuevas
reciben la columna de versión desde `gestion_academica.sql`.

El porcentaje de asistencia usa `asistencia_minima` en la tabla `parametros`.
Las clases `JUSTIFICADO` se excluyen del denominador, según la regla acordada.

El rol ADMIN, PRECEPTOR o DIRECTIVO puede descargar analíticos individuales en
PDF/Excel desde la búsqueda y un reporte general de alumnos en Excel.
