# Manual de usuario del SGMA

**Actualizado:** pantallas y permisos B2 a B6.

## 1. Ingreso

El administrador habilita la aplicación y entrega a cada integrante un usuario y una contraseña individual. Abrir la dirección del panel en el navegador e iniciar sesión. Al terminar, usar **Cerrar sesión** y no compartir credenciales.

La primera cuenta ADMIN se crea una sola vez en `/setup`, antes de operar el sistema. La ruta se bloquea automáticamente después del alta inicial.

El panel valida los permisos en el servidor. Si un rol no puede realizar una acción, la pantalla no ofrece el control y el servidor rechaza el intento directo con acceso denegado.

## 2. Permisos por rol

| Rol | Consulta | Puede modificar |
| --- | --- | --- |
| **ADMIN** | Consulta alumnos, carreras, materias, docentes, ciclos, cursadas, asistencia, correlatividades, asignaciones, matrículas y reportes. | Administra cuentas de usuario y roles; no modifica datos académicos. |
| **PRECEPTOR** | Acceso a las pantallas de gestión y consulta. | Mantiene alumnos (alta, edición y baja); crea carreras, materias, docentes y ciclos; define correlatividades, asignaciones y matrículas; gestiona inscripciones y mesas; carga notas, actas y asistencia; corrige notas y actas y anula inscripciones, notas y actas. Gestiona cargas masivas. |
| **DIRECTIVO** | Consulta información académica y reportes; descarga analíticos e informes. | No modifica datos académicos, usuarios ni cargas masivas. |
| **DOCENTE** | Consulta materias y ciclos; ve cursadas asignadas y sus alumnos. En alumnos solo ve legajo, apellido y nombre. | Carga notas de cursada, actas y asistencia solo en la materia y ciclo asignados. No corrige ni anula registros y no abre reportes generales. |

## 3. Pantallas de gestión

### Alumnos y matrículas

- **Alumnos:** PRECEPTOR crea, edita y da de baja alumnos. ADMIN y DIRECTIVO consultan. DOCENTE solo ve alumnos de sus cursadas asignadas y solo los datos permitidos en la tabla.
- **Matrículas:** PRECEPTOR matricula al alumno en una carrera e indica el año de ingreso. ADMIN y DIRECTIVO consultan el listado. No se permite repetir el mismo vínculo alumno-carrera.

### Carreras, materias y ciclos

PRECEPTOR crea carreras, materias y ciclos lectivos. ADMIN, DIRECTIVO y DOCENTE consultan estas pantallas. Para crear un ciclo, se indican el año y las fechas.

### Correlatividades

En **Correlatividades**, PRECEPTOR define la materia requerida para cursar otra. ADMIN y DIRECTIVO consultan las reglas. Al inscribir a una cursada o a un examen, el sistema comprueba las correlatividades aprobadas y bloquea la inscripción si faltan requisitos.

### Asignaciones de docentes

En **Asignaciones**, PRECEPTOR vincula un docente con una materia y un ciclo. ADMIN y DIRECTIVO consultan. La asignación delimita las cursadas, notas, actas y asistencias que puede operar DOCENTE; asignar una materia en otro ciclo no habilita el ciclo actual.

## 4. Cursadas, notas y actas

En **Cursadas y actas**, PRECEPTOR inscribe alumnos en cursadas y mesas, crea mesas de examen, carga notas y registra actas. DOCENTE carga notas de cursada y actas solo dentro de sus asignaciones. ADMIN y DIRECTIVO consultan.

Los controles de corrección y anulación aparecen solo para PRECEPTOR:

- Puede corregir notas de cursada y los campos de un acta: fecha, libro, folio, nota y estado.
- Puede anular una inscripción, una nota o un acta. La anulación es lógica: el registro permanece en la base con `activo = FALSE` y queda auditado; no se borra físicamente desde el panel.
- DOCENTE carga actas, pero no puede corregirlas ni anularlas. ADMIN y DIRECTIVO tampoco pueden modificarlas.

Si el estado del acta es `AUSENTE`, la nota debe quedar vacía. Para `APROBADO` o `DESAPROBADO`, se informa una nota numérica entre 1 y 10.

## 5. Asistencias

En **Asistencias**, PRECEPTOR y DOCENTE registran asistencia. DOCENTE solo puede hacerlo para cursadas de sus materias y ciclos asignados. ADMIN y DIRECTIVO consultan.

El porcentaje es `PRESENTE / (PRESENTE + AUSENTE) x 100`, redondeado a un decimal. Las clases `JUSTIFICADO` se muestran por separado y se excluyen del numerador y del denominador. Si no hay clases `PRESENTE` o `AUSENTE`, el porcentaje queda sin informar. El umbral se configura en `parametros.asistencia_minima`; el valor semilla actual de 75 % es provisorio hasta confirmación institucional.

## 6. Promedios y reportes

En **Búsqueda**, ingresar DNI o legajo para consultar el registro. DOCENTE busca por legajo y solo accede a alumnos de sus cursadas asignadas. ADMIN, PRECEPTOR y DIRECTIVO pueden descargar el analítico individual en PDF o Excel.

El analítico muestra promedios separados:

- **Promedio de exámenes con aplazos:** todas las actas activas con nota numérica.
- **Promedio de exámenes sin aplazos:** solo actas activas con estado `APROBADO`.
- **Promedio de cursada:** notas activas de cursada.

Las actas `AUSENTE` no tienen nota numérica y no entran en los promedios de examen. El promedio combinado se muestra como dato separado.

En **Reportes**, disponible para ADMIN, PRECEPTOR y DIRECTIVO:

1. **Listado de actas:** muestra actas activas con alumno, carrera, materia, ciclo, fecha, nota, estado y libro/folio. Se puede filtrar por materia y ciclo. La pantalla muestra hasta 1000 filas; los resultados completos pueden descargarse en PDF o Excel.
2. **Asistencia por materia y ciclo:** resume alumnos, presentes, ausentes, justificadas y porcentaje agregado. Las justificadas se excluyen del denominador. El listado puede descargarse en PDF o Excel.
3. **Reporte Excel de alumnos:** incluye los promedios y el porcentaje de asistencia general.

Los reportes y analíticos contienen datos académicos personales; descargarlos y compartirlos solo con personas autorizadas.

## 7. Cargas masivas

ADMIN y PRECEPTOR pueden abrir **Cargas**, descargar una plantilla y conservar sus encabezados. Completar las filas sin cambiar los nombres ni el orden de columnas, guardar como `.xlsx`, seleccionar el tipo de carga y enviar. Revisar el resultado del lote y descargar el log si hubo errores. El log identifica archivo, fila, campo, código y mensaje, y omite los valores personales ingresados.

Plantillas vigentes en `Fase 2 Diseño y Base de Datos`:

- `Plantilla_Alumnos.xlsx`
- `Plantilla_Inscripciones.xlsx`
- `Plantilla_Actas.xlsx`

No reenviar un lote de actas sin comprobar primero si ya fue procesado.

## 8. Ayuda

Ante un acceso denegado, pedir al administrador que confirme el rol y, para DOCENTE, que revise la asignación de materia y ciclo. Ante un error de carga, corregir la fila indicada y volver a procesarla. Para corregir un acta ya registrada, solicitarlo a PRECEPTOR.
