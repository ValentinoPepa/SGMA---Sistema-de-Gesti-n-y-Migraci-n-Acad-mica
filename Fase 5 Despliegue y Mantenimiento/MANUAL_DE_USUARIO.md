# Manual de usuario del SGMA

## Ingreso

El administrador habilita la aplicación y entrega a cada integrante un usuario y una contraseña individual. Abrir la dirección del panel en el navegador e iniciar sesión. Al terminar, usar **Cerrar sesión**; no compartir credenciales.

La primera cuenta ADMIN se crea una sola vez en `/setup`, antes de operar el sistema. Esa ruta se bloquea automáticamente después del alta inicial.

## Funciones por rol

| Rol | Funciones principales |
| --- | --- |
| ADMIN | Administra usuarios y roles; accede a alumnos, estructura académica, docentes, cursadas, asistencias, cargas y reportes. |
| PRECEPTOR | Gestiona alumnos, estructura académica, docentes, cursadas, asistencias y cargas masivas; consulta y exporta analíticos. |
| DIRECTIVO | Consulta la información académica y descarga analíticos e informes. No administra usuarios ni carga planillas. |
| DOCENTE | Consulta alumnos, materias, ciclos y cursadas; registra información de cursada y asistencia según los permisos de la aplicación. |

El panel aplica los permisos en el servidor. Una operación no habilitada responde con acceso denegado aunque se intente abrir su URL directamente.

## Operaciones frecuentes

1. **Buscar un alumno:** abrir **Búsqueda**, ingresar DNI o legajo y seleccionar el resultado. Desde el detalle se pueden descargar analíticos en PDF o Excel cuando el rol lo permite.
2. **Registrar actividad académica:** usar las secciones de alumnos, carreras, materias, docentes, ciclos, cursadas y asistencias. Completar los datos requeridos y guardar. Las validaciones informan datos incompletos, duplicados o referencias inválidas.
3. **Cargar una planilla:** abrir **Cargas**, descargar la plantilla correspondiente y conservar sus encabezados. Completar filas sin cambiar nombres ni orden de columnas, guardar como `.xlsx`, seleccionar tipo de carga y enviar. Revisar el resultado del lote y descargar el log si hubo errores.
4. **Interpretar asistencia:** el porcentaje se calcula con las clases computables. Las clases `JUSTIFICADO` se excluyen del denominador. El mínimo se configura en `parametros.asistencia_minima`.
5. **Exportar reportes:** desde la búsqueda se descarga el analítico individual; el reporte general de alumnos se descarga en Excel. Los documentos contienen información académica personal y deben compartirse solo con personas autorizadas.

## Plantillas de carga

Las plantillas vigentes están en `Fase 2 Diseño y Base de Datos`:

- `Plantilla_Alumnos.xlsx`
- `Plantilla_Inscripciones.xlsx`
- `Plantilla_Actas.xlsx`

No cambiar los encabezados. Los registros inválidos quedan detallados por archivo, fila, campo, código y mensaje; el log omite los valores personales ingresados.

## Ayuda

Ante un acceso denegado, consultar al administrador para confirmar el rol asignado. Ante un error de validación, corregir la fila indicada y volver a cargarla. No reenviar el mismo lote de actas sin verificar si ya fue procesado.
