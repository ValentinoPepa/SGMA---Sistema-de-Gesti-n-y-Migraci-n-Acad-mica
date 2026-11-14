# SGMA — Versión 1.1

Esta carpeta reúne la documentación y la implementación de la versión 1.1 del Sistema de Gestión y Migración Académica. Las carpetas siguen las fases del proyecto; las planillas originales permanecen en esta carpeta para uso local y no deben subirse al repositorio público si contienen datos personales.

## Estructura

| Fase | Contenido |
| --- | --- |
| [Fase 1 — Análisis y Diagnóstico](Fase%201_%20An%C3%A1lisis%20y%20Diagn%C3%B3stico/) | Requisitos, diagnóstico y mapeo de datos legados. |
| [Fase 2 — Diseño y Base de Datos](Fase%202%20Dise%C3%B1o%20y%20Base%20de%20Datos/) | DDL MySQL, diagramas, arquitectura y plantillas de carga. |
| [Fase 3 — Implementación y Desarrollo](Fase%203%20Implementaci%C3%B3n%20y%20Desarrollo/) | Aplicación Python/Flask y ETL. El punto de entrada es [`codigo/README.md`](Fase%203%20Implementaci%C3%B3n%20y%20Desarrollo/codigo/README.md). |
| [Fase 4 — Verificación y QA](Fase%204%20Verificaci%C3%B3n%20y%20QA/) | Pruebas automatizadas y resultados de QA. |
| [Fase 5 — Despliegue y Mantenimiento](Fase%205%20Despliegue%20y%20Mantenimiento/) | Manual de usuario, despliegue, respaldo y restauración. |

## Empezar

Instalar las dependencias indicadas en `Fase 3 Implementación y Desarrollo/codigo/requirements.txt`, configurar MySQL y las variables `SGMA_DB_*` y `SGMA_SECRET_KEY`, y seguir el README de Fase 3. El ETL inicia en modo de ensayo; la escritura requiere `--apply` explícito.

Las pruebas se ejecutan desde la carpeta del código con:

```powershell
python -m unittest discover -s "../../Fase 4 Verificación y QA/pruebas" -v
```

## Datos de origen

`Alumnos_2026_Final.xlsx`, `Actas_Historicas.csv` y `Clave_Errores_Inyectados.xlsx` son entradas de trabajo locales. No publicarlos en un repositorio público. El ensayo local produjo 80 alumnos, 2 carreras, 24 materias y 189 actas preparadas; registró 25 filas con errores, sin escribir en MySQL.
