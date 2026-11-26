# Resultados A5 — Carga masiva con vista previa, campos opcionales y límite de filas

**Fecha:** 26 de noviembre de 2026  
**Alcance:** `sgma/web.py`, `sgma/templates/cargas.html` y `Fase 4 Verificación y QA/pruebas/test_web_permisos_y_plantillas.py`.

## Cambios realizados

| Requisito A5 | Implementación |
|---|---|
| Vista previa y confirmación (`RF-CMA-02`) | `POST /cargas` con `accion=previsualizar` valida encabezados y todas las filas en modo lectura (`_validar_fila_carga`), muestra totales (`total`, `ok`, `error`, `sin_matricula` y primeros 20 errores) y guarda un archivo temporal con token CSRF/sesión para ejecutar la inserción al confirmar (`accion=confirmar`) o descartar al cancelar (`accion=cancelar`). |
| `carrera` y `anio_ingreso` opcionales en `Plantilla_Alumnos.xlsx` | Si `carrera` viene vacía, el alumno se inserta en `alumnos` sin generar registro en `matriculas` ni error `ERR_02_FK_NOTFOUND`. Si `carrera` está informada, se valida su existencia y `anio_ingreso` (`1900..2200`). |
| Límite de filas (`D8`) | Se definió `MAX_FILAS_CARGA_MASIVA = 5000`. Los archivos que superan el límite se rechazan antes de abrir `lotes_carga` o insertar filas. |

## Verificación

- **Suite unitaria:** `Ran 23 tests in 0.444s — OK` (con conexiones simuladas en `test_web_permisos_y_plantillas.py`, incluyendo vista previa + confirmación, alumno sin carrera/matrícula y rechazo por límite de filas).
