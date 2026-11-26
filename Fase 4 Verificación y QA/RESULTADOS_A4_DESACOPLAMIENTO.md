# Resultados A4 — Desacoplamiento de panel y ETL de planillas legadas

**Fecha:** 26 de noviembre de 2026  
**Alcance:** `sgma/rutas.py`, `sgma/web.py`, `sgma/etl.py` y pruebas en `Fase 4 Verificación y QA/pruebas/`.

## Cambios realizados

| Componente | Situación anterior | Ajuste aplicado |
|---|---|---|
| `sgma/rutas.py` | `buscar_carpeta_v11()` lanzaba `FileNotFoundError` si no existían `Fase 2 Diseño y Base de Datos` y `Fase 3 Implementación y Desarrollo`, rompiendo el import de `web.py` y `etl.py`. | Se agregaron `buscar_carpeta_v11_opcional()`, `resolver_carpeta_plantillas()` (soporta `SGMA_PLANTILLAS_DIR`, `sgma/plantillas` o Fase 2 opcional) y `resolver_directorio_fuentes()` (soporta `SGMA_FUENTES_DIR`, raíz opcional o `cwd`). |
| `sgma/web.py` | Llamaba `buscar_carpeta_v11()` al importar y servía `/plantillas/<nombre>` solo desde `Fase 2 Diseño y Base de Datos`. | Usa `resolver_carpeta_plantillas()` sin fallar al arrancar; si no existe archivo en disco, `descargar_plantilla` genera la plantilla `.xlsx` oficial en memoria con `openpyxl`. |
| `sgma/etl.py` | Llamaba `buscar_carpeta_v11()` al importar. | Usa `resolver_directorio_fuentes()`, agrega `--fuentes-dir` en CLI y valida las 3 fuentes al ejecutar `preparar()` / `_totales_fuente()` con mensaje explícito. |

## Verificación

- **Suite unitaria:** `Ran 20 tests in 0.359s — OK` (`test_descarga_plantilla_funciona_sin_carpeta_de_fases` y `test_etl_desacoplado_de_carpeta_de_fases_y_planillas` incluidos).
- **Prueba de humo aislada:** copia de `sgma/` en carpeta temporal sin carpetas de fases ni planillas legadas importó `sgma.web` (`CARPETA_PLANTILLAS: None`) y `sgma.etl` sin errores.
