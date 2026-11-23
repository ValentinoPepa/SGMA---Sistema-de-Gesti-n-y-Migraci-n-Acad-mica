-- =====================================================================
-- SGMA - Pruebas automáticas del esquema
-- Plan de pruebas: "Documento Técnico de Arquitectura de la Base de Datos", sección 10.
--
-- Cómo ejecutarlo (cuenta de administración, con la base ya creada por gestion_academica.sql):
--     mysql -u root -p -t < pruebas_base.sql
--
-- Qué hace:
--   * Crea datos mínimos de prueba y corre las pruebas dentro de UNA transacción
--     que termina en ROLLBACK: no deja datos en la base. (Los contadores
--     AUTO_INCREMENT sí avanzan, y no importa.)
--   * Al final muestra un resumen y una tabla con OK o FALLA por prueba.
--
-- Importante:
--   * Usar MySQL 8.0.16 o superior. En MariaDB (XAMPP) los códigos de error de los
--     CHECK son otros y esas pruebas darán FALLA aunque el esquema esté bien.
--   * El resultado esperado es que TODAS den OK. Si alguna da FALLA, copie la
--     tabla completa del final para analizarla.
--   * NO ejecutar sobre una base con datos reales.
-- =====================================================================

USE gestion_academica;

DROP PROCEDURE IF EXISTS t_esperar_error;
DROP PROCEDURE IF EXISTS t_comparar;
DROP TEMPORARY TABLE IF EXISTS t_res;

-- Tabla de resultados. MEMORY no es transaccional: sobrevive al ROLLBACK.
CREATE TEMPORARY TABLE t_res (
  n INT AUTO_INCREMENT PRIMARY KEY,
  prueba VARCHAR(120) NOT NULL,
  resultado VARCHAR(5) NOT NULL,
  detalle VARCHAR(200) NULL
) ENGINE=MEMORY;

DELIMITER $$

-- Ejecuta una sentencia y comprueba el número de error que devuelve (0 = sin error).
CREATE PROCEDURE t_esperar_error(IN p_prueba VARCHAR(120), IN p_sql TEXT, IN p_errno INT)
BEGIN
  DECLARE v_errno INT DEFAULT 0;
  DECLARE CONTINUE HANDLER FOR SQLEXCEPTION
  BEGIN
    GET DIAGNOSTICS CONDITION 1 v_errno = MYSQL_ERRNO;
  END;
  SET @t_sql = p_sql;
  PREPARE t_stmt FROM @t_sql;
  EXECUTE t_stmt;
  DEALLOCATE PREPARE t_stmt;
  INSERT INTO t_res (prueba, resultado, detalle)
  VALUES (p_prueba, IF(v_errno = p_errno, 'OK', 'FALLA'),
          CONCAT('error obtenido: ', v_errno, ' | esperado: ', p_errno));
END$$

-- Compara un valor obtenido contra el esperado.
CREATE PROCEDURE t_comparar(IN p_prueba VARCHAR(120), IN p_obtenido VARCHAR(100), IN p_esperado VARCHAR(100))
BEGIN
  INSERT INTO t_res (prueba, resultado, detalle)
  VALUES (p_prueba, IF(p_obtenido <=> p_esperado, 'OK', 'FALLA'),
          CONCAT('obtenido: ', IFNULL(p_obtenido, 'NULL'), ' | esperado: ', p_esperado));
END$$

DELIMITER ;

-- =====================================================================
-- A. ESTRUCTURA (no necesita datos)
-- =====================================================================

SELECT COUNT(*) INTO @n FROM information_schema.tables
 WHERE table_schema = 'gestion_academica' AND table_type = 'BASE TABLE';
CALL t_comparar('Esquema: 19 tablas', @n, '19');

SELECT COUNT(*) INTO @n FROM information_schema.triggers
 WHERE trigger_schema = 'gestion_academica';
CALL t_comparar('Esquema: 14 triggers (si da 11, es la versión vieja del SQL)', @n, '14');

SELECT COUNT(*) INTO @n FROM information_schema.routines
 WHERE routine_schema = 'gestion_academica'
   AND routine_name IN ('sp_proximo_legajo', 'sp_sincronizar_legajo', 'sp_auditar');
CALL t_comparar('Esquema: 3 procedimientos', @n, '3');

SELECT COUNT(*) INTO @n FROM information_schema.referential_constraints
 WHERE constraint_schema = 'gestion_academica';
CALL t_comparar('Esquema: 25 claves foráneas', @n, '25');

SELECT COUNT(*) INTO @n FROM information_schema.check_constraints
 WHERE constraint_schema = 'gestion_academica';
CALL t_comparar('Esquema: 10 restricciones CHECK (si da 0, el motor no las aplica)', @n, '10');

SELECT COUNT(*) INTO @n FROM information_schema.table_constraints
 WHERE table_schema = 'gestion_academica' AND constraint_type = 'UNIQUE';
CALL t_comparar('Esquema: 15 restricciones UNIQUE (si da 14, falta la clave de acta y mesa)', @n, '15');

SELECT COUNT(*) INTO @n FROM information_schema.columns
 WHERE table_schema = 'gestion_academica' AND column_name = 'activo'
   AND table_name IN ('inscripciones', 'inscripciones_examen', 'mesas_examen', 'notas_cursada', 'asistencias');
CALL t_comparar('Esquema: columna activo en las 5 tablas (el panel web la necesita)', @n, '5');

-- =====================================================================
-- B. DATOS MÍNIMOS DE PRUEBA (se deshacen al final)
-- =====================================================================

START TRANSACTION;

INSERT INTO carreras (nombre) VALUES ('Carrera de prueba');
SELECT id_carrera INTO @c FROM carreras WHERE nombre = 'Carrera de prueba';

INSERT INTO materias (id_carrera, codigo, nombre, anio_nivel)
VALUES (@c, 'TST101', 'Materia A', 1), (@c, 'TST102', 'Materia B', 1);
SELECT id_materia INTO @m1 FROM materias WHERE codigo = 'TST101';
SELECT id_materia INTO @m2 FROM materias WHERE codigo = 'TST102';

INSERT INTO ciclos_lectivos (anio, fecha_inicio, fecha_fin) VALUES (2099, '2099-03-01', '2099-12-15');
SELECT id_ciclo INTO @ciclo FROM ciclos_lectivos WHERE anio = 2099;

INSERT INTO docentes (nombre, apellido, dni) VALUES ('Doc', 'Prueba', '30111222');
SELECT id_docente INTO @d FROM docentes WHERE dni = '30111222';

INSERT INTO usuarios (username, password_hash, id_rol)
VALUES ('admin_prueba', 'x', (SELECT id_rol FROM roles WHERE nombre = 'ADMIN'));
SELECT id_usuario INTO @u FROM usuarios WHERE username = 'admin_prueba';

-- A partir de acá la auditoría registra a este usuario
SET @app_user_id = @u;

CALL sp_proximo_legajo(@l1);
INSERT INTO alumnos (legajo, dni, nombre, apellido) VALUES (@l1, '40111222', 'Ana', 'Prueba');
SELECT id_alumno INTO @a FROM alumnos WHERE dni = '40111222';

INSERT INTO mesas_examen (id_materia, id_ciclo, fecha, llamado)
VALUES (@m1, @ciclo, '2099-07-10', 1), (@m2, @ciclo, '2099-07-12', 1);
SELECT id_mesa INTO @mesa1 FROM mesas_examen WHERE id_materia = @m1 AND fecha = '2099-07-10';
SELECT id_mesa INTO @mesa2 FROM mesas_examen WHERE id_materia = @m2 AND fecha = '2099-07-12';

INSERT INTO actas_examen (id_alumno, id_materia, fecha_examen, libro, folio, nota, estado)
VALUES (@a, @m1, '2099-07-10', 'L1', 'F1', 6, 'APROBADO');
SELECT id_acta INTO @acta FROM actas_examen WHERE id_alumno = @a AND libro = 'L1' AND folio = 'F1';

INSERT INTO inscripciones (id_alumno, id_materia, id_ciclo) VALUES (@a, @m1, @ciclo);
SELECT id_inscripcion INTO @insc FROM inscripciones WHERE id_alumno = @a AND id_materia = @m1 AND id_ciclo = @ciclo;

INSERT INTO notas_cursada (id_inscripcion, instancia, nota, fecha) VALUES (@insc, 'Parcial 1', 7, '2099-05-01');

-- =====================================================================
-- C. RESTRICCIONES: lo inválido debe rechazarse (y lo válido, aceptarse)
-- =====================================================================

CALL t_esperar_error('CHECK: DNI con letras se rechaza',
  "INSERT INTO alumnos (legajo, dni, nombre, apellido) VALUES (990001, '12A45', 'X', 'Y')", 3819);

CALL t_esperar_error('CHECK: acta AUSENTE con nota se rechaza',
  "INSERT INTO actas_examen (id_alumno, id_materia, fecha_examen, libro, folio, nota, estado) VALUES (@a, @m1, '2099-07-11', 'L1', 'F2', 7, 'AUSENTE')", 3819);

CALL t_esperar_error('CHECK: acta APROBADO sin nota se rechaza',
  "INSERT INTO actas_examen (id_alumno, id_materia, fecha_examen, libro, folio, nota, estado) VALUES (@a, @m1, '2099-07-11', 'L1', 'F2', NULL, 'APROBADO')", 3819);

CALL t_esperar_error('CHECK: nota 11 se rechaza',
  "INSERT INTO actas_examen (id_alumno, id_materia, fecha_examen, libro, folio, nota, estado) VALUES (@a, @m1, '2099-07-11', 'L1', 'F2', 11, 'APROBADO')", 3819);

CALL t_esperar_error('CHECK: una materia no es correlativa de sí misma',
  "INSERT INTO correlatividades VALUES (@m1, @m1)", 3819);

CALL t_esperar_error('UNIQUE: inscripción repetida se rechaza',
  "INSERT INTO inscripciones (id_alumno, id_materia, id_ciclo) VALUES (@a, @m1, @ciclo)", 1062);

CALL t_esperar_error('FK: no se borra una materia con datos asociados',
  "DELETE FROM materias WHERE id_materia = @m1", 1451);

CALL t_esperar_error('Trigger: usuario DOCENTE sin docente se rechaza',
  "INSERT INTO usuarios (username, password_hash, id_rol) VALUES ('doc_sin_docente', 'x', (SELECT id_rol FROM roles WHERE nombre = 'DOCENTE'))", 1644);

CALL t_esperar_error('Trigger: usuario DOCENTE con docente se crea',
  "INSERT INTO usuarios (username, password_hash, id_rol, id_docente) VALUES ('doc_ok', 'x', (SELECT id_rol FROM roles WHERE nombre = 'DOCENTE'), @d)", 0);

CALL t_esperar_error('FK compuesta: acta con la mesa de otra materia se rechaza',
  "INSERT INTO actas_examen (id_alumno, id_materia, id_mesa, fecha_examen, libro, folio, nota, estado) VALUES (@a, @m1, @mesa2, '2099-07-12', 'L1', 'F3', 7, 'APROBADO')", 1452);

CALL t_esperar_error('FK compuesta: acta con su propia mesa se acepta',
  "INSERT INTO actas_examen (id_alumno, id_materia, id_mesa, fecha_examen, libro, folio, nota, estado) VALUES (@a, @m1, @mesa1, '2099-07-10', 'L1', 'F4', 7, 'APROBADO')", 0);

CALL t_esperar_error('FK compuesta: acta sin mesa (migradas) se acepta',
  "INSERT INTO actas_examen (id_alumno, id_materia, id_mesa, fecha_examen, libro, folio, nota, estado) VALUES (@a, @m1, NULL, '2099-07-10', 'L1', 'F5', 7, 'APROBADO')", 0);

-- =====================================================================
-- D. LEGAJOS
-- =====================================================================

CALL sp_proximo_legajo(@x1);
CALL sp_proximo_legajo(@x2);
SET @dif = @x2 - @x1;
CALL t_comparar('Legajos: dos pedidos seguidos son consecutivos', @dif, '1');

CALL sp_sincronizar_legajo();
SELECT valor INTO @v FROM parametros WHERE clave = 'ultimo_legajo';
SELECT MAX(legajo) INTO @mx FROM alumnos;
CALL t_comparar('Legajos: sp_sincronizar_legajo deja el contador en el mayor legajo', @v, @mx);

-- =====================================================================
-- E. AUDITORÍA (registra a la persona de @app_user_id)
-- =====================================================================

SELECT COUNT(*) INTO @n FROM auditoria
 WHERE tabla = 'actas_examen' AND operacion = 'INSERT' AND id_registro = @acta AND id_usuario = @u;
CALL t_comparar('Auditoría: el alta de un acta queda registrada con el usuario', @n, '1');

UPDATE actas_examen SET nota = 8 WHERE id_acta = @acta;
SELECT COUNT(*) INTO @n FROM auditoria
 WHERE tabla = 'actas_examen' AND id_registro = @acta AND campo = 'nota'
   AND valor_anterior = '6.00' AND valor_nuevo = '8.00' AND id_usuario = @u;
CALL t_comparar('Auditoría: el cambio de una nota guarda valor anterior y nuevo', @n, '1');

UPDATE notas_cursada SET activo = FALSE WHERE id_inscripcion = @insc AND instancia = 'Parcial 1';
SELECT COUNT(*) INTO @n FROM auditoria
 WHERE tabla = 'notas_cursada' AND campo = 'activo' AND id_usuario = @u;
CALL t_comparar('Auditoría: la anulación de una nota queda registrada', @n, '1');

UPDATE alumnos SET dni = '40999888' WHERE id_alumno = @a;
SELECT COUNT(*) INTO @n FROM auditoria
 WHERE tabla = 'alumnos' AND campo = 'dni' AND valor_anterior = '40111222'
   AND valor_nuevo = '40999888' AND id_usuario = @u;
CALL t_comparar('Auditoría: el cambio de DNI de un alumno queda registrado', @n, '1');

UPDATE usuarios SET id_rol = (SELECT id_rol FROM roles WHERE nombre = 'PRECEPTOR') WHERE id_usuario = @u;
SELECT COUNT(*) INTO @n FROM auditoria
 WHERE tabla = 'usuarios' AND campo = 'id_rol' AND id_registro = @u AND id_usuario = @u;
CALL t_comparar('Auditoría: el cambio de rol de un usuario queda registrado', @n, '1');

-- =====================================================================
-- F. RESULTADOS (se deshace todo y se muestra el resumen)
-- =====================================================================

ROLLBACK;

SELECT resultado, COUNT(*) AS cantidad FROM t_res GROUP BY resultado;
SELECT n, prueba, resultado, detalle FROM t_res ORDER BY n;

DROP PROCEDURE t_esperar_error;
DROP PROCEDURE t_comparar;
