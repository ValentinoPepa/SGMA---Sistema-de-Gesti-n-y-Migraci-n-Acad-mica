# Resultados de QA de SGMA v1.1

Última revisión local: 16 de noviembre de 2026.

## Pruebas automatizadas

Ejecución desde `Fase 3 Implementación y Desarrollo/codigo`:

```powershell
python -m unittest discover -s "../../Fase 4 Verificación y QA/pruebas" -v
```

Resultado actual: **20 pruebas aprobadas**. Cubren normalización y validación de datos, preparación ETL, permisos por rol, carga de planillas, lectura del legajo devuelto por MySQL Connector como diccionario, renderizado del detalle de asistencias y los accesos del inicio.

Las rutas web se prueban con conexiones simuladas. Estas pruebas no sustituyen la integración contra una instancia MySQL aislada.

## Ensayo ETL con las fuentes locales v1.1

Comando ejecutado en modo de solo lectura (`--dry-run`), con el log guardado fuera del repositorio:

```powershell
python -m sgma.etl --dry-run --log "$env:TEMP\sgma-qa-dry-run.log"
```

| Resultado preparado | Cantidad |
| --- | ---: |
| Alumnos | 80 |
| Carreras | 2 |
| Materias | 24 |
| Actas | 189 |
| Registros reportados para revisión | 25 |

El ensayo no se conectó a MySQL y no escribió registros. Las 25 observaciones agregadas, sin valores personales, fueron: 1 materia duplicada; 3 DNI duplicados; 2 fechas de nacimiento inválidas; 4 correos inválidos; 4 referencias de alumno y 4 de materia no encontradas en actas; 4 fechas de examen inválidas; y 3 notas/condiciones inválidas.

Los archivos fuente contienen información personal. Permanecen fuera del repositorio Git; el `.gitignore` excluye las planillas de alumnos, actas y claves de errores. El log generado contiene archivo, fila, campo, código y mensaje, no los valores personales de las filas.

## Ensayo de rendimiento ETL sintético

Se ejecutó `pruebas/benchmark_etl_sintetico.py` con 50.000 alumnos y 50.000 actas ficticias. El parseo y la transformación terminaron en **59,07 segundos** en esta PC; se generaron 50.000 alumnos y 50.000 actas válidas, sin errores. El ensayo no usó datos personales.

Esto valida solo el parseo y la transformación local, no la inserción transaccional en MySQL. El requisito histórico RNF-02 indica procesar 50.000 registros en menos de 10 minutos; el tiempo integral de migración debe medirse contra una base de QA en el servidor destino.

## Revisión estática del DDL

Conteos calculados sobre `Fase 2 Diseño y Base de Datos/gestion_academica.sql`:

- 19 tablas.
- 25 declaraciones de clave foránea.
- 10 restricciones `CHECK`.
- 15 restricciones `UNIQUE`.
- 14 triggers y 3 procedimientos almacenados.

La inspección confirma que esas declaraciones están escritas en el DDL; no demuestra que el motor instalado las haya creado o esté aplicando correctamente.

## Respaldo MySQL en Windows

El 16 de noviembre de 2026 quedó configurada en esta PC la tarea `SGMA MySQL Daily Backup`, diaria a las 02:00 (hora local), con inicio al volver a estar disponible, retención de 30 días y destino `%LOCALAPPDATA%\SGMA\backups`. La tarea se ejecutó correctamente (`LastTaskResult = 0`) y generó un dump comprimido de 5.335 bytes. Se leyó completamente el flujo gzip de la copia (41.452 bytes descomprimidos), sin errores.

Las credenciales de respaldo están en `%LOCALAPPDATA%\SGMA\secrets\backup.cnf`, fuera del repo y con ACL restringida; MySQL usa la cuenta dedicada `sgma_backup`. El único destino está en esta PC. La integridad gzip no prueba que el dump pueda restaurarse; esa comprobación sigue pendiente.

## Alcance pendiente para cerrar QA

- Ejecutar pruebas de integridad referencial y restricciones en una base MySQL de QA aislada.
- Ejecutar la migración completa y pruebas de concurrencia contra MySQL, midiendo RNF-01, RNF-02 y los RNF-10/11 definidos por la línea base vigente. Está disponible el informe aprobado v1.0 y el mapeo v1.1; no se encontró el SRS v1.1 aprobado.
- Ejecutar la migración inicial autorizada y reconciliar los datos migrados con las fuentes originales. La base `gestion_academica` conserva sus datos de demostración: la ejecución `--apply` no llegó a realizarse.
- Restaurar el backup reciente en una base aislada y registrar los conteos y el resultado.

No se deben cerrar estas comprobaciones usando solo pruebas unitarias, conteos estáticos o datos de demostración.
