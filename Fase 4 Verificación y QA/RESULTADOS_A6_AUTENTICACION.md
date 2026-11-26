# Resultados A6 — Bloqueo de login y cierre de sesión por inactividad

**Fecha:** 26 de noviembre de 2026  
**Alcance:** `sgma/web.py` y `Fase 4 Verificación y QA/pruebas/test_web_permisos_y_plantillas.py`.

## Cambios realizados

| Requisito A6 (`D5`) | Implementación |
|---|---|
| Bloqueo tras 5 intentos fallidos | En `POST /login`, `app.extensions["intentos_login"]` contabiliza fallos por usuario (`MAX_INTENTOS_LOGIN = 5`). Al alcanzar el 5.º fallo, bloquea el acceso por 15 minutos (`DURACION_BLOQUEO_LOGIN_SEGUNDOS = 900`) y responde `429` incluso ante credenciales correctas hasta que expire el bloqueo. Un login exitoso limpia el contador. |
| Cierre de sesión por 30 minutos de inactividad | `PERMANENT_SESSION_LIFETIME` se ajustó a `30` minutos (`INACTIVIDAD_SESION_SEGUNDOS = 1800`) y `@app.before_request` (`cargar_usuario`) verifica `session["ultima_actividad"]`: si supera los 30 minutos limpia la sesión y fuerza reautenticación; si sigue vigente actualiza la marca de tiempo. |

## Verificación

- **Suite unitaria:** `Ran 25 tests in 3.741s — OK`, incluyendo `test_login_se_bloquea_tras_cinco_intentos_fallidos` y `test_sesion_expira_tras_30_minutos_de_inactividad`.
