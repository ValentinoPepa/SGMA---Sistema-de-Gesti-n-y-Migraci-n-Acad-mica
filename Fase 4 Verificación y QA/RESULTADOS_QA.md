# Resultados de QA del SGMA

## Pruebas automatizadas de la aplicación

La suite automatizada de 25 pruebas cubre validaciones, normalización de fuentes legadas, referencias de actas, control de acceso por rol, desacoplamiento de planillas legadas, carga masiva y seguridad de sesión/login. Las rutas web se probaron con conexiones simuladas; esto no equivale a una prueba de integración contra una base real.

## Verificación del esquema y restricciones

La evidencia de C5 registra **26/26 pruebas SQL aprobadas** en MySQL 8.4.13: 19 tablas, 14 triggers, 3 procedimientos, 25 claves foráneas, 10 restricciones `CHECK`, 15 restricciones `UNIQUE`, rechazos esperados ante datos inválidos, asignación y sincronización de legajos y eventos de auditoría. Las pruebas de permisos P1 a P8 también se ejecutaron en ese servidor: las operaciones prohibidas para `sgma_app` devuelven error 1142; los triggers pueden escribir auditoría y conservar el identificador del usuario.

## Migración y rendimiento

La carga inicial registrada en C3 produjo 80 alumnos, 2 carreras, 24 materias y 189 actas; el lote informó 204 filas de origen, 189 correctas y 15 con error. Los conteos describen la carga efectivamente realizada en MariaDB 10.4.32.

El ensayo C4 de rendimiento y concurrencia está documentado en [RESULTADOS_C4_RENDIMIENTO_CONCURRENCIA.md](RESULTADOS_C4_RENDIMIENTO_CONCURRENCIA.md). Se ejecutó en MariaDB 10.4.32. Al contrastarlo con el SRS v1.2 recibido, las pruebas resultan parciales frente a RNF-01, RNF-02, RNF-10 y RNF-11; el informe detalla qué escenarios faltan. No se presentan como certificación de producción.

## Alcance y evidencia

- [Informe C5 de calidad e integridad](INFORME_C5_CALIDAD_INTEGRIDAD.md), con capturas de resultados.
- [Resultados C4 de rendimiento y concurrencia](RESULTADOS_C4_RENDIMIENTO_CONCURRENCIA.md).
- [Manual de usuario](../Fase%205%20Despliegue%20y%20Mantenimiento/MANUAL_DE_USUARIO.md) y [guía de operación](../Fase%205%20Despliegue%20y%20Mantenimiento/OPERACION_Y_RESPALDOS.md).

Los resultados corresponden a los motores, versiones, volúmenes y procedimientos indicados en cada evidencia. No se extrapolan automáticamente a un servidor productivo.

## Trazabilidad ETL A2

La carga A2, sus tres lotes, la identidad ADMIN de auditoria y el ensayo de rollback estan verificados en [RESULTADOS_A2_ETL.md](RESULTADOS_A2_ETL.md).


## Alineación de validaciones A3

La alineación con el Diccionario v1.2 (`ERR_10_DNI_INVALID`, `ERR_11_NOMBRE_INVALID`, `ERR_12_DATO_INVALID`, partículas en nombres y preservación de mayúsculas en carreras) está verificada en [RESULTADOS_A3_VALIDACIONES.md](RESULTADOS_A3_VALIDACIONES.md).


## Desacoplamiento A4

El arranque independiente del panel web y del ETL sin la carpeta de planillas legadas ni la estructura de fases está verificado en [RESULTADOS_A4_DESACOPLAMIENTO.md](RESULTADOS_A4_DESACOPLAMIENTO.md).


## Carga masiva A5

La vista previa con confirmación, la carga opcional de `carrera`/`anio_ingreso` y el límite de 5.000 filas están verificados en [RESULTADOS_A5_CARGA_MASIVA.md](RESULTADOS_A5_CARGA_MASIVA.md).


## Autenticación y sesión A6

El bloqueo tras 5 intentos fallidos y el cierre de sesión tras 30 minutos de inactividad están verificados en [RESULTADOS_A6_AUTENTICACION.md](RESULTADOS_A6_AUTENTICACION.md).


## Permisos por rol A7

La matriz de acceso por rol y el alcance de datos del DOCENTE están documentados en [RESULTADOS_A7_PERMISOS.md](RESULTADOS_A7_PERMISOS.md). La ruta de registro de actas también exige que la mesa pertenezca a la materia y ciclo asignados al docente.
