-- =====================================================================
-- SGMA - Pruebas de permisos de la cuenta de la aplicación (sgma_app)
-- Plan de pruebas: sección 10 del Documento Técnico, pruebas 8 y 11, más la
-- comprobación de que los triggers escriben en auditoria aunque sgma_app no pueda.
--
-- Cómo ejecutarlo, CONECTADO COMO sgma_app (no como administrador):
--     mysql -u sgma_app -p -t --force gestion_academica < pruebas_permisos_sgma_app.sql
-- La opción --force hace que siga después de los errores, que acá son esperados.
--
-- Cada paso imprime un título con lo que se espera. Revise que el resultado
-- coincida. Los pasos marcados "ERROR 1142" deben fallar con ese error.
--
-- Importante: la parte final DEJA DATOS GUARDADOS. Ejecutar solo en una base de
-- prueba. Para limpiar: DROP DATABASE gestion_academica; y volver a crear el esquema.
-- =====================================================================

SELECT 'P1: SELECT permitido. Esperado: devuelve un número' AS paso;
SELECT COUNT(*) AS alumnos FROM alumnos;

SELECT 'P2: DELETE sobre registros académicos. Esperado: ERROR 1142 (comando denegado)' AS paso;
DELETE FROM actas_examen WHERE id_acta = 0;

SELECT 'P3: INSERT directo en auditoria. Esperado: ERROR 1142' AS paso;
INSERT INTO auditoria (tabla, operacion, id_registro) VALUES ('prueba', 'INSERT', 1);

SELECT 'P4: UPDATE directo en auditoria. Esperado: ERROR 1142' AS paso;
UPDATE auditoria SET tabla = 'x' WHERE id_evento = 0;

SELECT 'P5: DDL (crear una tabla). Esperado: ERROR 1142' AS paso;
CREATE TABLE zz_prueba (a INT);

SELECT 'P6: DELETE sobre correlatividades (configuración). Esperado: sin error' AS paso;
DELETE FROM correlatividades WHERE id_materia = 0;

SELECT 'P7: sp_proximo_legajo ejecutable. Esperado: devuelve un legajo' AS paso;
CALL sp_proximo_legajo(@legajo);
SELECT @legajo AS legajo_asignado;

-- ---------------------------------------------------------------------
-- P8: la auditoría se escribe aunque sgma_app NO tenga permiso sobre la tabla.
-- Los triggers se ejecutan con los privilegios de quien los creó (el administrador).
-- ---------------------------------------------------------------------
INSERT INTO carreras (nombre) VALUES ('Carrera permisos');
SELECT id_carrera INTO @c FROM carreras WHERE nombre = 'Carrera permisos';
INSERT INTO materias (id_carrera, codigo, nombre, anio_nivel) VALUES (@c, 'PRM101', 'Materia permisos', 1);
SELECT id_materia INTO @m FROM materias WHERE codigo = 'PRM101';

INSERT INTO usuarios (username, password_hash, id_rol)
VALUES ('usuario_permisos', 'x', (SELECT id_rol FROM roles WHERE nombre = 'PRECEPTOR'));
SELECT id_usuario INTO @u FROM usuarios WHERE username = 'usuario_permisos';
SET @app_user_id = @u;

CALL sp_proximo_legajo(@l);
INSERT INTO alumnos (legajo, dni, nombre, apellido) VALUES (@l, '40555666', 'Pa', 'Permisos');
SELECT id_alumno INTO @a FROM alumnos WHERE dni = '40555666';

INSERT INTO actas_examen (id_alumno, id_materia, fecha_examen, libro, folio, nota, estado)
VALUES (@a, @m, '2099-07-10', 'LP', 'FP', 6, 'APROBADO');
SELECT id_acta INTO @acta FROM actas_examen WHERE id_alumno = @a AND libro = 'LP';
UPDATE actas_examen SET nota = 9 WHERE id_acta = @acta;

SELECT 'P8: auditoría escrita por los triggers. Esperado: 2 filas (INSERT y UPDATE de nota 6.00 a 9.00) con es_el_usuario = 1' AS paso;
SELECT operacion, campo, valor_anterior, valor_nuevo, (id_usuario = @u) AS es_el_usuario
  FROM auditoria
 WHERE tabla = 'actas_examen' AND id_registro = @acta
 ORDER BY id_evento;
