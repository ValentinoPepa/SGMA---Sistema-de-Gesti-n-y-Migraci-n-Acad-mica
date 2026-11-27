# B1 — Recorrido del panel contra la base real

**Fecha:** 26/11/2026  
**Base:** `gestion_academica_v2`  
**Motor:** MariaDB 10.4.32, puerto 3306  
**Método:** servidor WSGI local en `127.0.0.1` y solicitudes HTTP reales; no se usó Flask `test_client` ni cursores simulados.

## Recorrido por rol

Los tres usuarios temporales iniciaron sesión por el formulario real. Se recorrieron las páginas comunes (`/`, `/alumnos`, `/carreras`, `/materias`, `/ciclos`, `/cursadas`, `/asistencias`, `/busqueda`) y las páginas con permisos diferenciados.

| Rol | `/docentes` | `/usuarios` | `/cargas` | POST de alumno | Resultado |
|---|---:|---:|---:|---:|---|
| ADMIN | 200 | 200 | 200 | 403 | Conforme |
| PRECEPTOR | 200 | 403 | 200 | — | Conforme |
| DOCENTE | 403 | 403 | 403 | — | Conforme |

Las ocho páginas comunes devolvieron HTTP 200 para los tres roles. En la vista DOCENTE no aparecieron los campos DNI ni E-mail. El ADMIN recibió HTTP 403 al intentar enviar un POST académico.

## Auditoría y datos de prueba

Como ADMIN temporal se desactivó una cuenta PRECEPTOR temporal desde `/usuarios`. El trigger guardó el evento con el `id_usuario` del ADMIN autenticado, confirmando que la aplicación fija `@app_user_id` durante la solicitud.

La base tenía 190 eventos de auditoría antes del recorrido y 202 después: los 12 eventos corresponden a creación y desactivación de cuentas sintéticas de las dos ejecuciones que llegaron a preparar fixtures. La primera ejecución se interrumpió en la inicialización del cliente HTTP; la segunda completó el recorrido sin fallas. En ambos casos las fixtures se desactivaron. No se añadieron alumnos ni actas: los conteos permanecen en 80 y 189. Verificación final: seis cuentas temporales y dos perfiles docentes de prueba están inactivos.

## Resultado y alcance

**B1: 0 fallas de acceso en el recorrido HTTP.** Las sesiones, páginas, restricciones por rol y la identidad de auditoría respondieron según lo esperado. No había asignaciones docentes activas en la base; por eso el recorrido DOCENTE confirmó pantallas con datos vacíos y ausencia de DNI/correo, pero no cubrió una materia asignada. La prueba cubrió respuestas del panel en HTTP local, no la presentación visual de cada pantalla en el navegador.

Script reproducible: `pruebas/test_b1_panel_base_real.py`. Las cuentas temporales quedan inactivas al terminar.
