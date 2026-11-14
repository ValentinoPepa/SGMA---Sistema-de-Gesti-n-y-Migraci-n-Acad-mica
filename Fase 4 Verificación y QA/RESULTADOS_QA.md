# Resultados de QA de v1.1

## Pruebas automatizadas

Ejecución local desde `Fase 3 Implementación y Desarrollo/codigo`:

```powershell
python -m unittest discover -s "../../Fase 4 Verificación y QA/pruebas" -v
```

Resultado: 17 pruebas aprobadas. Cubren validaciones, normalización de fuentes legadas, referencias de actas, control de acceso por rol y validaciones de carga masiva. Las rutas del panel se verificaron con conexiones simuladas; no se conectaron a una base real.

## Revisión estática del DDL

El archivo `Fase 2 Diseño y Base de Datos/gestion_academica.sql` contiene 19 tablas, 25 declaraciones `FOREIGN KEY`, 10 restricciones `CHECK` con prefijo `chk_` y 14 restricciones `UNIQUE` con prefijo `uq_`. Esto confirma que las restricciones están declaradas en el script; no reemplaza su ejecución y prueba en MySQL.

## Ensayo ETL

En modo `--dry-run`: 80 alumnos, 2 carreras, 24 materias y 189 actas preparadas; 25 errores registrados en un log temporal. No se escribieron datos en MySQL.

## Pendiente de entorno

La prueba real de integridad referencial, la auditoría posterior a la migración, el rendimiento y concurrencia requieren instalar el DDL en un servidor MySQL y trabajar sobre una base de QA con datos de prueba. No se debe cerrar la QA de base de datos basándose solo en esta revisión estática.
