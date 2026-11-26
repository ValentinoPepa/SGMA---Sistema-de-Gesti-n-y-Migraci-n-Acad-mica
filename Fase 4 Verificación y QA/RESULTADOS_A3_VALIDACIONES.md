# Resultados A3 — Alineación de validaciones con Diccionario v1.2

**Fecha:** 26 de noviembre de 2026  
**Alcance:** `sgma/validaciones.py`, `sgma/etl.py`, `sgma/web.py` y pruebas unitarias en `Fase 4 Verificación y QA/pruebas/`.

## Cambios realizados

| Requisito A3 | Situación anterior | Ajuste aplicado | Estado |
|---|---|---|---|
| Códigos `ERR_10`, `ERR_11` y `ERR_12` (sin `"VALIDACION"` genérico) | DNI vacío/no numérico, nombres vacíos/`>50` chars/sin coma, libro-folio, condición desconocida, año de ingreso/ciclo inválido y filas incompletas/duplicadas emitían `codigo=None` o `"VALIDACION"`. | Se asignaron `ERR_10_DNI_INVALID` (DNI obligatorio o no numérico), `ERR_11_NOMBRE_INVALID` (nombre/apellido vacío, `>50` caracteres o formato inválido) y `ERR_12_DATO_INVALID` (datos/formato de registro inválidos en ETL y carga masiva web). | Alineado |
| Nombres con partículas (`"de la"`) | `normalizar_nombre` aplicaba `texto.title()`, capitalizando partículas como `"De La Cruz"` o `"Del Carmen"`. | Se reemplazó por `_capitalizar_nombre_propio`, manteniendo en minúscula las partículas (`de`, `del`, `la`, `las`, `los`, `y`, `e`, `da`, `das`, `do`, `dos`) cuando no inician el campo (ej. `"Pérez de la Cruz"`, `"María del Carmen"`, `"De la Torre"`). | Alineado |
| No alterar mayúsculas de las carreras | `etl.transformar_plan` aplicaba `.title()` sobre `Nom_Carrera`, alterando siglas y mayúsculas originales. | Se eliminó `.title()` en `Nom_Carrera`, conservando el texto tal como viene en la fuente tras normalizar espacios. | Alineado |

## Verificación

Se ejecutó la suite automatizada completa (`test_validaciones.py`, `test_etl_fuentes.py`, `test_web_permisos_y_plantillas.py`):

- **Resultado:** `Ran 18 tests in 0.374s — OK`
- Se verificaron explícitamente `ERR_10_DNI_INVALID`, `ERR_11_NOMBRE_INVALID`, `ERR_12_DATO_INVALID`, la ausencia de `\tVALIDACION\t` en logs de carga masiva, nombres con partículas (`"Pérez de la Cruz"`, `"María del Carmen"`, `"De la Torre"`) y la preservación de mayúsculas en carreras (`"Tecnicatura en Desarrollo de Software (TSDS)"`).
