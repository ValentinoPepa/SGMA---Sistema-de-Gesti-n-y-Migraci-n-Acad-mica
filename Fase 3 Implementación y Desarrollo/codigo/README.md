# Código SGMA

Implementación Python del proyecto, alineada con los artefactos de `v1.1`.

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

## Aplicar la migración

Ejecutar primero `../../Fase 2 Diseño y Base de Datos/gestion_academica.sql`
en MySQL 8.0.16 o superior. Luego
configurar `SGMA_DB_HOST`, `SGMA_DB_USER` y `SGMA_DB_PASSWORD`; opcionalmente,
`SGMA_DB_PORT` (predeterminado `3306`) y `SGMA_DB_NAME` (predeterminado
`gestion_academica`). Con esas variables, aplicar explícitamente:

```powershell
python -m sgma.etl --apply
```

La escritura se hace en una transacción. Si ya existe un lote de migración de
`Actas_Historicas.csv`, el proceso se detiene para evitar duplicar actas. El log
registra archivo, fila, campo, código y mensaje; omite valores personales de las
planillas.

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

El porcentaje de asistencia usa `asistencia_minima` en la tabla `parametros`.
Las clases `JUSTIFICADO` se excluyen del denominador, según la regla acordada.

El rol ADMIN, PRECEPTOR o DIRECTIVO puede descargar analíticos individuales en
PDF/Excel desde la búsqueda y un reporte general de alumnos en Excel.
